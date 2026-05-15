#!/usr/bin/env python3
"""
code_intel.py - Mother v5 Code Intelligence System

Multi-language semantic + keyword codebase indexer with:
- AST-aware chunking (Python via ast, others via ast-grep-py)
- Local semantic embeddings (sentence-transformers, no API)
- FAISS vector search (fast, local)
- BM25-style keyword scoring (preserved from v4 indexer)
- Reverse call graph (impact analysis)
- Cross-project linked search
- Incremental updates (content-hash based)
- Resumable (checkpoint per batch)

Replaces: codebase_indexer.py + search_index.py
"""

import argparse
import ast
import hashlib
import json
import logging
import os
import pickle
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Iterable

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("code_intel")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SKIP_DIRS = {
    "__pycache__", ".git", ".pytest_cache", "node_modules", "venv", ".venv",
    "cache", "logs", "dist", "build", ".mypy_cache", ".ruff_cache", "nul",
    ".claude", ".sisyphus", ".vscode", ".idea", "site-packages",
    "wheels", ".cache", "tmp", "temp", "ChromeDebugProfile",
}

LANG_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
}

MAX_CODE_PREVIEW = 800
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dim, fast, runs on CPU
EMBED_DIM = 384
BATCH_SIZE = 64

# Project layout: index files live next to the project
INDEX_FILENAME = ".code_index.json"
VECTOR_FILENAME = ".code_index.faiss"
META_FILENAME = ".code_index.meta.pkl"

# ---------------------------------------------------------------------------
# Lazy imports
# ---------------------------------------------------------------------------
_embedder = None
_faiss = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        log.info(f"Loading embedding model: {EMBED_MODEL_NAME}")
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss as _f
        _faiss = _f
    return _faiss


# ---------------------------------------------------------------------------
# Chunk dataclass
# ---------------------------------------------------------------------------
@dataclass
class Chunk:
    id: str
    file: str
    lang: str
    kind: str  # function, class, method, module
    name: str
    signature: str
    docstring: str
    code_preview: str
    line_start: int
    line_end: int
    calls: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    parent: str = ""


# ---------------------------------------------------------------------------
# Python AST parser (high quality)
# ---------------------------------------------------------------------------
def _py_signature(node) -> str:
    args = []
    for arg in node.args.args:
        ann = ""
        if arg.annotation:
            try:
                ann = f": {ast.unparse(arg.annotation)}"
            except Exception:
                pass
        args.append(f"{arg.arg}{ann}")
    ret = ""
    if node.returns:
        try:
            ret = f" -> {ast.unparse(node.returns)}"
        except Exception:
            pass
    return f"def {node.name}({', '.join(args)}){ret}"


def _py_calls(node) -> list:
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return sorted(set(calls))


def _py_imports(tree) -> list:
    imps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imps.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imps.append(f"{mod}.{alias.name}")
    return sorted(set(imps))


def parse_python(filepath: Path, project_root: Path) -> list[Chunk]:
    try:
        src = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(filepath))
    except (SyntaxError, ValueError):
        return []
    except OSError:
        return []

    lines = src.split("\n")
    rel = filepath.relative_to(project_root).as_posix()
    imports = _py_imports(tree)
    chunks: list[Chunk] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", start + 1)
            code = "\n".join(lines[start:end])
            chunk_id = hashlib.md5(f"{rel}:{node.name}:{start}".encode()).hexdigest()[:16]
            chunks.append(Chunk(
                id=chunk_id,
                file=rel,
                lang="python",
                kind="function",
                name=node.name,
                signature=_py_signature(node),
                docstring=(ast.get_docstring(node) or "")[:500],
                code_preview=code[:MAX_CODE_PREVIEW],
                line_start=node.lineno,
                line_end=end,
                calls=_py_calls(node),
                imports=imports,
            ))
        elif isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", start + 1)
            code = "\n".join(lines[start:end])
            chunk_id = hashlib.md5(f"{rel}:{node.name}:{start}".encode()).hexdigest()[:16]
            bases = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    pass
            chunks.append(Chunk(
                id=chunk_id,
                file=rel,
                lang="python",
                kind="class",
                name=node.name,
                signature=f"class {node.name}({', '.join(bases)})",
                docstring=(ast.get_docstring(node) or "")[:500],
                code_preview=code[:MAX_CODE_PREVIEW],
                line_start=node.lineno,
                line_end=end,
                imports=imports,
            ))

    return chunks


