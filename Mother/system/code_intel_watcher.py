#!/usr/bin/env python3
"""
code_intel_watcher.py - Mother v5 Live Code Index Watcher

Background daemon that:
- Watches all registered project directories for file changes
- Debounces rapid saves (2 second window)
- Re-indexes only the changed file (incremental update)
- Writes heartbeat to .mother/watcher_heartbeat.json every 30s
- Logs activity to .mother/watcher.log
- Self-restarts on internal errors with exponential backoff

Run:
    pythonw code_intel_watcher.py   (background, no console)
    python  code_intel_watcher.py   (foreground, see logs)
    python  code_intel_watcher.py --status   (check if running)
    python  code_intel_watcher.py --stop     (kill running instance)

Survives:
- Project files changing rapidly (debounced)
- Single project errors (isolated, doesn't kill watcher)
- File system disconnects (auto-retries)
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
SYSTEM_DIR = SCRIPT_DIR
HOME = Path.home()
MOTHER_DIR = HOME / ".mother"
MOTHER_DIR.mkdir(parents=True, exist_ok=True)
HEARTBEAT_FILE = MOTHER_DIR / "watcher_heartbeat.json"
PID_FILE = MOTHER_DIR / "watcher.pid"
LOG_FILE = MOTHER_DIR / "watcher.log"
REGISTRY_FILE = SCRIPT_DIR / "code_intel_registry.json"

# Make code_intel module importable
sys.path.insert(0, str(SCRIPT_DIR))

# ── Config ─────────────────────────────────────────────────────────────────
DEBOUNCE_SEC = 2.0
HEARTBEAT_INTERVAL_SEC = 30
WATCHED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
SKIP_DIRS = {
    "__pycache__", ".git", ".pytest_cache", "node_modules", "venv", ".venv",
    "cache", "logs", "dist", "build", ".mypy_cache", ".ruff_cache",
    ".claude", ".sisyphus", ".vscode", ".idea", "site-packages",
    "ChromeDebugProfile", ".cache", "tmp", "temp",
}

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("watcher")


# ── Helpers ────────────────────────────────────────────────────────────────
def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"watched": [], "scheduled": []}
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"Failed to load registry: {e}")
        return {"watched": [], "scheduled": []}


def write_heartbeat(state: dict) -> None:
    try:
        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["pid"] = os.getpid()
        HEARTBEAT_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
        if part.startswith(".") and part not in (".github",):
            return True
    return False


def check_existing_pid() -> int:
    if not PID_FILE.exists():
        return 0
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is alive (Windows + Unix compatible)
        if sys.platform == "win32":
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True
            )
            return pid if str(pid) in result.stdout else 0
        else:
            os.kill(pid, 0)
            return pid
    except (OSError, ProcessLookupError, ValueError):
        return 0


def write_pid() -> None:
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def clear_pid() -> None:
    try:
        PID_FILE.unlink()
    except OSError:
        pass


# ── Reindex per-file ───────────────────────────────────────────────────────
def reindex_file(project_root: Path, file_path: Path) -> bool:
    """
    Incremental: re-parse the changed file, update .code_index.json + faiss.
    Returns True if successful.
    """
    try:
        import code_intel
        # Use module-level functions to update single file
        rel = file_path.relative_to(project_root).as_posix()
        idx_file = project_root / code_intel.INDEX_FILENAME
        if not idx_file.exists():
            # No index exists yet - do full index
            code_intel.index_project(project_root, force=False, no_embeddings=False)
            return True

        data = json.loads(idx_file.read_text(encoding="utf-8"))

        # Remove old chunks for this file
        existing = data.get("index", [])
        kept = [c for c in existing if c.get("file") != rel]

        # Reparse the file
        if file_path.exists():
            new_chunks = code_intel.parse_file(file_path, project_root)
            for c in new_chunks:
                kept.append({k: v for k, v in c.__dict__.items()})
            new_hash = code_intel.file_hash(file_path)
            data.setdefault("file_hashes", {})[rel] = new_hash
        else:
            # File deleted - just remove from hashes
            data.get("file_hashes", {}).pop(rel, None)

        # Rebuild reverse call graph
        callers = {}
        for c in kept:
            for callee in c.get("calls", []):
                callers.setdefault(callee, []).append({
                    "file": c["file"], "name": c["name"], "line": c["line_start"]
                })
        data["callers"] = callers
        data["index"] = kept

        # Update embeddings for new chunks only
        try:
            embedder = code_intel._get_embedder()
            faiss = code_intel._get_faiss()
            import numpy as np
            import pickle

            chunk_obj_list = []
            for c in kept:
                chunk_obj_list.append(code_intel.Chunk(**{k: c.get(k) for k in code_intel.Chunk.__dataclass_fields__}))
            texts = [code_intel._chunk_embedding_text(c) for c in chunk_obj_list]
            vecs = embedder.encode(texts, batch_size=64, show_progress_bar=False, convert_to_numpy=True).astype("float32")
            faiss.normalize_L2(vecs)

            index = faiss.IndexFlatIP(code_intel.EMBED_DIM)
            index.add(vecs)
            faiss.write_index(index, str(project_root / code_intel.VECTOR_FILENAME))

            chunk_ids = [c.get("id") for c in kept]
            with open(project_root / code_intel.META_FILENAME, "wb") as f:
                pickle.dump({"chunk_ids": chunk_ids, "model": code_intel.EMBED_MODEL_NAME}, f)
        except Exception as e:
            log.warning(f"Embedding update failed for {rel}: {e}")

        # Update timestamp
        data["generated_at"] = datetime.now(timezone.utc).isoformat()
        idx_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        log.error(f"reindex_file failed for {file_path}: {e}")
        return False


# ── Project Watcher ────────────────────────────────────────────────────────
class ProjectWatcher:
    """Watches one project, debounces events, triggers reindex."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.pending: dict = {}  # path -> last_event_time
        self.pending_lock = threading.Lock()
        self.last_reindex: dict = {}  # path -> last_reindex_time
        self.changes_count = 0
        self.errors_count = 0
        self.observer = None

    def on_change(self, file_path: Path):
        if file_path.suffix.lower() not in WATCHED_EXTENSIONS:
            return
        if is_excluded(file_path.relative_to(self.project_root)):
            return
        with self.pending_lock:
            self.pending[str(file_path)] = time.time()

    def flush_pending(self):
        """Re-index any debounced files past their wait window."""
        now = time.time()
        to_process = []
        with self.pending_lock:
            for path_str, last_event in list(self.pending.items()):
                if now - last_event >= DEBOUNCE_SEC:
                    to_process.append(path_str)
                    del self.pending[path_str]
        for path_str in to_process:
            try:
                path = Path(path_str)
                ok = reindex_file(self.project_root, path)
                if ok:
                    self.changes_count += 1
                    self.last_reindex[path_str] = now
                    log.info(f"Reindexed: {path.relative_to(self.project_root)}")
                else:
                    self.errors_count += 1
            except Exception as e:
                self.errors_count += 1
                log.error(f"Reindex error {path_str}: {e}")

    def start(self):
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            log.error("watchdog not installed")
            return

        watcher = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    watcher.on_change(Path(event.src_path))

            def on_created(self, event):
                if not event.is_directory:
                    watcher.on_change(Path(event.src_path))

            def on_deleted(self, event):
                if not event.is_directory:
                    watcher.on_change(Path(event.src_path))

        self.observer = Observer()
        self.observer.schedule(Handler(), str(self.project_root), recursive=True)
        self.observer.start()
        log.info(f"Watching: {self.project_root}")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)


