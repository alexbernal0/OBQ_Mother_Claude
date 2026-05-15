#!/usr/bin/env python3
"""
codebase_indexer.py — OBQ Codebase RAG Indexer
Parses Python projects into searchable function-level chunks.
Saves to local JSON index + optionally pushes to Supermemory.

Usage:
  python codebase_indexer.py --project "C:\path\to\project" --name "ProjectLabel"
  python codebase_indexer.py --project "C:\path\to\project" --name "ProjectLabel" --supermemory
  python codebase_indexer.py --project "C:\path\to\project" --stats-only

Output:
  {project}/.code_index.json  — local searchable index
  Supermemory entries          — if --supermemory flag set
"""

import argparse
import ast
import json
import logging
import os
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("indexer")

# Directories to always skip
SKIP_DIRS = {
    "__pycache__", ".git", ".pytest_cache", "node_modules", "venv", ".venv",
    "cache", "logs", "dist", "build", ".mypy_cache", ".ruff_cache", "nul",
}

# Max chars of code body to store per chunk (keeps index lean)
MAX_CODE_PREVIEW = 800


# ── AST Parsing ───────────────────────────────────────────────────────────────

def _get_source_segment(lines: list[str], node: ast.AST) -> str:
    """Extract source code for an AST node."""
    start = node.lineno - 1
    end = getattr(node, "end_lineno", start + 1)
    return "\n".join(lines[start:end])


def _extract_calls(node: ast.AST) -> list[str]:
    """Find all function calls within a node."""
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return sorted(set(calls))


def _extract_imports(tree: ast.Module) -> list[str]:
    """Get all imports from a module."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
    return sorted(set(imports))


def _get_signature(node: ast.FunctionDef) -> str:
    """Build function signature string."""
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


def parse_file(filepath: Path, project_root: Path) -> list[dict]:
    """Parse a single Python file into function/class chunks."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        lines = source.splitlines()
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        log.debug(f"Parse error in {filepath}: {e}")
        return []

    rel_path = str(filepath.relative_to(project_root)).replace("\\", "/")
    file_imports = _extract_imports(tree)
    chunks = []

    def _process_node(node, parent_class: Optional[str] = None):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            name = f"{parent_class}.{node.name}" if parent_class else node.name
            sig = _get_signature(node)
            docstring = ast.get_docstring(node) or ""
            code = _get_source_segment(lines, node)
            calls = _extract_calls(node)
            line_count = (getattr(node, "end_lineno", node.lineno) - node.lineno) + 1

            chunks.append({
                "file": rel_path,
                "name": name,
                "type": "method" if parent_class else "function",
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "line_count": line_count,
                "signature": sig,
                "docstring": docstring[:300],
                "code_preview": code[:MAX_CODE_PREVIEW],
                "calls": calls[:20],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [
                    ast.unparse(d) if hasattr(ast, "unparse") else ""
                    for d in node.decorator_list
                ],
            })

        elif isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node) or ""
            code = _get_source_segment(lines, node)
            methods = [n.name for n in node.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            bases = []
            for base in node.bases:
                try:
                    bases.append(ast.unparse(base))
                except Exception:
                    pass

            chunks.append({
                "file": rel_path,
                "name": node.name,
                "type": "class",
                "line_start": node.lineno,
                "line_end": getattr(node, "end_lineno", node.lineno),
                "line_count": (getattr(node, "end_lineno", node.lineno) - node.lineno) + 1,
                "signature": f"class {node.name}({', '.join(bases)})",
                "docstring": docstring[:300],
                "code_preview": code[:MAX_CODE_PREVIEW],
                "methods": methods,
                "calls": [],
                "decorators": [],
            })

            # Process methods inside the class
            for child in node.body:
                _process_node(child, parent_class=node.name)

    for node in tree.body:
        _process_node(node)

    # File-level metadata chunk
    module_docstring = ast.get_docstring(tree) or ""
    chunks.insert(0, {
        "file": rel_path,
        "name": "__module__",
        "type": "module",
        "line_start": 1,
        "line_end": len(lines),
        "line_count": len(lines),
        "signature": rel_path,
        "docstring": module_docstring[:300],
        "code_preview": "",
        "imports": file_imports,
        "calls": [],
        "decorators": [],
    })

    return chunks


# ── Project Walker ────────────────────────────────────────────────────────────

def index_project(project_path: str, project_name: str) -> dict:
    """Walk a project, parse all .py files, build full index."""
    root = Path(project_path).resolve()
    if not root.exists():
        log.error(f"Project path does not exist: {root}")
        sys.exit(1)

    all_chunks = []
    file_count = 0
    total_lines = 0

    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            filepath = Path(dirpath) / f
            chunks = parse_file(filepath, root)
            if chunks:
                all_chunks.extend(chunks)
                file_count += 1
                total_lines += chunks[0].get("line_count", 0)

    # Build summary stats
    functions = [c for c in all_chunks if c["type"] in ("function", "method")]
    classes   = [c for c in all_chunks if c["type"] == "class"]
    large_fns = [c for c in functions if c.get("line_count", 0) > 50]
    no_docs   = [c for c in functions if not c.get("docstring")]

    # Connection analysis: which functions are called most?
    call_counts = {}
    for chunk in all_chunks:
        for call in chunk.get("calls", []):
            call_counts[call] = call_counts.get(call, 0) + 1
    most_connected = sorted(call_counts.items(), key=lambda x: -x[1])[:15]

    index = {
        "project": project_name,
        "project_path": str(root),
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "files": file_count,
            "total_lines": total_lines,
            "functions": len(functions),
            "classes": len(classes),
            "chunks": len(all_chunks),
            "large_functions_over_50_lines": len(large_fns),
            "functions_without_docstrings": len(no_docs),
        },
        "most_connected_functions": most_connected,
        "large_functions": [
            {"file": c["file"], "name": c["name"], "lines": c["line_count"]}
            for c in sorted(large_fns, key=lambda x: -x["line_count"])
        ],
        "files_by_size": sorted(
            [{"file": c["file"], "lines": c["line_count"]}
             for c in all_chunks if c["type"] == "module"],
            key=lambda x: -x["lines"]
        ),
        "index": all_chunks,
    }

    return index