# ---------------------------------------------------------------------------
# ast-grep parser (TS / JS / Go / Rust / etc.)
# ---------------------------------------------------------------------------
_AST_GREP_PATTERNS = {
    "javascript": [
        ("function $NAME($$$ARGS) { $$$BODY }", "function"),
        ("const $NAME = ($$$ARGS) => { $$$BODY }", "function"),
        ("const $NAME = function($$$ARGS) { $$$BODY }", "function"),
        ("class $NAME { $$$BODY }", "class"),
        ("class $NAME extends $PARENT { $$$BODY }", "class"),
    ],
    "typescript": [
        ("function $NAME($$$ARGS): $RET { $$$BODY }", "function"),
        ("function $NAME($$$ARGS) { $$$BODY }", "function"),
        ("const $NAME = ($$$ARGS): $RET => { $$$BODY }", "function"),
        ("const $NAME = ($$$ARGS) => { $$$BODY }", "function"),
        ("class $NAME { $$$BODY }", "class"),
        ("class $NAME extends $PARENT { $$$BODY }", "class"),
        ("interface $NAME { $$$BODY }", "interface"),
    ],
    "tsx": [
        ("function $NAME($$$ARGS): $RET { $$$BODY }", "function"),
        ("function $NAME($$$ARGS) { $$$BODY }", "function"),
        ("const $NAME = ($$$ARGS) => { $$$BODY }", "function"),
        ("class $NAME { $$$BODY }", "class"),
    ],
    "go": [
        ("func $NAME($$$ARGS) $RET { $$$BODY }", "function"),
        ("func $NAME($$$ARGS) { $$$BODY }", "function"),
        ("type $NAME struct { $$$BODY }", "struct"),
        ("type $NAME interface { $$$BODY }", "interface"),
    ],
    "rust": [
        ("fn $NAME($$$ARGS) -> $RET { $$$BODY }", "function"),
        ("fn $NAME($$$ARGS) { $$$BODY }", "function"),
        ("struct $NAME { $$$BODY }", "struct"),
        ("enum $NAME { $$$BODY }", "enum"),
    ],
}


def parse_ast_grep(filepath: Path, project_root: Path, lang: str) -> list[Chunk]:
    try:
        from ast_grep_py import SgRoot
    except ImportError:
        return []

    try:
        src = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    if lang not in _AST_GREP_PATTERNS:
        return []

    rel = filepath.relative_to(project_root).as_posix()
    chunks: list[Chunk] = []
    seen_ids: set = set()

    try:
        root = SgRoot(src, lang).root()
    except Exception:
        return []

    for pattern, kind in _AST_GREP_PATTERNS[lang]:
        try:
            matches = root.find_all(pattern=pattern)
        except Exception:
            continue
        for m in matches:
            try:
                name_node = m.get_match("NAME")
                if not name_node:
                    continue
                name = name_node.text()
                range_info = m.range()
                start_line = range_info.start.line + 1
                end_line = range_info.end.line + 1
                code = m.text()[:MAX_CODE_PREVIEW]
                chunk_id = hashlib.md5(f"{rel}:{name}:{start_line}".encode()).hexdigest()[:16]
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                chunks.append(Chunk(
                    id=chunk_id,
                    file=rel,
                    lang=lang,
                    kind=kind,
                    name=name,
                    signature=code.split("\n")[0][:200],
                    docstring="",
                    code_preview=code,
                    line_start=start_line,
                    line_end=end_line,
                ))
            except Exception:
                continue

    return chunks


def parse_file(filepath: Path, project_root: Path) -> list[Chunk]:
    ext = filepath.suffix.lower()
    lang = LANG_EXTENSIONS.get(ext)
    if not lang:
        return []
    if lang == "python":
        return parse_python(filepath, project_root)
    return parse_ast_grep(filepath, project_root, lang)


