---
description: "Full OpenCode debloat — kills zombies, vacuums DB, preserves session knowledge via handoff, reports health. Run before restarting OpenCode."
argument-hint: "[--clean | --dry-run | --report-only]"
allowed-tools: "Bash"
---

# /debloat — OpenCode Full Debloat & Cleanup

Windows-native 8-phase debloat. Preserves session knowledge BEFORE cleaning.
Parses `$ARGUMENTS` for `--clean` (delete stale files), `--dry-run` / `--report-only` (no changes).

---

## Phase 0 — Setup & Flags

```powershell
$ARGS_RAW = "$ARGUMENTS"
$DRY_RUN  = $ARGS_RAW -match "--dry-run|--report-only"
$CLEAN    = $ARGS_RAW -match "--clean"
$DEBLOAT_LOG = "$env:USERPROFILE\.local\share\opencode\debloat-last-run.log"
New-Item -ItemType Directory -Force -Path (Split-Path $DEBLOAT_LOG) | Out-Null
"========================================`nOpenCode Debloat Log`n========================================`nTimestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`nMode: $(if ($DRY_RUN) {'DRY RUN'} else {'LIVE'})`n" | Set-Content $DEBLOAT_LOG -Encoding UTF8
Write-Host "[Phase 0] Setup complete. DRY_RUN=$DRY_RUN  CLEAN=$CLEAN"
Write-Host "Log: $DEBLOAT_LOG"
```

---

## Phase 0.5 — Pre-Debloat Knowledge Extraction (CRITICAL — runs BEFORE any cleanup)

This preserves session knowledge before anything is deleted. Never skip this.

```powershell
"=== Phase 0.5: Pre-Debloat Knowledge Extraction ===" | Add-Content $DEBLOAT_LOG
$DB = "$env:USERPROFILE\.local\share\opencode\opencode.db"
$HANDOFF_DIR = "$env:USERPROFILE\.mother\handoffs"
New-Item -ItemType Directory -Force -Path $HANDOFF_DIR | Out-Null

if (Test-Path $DB) {
    $script = @"
import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8')
db = r'$DB'
con = sqlite3.connect(db, timeout=3)
con.row_factory = sqlite3.Row
rows = con.execute("""
    SELECT s.id, COUNT(m.id) as cnt, COALESCE(SUBSTR(s.title,1,70),'untitled') as title
    FROM session s JOIN message m ON m.session_id = s.id
    WHERE s.parent_id IS NULL
    GROUP BY s.id HAVING COUNT(m.id) >= 30
    ORDER BY COUNT(m.id) DESC LIMIT 10
""").fetchall()
for r in rows:
    print(f"{r['cnt']}|{r['id']}|{r['title']}")
con.close()
"@
    $sessions = $script | python 2>$null
    if ($sessions) {
        Write-Host "High-value sessions (>=30 messages):"
        $sessions | ForEach-Object {
            $parts = $_ -split "\|", 3
            Write-Host "  [$($parts[0]) msgs] $($parts[2])"
        }
        # Auto-generate handoff summary
        $ts = Get-Date -Format "yyyy-MM-dd_HHmm"
        $handoffContent = @"
# Pre-Debloat Handoff — $(Get-Date -Format 'yyyy-MM-dd HH:mm')

## Sessions Preserved
$($sessions | ForEach-Object {
    $p = $_ -split "\|", 3
    "- **$($p[2])** ($($p[0]) messages) — ID: $($p[1])"
} | Out-String)

## Action Required on Next Session
1. Review sessions above — reopen any needing continuation
2. Run ``/zq --latest`` to check ZQ score for last session
3. Run ``/session-start`` to re-orient

## Auto-Generated
By ``/debloat`` Phase 0.5 at $ts
"@
        $handoffFile = "$HANDOFF_DIR\handoff-debloat-$ts.md"
        $handoffContent | Set-Content $handoffFile -Encoding UTF8
        # Also write to .claude/handoff.md
        $handoffContent | Set-Content "$env:USERPROFILE\.claude\handoff.md" -Encoding UTF8 -ErrorAction SilentlyContinue
        Write-Host "Handoff saved: $handoffFile"
        "Sessions preserved + handoff written to: $handoffFile" | Add-Content $DEBLOAT_LOG
    } else {
        Write-Host "No high-value sessions found (all < 30 messages)"
        "No high-value sessions." | Add-Content $DEBLOAT_LOG
    }
} else {
    Write-Host "OpenCode DB not found — skipping session extraction"
}
Write-Host "[Phase 0.5 COMPLETE]"
```

---

## Phase 1 — Data Collection (Read-Only)

```powershell
"=== Phase 1: Data Collection ===" | Add-Content $DEBLOAT_LOG
$DB = "$env:USERPROFILE\.local\share\opencode\opencode.db"

