#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M.O.T.H.E.R Widget — Windows floating panel v5.0
Sci-fi system monitor for the OBQ Mother AI platform.

Run:  pythonw mother_widget.py   (no console)
Stop: Right-click -> Exit
"""

import tkinter as tk
import threading
import time
import os
import pathlib
import json
import subprocess
from datetime import datetime
from collections import deque

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pystray
    from PIL import Image, ImageDraw

    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# ── Paths ────────────────────────────────────────────────────────────────────────
HOME = pathlib.Path.home()
SKILLS_DIR = HOME / ".claude" / "skills"
SKILLS_INACTIVE = HOME / ".claude" / "skills-inactive"
TRANSCRIPTS_DIR = HOME / ".claude" / "transcripts"
OPENCODE_DIR = HOME / ".config" / "opencode"
PROJECTS_DIR = HOME / ".claude" / "projects"
PENDING_RSL = HOME / ".claude" / ".pending-supermemory-review"
LAST_SESSION = HOME / ".claude" / ".last-session-date"
LEARNING_SIG = HOME / ".claude" / ".learning-signals"
SKILL_MONITOR = pathlib.Path(__file__).parent / "skill-monitor.html"
OC_HOOKS = HOME / ".claude" / "hooks"
OMO_CONFIG = HOME / ".config" / "opencode" / "oh-my-opencode.json"
MOTHER_TEL    = HOME / ".mother" / "telemetry" / "usage.jsonl"
MOTHER_SCORES = HOME / ".mother" / "scores" / "scores.jsonl"

# ── Spec-enabled projects ────────────────────────────────────────────────────────
SPEC_PROJECTS = {
    "JCN": HOME / "Desktop" / "JCNDashboardApp",
    "Muthr.ai": HOME / "Desktop" / "Muthr.ai",
    "OptionsApp": HOME / "Desktop" / "OBQ_AI" / "OBQ_AI_OptionsApp",
    "DeepResearch": HOME / "Desktop" / "OBQ_AI" / "OBQ_AI_DeepResearch",
}

# ── Hardware constants (verified) ────────────────────────────────────────────────
HW_CPU_NAME = "i9-7940X"
HW_CPU_CORES = 14
HW_CPU_THREADS = 28
HW_RAM_GB = 128
HW_GPU_COMPUTE = "RTX 3090"
HW_GPU_VRAM_GB = 24
HW_GPU_DISPLAY = "Quadro P620"
HW_DRIVES = ["C", "D", "G", "H"]

# ── Dimensions & Timing ──────────────────────────────────────────────────────────
PANEL_W = 285
PANEL_H_MINI = 32
MARGIN = 10
REFRESH_SECS = 5   # full status refresh (was 15 — now 5s heartbeat)
LIVE_SECS = 1      # live graph refresh rate (CPU/GPU/VRAM)
GRAPH_W = 180      # sparkline graph width in pixels
GRAPH_H = 28       # sparkline graph height in pixels
HISTORY_LEN = 60   # 60 seconds of history

# ── Colors ───────────────────────────────────────────────────────────────────────
C_BG = "#080810"
C_CYAN = "#00f0ff"
C_GREEN = "#39ff14"
C_RED = "#ff2040"
C_YELLOW = "#ffb300"
C_GRAY = "#4a4a6a"
C_WHITE = "#c0c0d0"
C_DIM = "#2a2a3a"
C_BORDER = "#1a1a2e"
C_MAG = "#ff00ff"

# ── Fonts ────────────────────────────────────────────────────────────────────────
FONT_TITLE = ("Consolas", 11, "bold")
FONT_MAIN = ("Consolas", 9)
FONT_SMALL = ("Consolas", 8)
FONT_DOT = ("Consolas", 10, "bold")

# ── All commands (for quick-ref panel) ───────────────────────────────────────────
ALL_COMMANDS = [
    ("/healthcheck", "system health audit"),
    ("/housekeeping", "weekly maintenance"),
    ("/handoff", "session snapshot"),
    ("/debloat", "kill zombies + cleanup"),
    ("/zq", "session quality score"),
    ("/zq --trend 7d", "7-day ZQ trend"),
    ("/napkin", "project runbook"),
    ("/harden-code", "3-agent code audit"),
    ("/compress-now", "compact context"),
    ("/update-knowledge", "refresh memory"),
    ("/skill-scan", "find new skills"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────────
def dir_size_mb(path):
    if not path.is_dir():
        return 0.0
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total / (1024 * 1024)


def count_dir(path):
    if not path.is_dir():
        return 0
    try:
        return sum(
            1 for d in path.iterdir() if d.is_dir() and not d.name.startswith(".")
        )
    except OSError:
        return 0


def ascii_bar(value, max_val, width=10):
    ratio = min(value / max_val, 1.0) if max_val > 0 else 0.0
    filled = int(ratio * width)
    return chr(9608) * filled + chr(9617) * (width - filled)


def gauge_color(value, warn, red):
    if value >= red:
        return C_RED
    if value >= warn:
        return C_YELLOW
    return C_GREEN


def count_processes(name_fragment):
    if HAS_PSUTIL:
        try:
            return sum(
                1
                for p in psutil.process_iter(["name"])
                if p.info["name"] and name_fragment.lower() in p.info["name"].lower()
            )
        except Exception:
            return 0
    try:
        out = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True,
            timeout=5,
            creationflags=0x08000000,
        )
        return sum(
            1 for line in out.splitlines() if name_fragment.lower() in line.lower()
        )
    except Exception:
        return 0


def recent_skills(n=3):
    if not SKILLS_DIR.is_dir():
        return []
    try:
        dirs = [(d.stat().st_mtime, d.name) for d in SKILLS_DIR.iterdir() if d.is_dir()]
        dirs.sort(reverse=True)
        return [name for _, name in dirs[:n]]
    except OSError:
        return []


def count_lessons():
    if not PROJECTS_DIR.is_dir():
        return 0
    count = 0
    try:
        for f in PROJECTS_DIR.rglob("lessons.md"):
            try:
                lines = f.read_text(errors="ignore").splitlines()
                count += sum(
                    1
                    for l in lines
                    if l.strip().startswith("- Date:") or l.strip().startswith("##")
                )
            except OSError:
                pass
    except OSError:
        pass
    return count


def count_learning_signals():
    if not LEARNING_SIG.exists():
        return 0
    try:
        lines = LEARNING_SIG.read_text(encoding="utf-8").splitlines()
        return len([l for l in lines if l.strip()])
    except Exception:
        return 0


def get_sys_perf():
    """
    Returns live system performance metrics.
    Uses psutil when available, falls back to subprocess/WMI.
    """
    perf = {
        "cpu_pct": 0.0,
        "ram_used_gb": 0.0,
        "ram_free_gb": 0.0,
        "ram_pct": 0.0,
        "drives": {},  # {letter: (used_gb, total_gb, pct)}
        "ollama_on": False,
        "svchost_n": 0,
        "py_procs": 0,
        "gpu_util_pct": 0.0,  # RTX 3090 GPU core utilization %
        "gpu_vram_pct": 0.0,  # RTX 3090 VRAM utilization %
        "gpu_vram_used_gb": 0.0,
        "gpu_temp": 0,
        "top_cpu_name": "",
        "top_cpu_sec": 0,
    }

    if HAS_PSUTIL:
        try:
            perf["cpu_pct"] = psutil.cpu_percent(interval=0.3)
            vm = psutil.virtual_memory()
            perf["ram_used_gb"] = round(vm.used / 1024**3, 1)
            perf["ram_free_gb"] = round(vm.available / 1024**3, 1)
            perf["ram_pct"] = vm.percent
            perf["svchost_n"] = sum(
                1
                for p in psutil.process_iter(["name"])
                if p.info["name"] and "svchost" in p.info["name"].lower()
            )
            perf["py_procs"] = sum(
                1
                for p in psutil.process_iter(["name"])
                if p.info["name"] and "python" in p.info["name"].lower()
            )
            perf["ollama_on"] = any(
                p.info["name"] and "ollama" in p.info["name"].lower()
                for p in psutil.process_iter(["name"])
            )
            # Top CPU hog detection
            try:
                procs = [(p.info["name"], p.cpu_times().user + p.cpu_times().system)
                         for p in psutil.process_iter(["name", "cpu_times"])
                         if p.info["name"] and p.info.get("cpu_times")]
                if procs:
                    top = max(procs, key=lambda x: x[1])
                    perf["top_cpu_name"] = top[0]
                    perf["top_cpu_sec"] = round(top[1], 0)
                else:
                    perf["top_cpu_name"] = ""
                    perf["top_cpu_sec"] = 0
            except Exception:
                perf["top_cpu_name"] = ""
                perf["top_cpu_sec"] = 0
            for letter in HW_DRIVES:
                try:
                    du = psutil.disk_usage(letter + ":\\")
                    perf["drives"][letter] = (
                        round(du.used / 1024**3, 1),
                        round(du.total / 1024**3, 1),
                        du.percent,
                    )
                except Exception:
                    pass
        except Exception:
            pass
    else:
        # Fallback via WMI
        try:
            import wmi

            c = wmi.WMI()
            cpu_load = c.Win32_Processor()[0].LoadPercentage or 0
            perf["cpu_pct"] = float(cpu_load)
            os_info = c.Win32_OperatingSystem()[0]
            total_kb = float(os_info.TotalVisibleMemorySize)
            free_kb = float(os_info.FreePhysicalMemory)
            perf["ram_used_gb"] = round((total_kb - free_kb) / 1024**2, 1)
            perf["ram_free_gb"] = round(free_kb / 1024**2, 1)
            perf["ram_pct"] = round((total_kb - free_kb) / total_kb * 100, 1)
        except Exception:
            pass

    # nvidia-smi for RTX 3090 — GPU util%, VRAM, temp
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
                "--id=0",
            ],  # GPU index 0 = RTX 3090
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=0x08000000,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 4:
                perf["gpu_util_pct"] = float(parts[0].strip())
                vram_used = float(parts[1].strip())
                vram_total = float(parts[2].strip())
                perf["gpu_vram_pct"] = round(vram_used / vram_total * 100, 1)
                perf["gpu_vram_used_gb"] = round(vram_used / 1024, 1)
                perf["gpu_temp"] = int(parts[3].strip())
    except Exception:
        pass

    return perf


def check_spec_status():
    """
    Returns list of (project_short, active_count, stale_count) for all spec projects.
    active_count = number of in-progress changes (active/ subdirs with proposal.md)
    stale_count  = active changes older than 14 days with no tasks checked off
    """
    results = []
    now = datetime.now()
    for short, path in SPEC_PROJECTS.items():
        active_dir = path / ".spec" / "changes" / "active"
        if not active_dir.is_dir():
            results.append((short, -1, 0))  # -1 = spec not initialised
            continue
        active, stale = 0, 0
        try:
            for change in active_dir.iterdir():
                if not change.is_dir():
                    continue
                proposal = change / "proposal.md"
                tasks = change / "tasks.md"
                if not proposal.exists():
                    continue
                active += 1
                age_days = (now - datetime.fromtimestamp(proposal.stat().st_mtime)).days
                # stale: >14 days old AND no tasks checked off yet
                if age_days > 14:
                    if tasks.exists():
                        done = sum(
                            1
                            for l in tasks.read_text(errors="ignore").splitlines()
                            if "- [x]" in l
                        )
                        if done == 0:
                            stale += 1
                    else:
                        stale += 1
        except OSError:
            pass
        results.append((short, active, stale))
    return results


def check_persistent_systems():
    systems = []

    comp = OC_HOOKS / "capture_error_fix.py"
    sig = OC_HOOKS / "detect_learning_signal.py"
    chk = OC_HOOKS / "session_checkpoint.py"
    hooks_ok = comp.exists() and sig.exists() and chk.exists()
    # Check hooks are actually registered
    try:
        s = (HOME / ".claude" / "settings.json").read_text(encoding="utf-8")
        hooks_registered = "capture_error_fix" in s
    except Exception:
        hooks_registered = False
    systems.append(
        (
            "Learning hooks",
            "ACTIVE" if (hooks_ok and hooks_registered) else "NOT REGISTERED",
            C_GREEN if (hooks_ok and hooks_registered) else C_YELLOW,
        )
    )

    omo_ok = False
    try:
        if OMO_CONFIG.exists():
            d = json.loads(OMO_CONFIG.read_text(encoding="utf-8"))
            omo_ok = "agents" in d
    except Exception:
        pass
    systems.append(
        ("OMO plugin", "ACTIVE" if omo_ok else "MISSING", C_GREEN if omo_ok else C_RED)
    )

    ollama_ok = False
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=0x08000000,
        )
        ollama_ok = result.returncode == 0 and len(result.stdout.strip()) > 0
    except Exception:
        pass
    systems.append(
        (
            "Local LLMs",
            "ONLINE" if ollama_ok else "OFFLINE",
            C_GREEN if ollama_ok else C_YELLOW,
        )
    )

    sm_ok = False
    try:
        s_path = HOME / ".claude" / "settings.json"
        if s_path.exists():
            d = json.loads(s_path.read_text(encoding="utf-8"))
            sm_ok = any("supermemory" in k.lower() for k in d.get("enabledPlugins", {}))
    except Exception:
        pass
    systems.append(
        (
            "SuperMemory",
            "ENABLED" if sm_ok else "DISABLED",
            C_GREEN if sm_ok else C_GRAY,
        )
    )

    rtk_ok = (HOME / ".local" / "bin" / "rtk.exe").exists()
    systems.append(
        (
            "RTK v0.33.1",
            "ACTIVE" if rtk_ok else "NOT FOUND",
            C_GREEN if rtk_ok else C_YELLOW,
        )
    )

    harden_ok = (SKILLS_DIR / "harden-code").exists()
    compound_ok = (SKILLS_DIR / "compound-knowledge").exists()
    systems.append(
        (
            "harden-code",
            "READY" if harden_ok else "MISSING",
            C_GREEN if harden_ok else C_GRAY,
        )
    )
    systems.append(
        (
            "compound-knowledge",
            "READY" if compound_ok else "MISSING",
            C_GREEN if compound_ok else C_GRAY,
        )
    )

    return systems


# ── Performance Scores Reader ─────────────────────────────────────────────────────
def read_perf_scores():
    """Read last 7 days of session scores, return averages + last session."""
    default = {"overall": 0, "speed": 0, "accuracy": 0, "tokens": 0,
               "skills": 0, "memory": 0, "sessions": 0, "trend": ""}
    if not MOTHER_SCORES.exists():
        return default
    try:
        import datetime as dt
        cutoff = (dt.date.today() - dt.timedelta(days=7)).isoformat()
        records = []
        with open(MOTHER_SCORES, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    if r.get("date", "") >= cutoff:
                        records.append(r)
                except Exception:
                    pass
        if not records:
            return default
        def avg(key):
            vals = [r["scores"].get(key, 0) for r in records if "scores" in r]
            return int(sum(vals) / len(vals)) if vals else 0
        last = records[-1]["scores"] if records else {}
        # Trend: compare last 3 vs prior 3
        trend = ""
        if len(records) >= 4:
            recent  = sum(r["scores"].get("overall",0) for r in records[-3:]) / 3
            earlier = sum(r["scores"].get("overall",0) for r in records[-6:-3]) / max(len(records[-6:-3]),1)
            trend = "UP" if recent > earlier + 3 else ("DOWN" if recent < earlier - 3 else "FLAT")
        return {
            "overall":  avg("overall"),
            "speed":    avg("speed"),
            "accuracy": avg("accuracy"),
            "tokens":   avg("tokens"),
            "skills":   avg("skills"),
            "memory":   avg("memory"),
            "sessions": len(records),
            "last":     last,
            "trend":    trend,
        }
    except Exception:
        return default


# ── Status Reader ─────────────────────────────────────────────────────────────────
def read_venv_status():
    """Quick venv health check — count projects with/without venvs."""
    reg_file = pathlib.Path(__file__).resolve().parent / "code_intel_registry.json"
    if not reg_file.exists():
        return None
    try:
        data = json.loads(reg_file.read_text(encoding="utf-8"))
        projects = data.get("watched", []) + data.get("scheduled", [])
        ok = sum(1 for p in projects if
                 (pathlib.Path(p) / ".venv" / "Scripts" / "python.exe").exists())
        return {"total": len(projects), "ok": ok, "missing": len(projects) - ok}
    except Exception:
        return None


def read_code_intel():
    """Read code intel watcher heartbeat. Returns dict or None."""
    hb_file = HOME / ".mother" / "watcher_heartbeat.json"
    if not hb_file.exists():
        return None
    try:
        data = json.loads(hb_file.read_text(encoding="utf-8"))
        # Check if heartbeat is fresh (< 2 min old)
        ts = data.get("timestamp", "")
        if ts:
            try:
                hb_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                age_sec = (datetime.now(hb_time.tzinfo) - hb_time).total_seconds()
                data["age_sec"] = int(age_sec)
                data["stale"] = age_sec > 120
            except Exception:
                data["stale"] = True
        return data
    except Exception:
        return None


def read_zq_score():
    """Read latest ZQ score from zq_reports/latest.json + trend.json. Returns dict or None."""
    zq_dir = pathlib.Path(__file__).resolve().parent.parent / "zq_reports"
    latest = zq_dir / "latest.json"
    trend = zq_dir / "trend.json"
    if not latest.exists():
        return None
    try:
        data = json.loads(latest.read_text())
        score = data.get("score", {})
        result = {
            "zq": score.get("zq", 0.0),
            "grade": score.get("grade", "?"),
            "accuracy": score.get("accuracy_score", 0.0),
            "efficiency": score.get("efficiency_score", 0.0),
            "speed": score.get("speed_score", 0.0),
            "output": score.get("output_score", 0.0),
            "trend": "n/a",
            "delta": 0.0,
        }
        if trend.exists():
            try:
                t = json.loads(trend.read_text())
                result["trend"] = t.get("trend", "n/a")
                result["delta"] = t.get("delta", 0.0)
            except Exception:
                pass
        return result
    except Exception:
        return None


def refresh_zq_score():
    """Trigger a background ZQ score recompute (non-blocking)."""
    zq_script = pathlib.Path(__file__).resolve().parent / "zq_score.py"
    if not zq_script.exists():
        return
    try:
        subprocess.Popen(
            ["python", str(zq_script), "--summary"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    except Exception:
        pass


def read_status():
    info = {
        "skills_active": 0,
        "skills_inactive": 0,
        "recent_skills": [],
        "rsl_pending": False,
        "last_session": "unknown",
        "lessons": 0,
        "signals": 0,
        "transcripts_mb": 0.0,
        "skills_mb": 0.0,
        "opencode_mb": 0.0,
        "py_procs": 0,
        "node_procs": 0,
        "health_pct": 100,
        "actions": [],
        "persistent": [],
        "specs": [],
        "perf": {},
        "zq": None,
        "refreshed": datetime.now().strftime("%H:%M:%S"),
    }

    info["skills_active"] = count_dir(SKILLS_DIR)
    info["skills_inactive"] = count_dir(SKILLS_INACTIVE)
    info["recent_skills"] = recent_skills(3)
    info["rsl_pending"] = PENDING_RSL.exists()
    info["signals"] = count_learning_signals()

    if LAST_SESSION.exists():
        try:
            info["last_session"] = LAST_SESSION.read_text(errors="ignore").strip()[:10]
        except OSError:
            pass

    info["lessons"] = count_lessons()
    info["transcripts_mb"] = dir_size_mb(TRANSCRIPTS_DIR)
    info["skills_mb"] = dir_size_mb(SKILLS_DIR)
    # Exclude node_modules from opencode size — legitimate plugin install
    oc_mb = 0.0
    try:
        for p in OPENCODE_DIR.iterdir():
            if p.name == "node_modules":
                continue
            if p.is_file():
                try: oc_mb += p.stat().st_size / (1024*1024)
                except: pass
            elif p.is_dir():
                oc_mb += dir_size_mb(p)
    except Exception:
        oc_mb = dir_size_mb(OPENCODE_DIR)
    info["opencode_mb"] = oc_mb
    info["py_procs"] = count_processes("python")
    info["node_procs"] = count_processes("node")
    info["persistent"] = check_persistent_systems()
    info["perf_scores"] = read_perf_scores()
    info["specs"] = check_spec_status()
    info["perf"] = get_sys_perf()
    info["zq"] = read_zq_score()
    info["code_intel"] = read_code_intel()
    info["venvs"] = read_venv_status()

    score_map = {C_GREEN: 100, C_YELLOW: 50, C_RED: 0}
    gauges = [
        gauge_color(info["transcripts_mb"], 150, 400),  # raised: active dev generates transcripts
        gauge_color(info["skills_mb"], 5, 10),
        gauge_color(info["opencode_mb"], 50, 150),       # raised: excludes node_modules now
    ]
    info["health_pct"] = int(sum(score_map[g] for g in gauges) / len(gauges))

    if info["transcripts_mb"] > 300:
        info["actions"].append(
            "! /debloat  (transcripts %.0fMB)" % info["transcripts_mb"]
        )
    if info["rsl_pending"]:
        info["actions"].append("! RSL REVIEW PENDING")
    if info["signals"] > 0:
        info["actions"].append(
            "! %d learning signal(s) — /housekeeping" % info["signals"]
        )
    if info["skills_mb"] > 5:
        info["actions"].append("! /housekeeping  (skills %.1fMB)" % info["skills_mb"])
    for proj, active, stale in info.get("specs", []):
        if stale > 0:
            info["actions"].append("! %s spec STALE >14d — review" % proj)

    return info


# ── Widget ────────────────────────────────────────────────────────────────────────
class MotherWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self._running = True
        self._collapsed = False
        self._show_cmds = False
        self._info = read_status()

        # ── Live graph history buffers ─────────────────────────────────────────
        self._cpu_hist  = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self._gpu_hist  = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self._vram_hist = deque([0.0] * HISTORY_LEN, maxlen=HISTORY_LEN)
        self._live_cpu  = 0.0
        self._live_gpu  = 0.0
        self._live_vram = 0.0
        self._live_temp = 0
        self._live_lock = threading.Lock()

        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-alpha", 0.93)
        self.configure(bg=C_BG)

        # Use tkinter's scaling-aware methods to get actual usable screen size
        self.update_idletasks()  # ensure geometry is initialized
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        # Account for Windows DPI scaling — position near top-right, always visible
        # Use 40px from right edge, 40px from top (safe on any resolution/scaling)
        x = max(sw - PANEL_W - 40, 0)
        y = 40
        self.geometry("%dx%d+%d+%d" % (PANEL_W, 600, x, y))

        self.cv = tk.Canvas(
            self, width=PANEL_W, height=600, bg=C_BG, highlightthickness=0, bd=0
        )
        self.cv.pack(fill="both", expand=True)

        self.cv.bind("<ButtonPress-1>", self._drag_start)
        self.cv.bind("<B1-Motion>", self._drag_move)
        self.cv.bind("<Button-3>", self._right_click)

        # Hide to tray on close instead of exiting
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

        self._menu = tk.Menu(
            self,
            tearoff=0,
            bg="#111122",
            fg=C_WHITE,
            activebackground="#222244",
            activeforeground=C_CYAN,
            font=("Consolas", 9),
        )
        self._menu.add_command(label="Refresh Now", command=self._manual_refresh)
        self._menu.add_command(label="Toggle Collapse", command=self._toggle_collapse)
        self._menu.add_command(label="Toggle Commands", command=self._toggle_cmds)
        self._menu.add_separator()
        self._menu.add_command(label="Open Skill Monitor", command=self._open_monitor)
        self._menu.add_separator()
        self._menu.add_command(label="Exit Widget", command=self._quit)

        self._draw()
        threading.Thread(target=self._poll_loop, daemon=True).start()
        threading.Thread(target=self._live_poll_loop, daemon=True).start()
        self._schedule_live_update()
        # Also schedule main-thread status refresh as belt-and-suspenders
        self.after(REFRESH_SECS * 1000, self._schedule_status_refresh)
        # ZQ score auto-refresh every 60 seconds (non-blocking background recompute)
        self.after(2000, self._schedule_zq_refresh)  # initial after 2s

    def _schedule_zq_refresh(self):
        """Trigger ZQ score recompute every 60s. Non-blocking subprocess."""
        if self._running:
            try:
                refresh_zq_score()
            except Exception:
                pass
            self.after(60_000, self._schedule_zq_refresh)

    # ── Poll ──────────────────────────────────────────────────────────────────────
    def _poll_loop(self):
        """Full status refresh every REFRESH_SECS — runs in background thread."""
        while self._running:
            time.sleep(REFRESH_SECS)
            if not self._running:
                break
            try:
                self._info = read_status()
                self.after(0, self._draw)  # trigger redraw on main thread
            except Exception:
                pass

    def _schedule_status_refresh(self):
        """Also schedule status refresh on main thread timer as backup."""
        if self._running:
            try:
                self._info = read_status()
                self._draw()
            except Exception:
                pass
            self.after(REFRESH_SECS * 1000, self._schedule_status_refresh)

    def _manual_refresh(self):
        self._info = read_status()
        self._draw()

    # ── Live polling (background thread, 1s) ──────────────────────────────────
    def _live_poll_loop(self):
        """Collect CPU/GPU samples every second in background thread."""
        # Prime psutil cpu_percent (first call always returns 0)
        if HAS_PSUTIL:
            try:
                psutil.cpu_percent(interval=None)
            except Exception:
                pass
        while self._running:
            time.sleep(LIVE_SECS)
            if not self._running:
                break
            cpu = 0.0
            gpu = 0.0
            vram = 0.0
            temp = 0
            try:
                if HAS_PSUTIL:
                    cpu = psutil.cpu_percent(interval=None)
            except Exception:
                pass
            try:
                result = subprocess.run(
                    ["nvidia-smi",
                     "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                     "--format=csv,noheader,nounits", "--id=0"],
                    capture_output=True, text=True, timeout=2,
                    creationflags=0x08000000,
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split(",")
                    if len(parts) >= 4:
                        gpu  = float(parts[0].strip())
                        vram_used  = float(parts[1].strip())
                        vram_total = float(parts[2].strip())
                        vram = round(vram_used / vram_total * 100, 1) if vram_total else 0.0
                        temp = int(parts[3].strip())
            except Exception:
                pass
            with self._live_lock:
                self._cpu_hist.append(cpu)
                self._gpu_hist.append(gpu)
                self._vram_hist.append(vram)
                self._live_cpu  = cpu
                self._live_gpu  = gpu
                self._live_vram = vram
                self._live_temp = temp

    # ── Live graph UI update (main thread, scheduled) ─────────────────────────
    def _schedule_live_update(self):
        if self._running:
            self._update_live_graphs()
            self.after(1000, self._schedule_live_update)

    def _update_live_graphs(self):
        """Redraw only the live graph canvas — fast, no full widget redraw."""
        if self._collapsed or self._show_cmds:
            return
        if not hasattr(self, "_graph_canvas"):
            return
        with self._live_lock:
            cpu_h  = list(self._cpu_hist)
            gpu_h  = list(self._gpu_hist)
            vram_h = list(self._vram_hist)
            cpu_v  = self._live_cpu
            gpu_v  = self._live_gpu
            vram_v = self._live_vram
            temp_v = self._live_temp

        gc = self._graph_canvas
        gc.delete("all")
        self._draw_sparkline_row(gc, cpu_h,  cpu_v,  "CPU",  0,   max_val=100)
        self._draw_sparkline_row(gc, gpu_h,  gpu_v,  "GPU",  48,  max_val=100, suffix="% {}°C".format(temp_v) if temp_v else "%")
        self._draw_sparkline_row(gc, vram_h, vram_v, "VRAM", 96,  max_val=100)

    def _draw_sparkline_row(self, canvas, history, current_val, label, y_off,
                            max_val=100, suffix="%"):
        """Draw one sparkline row: label | graph | value."""
        W = PANEL_W - 20
        GW = GRAPH_W
        GH = GRAPH_H

        # Color based on value
        if current_val >= 90:
            clr = C_RED
        elif current_val >= 70:
            clr = C_YELLOW
        else:
            clr = C_GREEN

        # Label
        canvas.create_text(10, y_off + 8, text=label, font=FONT_SMALL,
                           fill=C_GRAY, anchor="w")

        # Value (right side)
        val_text = "{:.0f}{}".format(current_val, suffix)
        canvas.create_text(W + 10, y_off + 8, text=val_text, font=FONT_SMALL,
                           fill=clr, anchor="e")

        # Graph background
        gx = 38
        gy = y_off + 16
        canvas.create_rectangle(gx, gy, gx + GW, gy + GH,
                                fill="#0d0d20", outline=C_BORDER)

        # Sparkline — connect the dots
        if len(history) < 2:
            return
        pts = []
        for i, v in enumerate(history):
            x = gx + int(i / (HISTORY_LEN - 1) * (GW - 2)) + 1
            y = gy + GH - 2 - int(min(v, max_val) / max_val * (GH - 4))
            pts.extend([x, y])
        if len(pts) >= 4:
            canvas.create_line(pts, fill=clr, width=1, smooth=False)

        # Fill area under line (subtle)
        fill_pts = [pts[0], gy + GH - 1] + pts + [pts[-2], gy + GH - 1]
        canvas.create_polygon(fill_pts,
                              fill=clr.replace("ff", "22").replace("39", "0a"),
                              outline="")

    # ── Draw ──────────────────────────────────────────────────────────────────────
    def _draw(self):
        c = self.cv
        c.delete("all")
        info = self._info
        W = PANEL_W

        if self._collapsed:
            self._draw_collapsed(c, info, W)
            return

        if self._show_cmds:
            self._draw_commands(c, W)
            return

        y = 10

        # Border
        c.create_rectangle(1, 1, W - 1, 2000, outline=C_BORDER, fill=C_BG, width=1)
        c.create_rectangle(2, 2, W - 2, 2000, outline="#0d0d20", fill="", width=1)
        for sy in range(0, 2000, 4):
            c.create_line(3, sy, W - 3, sy, fill="#0a0a18", width=1)

        # ── Header ────────────────────────────────────────────────────────────────
        c.create_text(
            W // 2,
            y + 8,
            text="M.O.T.H.E.R  v5.0",
            font=FONT_TITLE,
            fill=C_CYAN,
            anchor="center",
        )
        y += 20

        # ── Live Monitor (embedded canvas, updates every 1s) ──────────────────
        GRAPH_SECTION_H = 130
        c.create_text(12, y + 6, text="LIVE MONITOR",
                      font=("Consolas", 9, "bold"), fill=C_CYAN, anchor="w")
        c.create_text(W - 12, y + 6, text="1s refresh",
                      font=("Consolas", 7), fill=C_GRAY, anchor="e")
        y += 14

        # Create or reuse the embedded graph canvas
        if not hasattr(self, "_graph_canvas"):
            self._graph_canvas = tk.Canvas(
                self, width=PANEL_W - 10, height=GRAPH_SECTION_H,
                bg=C_BG, highlightthickness=0, bd=0
            )
        self._graph_canvas.place(x=5, y=y)
        y += GRAPH_SECTION_H + 4

        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        hp = info["health_pct"]
        filled = hp // 10
        hclr = C_GREEN if hp >= 80 else (C_YELLOW if hp >= 50 else C_RED)
        dots = chr(9679) * filled + chr(9675) * (10 - filled)
        c.create_text(
            W // 2,
            y + 7,
            text="HEALTH %d%%  %s" % (hp, dots),
            font=FONT_DOT,
            fill=hclr,
            anchor="center",
        )
        y += 18
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── ZQ Score Panel (compact, 3 lines) ────────────────────────────────────
        zq_data = info.get("zq")
        if zq_data:
            zq_val = zq_data.get("zq", 0.0)
            zq_grade = zq_data.get("grade", "?")
            zq_trend = zq_data.get("trend", "n/a")
            zq_delta = zq_data.get("delta", 0.0)
            # Color by grade
            if zq_grade in ("A",):
                zq_clr = C_GREEN
            elif zq_grade in ("B",):
                zq_clr = C_CYAN
            elif zq_grade in ("C",):
                zq_clr = C_YELLOW
            else:
                zq_clr = C_RED
            # Trend arrow
            if zq_trend == "improving":
                arrow, arrow_clr = chr(8599), C_GREEN  # ↗
            elif zq_trend == "declining":
                arrow, arrow_clr = chr(8600), C_RED  # ↘
            else:
                arrow, arrow_clr = chr(8594), C_GRAY  # →
            # Line 1: ZQ SCORE label + grade
            c.create_text(12, y + 6, text="ZQ SCORE", font=("Consolas", 9, "bold"),
                          fill=C_CYAN, anchor="w")
            c.create_text(W - 12, y + 6, text="60s refresh",
                          font=("Consolas", 7), fill=C_GRAY, anchor="e")
            y += 14
            # Line 2: Current score + grade (big, color-coded)
            c.create_text(W // 2, y + 7,
                          text="%.3f  (%s)" % (zq_val, zq_grade),
                          font=("Consolas", 11, "bold"), fill=zq_clr, anchor="center")
            y += 18
            # Line 3: 4-component breakdown
            acc = zq_data.get("accuracy", 0.0)
            eff = zq_data.get("efficiency", 0.0)
            spd = zq_data.get("speed", 0.0)
            out = zq_data.get("output", 0.0)
            c.create_text(14, y + 5,
                          text="A:%.2f  E:%.2f  S:%.2f  O:%.2f" % (acc, eff, spd, out),
                          font=("Consolas", 8), fill=C_WHITE, anchor="w")
            y += 13
            # Line 4: Trend
            trend_txt = "7d: %s %s%+.3f" % (zq_trend, arrow, zq_delta)
            c.create_text(14, y + 5, text=trend_txt,
                          font=("Consolas", 8), fill=arrow_clr, anchor="w")
            y += 14
        else:
            c.create_text(W // 2, y + 6, text="ZQ SCORE: pending /zq run",
                          font=("Consolas", 9), fill=C_GRAY, anchor="center")
            y += 16

        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Code Intel Watcher (compact) ──────────────────────────────────────────
        ci = info.get("code_intel")
        if ci and ci.get("status") == "running" and not ci.get("stale"):
            n_proj = ci.get("watched_projects", 0)
            n_changes = ci.get("changes_count", 0)
            n_errors = ci.get("errors_count", 0)
            age = ci.get("age_sec", 0)
            ci_clr = C_GREEN if n_errors == 0 else C_YELLOW
            c.create_text(12, y + 6, text="CODE INTEL", font=("Consolas", 9, "bold"),
                          fill=C_CYAN, anchor="w")
            c.create_text(W - 12, y + 6, text=("live %ds" % age),
                          font=("Consolas", 7), fill=C_GRAY, anchor="e")
            y += 14
            line = "%d projects  %d changes  %d errors" % (n_proj, n_changes, n_errors)
            c.create_text(W // 2, y + 5, text=line,
                          font=("Consolas", 8), fill=ci_clr, anchor="center")
            y += 14
        else:
            ci_status = "no heartbeat" if not ci else ("STALE" if ci.get("stale") else ci.get("status", "?"))
            c.create_text(W // 2, y + 6, text="CODE INTEL: " + ci_status,
                          font=("Consolas", 8), fill=C_GRAY, anchor="center")
            y += 14

        # ── Venv Status (compact 1 line) ─────────────────────────────────────────
        venv_data = info.get("venvs")
        if venv_data:
            vok = venv_data.get("ok", 0)
            vtot = venv_data.get("total", 0)
            vmiss = venv_data.get("missing", 0)
            vclr = C_GREEN if vmiss == 0 else (C_YELLOW if vmiss <= 3 else C_RED)
            vtext = "VENVS  %d/%d ok" % (vok, vtot)
            if vmiss > 0:
                vtext += "  (%d missing)" % vmiss
            c.create_text(W // 2, y + 6, text=vtext,
                          font=("Consolas", 8), fill=vclr, anchor="center")
            y += 14

        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── System Performance ────────────────────────────────────────────────────
        perf = info.get("perf", {})
        c.create_text(
            12,
            y + 6,
            text="SYSTEM PERFORMANCE",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        y += 15

        def perf_bar(val, maxv=100, width=12):
            filled = int(min(val / maxv, 1.0) * width)
            return chr(9608) * filled + chr(9617) * (width - filled)

        def pct_color(pct, warn=70, red=90):
            if pct >= red:
                return C_RED
            if pct >= warn:
                return C_YELLOW
            return C_GREEN

        # CPU
        cpu_pct = perf.get("cpu_pct", 0.0)
        cpu_clr = pct_color(cpu_pct)
        c.create_text(14, y + 5, text="CPU", font=FONT_SMALL, fill=C_GRAY, anchor="w")
        c.create_text(
            40,
            y + 5,
            text="[%s]" % perf_bar(cpu_pct),
            font=("Consolas", 7),
            fill=cpu_clr,
            anchor="w",
        )
        c.create_text(
            W - 12,
            y + 5,
            text="%.0f%%" % cpu_pct,
            font=FONT_SMALL,
            fill=cpu_clr,
            anchor="e",
        )
        y += 12

        # RAM
        ram_pct = perf.get("ram_pct", 0.0)
        ram_free = perf.get("ram_free_gb", 0.0)
        ram_clr = pct_color(ram_pct, warn=60, red=85)
        c.create_text(14, y + 5, text="RAM", font=FONT_SMALL, fill=C_GRAY, anchor="w")
        c.create_text(
            40,
            y + 5,
            text="[%s]" % perf_bar(ram_pct),
            font=("Consolas", 7),
            fill=ram_clr,
            anchor="w",
        )
        c.create_text(
            W - 12,
            y + 5,
            text="%.0fGB free" % ram_free,
            font=FONT_SMALL,
            fill=ram_clr,
            anchor="e",
        )
        y += 12

        # RTX 3090 — GPU util% row
        gpu_util = perf.get("gpu_util_pct", 0.0)
        gpu_temp = perf.get("gpu_temp", 0)
        gpu_clr  = pct_color(gpu_util, warn=70, red=90)
        c.create_text(14, y + 5, text="GPU ", font=FONT_SMALL, fill=C_GRAY, anchor="w")
        c.create_text(40, y + 5, text="[%s]" % perf_bar(gpu_util),
                      font=("Consolas", 7), fill=gpu_clr, anchor="w")
        temp_str = " %d\u00b0C" % gpu_temp if gpu_temp > 0 else ""
        c.create_text(W - 12, y + 5,
                      text="%.0f%%%s" % (gpu_util, temp_str),
                      font=FONT_SMALL, fill=gpu_clr, anchor="e")
        y += 12

        # RTX 3090 — VRAM row
        vram_pct    = perf.get("gpu_vram_pct", 0.0)
        vram_used   = perf.get("gpu_vram_used_gb", 0.0)
        vram_clr    = pct_color(vram_pct, warn=70, red=90)
        c.create_text(14, y + 5, text="VRAM", font=FONT_SMALL, fill=C_GRAY, anchor="w")
        c.create_text(40, y + 5, text="[%s]" % perf_bar(vram_pct),
                      font=("Consolas", 7), fill=vram_clr, anchor="w")
        c.create_text(W - 12, y + 5,
                      text="%.1f/24GB" % vram_used if vram_used > 0 else "0/24GB",
                      font=FONT_SMALL, fill=vram_clr, anchor="e")
        y += 12

        # Drives C and D
        for letter in ["C", "D"]:
            dinfo = perf.get("drives", {}).get(letter)
            if dinfo:
                used, total, pct = dinfo
                dclr = pct_color(pct, warn=80, red=92)
                c.create_text(
                    14,
                    y + 5,
                    text=letter + ":",
                    font=FONT_SMALL,
                    fill=C_GRAY,
                    anchor="w",
                )
                c.create_text(
                    40,
                    y + 5,
                    text="[%s]" % perf_bar(pct),
                    font=("Consolas", 7),
                    fill=dclr,
                    anchor="w",
                )
                c.create_text(
                    W - 12,
                    y + 5,
                    text="%.0f/%.0fGB" % (used, total),
                    font=FONT_SMALL,
                    fill=dclr,
                    anchor="e",
                )
                y += 12

        # Ollama + svchost row
        ollama_on = perf.get("ollama_on", False)
        svchost_n = perf.get("svchost_n", 0)
        py_n = perf.get("py_procs", 0)
        olm_clr = C_GREEN if ollama_on else C_GRAY
        c.create_oval(14, y + 2, 21, y + 9, fill=olm_clr, outline="")
        c.create_text(
            26,
            y + 5,
            text="OLLAMA ON" if ollama_on else "OLLAMA OFF",
            font=FONT_SMALL,
            fill=olm_clr,
            anchor="w",
        )
        svc_clr = C_GREEN if svchost_n < 40 else (C_YELLOW if svchost_n < 60 else C_RED)
        c.create_text(
            W - 12,
            y + 5,
            text="svc%d py%d" % (svchost_n, py_n),
            font=FONT_SMALL,
            fill=svc_clr,
            anchor="e",
        )
        y += 14

        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Skills ────────────────────────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="SKILLS",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        c.create_text(
            W - 12,
            y + 6,
            text="active:%d  inactive:%d"
            % (info["skills_active"], info["skills_inactive"]),
            font=FONT_SMALL,
            fill=C_WHITE,
            anchor="e",
        )
        y += 15
        for sk in info["recent_skills"]:
            sk_s = sk if len(sk) <= 29 else sk[:26] + "..."
            c.create_text(
                20, y + 5, text=">> %s" % sk_s, font=FONT_SMALL, fill=C_GRAY, anchor="w"
            )
            y += 13
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Session ───────────────────────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="SESSION",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        y += 15
        rsl_clr = C_RED if info["rsl_pending"] else C_GREEN
        rsl_txt = "RSL  PENDING" if info["rsl_pending"] else "RSL  CLEAR"
        c.create_oval(20, y + 2, 27, y + 9, fill=rsl_clr, outline="")
        c.create_text(32, y + 5, text=rsl_txt, font=FONT_MAIN, fill=rsl_clr, anchor="w")
        y += 14
        c.create_text(
            20,
            y + 5,
            text="LAST  %s" % info["last_session"],
            font=FONT_MAIN,
            fill=C_WHITE,
            anchor="w",
        )
        y += 14
        lc = info["lessons"]
        c.create_text(
            20,
            y + 5,
            text="LESSONS  %d entries" % lc,
            font=FONT_MAIN,
            fill=C_YELLOW if lc >= 20 else C_WHITE,
            anchor="w",
        )
        y += 14
        sc = info["signals"]
        sig_clr = C_YELLOW if sc > 0 else C_GREEN
        c.create_text(
            20,
            y + 5,
            text="SIGNALS  %d pending" % sc,
            font=FONT_MAIN,
            fill=sig_clr,
            anchor="w",
        )
        y += 14
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Health Gauges ─────────────────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="HEALTH GAUGES",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        y += 15
        for label, val, maxv, warn, red, unit in [
            ("TRANSCRIPTS", info["transcripts_mb"], 500, 150, 400, "MB"),
            ("SKILLS DIR", info["skills_mb"], 20, 5, 10, "MB"),
            ("OC CONFIG", info["opencode_mb"], 200, 50, 150, "MB"),
        ]:
            bar = ascii_bar(val, maxv, 10)
            clr = gauge_color(val, warn, red)
            c.create_text(
                20, y + 5, text=label, font=FONT_SMALL, fill=C_GRAY, anchor="w"
            )
            c.create_text(
                W - 12,
                y + 5,
                text="%.0f%s" % (val, unit),
                font=FONT_SMALL,
                fill=clr,
                anchor="e",
            )
            y += 12
            c.create_text(
                20, y + 5, text="[%s]" % bar, font=("Consolas", 8), fill=clr, anchor="w"
            )
            y += 13
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Persistent Systems ─────────────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="PERSISTENT SYSTEMS",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        y += 15
        for label, status, clr in info.get("persistent", []):
            c.create_oval(20, y + 2, 27, y + 9, fill=clr, outline="")
            c.create_text(
                32, y + 5, text=label, font=FONT_SMALL, fill=C_WHITE, anchor="w"
            )
            c.create_text(
                W - 12, y + 5, text=status, font=FONT_SMALL, fill=clr, anchor="e"
            )
            y += 13
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Processes ─────────────────────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="PROCESSES",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        y += 15
        py_n = info["py_procs"]
        nd_n = info["node_procs"]
        c.create_text(
            20,
            y + 5,
            text="PYTHON  %d procs" % py_n,
            font=FONT_MAIN,
            fill=C_YELLOW if py_n > 8 else C_WHITE,
            anchor="w",
        )
        c.create_text(
            W - 12,
            y + 5,
            text="NODE  %d" % nd_n,
            font=FONT_MAIN,
            fill=C_YELLOW if nd_n > 5 else C_WHITE,
            anchor="e",
        )
        y += 14
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── SDD Spec Status ───────────────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="SDD SPECS",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        y += 15
        for proj, active, stale in info.get("specs", []):
            if active == -1:
                clr = C_GRAY
                stat = "no spec"
            elif active == 0:
                clr = C_GREEN
                stat = "clean"
            elif stale > 0:
                clr = C_RED
                stat = "%d active  %d STALE" % (active, stale)
            else:
                clr = C_YELLOW
                stat = "%d in progress" % active
            c.create_oval(20, y + 2, 27, y + 9, fill=clr, outline="")
            c.create_text(
                32, y + 5, text=proj, font=FONT_SMALL, fill=C_WHITE, anchor="w"
            )
            c.create_text(
                W - 12, y + 5, text=stat, font=FONT_SMALL, fill=clr, anchor="e"
            )
            y += 13
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Action Alerts ─────────────────────────────────────────────────────────
        actions = info["actions"]
        if actions:
            c.create_text(
                12,
                y + 6,
                text="ACTIONS NEEDED",
                font=("Consolas", 9, "bold"),
                fill=C_YELLOW,
                anchor="w",
            )
            y += 15
            for act in actions:
                act_s = act if len(act) <= 32 else act[:29] + "..."
                c.create_text(
                    20, y + 5, text=act_s, font=FONT_SMALL, fill=C_YELLOW, anchor="w"
                )
                y += 12
        else:
            c.create_text(
                W // 2,
                y + 6,
                text="ALL SYSTEMS NOMINAL",
                font=FONT_MAIN,
                fill=C_GREEN,
                anchor="center",
            )
            y += 16
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── C Drive Health ────────────────────────────────────────────────────────
        c_drive = perf.get("drives", {}).get("C")
        if c_drive:
            used_gb, total_gb, pct = c_drive
            free_gb = round(total_gb - used_gb, 1)
            c.create_text(
                12, y + 6, text="C DRIVE", font=("Consolas", 9, "bold"),
                fill=C_CYAN, anchor="w",
            )
            c_clr = C_RED if pct >= 90 else (C_YELLOW if pct >= 75 else C_GREEN)
            bar = ascii_bar(pct, 100, 10)
            c.create_text(W - 12, y + 6, text="%.0f GB free" % free_gb,
                          font=FONT_SMALL, fill=c_clr, anchor="e")
            y += 14
            c.create_text(20, y + 5, text="[%s]" % bar, font=("Consolas", 8), fill=c_clr, anchor="w")
            c.create_text(W - 12, y + 5, text="%.0f%% used" % pct,
                          font=FONT_SMALL, fill=c_clr, anchor="e")
            y += 14
            if pct >= 75:
                c.create_text(20, y + 5, text="! run /disk-cleanup",
                              font=FONT_SMALL, fill=C_YELLOW, anchor="w")
                y += 12
            c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
            y += 8

        # ── CPU Hog Alert ─────────────────────────────────────────────────────────
        top_name = perf.get("top_cpu_name", "")
        top_sec = perf.get("top_cpu_sec", 0)
        if top_name and top_sec > 200:
            hog_clr = C_RED if top_sec > 500 else C_YELLOW
            c.create_text(
                12, y + 6, text="CPU HOG DETECTED",
                font=("Consolas", 9, "bold"), fill=hog_clr, anchor="w",
            )
            y += 14
            name_s = top_name[:26] + "..." if len(top_name) > 29 else top_name
            c.create_text(20, y + 5, text=name_s, font=FONT_SMALL, fill=C_WHITE, anchor="w")
            c.create_text(W - 12, y + 5, text="%.0fs CPU" % top_sec,
                          font=FONT_SMALL, fill=hog_clr, anchor="e")
            y += 14
            c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
            y += 8

        # ── Performance Scores ────────────────────────────────────────────────────
        ps = info.get("perf_scores", {})
        overall = ps.get("overall", 0)
        sessions = ps.get("sessions", 0)
        trend = ps.get("trend", "")

        c.create_text(12, y + 6, text="PERFORMANCE",
                      font=("Consolas", 9, "bold"), fill=C_CYAN, anchor="w")
        trend_clr = C_GREEN if trend == "UP" else (C_RED if trend == "DOWN" else C_GRAY)
        trend_sym = "+" if trend == "UP" else ("-" if trend == "DOWN" else "=")
        c.create_text(W - 12, y + 6,
                      text="7d: %d sessions %s" % (sessions, trend_sym) if sessions > 0 else "no data yet",
                      font=FONT_SMALL, fill=trend_clr, anchor="e")
        y += 15

        if sessions == 0:
            c.create_text(W // 2, y + 6, text="Scores appear after first session ends",
                          font=FONT_SMALL, fill=C_GRAY, anchor="center")
            y += 14
        else:
            # Overall score bar
            o_clr = C_GREEN if overall >= 80 else (C_YELLOW if overall >= 60 else C_RED)
            grade = "A" if overall >= 85 else ("B" if overall >= 70 else ("C" if overall >= 55 else "D"))
            c.create_text(20, y + 5, text="OVERALL", font=FONT_SMALL, fill=C_GRAY, anchor="w")
            c.create_text(W - 12, y + 5, text="%d/100 [%s]" % (overall, grade),
                          font=("Consolas", 9, "bold"), fill=o_clr, anchor="e")
            y += 13

            # Individual scores in two columns
            metrics = [
                ("Speed",    ps.get("speed", 0)),
                ("Accuracy", ps.get("accuracy", 0)),
                ("Tokens",   ps.get("tokens", 0)),
                ("Skills",   ps.get("skills", 0)),
                ("Memory",   ps.get("memory", 0)),
            ]
            for i, (label, val) in enumerate(metrics):
                col = i % 2
                row = i // 2
                xbase = 20 if col == 0 else (W // 2 + 5)
                ypos = y + row * 13
                m_clr = C_GREEN if val >= 75 else (C_YELLOW if val >= 50 else C_RED)
                c.create_text(xbase, ypos + 5, text="%s:%d" % (label, val),
                              font=FONT_SMALL, fill=m_clr, anchor="w")
            y += (len(metrics) // 2 + 1) * 13

        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        # ── Commands Quick-Ref (top 6) ────────────────────────────────────────────
        c.create_text(
            12,
            y + 6,
            text="COMMANDS",
            font=("Consolas", 9, "bold"),
            fill=C_CYAN,
            anchor="w",
        )
        c.create_text(
            W - 12,
            y + 6,
            text="[right-click: all]",
            font=("Consolas", 7),
            fill=C_GRAY,
            anchor="e",
        )
        y += 14
        for cmd, desc in ALL_COMMANDS[:6]:
            c.create_text(
                20, y + 4, text=cmd, font=FONT_SMALL, fill=C_WHITE, anchor="w"
            )
            c.create_text(
                W - 12, y + 4, text=desc, font=FONT_SMALL, fill=C_GRAY, anchor="e"
            )
            y += 12

        # ── Footer ────────────────────────────────────────────────────────────────
        y += 4
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 6
        c.create_text(
            W // 2,
            y + 5,
            text="REFRESHED %s" % info["refreshed"],
            font=("Consolas", 7),
            fill=C_GRAY,
            anchor="center",
        )
        y += 14

        self._resize(max(y + 6, 400))

    def _draw_collapsed(self, c, info, W):
        c.create_rectangle(
            1, 1, W - 1, PANEL_H_MINI - 1, outline=C_BORDER, fill=C_BG, width=1
        )
        hp = info["health_pct"]
        hclr = C_GREEN if hp >= 80 else (C_YELLOW if hp >= 50 else C_RED)
        dots = chr(9679) * (hp // 10) + chr(9675) * (10 - hp // 10)
        c.create_text(
            W // 2,
            PANEL_H_MINI // 2,
            text="M.O.T.H.E.R  %d%%  %s" % (hp, dots),
            font=FONT_DOT,
            fill=hclr,
            anchor="center",
        )
        self.geometry("%dx%d" % (W, PANEL_H_MINI))

    def _draw_commands(self, c, W):
        c.create_rectangle(1, 1, W - 1, 2000, outline=C_BORDER, fill=C_BG, width=1)
        for sy in range(0, 2000, 4):
            c.create_line(3, sy, W - 3, sy, fill="#0a0a18", width=1)

        y = 10
        c.create_text(
            W // 2,
            y + 8,
            text="ALL COMMANDS",
            font=FONT_TITLE,
            fill=C_MAG,
            anchor="center",
        )
        y += 22
        c.create_line(10, y, W - 10, y, fill=C_BORDER, width=1)
        y += 8

        for cmd, desc in ALL_COMMANDS:
            c.create_text(14, y + 4, text=cmd, font=FONT_SMALL, fill=C_CYAN, anchor="w")
            y += 12
            c.create_text(
                18, y + 4, text=desc, font=("Consolas", 7), fill=C_GRAY, anchor="w"
            )
            y += 12
            c.create_line(10, y, W - 10, y, fill=C_DIM, width=1)
            y += 4

        y += 4
        c.create_text(
            W // 2,
            y + 6,
            text="right-click > Toggle Commands to go back",
            font=("Consolas", 7),
            fill=C_GRAY,
            anchor="center",
        )
        y += 16
        self._resize(max(y + 6, 200))

    # ── Resize ────────────────────────────────────────────────────────────────────
    def _resize(self, new_h):
        x = self.winfo_x()
        y = self.winfo_y()
        self.cv.config(height=new_h)
        self.geometry("%dx%d+%d+%d" % (PANEL_W, new_h, x, y))

    # ── Drag ──────────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._dx = e.x_root - self.winfo_x()
        self._dy = e.y_root - self.winfo_y()

    def _drag_move(self, e):
        self.geometry("+%d+%d" % (e.x_root - self._dx, e.y_root - self._dy))

    # ── Menu actions ──────────────────────────────────────────────────────────────
    def _right_click(self, e):
        try:
            self._menu.tk_popup(e.x_root, e.y_root)
        finally:
            self._menu.grab_release()

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        if not self._collapsed:
            self.cv.config(height=600)
            self.geometry("%dx%d" % (PANEL_W, 600))
        self._draw()

    def _toggle_cmds(self):
        self._show_cmds = not self._show_cmds
        self._collapsed = False
        self.cv.config(height=600)
        self.geometry("%dx%d" % (PANEL_W, 600))
        self._draw()

    def _open_monitor(self):
        if SKILL_MONITOR.exists():
            os.startfile(str(SKILL_MONITOR))
        else:
            os.startfile(str(pathlib.Path(__file__).parent.parent))

    def _hide_to_tray(self):
        """Hide window to tray — does NOT exit. Widget stays alive."""
        self.withdraw()

    def _show_from_tray(self):
        """Restore window from tray."""
        self.deiconify()
        self.lift()
        self.wm_attributes("-topmost", True)

    def _quit(self):
        self._running = False
        self.destroy()


# ── System Tray ───────────────────────────────────────────────────────────────────
def _make_tray_icon(widget):
    if not HAS_TRAY:
        return None
    try:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([8, 8, 56, 56], outline=(0, 240, 255, 255), width=3)
        d.ellipse([20, 20, 44, 44], fill=(0, 240, 255, 200))

        def on_show(icon, item):
            widget.after(0, widget._show_from_tray)

        def on_hide(icon, item):
            widget.after(0, widget._hide_to_tray)

        def on_quit(icon, item):
            icon.stop()
            widget.after(0, widget._quit)

        menu = pystray.Menu(
            pystray.MenuItem("Show Widget", on_show),
            pystray.MenuItem("Hide Widget", on_hide),
            pystray.MenuItem("Refresh Now", lambda icon, item: widget.after(0, widget._manual_refresh)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", on_quit),
        )
        icon = pystray.Icon("Mother", img, "M.O.T.H.E.R v5.0 — running", menu)
        # Double-click tray icon = toggle show/hide
        icon.default_action = on_show
        # NON-daemon: tray thread keeps the process alive even if mainloop exits.
        # This is intentional — the process must survive opencode/terminal closing.
        t = threading.Thread(target=icon.run, daemon=False, name="MotherTray")
        t.start()
        return icon
    except Exception:
        return None


if __name__ == "__main__":
    import ctypes
    import os
    import sys
    import subprocess

    # ── True process detachment ────────────────────────────────────────────────
    # If we were launched by OpenCode/terminal, relaunch via Windows shell
    # so our parent becomes explorer.exe (never dies) instead of OpenCode.
    # --detached flag marks the relaunched copy so it doesn't loop.
    if "--detached" not in sys.argv:
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        script = os.path.abspath(__file__)
        workdir = os.path.dirname(script)
        # Use ShellExecute via ctypes — makes explorer.exe the parent
        ctypes.windll.shell32.ShellExecuteW(
            None, "open", pythonw,
            f'"{script}" --detached',
            workdir, 0  # SW_HIDE
        )
        sys.exit(0)  # Exit the OpenCode-owned copy immediately

    # We are the detached copy — explorer.exe is our parent
    # Break any remaining signal chain
    try:
        ctypes.windll.kernel32.SetConsoleCtrlHandler(None, True)
    except Exception:
        pass

    # ── Crash-resistant mainloop ───────────────────────────────────────────────
    # Log errors to a file (pythonw has no console) and restart on crash.
    # Only a deliberate _quit() (sets _running=False) or explicit Exit stops the widget.
    import traceback

    LOG = pathlib.Path(__file__).parent / "widget_crash.log"

    def _log(msg: str):
        try:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
        except Exception:
            pass

    _log("Widget starting (detached, explorer.exe parent)")

    _tray_icon = None
    while True:
        try:
            widget = MotherWidget()
            if _tray_icon is None:
                # Only create tray once — reuse across restarts
                _tray_icon = _make_tray_icon(widget)
            widget.mainloop()

            # mainloop() returned cleanly — check if user chose Exit
            if not widget._running:
                _log("Widget exited cleanly via Exit menu")
                if _tray_icon is not None:
                    try:
                        _tray_icon.stop()
                    except Exception:
                        pass
                break

            # mainloop() exited but _running is still True = unexpected exit.
            # Restart the window (tray stays alive, process stays alive).
            _log("mainloop() exited unexpectedly — restarting window in 2s")
            time.sleep(2)

        except Exception as exc:
            _log(f"CRASH: {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
            time.sleep(3)
            _log("Restarting after crash...")