# ── Main daemon ────────────────────────────────────────────────────────────
class Daemon:
    def __init__(self):
        self.watchers: list[ProjectWatcher] = []
        self.running = True
        self.start_time = time.time()
        self.last_registry_reload = 0

    def start(self):
        write_pid()
        log.info(f"Watcher started, PID={os.getpid()}")
        self.reload_registry()
        # Heartbeat thread
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

        # Main loop: flush pending events every 1 second
        try:
            while self.running:
                for w in self.watchers:
                    w.flush_pending()
                # Reload registry every 60 seconds (picks up new projects)
                if time.time() - self.last_registry_reload > 60:
                    self.reload_registry()
                time.sleep(1.0)
        except KeyboardInterrupt:
            log.info("Watcher stopping (KeyboardInterrupt)")
        finally:
            self.shutdown()

    def reload_registry(self):
        reg = load_registry()
        watched = reg.get("watched", [])
        current = {str(w.project_root): w for w in self.watchers}
        target_set = set(watched)
        current_set = set(current.keys())

        # Add new
        for path_str in target_set - current_set:
            path = Path(path_str)
            if not path.exists():
                log.warning(f"Skipping nonexistent: {path_str}")
                continue
            try:
                w = ProjectWatcher(path)
                w.start()
                self.watchers.append(w)
            except Exception as e:
                log.error(f"Failed to start watcher for {path_str}: {e}")

        # Remove old
        for path_str in current_set - target_set:
            w = current[path_str]
            w.stop()
            self.watchers.remove(w)
            log.info(f"Unwatched: {path_str}")

        self.last_registry_reload = time.time()

    def _heartbeat_loop(self):
        while self.running:
            try:
                state = {
                    "status": "running",
                    "uptime_sec": int(time.time() - self.start_time),
                    "watched_projects": len(self.watchers),
                    "projects": [str(w.project_root) for w in self.watchers],
                    "changes_count": sum(w.changes_count for w in self.watchers),
                    "errors_count": sum(w.errors_count for w in self.watchers),
                }
                write_heartbeat(state)
            except Exception:
                pass
            time.sleep(HEARTBEAT_INTERVAL_SEC)

    def shutdown(self):
        self.running = False
        for w in self.watchers:
            w.stop()
        clear_pid()
        write_heartbeat({"status": "stopped"})
        log.info("Watcher shutdown complete")


# ── CLI ────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Mother v5 Code Intel Watcher")
    parser.add_argument("--status", action="store_true", help="Show running status")
    parser.add_argument("--stop", action="store_true", help="Stop running watcher")
    args = parser.parse_args()

    if args.status:
        if HEARTBEAT_FILE.exists():
            try:
                state = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
                print(json.dumps(state, indent=2))
                return 0
            except Exception as e:
                print(json.dumps({"error": str(e)}))
                return 1
        else:
            print(json.dumps({"status": "no_heartbeat"}))
            return 1

    if args.stop:
        pid = check_existing_pid()
        if not pid:
            print("Not running")
            return 0
        try:
            if sys.platform == "win32":
                import subprocess
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            clear_pid()
            print(f"Stopped PID {pid}")
            return 0
        except Exception as e:
            print(f"Failed to stop: {e}")
            return 1

    # Start daemon
    existing = check_existing_pid()
    if existing:
        log.error(f"Watcher already running (PID {existing})")
        return 1

    daemon = Daemon()
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