# Python processes
$py = Get-Process python,pythonw -ErrorAction SilentlyContinue
$pyCount = ($py | Measure-Object).Count
$pyMB = [math]::Round(($py | Measure-Object WorkingSet64 -Sum).Sum/1MB)
$pyZombies = @($py | Where-Object {$_.WorkingSet64 -lt 10MB -and $_.CPU -lt 0.1}).Count
Write-Host "Python: $pyCount processes  ${pyMB}MB total  ($pyZombies idle zombies)"

# OpenCode/Node processes
$oc = Get-Process OpenCode,opencode-cli,node -ErrorAction SilentlyContinue
$ocCount = ($oc | Measure-Object).Count
$ocMB = [math]::Round(($oc | Measure-Object WorkingSet64 -Sum).Sum/1MB)
Write-Host "OpenCode/Node: $ocCount processes  ${ocMB}MB total"
if ($ocMB -gt 1500) { Write-Host "  WARNING: OpenCode using >1.5GB — restart recommended" }

# DB health
if (Test-Path $DB) {
    $script2 = @'
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
import pathlib
db = pathlib.Path.home() / ".local" / "share" / "opencode" / "opencode.db"
con = sqlite3.connect(str(db), timeout=3)
pages = con.execute("PRAGMA page_count;").fetchone()[0]
free  = con.execute("PRAGMA freelist_count;").fetchone()[0]
frag  = int(free*100/pages) if pages > 0 else 0
sessions = con.execute("SELECT COUNT(*) FROM session WHERE parent_id IS NULL;").fetchone()[0]
msgs     = con.execute("SELECT COUNT(*) FROM message;").fetchone()[0]
bloated  = con.execute("SELECT COUNT(*) FROM (SELECT COUNT(*) c FROM message m JOIN session s ON s.id=m.session_id WHERE s.parent_id IS NULL GROUP BY s.id HAVING c > 200);").fetchone()[0]
wal = db.parent / "opencode.db-wal"
wal_mb = round(wal.stat().st_size/1024/1024, 1) if wal.exists() else 0
print(f"DB: {round(db.stat().st_size/1024/1024,1)}MB  WAL: {wal_mb}MB  Frag: {frag}%")
print(f"Sessions: {sessions} top-level  Messages: {msgs}")
if bloated: print(f"WARNING: {bloated} sessions with >200 msgs (context rot)")
con.close()
'@
    $script2 | python 2>$null
}

# .claude dir sizes
@("transcripts","file-history","projects") | ForEach-Object {
    $p = "$env:USERPROFILE\.claude\$_"
    if (Test-Path $p) {
        $sz = [math]::Round((Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)
        $stale = @(Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30) -and -not $_.PSIsContainer}).Count
        Write-Host ".claude/$_: ${sz}MB  ($stale files stale >30d)"
    }
}

# Code intel watcher
$hb = "$env:USERPROFILE\.mother\watcher_heartbeat.json"
if (Test-Path $hb) {
    $hbData = Get-Content $hb | ConvertFrom-Json
    Write-Host "Code Intel Watcher: $($hbData.status)  $($hbData.watched_projects) projects  $($hbData.changes_count) changes"
}

Write-Host "[Phase 1 COMPLETE]"
```

---

## Phase 2 — Kill Zombie Python Processes

```powershell
"=== Phase 2: Zombie Python Cleanup ===" | Add-Content $DEBLOAT_LOG
$zombies = Get-Process python,pythonw -ErrorAction SilentlyContinue |
    Where-Object {$_.WorkingSet64 -lt 10MB -and $_.CPU -lt 0.1}
