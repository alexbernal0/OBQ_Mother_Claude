---
name: auto-tool
description: "Monitors conversations for repeated bash commands, Python snippets, SQL queries, and processes that are candidates for extraction into reusable scripts or utilities. When the same pattern appears 3+ times, proposes crystallizing it into a named tool in ~/.claude/tools/ or the project scripts/ folder. Use when user says 'auto-tool on', 'watch for tools', or 'detect repeated tools'."
---

# Auto-Tool

> **In one sentence:** When I notice the same command, script, or process repeated 3+ times, I offer to crystallize it into a named, reusable tool — so you never type it again.

---

## How It Differs From auto-skill

| auto-skill | auto-tool |
|---|---|
| Detects multi-step **workflows** (high-level processes) | Detects repeated **commands, scripts, or code snippets** |
| Output: SKILL.md (Claude behavior instruction) | Output: Python script, bash script, or SQL template |
| "How Claude should do X" | "Reusable executable that does X" |
| Examples: "run backtest + log results + deploy" | Examples: `eodhd_fetch.py`, `md_connect.py`, `atr_size.py` |

Both can fire in the same session. They are complementary.

---

## When Auto-Tool Is Active

Auto-tool is **always-on in silent mode**. It tracks patterns automatically and only surfaces an offer when the threshold is crossed.

- **Silent mode (always on):** Track patterns. No output until threshold crossed.
- **Explicit mode** (`auto-tool on` / `/autotool-on`): More aggressive — offers for 2+ repetitions and borderline cases.

---

## Detection Criteria

### Tier 1 — Bash Commands (threshold: 3 identical or semantically equivalent)

```bash
# Repeated 3x in a session → auto-tool candidate:
python "C:/Users/admin/.../deploy.py" all
PYTHONIOENCODING=utf-8 python deploy.py skills
gh auth status

# Pattern variations that count as the same:
python deploy.py skills
python deploy.py soul
python deploy.py hooks
→ These are 3 variants of "python deploy.py [target]" → candidate for deploy_obq.sh
```

### Tier 2 — Python Snippets (threshold: 2+ files or 3+ usages same session)

```python
# Same connection pattern in 3 places → candidate for md_connect():
import duckdb, os
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

# Same data loading pattern → candidate for load_close():
df = conn.execute("SELECT date, Symbol, adjusted_close FROM ...").df()
close = df.pivot(index='date', columns='Symbol', values='adjusted_close')
close.index = pd.to_datetime(close.index)

# Same VBT setup block → candidate for vbt_setup():
import sys; sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")
from PWB_tools import data_loader as dl, indicators as ind, signals as sig
```

### Tier 3 — SQL Queries (threshold: 2+ semantically equivalent queries)

```sql
-- Same table + same WHERE structure → candidate for a parameterized query template
SELECT date, Symbol, adjusted_close
FROM PROD_EODHD.main.PROD_EOD_survivorship
WHERE date >= '2020-01-01' AND date <= '2025-12-31'
ORDER BY date, Symbol
```

### Tier 4 — API Call Patterns (threshold: 2+ call sites without a wrapper)

```python
# Direct EODHD call appearing 2+ places → candidate for eodhd_get_eod():
resp = requests.get(f"https://eodhd.com/api/eod/{ticker}",
                    params={"api_token": os.getenv("EODHD_API_KEY"), "fmt": "json"})
```

---

## Before Offering — Checklist

Confirm ALL before surfacing an offer:

- [ ] Pattern has crossed the threshold (3x bash, 2x Python/SQL/API)
- [ ] No equivalent tool exists in `~/.claude/tools/`, project `scripts/`, or `PWB_tools/`
- [ ] Pattern is **generalizable** — not hardcoded to a single context
- [ ] The abstraction is worth the complexity (saves >5 minutes over 10 uses)
- [ ] Not better as a MEMORY.md entry (e.g., one-time setup fact)

---

## The Three Options

When the checklist passes, surface:

> I've seen this pattern 3+ times: `[brief description]`.
> This looks like a good candidate for a reusable tool.
>
> 1. **Extract It** — Create a named script/function now; you review before saving.
> 2. **Skip** — Note it as a candidate but don't extract now (won't re-offer this session).
> 3. **Show Me First** — Show me all detected candidates at session end (batch mode).

---

## Handling Each Choice

### 1. Extract It

Generate the tool in this order:

1. **Name** the tool: `verb_noun.py` format (e.g., `connect_motherduck.py`, `load_ohlcv.py`, `fetch_eodhd.py`)
2. **Determine scope:**
   - Reusable across all OBQ projects → `~/.claude/tools/[name].py`
   - Project-specific → `[project]/scripts/[name].py`
3. **Write the tool file:**
   - Full docstring: what it does, parameters, returns, usage example
   - Type hints
   - No hardcoded secrets — use `os.getenv()`
   - Comprehensive error handling with specific exception messages
4. **Show full path + full contents** — wait for explicit user approval before writing
5. **After saving:** Show how to use it with one-line import: `from tools.connect_motherduck import connect_md`

