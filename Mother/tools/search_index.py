#!/usr/bin/env python3
"""
search_index.py — Fast local codebase search using .code_index.json
No API calls. No token burn. Instant results.

Usage:
  python search_index.py --project <path> --query "scanner scoring"
  python search_index.py --project <path> --query "class Scanner" --top 5
  python search_index.py --all --query "DuckDB connection"   # search all indexed projects
  python search_index.py --project <path> --function "_score_contract"  # exact match

Output format (machine-readable for hook injection):
  FILE: <relative_path>
  FUNCTION: <name>
  LINES: <start>-<end>
  SIGNATURE: <sig>
  PREVIEW: <800 char code body>
  ---
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# All indexed project roots
INDEXED_PROJECTS = {
    "OBQ_AI":           Path(r"C:\Users\admin\Desktop\OBQ_AI"),
    "OBQ_OptionsApp":   Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_OptionsApp"),
    "OBQ_DeepResearch": Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch"),
    "OBQ_FactorLab":    Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_FactorLab"),
    "JCNDashboardApp":  Path(r"C:\Users\admin\Desktop\JCNDashboardApp"),
    "OBQ_RORO":         Path(r"C:\Users\admin\Desktop\OBQ_RORO"),
    "OBQ_ADE":          Path(r"C:\Users\admin\Desktop\OBQ_ADE"),
    "OBQ_AutoResearch": Path(r"C:\Users\admin\Desktop\OBQ_AutoResearch"),
    "Muthr_AI":         Path(r"C:\Users\admin\Desktop\Muthr.ai"),
    "OBQ_Strategies":   Path(r"C:\Users\admin\Desktop\OBQ_Strategies_Master_Corpus_26"),
}


def load_index(project_path: Path) -> list[dict]:
    idx_file = project_path / ".code_index.json"
    if not idx_file.exists():
        return []
    try:
        data = json.loads(idx_file.read_text(encoding="utf-8"))
        return data.get("index", [])
    except Exception:
        return []


def score_chunk(chunk: dict, query_tokens: list[str], exact_func: str | None) -> float:
    """Score a chunk against query tokens. Higher = more relevant."""
    if exact_func:
        name = chunk.get("name", "")
        return 100.0 if name == exact_func or name.endswith("." + exact_func) else 0.0

    score = 0.0
    text = " ".join([
        chunk.get("name", ""),
        chunk.get("file", ""),
        chunk.get("signature", ""),
        chunk.get("docstring", ""),
        chunk.get("code_preview", ""),
    ]).lower()

    for tok in query_tokens:
        tok_l = tok.lower()
        # Exact token in name = high value
        if tok_l in chunk.get("name", "").lower():
            score += 10.0
        # In file path
        if tok_l in chunk.get("file", "").lower():
            score += 5.0
        # In signature
        if tok_l in chunk.get("signature", "").lower():
            score += 4.0
        # In docstring
        if tok_l in chunk.get("docstring", "").lower():
            score += 3.0
        # In code body
        if tok_l in chunk.get("code_preview", "").lower():
            score += 1.0

    return score


def search_project(project_path: Path, query_tokens: list[str],
                   exact_func: str | None, top: int) -> list[dict]:
    chunks = load_index(project_path)
    if not chunks:
        return []

    scored = [(score_chunk(c, query_tokens, exact_func), c) for c in chunks]
    scored = [(s, c) for s, c in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top]]


def format_result(chunk: dict, project_path: Path, project_name: str) -> str:
    rel_file = chunk.get("file", "?")
    abs_file = project_path / rel_file
    lines = f"{chunk.get('line_start', '?')}-{chunk.get('line_end', '?')}"
    sig = chunk.get("signature", chunk.get("name", "?"))
    preview = chunk.get("code_preview", "")[:800]
    doc = chunk.get("docstring", "")

    out = [
        f"PROJECT: {project_name}",
        f"FILE: {abs_file}",
        f"FUNCTION: {chunk.get('name', '?')}",
        f"LINES: {lines}",
        f"SIGNATURE: {sig}",
    ]
    if doc:
        out.append(f"DOCSTRING: {doc[:200]}")
    if preview:
        out.append(f"PREVIEW:\n{preview}")
    out.append("---")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Search local codebase index")
    parser.add_argument("--project", help="Path to project root")
    parser.add_argument("--query", help="Search query (space-separated tokens)")
    parser.add_argument("--function", help="Exact function name lookup")
    parser.add_argument("--top", type=int, default=3, help="Max results (default 3)")
    parser.add_argument("--all", action="store_true", help="Search all indexed projects")
    parser.add_argument("--list", action="store_true", help="List all indexed projects")
    args = parser.parse_args()

    if args.list:
        print("Indexed projects:")
        for name, path in INDEXED_PROJECTS.items():
            idx = path / ".code_index.json"
            status = f"✓ ({idx.stat().st_size // 1024}KB)" if idx.exists() else "✗ not indexed"
            print(f"  {name:<20} {status}  {path}")
        return

    if not args.query and not args.function:
        parser.print_help()
        sys.exit(1)

    query_tokens = args.query.split() if args.query else []
    exact_func = args.function

    results_found = 0

    if args.all:
        for name, path in INDEXED_PROJECTS.items():
            results = search_project(path, query_tokens, exact_func, args.top)
            for chunk in results:
                print(format_result(chunk, path, name))
                results_found += 1
    elif args.project:
        project_path = Path(args.project)
        # Try to match project name
        project_name = project_path.name
        for name, path in INDEXED_PROJECTS.items():
            if path.resolve() == project_path.resolve():
                project_name = name
                break
        results = search_project(project_path, query_tokens, exact_func, args.top)
        for chunk in results:
            print(format_result(chunk, project_path, project_name))
            results_found += 1
    else:
        print("Error: provide --project <path> or --all")
        sys.exit(1)

    if results_found == 0:
        print("No results found. Try broader terms or check index exists with --list")
        sys.exit(0)

    print(f"\n[search_index] {results_found} result(s) found.")


if __name__ == "__main__":
    main()
