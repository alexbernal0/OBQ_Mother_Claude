---
description: "Audit system resource usage — Python, Node, VS Code processes, .claude directory bloat, MCP health."
argument-hint: "[--clean]"
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /debloat — System Resource Audit

Windows-native resource audit for Claude Code environments. Flags bloat, offers cleanup.

## Step 1 — Python Processes

```bash
echo "=== Python Processes ==="
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, @{N='MemMB';E={[math]::Round(\$_.WorkingSet64/1MB)}}, CommandLine | Sort-Object MemMB -Descending | Format-Table -AutoSize"
echo ""
echo "Flagged (>500MB):"
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Where-Object { \$_.WorkingSet64 -gt 500MB } | Select-Object Id, @{N='MemMB';E={[math]::Round(\$_.WorkingSet64/1MB)}} | Format-Table -AutoSize"
```

## Step 2 — Node Processes

```bash
echo "=== Node Processes ==="
powershell -Command "Get-Process node -ErrorAction SilentlyContinue | Select-Object Id, @{N='MemMB';E={[math]::Round(\$_.WorkingSet64/1MB)}}, CommandLine | Sort-Object MemMB -Descending | Format-Table -AutoSize"
echo ""
echo "Flagged (>300MB):"
powershell -Command "Get-Process node -ErrorAction SilentlyContinue | Where-Object { \$_.WorkingSet64 -gt 300MB } | Select-Object Id, @{N='MemMB';E={[math]::Round(\$_.WorkingSet64/1MB)}} | Format-Table -AutoSize"
```

## Step 3 — VS Code Processes

```bash
echo "=== VS Code Processes ==="
powershell -Command "\$procs = Get-Process Code -ErrorAction SilentlyContinue; \$count = (\$procs | Measure-Object).Count; \$totalMB = [math]::Round((\$procs | Measure-Object WorkingSet64 -Sum).Sum/1MB); Write-Output \"Count: \$count | Total: \${totalMB}MB\"; if (\$totalMB -gt 3072) { Write-Output 'WARNING: VS Code total >3GB' }"
```

## Step 4 — .claude Directory Size

```bash
echo "=== .claude Directory Audit ==="
CLAUDE_DIR="$HOME/.claude"
powershell -Command "foreach (\$d in @('transcripts','file-history','projects')) { \$p = Join-Path '$CLAUDE_DIR' \$d; if (Test-Path \$p) { \$size = [math]::Round((Get-ChildItem \$p -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB); Write-Output \"\$d: \${size}MB\" } }"
```

## Step 5 — Stale Transcripts (>30 days)

```bash
echo "=== Stale Files (>30 days) ==="
echo "Transcripts:"
powershell -Command "Get-ChildItem '$HOME/.claude/transcripts' -Recurse -ErrorAction SilentlyContinue | Where-Object { \$_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Select-Object Name, @{N='MB';E={[math]::Round(\$_.Length/1MB,1)}}, LastWriteTime | Format-Table -AutoSize"
echo "File-history:"
powershell -Command "Get-ChildItem '$HOME/.claude/file-history' -Recurse -ErrorAction SilentlyContinue | Where-Object { \$_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Select-Object Name, @{N='MB';E={[math]::Round(\$_.Length/1MB,1)}}, LastWriteTime | Format-Table -AutoSize"
```

If `--clean` flag: delete stale files. Otherwise, report count and total size.

## Step 6 — MCP Server Health

```bash
echo "=== MCP Servers ==="
powershell -Command "Get-Process | Where-Object { \$_.ProcessName -match 'mcp|supergateway|npx' } | Select-Object Id, ProcessName, @{N='MemMB';E={[math]::Round(\$_.WorkingSet64/1MB)}} | Format-Table -AutoSize"
```

## Step 7 — Summary

Print a table:

```
=== DEBLOAT SUMMARY ===
Python:       [count] processes, [total]MB [OK/WARNING]
Node:         [count] processes, [total]MB [OK/WARNING]
VS Code:      [count] processes, [total]MB [OK/WARNING]
.claude:      [total]MB across transcripts/file-history/projects
Stale files:  [count] files, [size]MB reclaimable
MCP servers:  [count] running, [total]MB

Recommendations:
- [List any actions needed based on flags above]
- [e.g., "Kill 2 python processes using >500MB each"]
- [e.g., "Delete 15 stale transcripts to reclaim 230MB"]
```
