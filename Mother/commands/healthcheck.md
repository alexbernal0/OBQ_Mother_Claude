---
description: "Full system health — processes, bloat, skills, MCPs, RSL status, token telemetry, zombie detection."
argument-hint: "[--clean]"
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /healthcheck — Mother System Health Dashboard

Single unified health check. Merges /debloat (system resources) + /rsl-status (learning loop) + skill/MCP usage tracking + zombie detection.

## Section 1 — System Resources

### Processes
```bash
echo "=== SYSTEM RESOURCES ==="
echo ""
echo "Python:"
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum | ForEach-Object { Write-Output \"  Count: \$(\$_.Count) | Total: \$([math]::Round(\$_.Sum/1MB))MB\" }"
echo "Node:"
powershell -Command "Get-Process node -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum | ForEach-Object { Write-Output \"  Count: \$(\$_.Count) | Total: \$([math]::Round(\$_.Sum/1MB))MB\" }"
echo "VS Code:"
powershell -Command "Get-Process Code -ErrorAction SilentlyContinue | Measure-Object -Property WorkingSet64 -Sum | ForEach-Object { Write-Output \"  Count: \$(\$_.Count) | Total: \$([math]::Round(\$_.Sum/1MB))MB\" }"
echo "MCP Servers:"
powershell -Command "Get-Process | Where-Object { \$_.ProcessName -match 'mcp|supergateway|npx' } | Measure-Object -Property WorkingSet64 -Sum | ForEach-Object { Write-Output \"  Count: \$(\$_.Count) | Total: \$([math]::Round(\$_.Sum/1MB))MB\" }"
```

### .claude Directory
```bash
echo ""
echo "=== .CLAUDE DIRECTORY ==="
CLAUDE_DIR="$HOME/.claude"
powershell -Command "foreach (\$d in @('transcripts','file-history','projects','skills','commands','hooks')) { \$p = Join-Path '$CLAUDE_DIR' \$d; if (Test-Path \$p) { \$size = [math]::Round((Get-ChildItem \$p -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB); \$count = (Get-ChildItem \$p -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count; Write-Output \"  \$d: \${size}MB (\$count files)\" } }"
echo ""
echo "Stale transcripts (>30 days):"
powershell -Command "\$stale = Get-ChildItem '$HOME/.claude/transcripts' -Recurse -ErrorAction SilentlyContinue | Where-Object { \$_.LastWriteTime -lt (Get-Date).AddDays(-30) }; \$mb = [math]::Round((\$stale | Measure-Object Length -Sum).Sum/1MB); Write-Output \"  \$(\$stale.Count) files, \${mb}MB reclaimable\""
```

## Section 2 — Skill Health & Zombie Detection

```bash
echo ""
echo "=== SKILL HEALTH ==="
echo ""
echo "Active skills:"
for d in "$HOME/.claude/skills"/*/; do
    if [ -d "$d" ]; then
        name=$(basename "$d")
        modified=$(stat -c '%Y' "$d" 2>/dev/null || powershell -Command "(Get-Item '$d').LastWriteTime.ToString('yyyy-MM-dd')" 2>/dev/null)
        echo "  $name (modified: $modified)"
    fi
done
echo ""
echo "Inactive skills:"
for d in "$HOME/.claude/skills-inactive"/*/; do
    if [ -d "$d" ]; then
        echo "  $(basename "$d") [INACTIVE]"
    fi
done
```

### Usage Telemetry
```bash
echo ""
echo "=== TOKEN TELEMETRY ==="
if [ -f "$HOME/.mother/telemetry/usage.jsonl" ]; then
    python3 -c "
import json, os
from collections import defaultdict
from datetime import datetime, timedelta

log = os.path.expanduser('~/.mother/telemetry/usage.jsonl')
stats = defaultdict(lambda: {'calls': 0, 'tokens': 0})
total_tokens = 0
today = datetime.now().date()
week_ago = today - timedelta(days=7)
week_tokens = 0

with open(log) as f:
    for line in f:
        try:
            e = json.loads(line)
            t = e['tool']
            tokens = e.get('est_tokens', 0)
            stats[t]['calls'] += 1
            stats[t]['tokens'] += tokens
            total_tokens += tokens
            ts = datetime.fromisoformat(e['ts']).date()
            if ts >= week_ago:
                week_tokens += tokens
        except: pass

print(f'Session total: ~{total_tokens:,} tokens across {sum(s[\"calls\"] for s in stats.values())} tool calls')
print(f'Last 7 days:   ~{week_tokens:,} tokens')
print()
print(f'{\"Tool\":<20} {\"Calls\":>6} {\"~Tokens\":>10}')
print('─' * 38)
for t, s in sorted(stats.items(), key=lambda x: -x[1]['tokens'])[:10]:
    print(f'{t:<20} {s[\"calls\"]:>6} {s[\"tokens\"]:>10,}')
" 2>/dev/null
else
    echo "  No telemetry data yet. Compressor hook will start collecting after next tool use."
fi
```