# ── Output ────────────────────────────────────────────────────────────────────

def save_local(index: dict, project_path: str):
    """Save index to {project}/.code_index.json."""
    out_path = Path(project_path) / ".code_index.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, default=str)
    log.info(f"Local index saved: {out_path} ({os.path.getsize(out_path) // 1024} KB)")
    return out_path


def push_to_supermemory(index: dict, project_name: str):
    """Push chunks to Supermemory API for cross-session retrieval."""
    try:
        import requests
    except ImportError:
        log.warning("requests not installed — skipping Supermemory push")
        return

    # Get Supermemory API key
    api_key = os.environ.get("SUPERMEMORY_API_KEY", "")
    if not api_key:
        try:
            import keyring
            api_key = keyring.get_password("OBQ_DeepResearch", "SUPERMEMORY_API_KEY") or ""
        except Exception:
            pass

    if not api_key:
        log.warning("SUPERMEMORY_API_KEY not found — skipping push. Set in env or keyring.")
        return

    base_url = "https://api.supermemory.ai/v1"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    pushed = 0

    for chunk in index["index"]:
        if chunk["type"] == "module" and not chunk.get("docstring"):
            continue  # skip module entries with no docstring

        # Build rich text for embedding
        text = (
            f"[{project_name}] {chunk['file']} :: {chunk['name']} "
            f"(L:{chunk['line_start']}-L:{chunk['line_end']})\n"
            f"{chunk.get('signature', '')}\n"
            f"{chunk.get('docstring', '')}\n"
            f"Calls: {', '.join(chunk.get('calls', []))}\n"
            f"---\n"
            f"{chunk.get('code_preview', '')}"
        )

        payload = {
            "content": text[:2000],
            "metadata": {
                "type": "architecture",
                "scope": "project",
                "project": project_name,
                "file": chunk["file"],
                "function": chunk["name"],
                "line_start": chunk["line_start"],
            },
        }

        try:
            r = requests.post(f"{base_url}/memories", headers=headers, json=payload, timeout=10)
            if r.status_code in (200, 201):
                pushed += 1
            else:
                log.debug(f"Supermemory push failed for {chunk['name']}: {r.status_code}")
        except Exception as e:
            log.debug(f"Supermemory push error: {e}")

    log.info(f"Pushed {pushed} chunks to Supermemory")


def print_stats(index: dict):
    """Print a summary of the index."""
    s = index["stats"]
    print(f"\n{'='*60}")
    print(f"CODEBASE INDEX: {index['project']}")
    print(f"{'='*60}")
    print(f"  Files:      {s['files']}")
    print(f"  Lines:      {s['total_lines']:,}")
    print(f"  Functions:  {s['functions']}")
    print(f"  Classes:    {s['classes']}")
    print(f"  Chunks:     {s['chunks']}")
    print(f"  Large (>50L): {s['large_functions_over_50_lines']}")
    print(f"  No docstring: {s['functions_without_docstrings']}")
    print(f"\nTop 10 files by size:")
    for f in index["files_by_size"][:10]:
        print(f"  {f['lines']:>5} lines  {f['file']}")
    print(f"\nMost-connected functions:")
    for name, count in index["most_connected_functions"][:10]:
        print(f"  {count:>3} calls  {name}")
    if index["large_functions"]:
        print(f"\nRefactor candidates (>50 lines):")
        for f in index["large_functions"][:10]:
            print(f"  {f['lines']:>5} lines  {f['file']} :: {f['name']}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OBQ Codebase RAG Indexer")
    parser.add_argument("--project", required=True, help="Path to project root")
    parser.add_argument("--name", default=None, help="Project label (default: folder name)")
    parser.add_argument("--supermemory", action="store_true", help="Push to Supermemory API")
    parser.add_argument("--stats-only", action="store_true", help="Print stats without saving")
    parser.add_argument("--max-preview", type=int, default=MAX_CODE_PREVIEW,
                        help="Max chars of code preview per chunk")
    args = parser.parse_args()

    max_preview = args.max_preview

    project_name = args.name or Path(args.project).resolve().name
    log.info(f"Indexing {args.project} as '{project_name}'...")

    index = index_project(args.project, project_name)
    print_stats(index)

    if args.stats_only:
        return

    out_path = save_local(index, args.project)

    if args.supermemory:
        push_to_supermemory(index, project_name)

    print(f"Done. Index at: {out_path}")


if __name__ == "__main__":
    main()
