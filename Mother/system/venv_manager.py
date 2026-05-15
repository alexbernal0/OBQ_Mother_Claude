#!/usr/bin/env python3
"""
venv_manager.py - Mother v5 Per-Project Python Venv Manager

Uses uv for all venv operations (fast, Rust-based, Windows-native).
Reads project registry from code_intel_registry.json.

Commands:
  venv_manager.py init <project>      Create .venv in project (uv venv)
  venv_manager.py init --all          Init all registered projects
  venv_manager.py status              Show all project venvs health
  venv_manager.py sync <project>      Sync deps from requirements.txt/pyproject.toml
  venv_manager.py sync --all          Sync all projects
  venv_manager.py which <project>     Print python path (for OpenCode)
  venv_manager.py zombies             Kill python processes from orphaned venvs
  venv_manager.py clean <project>     Remove .venv (force fresh)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REGISTRY_FILE = Path(__file__).resolve().parent / "code_intel_registry.json"
PYTHON_VERSION = "3.12"


def load_registry() -> list[str]:
    if not REGISTRY_FILE.exists():
        return []
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        return data.get("watched", []) + data.get("scheduled", [])
    except Exception:
        return []


def run(cmd: list[str], cwd: str = None) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, encoding="utf-8", errors="replace")
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def uv_path() -> str:
    """Find uv binary."""
    for candidate in ["uv", r"C:\Users\admin\.local\bin\uv.exe",
                      r"C:\Users\admin\AppData\Roaming\uv\bin\uv.exe"]:
        code, out, _ = run(["where", candidate] if os.name == "nt" else ["which", candidate])
        if code == 0:
            return candidate
    return "uv"


UV = None


def get_uv():
    global UV
    if UV is None:
        UV = uv_path()
    return UV


def venv_python(project_path: Path) -> Path | None:
    """Return path to .venv/Scripts/python.exe if venv exists."""
    candidates = [
        project_path / ".venv" / "Scripts" / "python.exe",  # Windows
        project_path / ".venv" / "bin" / "python",          # Unix
        project_path / "venv" / "Scripts" / "python.exe",
        project_path / "venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def venv_size_mb(project_path: Path) -> float:
    for venv_dir in [project_path / ".venv", project_path / "venv"]:
        if venv_dir.exists():
            total = sum(f.stat().st_size for f in venv_dir.rglob("*") if f.is_file())
            return round(total / 1024 / 1024, 1)
    return 0.0


def has_deps(project_path: Path) -> str:
    """Return dep file type or empty string."""
    if (project_path / "pyproject.toml").exists():
        return "pyproject.toml"
    if (project_path / "requirements.txt").exists():
        return "requirements.txt"
    if (project_path / "uv.lock").exists():
        return "uv.lock"
    return ""


def cmd_init(project_path: str, quiet: bool = False) -> bool:
    p = Path(project_path)
    if not p.exists():
        if not quiet:
            print(f"  SKIP {p.name}: path not found")
        return False

    existing = venv_python(p)
    if existing:
        if not quiet:
            print(f"  OK   {p.name}: venv already exists ({existing.parent.parent})")
        return True

    if not quiet:
        print(f"  INIT {p.name}...", end=" ", flush=True)

    code, out, err = run([get_uv(), "venv", "--python", PYTHON_VERSION, str(p / ".venv")], cwd=str(p))
    if code == 0:
        py = venv_python(p)
        if not quiet:
            print(f"OK -> {py}")
        return True
    else:
        if not quiet:
            print(f"FAIL: {err[:100]}")
        return False


def cmd_sync(project_path: str, quiet: bool = False) -> bool:
    p = Path(project_path)
    py = venv_python(p)
    if not py:
        if not quiet:
            print(f"  SKIP {p.name}: no venv (run init first)")
        return False

    dep_file = has_deps(p)
    if not dep_file:
        if not quiet:
            print(f"  SKIP {p.name}: no requirements.txt or pyproject.toml")
        return False

    if not quiet:
        print(f"  SYNC {p.name} ({dep_file})...", end=" ", flush=True)

    if dep_file == "pyproject.toml" or dep_file == "uv.lock":
        code, out, err = run([get_uv(), "sync"], cwd=str(p))
    else:
        code, out, err = run([get_uv(), "pip", "sync", dep_file,
                               "--python", str(py)], cwd=str(p))
    if code == 0:
        if not quiet:
            print("OK")
        return True
    else:
        if not quiet:
            print(f"FAIL: {err[:100]}")
        return False


def cmd_which(project_path: str) -> None:
    p = Path(project_path)
    py = venv_python(p)
    if py:
        print(str(py))
    else:
        # Fall back to global venv
        global_venv = Path(r"C:\Users\admin\Desktop\.venv-obq\Scripts\python.exe")
        if global_venv.exists():
            print(str(global_venv))
        else:
            print(sys.executable)


def cmd_status() -> None:
    projects = load_registry()
    if not projects:
        print("No projects registered. Run: code_intel.py register --project <path>")
        return

    print(f"\n{'Project':<30} {'Venv':<6} {'Size':>7} {'Deps':<16} {'Python'}")
    print("-" * 80)
    ok = stale = missing = 0
    for proj_str in projects:
        p = Path(proj_str)
        name = p.name[:29]
        py = venv_python(p)
        dep = has_deps(p)
        if py:
            sz = venv_size_mb(p)
            ver_code, ver_out, _ = run([str(py), "--version"])
            ver = ver_out.replace("Python ", "") if ver_code == 0 else "?"
            status = "YES"
            ok += 1
        else:
            sz = 0.0
            ver = "-"
            status = "no"
            missing += 1
        print(f"  {name:<28} {status:<6} {sz:>6.0f}MB  {dep or '-':<16} {ver}")
    print("-" * 80)
    print(f"  Total: {len(projects)} | With venv: {ok} | Missing: {missing}")
    print()


def cmd_zombies() -> None:
    """Kill python processes that belong to non-existent venvs."""
    import subprocess as sp
    projects = load_registry()
    valid_venv_paths = set()
    for proj_str in projects:
        p = Path(proj_str)
        py = venv_python(p)
        if py:
            valid_venv_paths.add(str(py.parent).lower())

    # Add global venv
    valid_venv_paths.add(r"c:\users\admin\desktop\.venv-obq\scripts")
    valid_venv_paths.add(r"c:\users\admin\appdata\local\programs\python\python312")

    try:
        result = sp.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process python,pythonw -ErrorAction SilentlyContinue | "
             "Select-Object Id,@{N='Path';E={$_.Path}},@{N='MB';E={[math]::Round($_.WorkingSet64/1MB)}},CPU | "
             "ConvertTo-Json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0 or not result.stdout.strip():
            print("No python processes found")
            return

        procs = json.loads(result.stdout)
        if isinstance(procs, dict):
            procs = [procs]

        killed = 0
        skipped = 0
        for proc in procs:
            pid = proc.get("Id")
            path = (proc.get("Path") or "").lower()
            mb = proc.get("MB", 0)
            cpu = proc.get("CPU", 0)

            if not path:
                # No path = zombie, kill if <15MB and 0 CPU
                if mb < 15 and (cpu or 0) < 0.1:
                    sp.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"],
                           capture_output=True)
                    print(f"  Killed zombie PID {pid} (no path, {mb}MB)")
                    killed += 1
                continue

            # Check if path is in a known valid venv
            path_dir = str(Path(path).parent).lower()
            is_known = any(v in path_dir or path_dir in v for v in valid_venv_paths)
            if not is_known:
                print(f"  Unknown venv PID {pid}: {path} ({mb}MB) — skipping (manual review)")
                skipped += 1
            else:
                skipped += 1

        print(f"Killed: {killed} | Skipped/known: {skipped}")
    except Exception as e:
        print(f"Error: {e}")


def cmd_clean(project_path: str) -> None:
    p = Path(project_path)
    for venv_dir in [p / ".venv", p / "venv"]:
        if venv_dir.exists():
            import shutil
            sz = venv_size_mb(p)
            shutil.rmtree(venv_dir)
            print(f"Removed {venv_dir} ({sz}MB)")
            return
    print(f"No venv found in {p}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mother v5 Venv Manager")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Create .venv in project(s)")
    p_init.add_argument("project", nargs="?")
    p_init.add_argument("--all", action="store_true")

    p_sync = sub.add_parser("sync", help="Sync deps into venv")
    p_sync.add_argument("project", nargs="?")
    p_sync.add_argument("--all", action="store_true")

    p_which = sub.add_parser("which", help="Print python path for project")
    p_which.add_argument("project")

    sub.add_parser("status", help="Show all venvs")
    sub.add_parser("zombies", help="Kill orphaned python processes")

    p_clean = sub.add_parser("clean", help="Remove .venv from project")
    p_clean.add_argument("project")

    args = parser.parse_args()

    if args.cmd == "init":
        if args.all or not args.project:
            projects = load_registry()
            print(f"Initializing {len(projects)} projects...")
            ok = sum(cmd_init(p) for p in projects)
            print(f"\nDone: {ok}/{len(projects)} venvs ready")
        else:
            cmd_init(args.project)

    elif args.cmd == "sync":
        if args.all or not args.project:
            projects = load_registry()
            print(f"Syncing {len(projects)} projects...")
            ok = sum(cmd_sync(p) for p in projects)
            print(f"\nDone: {ok}/{len(projects)} synced")
        else:
            cmd_sync(args.project)

    elif args.cmd == "which":
        cmd_which(args.project)

    elif args.cmd == "status":
        cmd_status()

    elif args.cmd == "zombies":
        cmd_zombies()

    elif args.cmd == "clean":
        cmd_clean(args.project)

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