$killed = 0
foreach ($z in $zombies) {
    if (-not $DRY_RUN) {
        Stop-Process -Id $z.Id -Force -ErrorAction SilentlyContinue
        $killed++
        Write-Host "  Killed zombie PID $($z.Id) ($([math]::Round($z.WorkingSet64/1MB))MB)"
    } else {
        Write-Host "  [DRY RUN] Would kill PID $($z.Id) ($([math]::Round($z.WorkingSet64/1MB))MB)"
    }
}
Write-Host "Zombies killed: $killed"
Write-Host "[Phase 2 COMPLETE]"
```

---

## Phase 3 — MCP & Background Process Check

```powershell
"=== Phase 3: MCP/Background Check ===" | Add-Content $DEBLOAT_LOG
$mcpProcs = Get-Process | Where-Object {$_.ProcessName -match "mcp|supergateway|npx"}
if ($mcpProcs) {
    $mcpProcs | Select-Object Id, ProcessName, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}} | Format-Table -AutoSize
} else {
    Write-Host "  No rogue MCP processes found"
}
Write-Host "[Phase 3 COMPLETE]"
```

---

## Phase 4 — OpenCode DB Maintenance

```powershell
"=== Phase 4: DB Maintenance ===" | Add-Content $DEBLOAT_LOG
$script3 = @'
import sqlite3, sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
db = pathlib.Path.home() / ".local" / "share" / "opencode" / "opencode.db"
if not db.exists():
    print("DB not found")
    sys.exit(0)
con = sqlite3.connect(str(db), timeout=5)
pages = con.execute("PRAGMA page_count;").fetchone()[0]
free  = con.execute("PRAGMA freelist_count;").fetchone()[0]
frag  = int(free*100/pages) if pages > 0 else 0
if frag > 15:
    print(f"Fragmentation {frag}% > 15% — running VACUUM...")
    con.execute("VACUUM;")
    con.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    print("VACUUM complete")
else:
    print(f"Fragmentation {frag}% — OK, running ANALYZE only")
con.execute("ANALYZE;")
con.close()
print("ANALYZE complete")
'@
if (-not $DRY_RUN) {
    $script3 | python 2>$null
} else {
    Write-Host "  [DRY RUN] Would run ANALYZE/VACUUM if needed"
}
Write-Host "[Phase 4 COMPLETE]"
```

---

## Phase 5 — Stale File Cleanup

```powershell
"=== Phase 5: Stale File Cleanup ===" | Add-Content $DEBLOAT_LOG
$totalDeleted = 0
$totalMB = 0
@("$env:USERPROFILE\.claude\file-history", "$env:USERPROFILE\.claude\projects") | ForEach-Object {
    if (Test-Path $_) {
        $stale = Get-ChildItem $_ -Recurse -ErrorAction SilentlyContinue |
            Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30) -and -not $_.PSIsContainer}
        $sizeMB = [math]::Round(($stale | Measure-Object Length -Sum).Sum/1MB, 1)
        if ($stale.Count -gt 0) {
            if ($CLEAN -and -not $DRY_RUN) {
                $stale | Remove-Item -Force -ErrorAction SilentlyContinue
                Write-Host "  Deleted $($stale.Count) stale files (${sizeMB}MB) from $(Split-Path $_ -Leaf)"
                $totalDeleted += $stale.Count
                $totalMB += $sizeMB
            } else {
                Write-Host "  Found $($stale.Count) stale files (${sizeMB}MB) in $(Split-Path $_ -Leaf) — run with --clean to delete"
            }
        }
    }
}
Write-Host "Stale files deleted: $totalDeleted (${totalMB}MB reclaimed)"
Write-Host "[Phase 5 COMPLETE]"
```

---

## Phase 6 — OpenCode Storage Cleanup

```powershell
"=== Phase 6: OpenCode Storage ===" | Add-Content $DEBLOAT_LOG
$storage = "$env:USERPROFILE\.local\share\opencode\storage"
if (Test-Path $storage) {
    $totalSz = [math]::Round((Get-ChildItem $storage -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)
    Write-Host "OpenCode storage: ${totalSz}MB"
    Get-ChildItem $storage -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $sz = [math]::Round((Get-ChildItem $_.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)
        if ($sz -gt 1) { Write-Host "  $($_.Name): ${sz}MB" }
    }
}
# Clean tool-output cache (safe — just cached bash output)
$toolOut = "$env:USERPROFILE\.local\share\opencode\tool-output"
if (Test-Path $toolOut) {
    $outFiles = Get-ChildItem $toolOut -ErrorAction SilentlyContinue
    $outSzMB = [math]::Round(($outFiles | Measure-Object Length -Sum).Sum/1MB, 1)
    $staleOut = @($outFiles | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-1)})
    Write-Host "tool-output cache: $($outFiles.Count) files  ${outSzMB}MB  ($($staleOut.Count) older than 1d)"
    if ($CLEAN -and -not $DRY_RUN -and $staleOut.Count -gt 0) {
        $staleOut | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "  Cleaned $($staleOut.Count) stale tool-output files"
    }
}
Write-Host "[Phase 6 COMPLETE]"
```

---

## Phase 7 — ZQ Score + Code Intel Health

```powershell
"=== Phase 7: ZQ + Code Intel Health ===" | Add-Content $DEBLOAT_LOG
# ZQ score
$zqScript = "C:\Users\admin\Desktop\MotherV4\Mother\system\zq_score.py"
if (Test-Path $zqScript) {
    $zqOut = python $zqScript --summary 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($zqOut) {
        Write-Host "ZQ Score: $($zqOut.zq) ($($zqOut.grade))  Trend: $($zqOut.trend_direction) ($([math]::Round($zqOut.trend_delta,3):+#;-#;0})"
        Write-Host "  Accuracy:$($zqOut.accuracy)  Efficiency:$($zqOut.efficiency)  Speed:$($zqOut.speed)  Output:$($zqOut.output)"
    }
}
# Code intel watcher
$watcherScript = "C:\Users\admin\Desktop\MotherV4\Mother\system\code_intel_watcher.py"
if (Test-Path $watcherScript) {
    $wiOut = python $watcherScript --status 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
    if ($wiOut) {
        Write-Host "Code Intel: $($wiOut.status)  $($wiOut.watched_projects) projects  $($wiOut.changes_count) changes  $($wiOut.errors_count) errors"
    }
}
Write-Host "[Phase 7 COMPLETE]"
```

---

## Phase 8 — Final Summary & Restart Recommendation

```powershell
"=== Phase 8: Final Summary ===" | Add-Content $DEBLOAT_LOG
Write-Host ""
Write-Host "================================================"
Write-Host "  DEBLOAT SUMMARY"
Write-Host "================================================"