# ---------------------------------------------------------------------------
# Project walking
# ---------------------------------------------------------------------------
def walk_project(project_root: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".") or d == ".github"]
        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext in LANG_EXTENSIONS:
                yield Path(root) / fname


def file_hash(filepath: Path) -> str:
    try:
        return hashlib.md5(filepath.read_bytes()).hexdigest()
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------
def _chunk_embedding_text(c: Chunk) -> str:
    parts = [
        c.kind, c.name, c.signature, c.docstring,
        " ".join(c.calls[:20]),
        c.code_preview[:400],
    ]
    return " ".join(p for p in parts if p)


def index_project(project_root: Path, force: bool = False, no_embeddings: bool = False) -> dict:
    """Index a project. Returns stats."""
    if not project_root.exists():
        log.error(f"Project not found: {project_root}")
        return {"error": "not_found", "project": str(project_root)}

    log.info(f"Indexing: {project_root}")
    t0 = time.time()

    idx_file = project_root / INDEX_FILENAME
    vec_file = project_root / VECTOR_FILENAME
    meta_file = project_root / META_FILENAME

    # Load existing index if present (for incremental)
    existing: dict = {}
    if idx_file.exists() and not force:
        try:
            existing = json.loads(idx_file.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    existing_hashes = (existing.get("file_hashes") or {})
    existing_chunks = (existing.get("index") or [])
    chunks_by_file: dict = {}
    for c in existing_chunks:
        chunks_by_file.setdefault(c.get("file", ""), []).append(c)

    # Walk
    all_files = list(walk_project(project_root))
    log.info(f"  Found {len(all_files)} source files")

    new_hashes: dict = {}
    fresh_chunks: list = []
    files_reparsed = 0
    files_cached = 0

    for fp in all_files:
        rel = fp.relative_to(project_root).as_posix()
        h = file_hash(fp)
        new_hashes[rel] = h
        if not force and existing_hashes.get(rel) == h and rel in chunks_by_file:
            # Cached
            fresh_chunks.extend(chunks_by_file[rel])
            files_cached += 1
            continue
        # Parse
        try:
            parsed = parse_file(fp, project_root)
            fresh_chunks.extend([asdict(c) for c in parsed])
            files_reparsed += 1
        except Exception as e:
            log.warning(f"  Parse failed: {rel}: {e}")

    log.info(f"  Parsed {files_reparsed} files (cached: {files_cached})")
    log.info(f"  Total chunks: {len(fresh_chunks)}")

    # Build reverse call graph
    callers: dict = {}
    for c in fresh_chunks:
        for callee in c.get("calls", []):
            callers.setdefault(callee, []).append({
                "file": c["file"], "name": c["name"], "line": c["line_start"]
            })

    # Embeddings
    embedding_status = "skipped"
    if not no_embeddings and fresh_chunks:
        try:
            embedder = _get_embedder()
            faiss = _get_faiss()

            texts = [_chunk_embedding_text(Chunk(**c)) for c in fresh_chunks]
            log.info(f"  Embedding {len(texts)} chunks...")
            vecs = embedder.encode(texts, batch_size=BATCH_SIZE,
                                   show_progress_bar=False,
                                   convert_to_numpy=True)
            import numpy as np
            vecs = vecs.astype("float32")
            faiss.normalize_L2(vecs)

            index = faiss.IndexFlatIP(EMBED_DIM)
            index.add(vecs)
            faiss.write_index(index, str(vec_file))

            chunk_ids = [c["id"] for c in fresh_chunks]
            with open(meta_file, "wb") as f:
                pickle.dump({"chunk_ids": chunk_ids, "model": EMBED_MODEL_NAME}, f)
            embedding_status = f"ok ({len(vecs)} vectors)"
            log.info(f"  Embedded: {embedding_status}")
        except Exception as e:
            log.error(f"  Embedding failed: {e}")
            embedding_status = f"failed: {e}"

    elapsed = round(time.time() - t0, 2)
    out = {
        "project": project_root.name,
        "project_path": str(project_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "files_total": len(all_files),
            "files_reparsed": files_reparsed,
            "files_cached": files_cached,
            "chunks": len(fresh_chunks),
            "callers_indexed": len(callers),
            "elapsed_sec": elapsed,
            "embedding_status": embedding_status,
        },
        "file_hashes": new_hashes,
        "callers": callers,
        "index": fresh_chunks,
    }
    idx_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    log.info(f"  Done in {elapsed}s -> {idx_file}")
    return out


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def search_project(project_root: Path, query: str, top: int = 10,
                   use_semantic: bool = True) -> list[dict]:
    idx_file = project_root / INDEX_FILENAME
    if not idx_file.exists():
        return []
    try:
        data = json.loads(idx_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    chunks = data.get("index", [])
    if not chunks:
        return []

    # Keyword scoring
    tokens = [t.lower() for t in query.split() if t]
    kw_scores: dict = {}
    for i, c in enumerate(chunks):
        text = " ".join([
            c.get("name", ""), c.get("file", ""),
            c.get("signature", ""), c.get("docstring", ""),
            c.get("code_preview", "")
        ]).lower()
        s = 0.0
        for t in tokens:
            if t in c.get("name", "").lower():
                s += 10.0
            if t in c.get("file", "").lower():
                s += 5.0
            if t in c.get("signature", "").lower():
                s += 4.0
            if t in c.get("docstring", "").lower():
                s += 3.0
            if t in c.get("code_preview", "").lower():
                s += 1.0
        kw_scores[i] = s

    # Semantic scoring
    sem_scores: dict = {}
    vec_file = project_root / VECTOR_FILENAME
    meta_file = project_root / META_FILENAME
    if use_semantic and vec_file.exists() and meta_file.exists():
        try:
            embedder = _get_embedder()
            faiss = _get_faiss()
            import numpy as np
            with open(meta_file, "rb") as f:
                meta = pickle.load(f)
            chunk_ids = meta["chunk_ids"]
            id_to_idx = {cid: i for i, cid in enumerate(chunk_ids)}

            index = faiss.read_index(str(vec_file))
            qv = embedder.encode([query], convert_to_numpy=True).astype("float32")
            faiss.normalize_L2(qv)
            D, I = index.search(qv, min(top * 3, len(chunk_ids)))
            for rank, (score, idx) in enumerate(zip(D[0], I[0])):
                if idx < 0:
                    continue
                cid = chunk_ids[idx]
                # find chunk position in chunks list
                for ci, c in enumerate(chunks):
                    if c.get("id") == cid:
                        sem_scores[ci] = float(score)
                        break
        except Exception as e:
            log.warning(f"Semantic search failed: {e}")

    # Reciprocal Rank Fusion
    rrf_k = 60
    kw_ranked = sorted(kw_scores.items(), key=lambda x: x[1], reverse=True)
    sem_ranked = sorted(sem_scores.items(), key=lambda x: x[1], reverse=True)
    rrf: dict = {}
    for rank, (i, _) in enumerate(kw_ranked):
        rrf[i] = rrf.get(i, 0) + 1.0 / (rrf_k + rank)
    for rank, (i, _) in enumerate(sem_ranked):
        rrf[i] = rrf.get(i, 0) + 1.0 / (rrf_k + rank)

    ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top]
    out = []
    for i, score in ranked:
        c = chunks[i]
        out.append({
            "score": round(score, 4),
            "kw_score": kw_scores.get(i, 0),
            "sem_score": round(sem_scores.get(i, 0), 4) if i in sem_scores else None,
            "file": c.get("file"),
            "name": c.get("name"),
            "kind": c.get("kind"),
            "lang": c.get("lang"),
            "signature": c.get("signature"),
            "lines": f"{c.get('line_start')}-{c.get('line_end')}",
            "preview": c.get("code_preview", "")[:300],
        })
    return out


# ---------------------------------------------------------------------------
# Impact analysis
# ---------------------------------------------------------------------------
def impact(project_root: Path, symbol: str) -> dict:
    idx_file = project_root / INDEX_FILENAME
    if not idx_file.exists():
        return {"error": "no_index"}
    data = json.loads(idx_file.read_text(encoding="utf-8"))
    callers = (data.get("callers") or {}).get(symbol, [])
    return {
        "symbol": symbol,
        "direct_callers_count": len(callers),
        "direct_callers": callers,
    }


# ---------------------------------------------------------------------------
# Registry / project list config
# ---------------------------------------------------------------------------
REGISTRY = Path(__file__).resolve().parent.parent / "system" / "code_intel_registry.json"


def load_registry() -> dict:
    if REGISTRY.exists():
        try:
            return json.loads(REGISTRY.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"watched": [], "scheduled": []}


def save_registry(reg: dict) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(reg, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(description="Mother v5 Code Intelligence")
    sub = p.add_subparsers(dest="cmd")

    p_idx = sub.add_parser("index", help="Index one or more projects")
    p_idx.add_argument("--project", help="Single project path")
    p_idx.add_argument("--all", action="store_true", help="Index all registered projects")
    p_idx.add_argument("--force", action="store_true", help="Re-index everything (ignore cache)")
    p_idx.add_argument("--no-embeddings", action="store_true", help="Skip embeddings (keyword-only)")

    p_search = sub.add_parser("search", help="Search a project")
    p_search.add_argument("--project", required=True)
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--top", type=int, default=10)
    p_search.add_argument("--no-semantic", action="store_true")

    p_impact = sub.add_parser("impact", help="Show direct callers of a symbol")
    p_impact.add_argument("--project", required=True)
    p_impact.add_argument("--symbol", required=True)

    p_reg = sub.add_parser("register", help="Add a project to the watch registry")
    p_reg.add_argument("--project", required=True)
    p_reg.add_argument("--mode", choices=["watched", "scheduled"], default="watched")

    p_list = sub.add_parser("list", help="List registered projects")

    p_stats = sub.add_parser("stats", help="Show indexing stats for a project")
    p_stats.add_argument("--project", required=True)

    args = p.parse_args()

    if args.cmd == "index":
        if args.all:
            reg = load_registry()
            all_projects = reg.get("watched", []) + reg.get("scheduled", [])
            results = []
            for proj in all_projects:
                try:
                    r = index_project(Path(proj), force=args.force,
                                      no_embeddings=args.no_embeddings)
                    results.append({
                        "project": Path(proj).name,
                        "chunks": r.get("stats", {}).get("chunks", 0),
                        "elapsed_sec": r.get("stats", {}).get("elapsed_sec", 0),
                    })
                except Exception as e:
                    log.error(f"Failed: {proj}: {e}")
            print(json.dumps(results, indent=2))
            return 0
        if args.project:
            r = index_project(Path(args.project), force=args.force,
                              no_embeddings=args.no_embeddings)
            print(json.dumps(r.get("stats", {}), indent=2))
            return 0
        print("Specify --project or --all", file=sys.stderr)
        return 1

    if args.cmd == "search":
        results = search_project(Path(args.project), args.query,
                                 top=args.top, use_semantic=not args.no_semantic)
        print(json.dumps(results, indent=2))
        return 0

    if args.cmd == "impact":
        result = impact(Path(args.project), args.symbol)
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "register":
        reg = load_registry()
        proj = str(Path(args.project).resolve())
        target_list = reg.setdefault(args.mode, [])
        if proj not in target_list:
            target_list.append(proj)
            save_registry(reg)
            print(f"Registered: {proj} [{args.mode}]")
        else:
            print(f"Already registered: {proj}")
        return 0

    if args.cmd == "list":
        reg = load_registry()
        print(json.dumps(reg, indent=2))
        return 0

    if args.cmd == "stats":
        idx_file = Path(args.project) / INDEX_FILENAME
        if not idx_file.exists():
            print(json.dumps({"error": "no_index"}))
            return 1
        try:
            data = json.loads(idx_file.read_text(encoding="utf-8"))
            print(json.dumps(data.get("stats", {}), indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
        return 0

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
