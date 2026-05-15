---
description: "Compress context — fold verbose outputs, summarize bloat, reclaim tokens."
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /compress-now — Deterministic Context Compressor

Compress the current conversation context to reclaim tokens. Rule-based, zero extra LLM calls on data — you (Claude) apply the rules directly.

## Step 1 — Assess Current Context

Review the conversation so far. Identify:
- Large tool outputs (backtest logs, pandas dumps, JSON filings, MCP results)
- Repeated information (same data shown multiple times)
- Verbose intermediate results no longer needed
- Raw data that can be summarized (time-series, filing dumps, code diffs)

## Step 2 — Apply Compression Rules (in order)

1. **Time-series folding**: Replace full OHLCV dumps with summary: `{ticker} | {start}→{end} | {rows} rows | close range [{min}–{max}]`
2. **Backtest collapse**: Replace verbose backtest output with: `Strategy: {name} | CAGR: {x}% | Sharpe: {x} | MaxDD: {x}% | Win%: {x}% | Trades: {n}`
3. **Filing dedup**: If same company/filing data appears multiple times, keep only the latest version
4. **DataFrame → summary**: Replace printed DataFrames with: `DataFrame: {rows}×{cols} | cols: [list] | dtypes: {summary}`
5. **JSON folding**: Replace large JSON with: key structure + value counts + sample of first 2 entries
6. **Code diff collapse**: Replace large diffs with: `{n} files changed | +{added} -{removed} | key changes: [list]`
7. **Error trace trim**: Keep only the final exception + the 2 most relevant stack frames
8. **Duplicate removal**: If information was stated, then re-read, then re-stated — keep only the final version
9. **MCP output trim**: Tool results that were consumed and acted on → replace with `[Used: {tool} → {1-line result}]`

## Step 3 — Check Telemetry

```bash
if [ -f "$HOME/.mother/telemetry/usage.jsonl" ]; then
    echo "=== Session Tool Usage ==="
    python3 -c "
import json
from collections import defaultdict
stats = defaultdict(lambda: {'calls': 0, 'chars': 0, 'tokens': 0})
with open('$HOME/.mother/telemetry/usage.jsonl') as f:
    for line in f:
        try:
            e = json.loads(line)
            t = e['tool']
            stats[t]['calls'] += 1
            stats[t]['chars'] += e.get('output_chars', 0)
            stats[t]['tokens'] += e.get('est_tokens', 0)
        except: pass
print(f'{'Tool':<20} {'Calls':>6} {'Chars':>10} {'~Tokens':>10}')
print('─' * 48)
total_tokens = 0
for t, s in sorted(stats.items(), key=lambda x: -x[1]['tokens']):
    print(f'{t:<20} {s[\"calls\"]:>6} {s[\"chars\"]:>10,} {s[\"tokens\"]:>10,}')
    total_tokens += s['tokens']
print('─' * 48)
print(f'{'TOTAL':<20} {sum(s[\"calls\"] for s in stats.values()):>6} {sum(s[\"chars\"] for s in stats.values()):>10,} {total_tokens:>10,}')
"
fi
```

## Step 4 — Report Compression

After applying rules, report:

```
COMPRESSION REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Items compressed:    [N]
Rules applied:       [list which rules fired]
Est. tokens before:  [N]
Est. tokens after:   [N]
Savings:             [N] tokens (~[X]%)

Stored references:   [N] in .mother/compressed/
Use /rewind to restore any compressed item.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 5 — Compressed References

Check for stored originals:
```bash
if [ -d "$HOME/.mother/compressed" ]; then
    echo "=== Stored References ==="
    ls -la "$HOME/.mother/compressed/"*.ref 2>/dev/null | wc -l
    echo "files stored for /rewind recovery"
fi
```

## Quant-Specific Rules (always enforce)

- NEVER compress: adjusted_close values, filing_date fields, strategy parameters, ticker symbols
- ALWAYS compress: raw OHLCV beyond summary stats, verbose pandas .describe() output, repeated error traces
- Preserve: any data law violations flagged during session (these are lessons, not bloat)