# Current state
$py2 = @(Get-Process python,pythonw -ErrorAction SilentlyContinue)
$oc2 = @(Get-Process OpenCode,opencode-cli,node -ErrorAction SilentlyContinue)
$py2MB = [math]::Round(($py2 | Measure-Object WorkingSet64 -Sum).Sum/1MB)
$oc2MB = [math]::Round(($oc2 | Measure-Object WorkingSet64 -Sum).Sum/1MB)

Write-Host "  Python processes:  $($py2.Count)  (${py2MB}MB)"
Write-Host "  OpenCode/Node:     $($oc2.Count)  (${oc2MB}MB)"

# Session message count (context rot signal)
$script4 = @'
import sqlite3, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
db = pathlib.Path.home() / ".local" / "share" / "opencode" / "opencode.db"
if not db.exists(): sys.exit(0)
con = sqlite3.connect(str(db), timeout=3)
row = con.execute("SELECT MAX(c) FROM (SELECT COUNT(*) c FROM message m JOIN session s ON s.id=m.session_id WHERE s.parent_id IS NULL GROUP BY s.id)").fetchone()
print(row[0] or 0)
con.close()
'@
$maxMsgs = $script4 | python 2>$null
Write-Host "  Heaviest session:  $maxMsgs messages"

# Recommendation
Write-Host ""
if ([int]$maxMsgs -gt 300) {
    Write-Host "  ACTION REQUIRED: This session has $maxMsgs messages — RESTART OPENCODE NOW" -ForegroundColor Red
    Write-Host "  1. Your handoff was saved to: $env:USERPROFILE\.mother\handoffs\"
    Write-Host "  2. Restart OpenCode"
    Write-Host "  3. Start fresh — use /handoff --show to restore context"
} elseif ([int]$maxMsgs -gt 150) {
    Write-Host "  RECOMMENDED: Session getting heavy ($maxMsgs msgs) — consider restarting soon" -ForegroundColor Yellow
} else {
    Write-Host "  HEALTHY: Session is clean ($maxMsgs msgs)" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Log: $DEBLOAT_LOG"
Write-Host "================================================"
Write-Host "[ALL PHASES COMPLETE]"
"[Debloat complete: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')]" | Add-Content $DEBLOAT_LOG
```