## Section 3 — RSL Status

```bash
echo ""
echo "=== RSL LOOP STATUS ==="

# Pending flags
echo ""
echo "Pending Flags:"
if [ -f "$HOME/.claude/.pending-supermemory-review" ]; then
    AGE=$(powershell -Command "((Get-Date) - (Get-Item '$HOME/.claude/.pending-supermemory-review').LastWriteTime).Days")
    echo "  .pending-supermemory-review → FOUND ($AGE days old)"
else
    echo "  .pending-supermemory-review → clear"
fi

if [ -f "$HOME/.claude/.last-session-date" ]; then
    echo "  Last session: $(cat "$HOME/.claude/.last-session-date")"
fi

# lessons.md
echo ""
echo "Lessons:"
LESSONS=$(find "$HOME/.claude/projects" -name "lessons.md" 2>/dev/null | head -5)
if [ -n "$LESSONS" ]; then
    for l in $LESSONS; do
        COUNT=$(grep -c "^## \|^### \|^- Date:" "$l" 2>/dev/null || echo "0")
        echo "  $l → $COUNT entries"
    done
else
    echo "  No lessons.md found"
fi

# Recent skill changes
echo ""
echo "Skills modified (last 7 days):"
powershell -Command "Get-ChildItem '$HOME/.claude/skills' -Directory -ErrorAction SilentlyContinue | Where-Object { \$_.LastWriteTime -gt (Get-Date).AddDays(-7) } | ForEach-Object { Write-Output \"  \$(\$_.Name) (\$(\$_.LastWriteTime.ToString('yyyy-MM-dd')))\" }"
```

## Section 4 — Compressed References

```bash
echo ""
echo "=== COMPRESSOR STATE ==="
if [ -d "$HOME/.mother/compressed" ]; then
    REF_COUNT=$(ls "$HOME/.mother/compressed/"*.ref 2>/dev/null | wc -l)
    echo "  Stored references: $REF_COUNT"
    TOTAL_SIZE=$(powershell -Command "[math]::Round((Get-ChildItem '$HOME/.mother/compressed' -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1KB)")
    echo "  Storage used: ${TOTAL_SIZE}KB"
else
    echo "  .mother/compressed/ not yet created"
fi

if [ -d "$HOME/.mother/crystals" ]; then
    CRYSTAL_COUNT=$(ls "$HOME/.mother/crystals/"*.yaml 2>/dev/null | wc -l)
    echo "  Strategy crystals: $CRYSTAL_COUNT"
else
    echo "  No crystals yet (use /crystallize after a backtest)"
fi
```

## Section 5 — Summary Dashboard

Print the unified dashboard:

```
MOTHER HEALTHCHECK — [DATE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM         Python: [N] procs [MB]  |  Node: [N] procs [MB]
               VS Code: [N] procs [MB] |  MCP: [N] procs [MB]
               .claude: [MB] total     |  Stale: [MB] reclaimable

SKILLS         Active: [N]  |  Inactive: [N]  |  Zombies: [N]
               Recently modified: [list]

TOKENS         Session: ~[N] tokens  |  This week: ~[N] tokens
               Top consumer: [tool] (~[N] tokens)
               Compressed refs: [N] stored

RSL            Pending review: [yes/no]  |  Lessons: [N] entries
               Last synthesis: [date]    |  Status: [OK/ACTION NEEDED]

CRYSTALS       [N] strategies crystallized

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATIONS:
- [Top 3 actions based on findings above]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If `--clean` flag is passed: auto-delete stale transcripts, clear old compressed refs (>30 days), and archive zombie skills to skills-inactive/.
