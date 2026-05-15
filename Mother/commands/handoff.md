---
description: "Session snapshot + handoff — compressed state export for seamless session continuity. Saves ZQ score, code intel status, and what was done."
argument-hint: "[--save | --show | --snapshot | --restore]"
allowed-tools: "Bash"
---

# /handoff — Session Snapshot & Handoff v3

Captures full session state before you close or restart OpenCode.
Parses `$ARGUMENTS` for mode: `--show` (display only), `--snapshot` (full YAML export), `--restore` (read last snapshot). Default is `--save`.

---

## Step 1 — Gather Machine + Git Context

```powershell
Write-Host "=== Session Handoff ==="
Write-Host "Machine: $env:COMPUTERNAME | Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm') | User: $env:USERNAME"
$projectRoot = git rev-parse --show-toplevel 2>$null
if (-not $projectRoot) { $projectRoot = (Get-Location).Path }
Write-Host "Project: $projectRoot"
$branch = git rev-parse --abbrev-ref HEAD 2>$null
$commit = git log -1 --format='%h %s' 2>$null
$ahead  = git rev-list --count '@{u}..HEAD' 2>$null
Write-Host "Branch: $branch  Commit: $commit  Ahead: $ahead"
git diff --stat HEAD 2>$null
git ls-files --others --exclude-standard 2>$null | Select-Object -First 10
```

---

## Step 2 — Gather Mother System State

```powershell
# ZQ Score
$zqScript = "C:\Users\admin\Desktop\MotherV4\Mother\system\zq_score.py"
if (Test-Path $zqScript) {
    Write-Host "`n=== ZQ Score ==="
    python $zqScript --latest 2>$null
}

# Code Intel Watcher status
$watcherScript = "C:\Users\admin\Desktop\MotherV4\Mother\system\code_intel_watcher.py"
if (Test-Path $watcherScript) {
    Write-Host "`n=== Code Intel Watcher ==="
    $wi = python $watcherScript --status 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($wi) {
        Write-Host "Status: $($wi.status)  Projects: $($wi.watched_projects)  Changes today: $($wi.changes_count)  Errors: $($wi.errors_count)"
    }
}

# OpenCode session health
$script = @'
import sqlite3, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
db = pathlib.Path.home() / ".local" / "share" / "opencode" / "opencode.db"
if not db.exists(): sys.exit(0)
con = sqlite3.connect(str(db), timeout=3)
rows = con.execute("""
    SELECT s.title, COUNT(m.id) c
    FROM session s JOIN message m ON m.session_id = s.id
    WHERE s.parent_id IS NULL
    GROUP BY s.id ORDER BY c DESC LIMIT 5
""").fetchall()
print("\n=== Session Health ===")
for r in rows:
    label = "[CRITICAL]" if r[1]>300 else "[WARNING] " if r[1]>150 else "[OK]      "
    print(f"  {label} {r[1]:4d} msgs  {(r[0] or 'untitled')[:60]}")
con.close()
'@
$script | python 2>$null

# Mother snapshot state
$crystals = @(Get-ChildItem "$env:USERPROFILE\.mother\crystals" -Filter "*.yaml" -ErrorAction SilentlyContinue).Count
$snaps    = @(Get-ChildItem "$env:USERPROFILE\.mother\snapshots" -ErrorAction SilentlyContinue).Count
$rsl      = Test-Path "$env:USERPROFILE\.claude\.pending-supermemory-review"
Write-Host "`nCrystals: $crystals  Snapshots: $snaps  RSL pending: $rsl"
```

---

## Step 3 — Generate Handoff Document

Based on the conversation history, git state, and Mother system state above, synthesize and write this exact structure:

```markdown
# Session Handoff
<!-- Generated: YYYY-MM-DD HH:MM | Machine: HOSTNAME | Branch: BRANCH -->

## What Was Done
- [Concise bullets — specific files changed, features added, bugs fixed]
- [Include file paths and function names where relevant]

## Current State
- **Branch:** branch-name (N commits ahead)
- **Last commit:** hash — message
- **Tests/Build:** passing / failing / not run
- **ZQ Score:** X.XXX (Grade) — Trend: direction
- **Code Intel:** N projects watched, N changes today

## Key Decisions Made
- [Decision + one-line rationale]

## Open Questions / Blockers
- [ ] [Specific question or blocker]

## Next Steps (Start Here)
1. [Exact first action — specific enough to start cold]
2. [Second priority]
3. [Third priority]

## Files Modified This Session
[From git diff --stat or manual list]

## Environment & Gotchas
- [Any env vars, running services, or gotchas discovered]

## Restore Commands
```powershell
cd "<project_root>"
git checkout <branch>
python "C:\Users\admin\Desktop\MotherV4\Mother\system\code_intel_watcher.py" --status
```
```

---

## Step 4 — Mode-Specific Save Actions

```powershell
$ARGS_RAW = "$ARGUMENTS"
$MODE = "save"
if ($ARGS_RAW -match "--show")     { $MODE = "show" }
if ($ARGS_RAW -match "--snapshot") { $MODE = "snapshot" }
if ($ARGS_RAW -match "--restore")  { $MODE = "restore" }

if ($MODE -eq "restore") {
    $latest = Get-ChildItem "$env:USERPROFILE\.mother\snapshots" -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latest) {
        Write-Host "=== Restoring from: $($latest.Name) ==="
        Get-Content $latest.FullName
    } else {
        Write-Host "No snapshots found at $env:USERPROFILE\.mother\snapshots"
    }
    return
}

if ($MODE -ne "show") {
    # Always save to .claude/handoff.md
    $handoffFile = "$env:USERPROFILE\.claude\handoff.md"
    # (the above generated markdown gets written here by the AI)
    Write-Host "Handoff saved: $handoffFile"

    # Update NOW.md
    $nowFile = "C:\Users\admin\Desktop\MotherV4\Mother\soul\NOW.md"
    if (Test-Path $nowFile) {
        Write-Host "Updating NOW.md..."
        # AI updates the active_task and next_step fields in NOW.md
    }
}

if ($MODE -eq "snapshot") {
    $snapDir = "$env:USERPROFILE\.mother\snapshots"
    New-Item -ItemType Directory -Force -Path $snapDir | Out-Null
    $snapFile = "$snapDir\snapshot_$(Get-Date -Format 'yyyyMMdd_HHmm').yaml"
    # AI writes the full YAML snapshot here
    Write-Host "Snapshot saved: $snapFile"
    Write-Host "Restore with: /handoff --restore"
}

Write-Host ""
Write-Host "Handoff complete. Safe to restart OpenCode."
Write-Host "On next session: /handoff --restore OR read .claude/handoff.md"
```
