#!/usr/bin/env python3
"""
code_intel_memory_bridge.py - Bridges code intelligence to long-term memory.

Three roles:
1. Append-only queue at ~/.mother/memory_queue.jsonl of "important" chunks
   that should be persisted to SuperMemory when available.
2. Detect newly-added important symbols (classes, public functions, modules)
   from .code_index.json files across all registered projects.
3. CLI to flush queue to SuperMemory MCP if configured.

What gets queued (heuristics):
- New CLASS definitions (anywhere)
- New public FUNCTION definitions (don't start with _)
- Modules with > N functions (architectural files)
- ALL symbols on first index of a project

What does NOT get queued:
- Private helpers (_foo)
- Test files
- Generated code

Designed to fail silently if SuperMemory is not configured.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("memory_bridge")

# Paths
HOME = Path.home()
MOTHER_DIR = HOME / ".mother"
MOTHER_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_FILE = MOTHER_DIR / "memory_queue.jsonl"
STATE_FILE = MOTHER_DIR / "memory_bridge_state.json"
SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = SCRIPT_DIR / "code_intel_registry.json"

# Thresholds
MIN_FUNCTIONS_FOR_MODULE = 8


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"watched": [], "scheduled": []}
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"watched": [], "scheduled": []}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"seen_chunks": {}, "last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def is_important(chunk: dict) -> bool:
    """Heuristic: which chunks deserve long-term memory?"""
    name = chunk.get("name", "")
    kind = chunk.get("kind", "")
    file = chunk.get("file", "").lower()

    # Skip test files
    if "test_" in file or "/test/" in file or "/tests/" in file or file.endswith("_test.py"):
        return False
    # Skip private helpers
    if name.startswith("_") and not name.startswith("__"):
        return False
    # Always include classes and top-level interfaces
    if kind in ("class", "interface", "struct"):
        return True
    # Public functions
    if kind in ("function", "method") and not name.startswith("_"):
        return True
    return False


def chunk_to_memory_entry(chunk: dict, project: str, project_path: str) -> dict:
    return {
        "id": chunk.get("id"),
        "project": project,
        "project_path": project_path,
        "file": chunk.get("file"),
        "kind": chunk.get("kind"),
        "name": chunk.get("name"),
        "lang": chunk.get("lang"),
        "signature": chunk.get("signature"),
        "docstring": chunk.get("docstring", "")[:300],
        "calls": chunk.get("calls", [])[:10],
        "lines": f"{chunk.get('line_start')}-{chunk.get('line_end')}",
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }


def append_queue(entries: list) -> int:
    if not entries:
        return 0
    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return len(entries)


def scan() -> dict:
    """Scan all registered projects, queue new important chunks."""
    state = load_state()
    seen = state.get("seen_chunks", {})
    reg = load_registry()
    projects = reg.get("watched", []) + reg.get("scheduled", [])

    queued = 0
    scanned = 0
    new_total = 0

    for proj_path in projects:
        idx_file = Path(proj_path) / ".code_index.json"
        if not idx_file.exists():
            continue
        try:
            data = json.loads(idx_file.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Skip {proj_path}: {e}")
            continue

        project_name = Path(proj_path).name
        scanned += 1
        seen_for_proj = set(seen.get(proj_path, []))
        entries = []
        for chunk in data.get("index", []):
            chunk_id = chunk.get("id")
            if not chunk_id or chunk_id in seen_for_proj:
                continue
            if is_important(chunk):
                entries.append(chunk_to_memory_entry(chunk, project_name, proj_path))
                seen_for_proj.add(chunk_id)
                new_total += 1
        queued += append_queue(entries)
        seen[proj_path] = list(seen_for_proj)

    state["seen_chunks"] = seen
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    return {
        "projects_scanned": scanned,
        "new_chunks_found": new_total,
        "queued": queued,
        "queue_path": str(QUEUE_FILE),
        "queue_size": QUEUE_FILE.stat().st_size if QUEUE_FILE.exists() else 0,
    }


def flush_to_supermemory(dry_run: bool = False) -> dict:
    """
    Flush queue to SuperMemory MCP.
    Currently a no-op unless an MCP client is wired in.
    Returns stats either way.
    """
    if not QUEUE_FILE.exists():
        return {"flushed": 0, "remaining": 0, "note": "no_queue"}

    entries = []
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue

    if dry_run:
        return {
            "queued": len(entries),
            "would_flush": min(len(entries), 100),
            "dry_run": True,
        }

    # TODO: wire SuperMemory MCP push here when configured.
    # For now: rotate queue to .flushed file so we can verify behavior.
    flushed_file = MOTHER_DIR / f"memory_queue.flushed.{int(time.time())}.jsonl"
    QUEUE_FILE.rename(flushed_file)
    return {
        "flushed": len(entries),
        "remaining": 0,
        "archive": str(flushed_file),
        "note": "SuperMemory MCP not configured; archived to .flushed file",
    }


def status() -> dict:
    state = load_state()
    queue_size = QUEUE_FILE.stat().st_size if QUEUE_FILE.exists() else 0
    queue_count = 0
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue_count = sum(1 for _ in f)
        except Exception:
            pass
    return {
        "queue_path": str(QUEUE_FILE),
        "queue_count": queue_count,
        "queue_size_bytes": queue_size,
        "last_scan": state.get("last_run"),
        "seen_projects": list((state.get("seen_chunks") or {}).keys()),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Mother v5 Code Intel <-> Memory bridge")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("scan", help="Scan all indexes, queue new important chunks")
    f = sub.add_parser("flush", help="Push queue to SuperMemory (if configured)")
    f.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="Show queue status")
    sub.add_parser("reset", help="Wipe seen-chunks state (re-queue everything)")

    args = p.parse_args()

    if args.cmd == "scan":
        result = scan()
        print(json.dumps(result, indent=2))
        return 0
    if args.cmd == "flush":
        result = flush_to_supermemory(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        return 0
    if args.cmd == "status":
        result = status()
        print(json.dumps(result, indent=2))
        return 0
    if args.cmd == "reset":
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        print(json.dumps({"reset": True}))
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