**Standard tool template:**
```python
#!/usr/bin/env python3
"""
[tool_name].py — [What it does in one sentence]

Usage:
    from tools.[tool_name] import [main_function]

    result = [main_function]([params])

Parameters:
    param_name (type): description

Returns:
    type: description
"""
import os
from typing import Optional

def [main_function]([params]) -> [return_type]:
    """[One-sentence docstring]."""
    # implementation
```

### 2. Skip

Acknowledge and continue. Do not re-offer for this pattern this session. The pattern IS recorded in session memory as a "seen but skipped" candidate — available in `/rsl-status`.

### 3. Show Me First

Continue working. At session end (before stopping), present ALL candidates detected this session:

```
AUTO-TOOL CANDIDATES DETECTED THIS SESSION:
1. MotherDuck connection pattern (3 usages) → proposed: connect_md.py
2. EODHD bulk fetch pattern (2 usages) → proposed: fetch_eodhd_bulk.py
3. OHLCV pivot + date convert pattern (2 files) → proposed: pivot_ohlcv.py

Which would you like to extract? (1, 2, 3, all, none)
```

---

## OBQ-Specific Patterns to Watch For

These are common OBQ patterns that are strong auto-tool candidates:

| Pattern | Proposed Tool | Scope |
|---|---|---|
| `duckdb.connect(f"md:?motherduck_token=...")` | `connect_md.py` | `~/.claude/tools/` |
| EODHD `requests.get` with rate limiter | `eodhd_client.py` | `~/.claude/tools/` |
| Parquet load + pivot + date convert | `load_ohlcv.py` | project `scripts/` |
| VBT `from_order_func` setup block | Already a skill (`vbt-patterns`) | — |
| `sys.path.insert(0, r"D:\Master...") + imports` | `pwb_setup.py` | `~/.claude/tools/` |
| `pf.value().iloc[:, 0]` + metrics extraction | Already in `PWB_tools.metrics` | — |
| GitHub auth check + status report | `gh_status.sh` | `~/.claude/tools/` |
| Deploy + verify cycle | Already a command (`deploy.py`) | — |

The "Already covered" entries mean auto-tool should NOT offer extraction — it's covered.

---

## Integration With ~/.claude/tools/

`~/.claude/tools/` is OBQ's personal tool library — scripts that are too specific for a PyPI package but too general to live in one project.

**Structure:**
```
~/.claude/tools/
├── connect_md.py       # MotherDuck connection factory
├── eodhd_client.py     # EODHD API wrapper with rate limiter
├── load_ohlcv.py       # Parquet load + pivot + date normalize
├── pwb_setup.py        # PapersWBacktest path + standard imports
└── README.md           # What each tool does
```

**Add to PYTHONPATH** (add to any project's session startup):
```python
import sys
sys.path.insert(0, r"C:\Users\admin\.claude\tools")
from connect_md import connect_md
from load_ohlcv import load_close_wide
```

---

## Relationship to auto-skill

When a pattern could be either:
- **Pure code/script** with no Claude reasoning needed → `auto-tool` (Python/bash script)
- **Workflow requiring Claude judgment** → `auto-skill` (SKILL.md)

When both apply (e.g., a complex pipeline with both code and judgment): create BOTH — the tool for the code, the skill for the orchestration.

---

## Examples

**Example 1: MotherDuck connection (Tier 2 Python)**
- Pattern: `duckdb.connect(f"md:?motherduck_token={os.getenv(...)}")` appears in 3 files
- Offer: "Extract to `~/.claude/tools/connect_md.py`?"
- Result: One-line import replaces 3-line block everywhere

**Example 2: Deploy sequence (Tier 1 Bash)**
- Pattern: `PYTHONIOENCODING=utf-8 python deploy.py skills` run 3x with different targets
- Offer: "Extract to `deploy_obq.sh [target]`?"
- Result: `./deploy_obq.sh skills` replaces the long command

**Example 3: Covered by existing module (no offer)**
- Pattern: ATR sizing calculation repeated
- Check: Already in `PWB_tools.indicators.atr` + `PWB_tools.commission`
- No offer — covered.

**Example 4: Too specific (no offer)**
- Pattern: One-time data cleaning step for a specific backfill
- No offer — not generalizable, one-time only.

---

## Turning Auto-Tool Off

"stop watching for tools", "auto-tool off", "skip all tools". Re-enable with `/autotool-on` or "auto-tool on".

---

## Troubleshooting

**Symptom:** Tool file created but import fails.
- **Cause:** `~/.claude/tools/` not on PYTHONPATH.
- **Solution:** Add `sys.path.insert(0, r"C:\Users\admin\.claude\tools")` at module load time.

**Symptom:** Same pattern detected but not offered.
- **Cause:** Pattern count below threshold, or equivalent already exists.
- **Solution:** Run `/rsl-status` to see detected candidates below threshold.

**Symptom:** Too many offers disrupting workflow.
- **Cause:** Explicit mode too aggressive.
- **Solution:** Use "Show Me First" option — batches all offers to session end.

---

*auto-tool | OBQ_Mother_Claude | v1.0 | 2026-02-28*
