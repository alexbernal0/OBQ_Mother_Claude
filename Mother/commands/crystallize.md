---
description: "Distill a strategy/backtest/session into an ultra-compact crystal for cross-project reuse."
argument-hint: "[strategy-name]"
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /crystallize — Quant Strategy Crystallizer

Distill any completed strategy, backtest, or research session into an ultra-compact "crystal" file (~200 tokens). Crystals are the minimum viable knowledge unit for cross-project reuse.

## Step 1 — Gather Source Material

Look for the strategy/backtest data in this priority order:
1. If a strategy name argument is given, search for it in the current project
2. Most recent backtest output in conversation context
3. Current notebook outputs
4. `knowledge/backtest_results_log.md` entries
5. Ask user what to crystallize

Extract these fields (all required):
- **Strategy name** and version
- **Signal logic** (1-2 sentence summary)
- **Universe** (what symbols, timeframe, data source)
- **Key parameters** (entry/exit thresholds, lookback periods, sizing)
- **Performance** (CAGR, Sharpe, MaxDD, Win%, total trades)
- **Data requirements** (adjusted_close, filing_date, specific fields)
- **Invariants** (rules that must hold — no lookahead, no survivorship bias, etc.)
- **Lessons learned** (what worked, what didn't, gotchas discovered)

## Step 2 — Create Crystal File

```bash
mkdir -p "$HOME/.mother/crystals"
```

Write to `$HOME/.mother/crystals/{strategy_name}_{date}.yaml`:

```yaml
# Strategy Crystal — {strategy_name}
# Generated: {YYYY-MM-DD} | Source: {project_name}
# ~200 tokens — minimum viable knowledge for reuse

strategy:
  name: "{name}"
  version: "{version}"
  signal: "{1-2 sentence signal logic summary}"
  type: "{long_short|long_only|short_only|market_neutral}"

universe:
  symbols: "{description — e.g., S&P 500 constituents, all US equities}"
  timeframe: "{daily|weekly|monthly}"
  period: "{start_date} → {end_date}"
  data_source: "{EODHD|other}"

parameters:
  # Only the parameters that matter for reproduction
  entry: "{entry condition + threshold}"
  exit: "{exit condition + threshold}"
  lookback: "{N periods}"
  sizing: "{method — e.g., ATR-based, equal weight, percent equity}"
  rebalance: "{frequency}"

performance:
  cagr: "{X.X}%"
  sharpe: "{X.XX}"
  max_drawdown: "{X.X}%"
  win_rate: "{X.X}%"
  total_trades: "{N}"
  profit_factor: "{X.XX}"
  benchmark: "{benchmark name}: {CAGR}%"

invariants:
  - adjusted_close_only
  - filing_date_only  # never quarter_date
  - no_survivorship_bias
  # Add any strategy-specific invariants discovered

lessons:
  - "{what worked — be specific}"
  - "{what didn't work — be specific}"
  - "{gotcha discovered — save others the pain}"

reproduction:
  notebook: "{path to source notebook}"
  data_file: "{path to data if applicable}"
  dependencies: ["{package versions that matter}"]
```

## Step 3 — Update Crystal Index

```bash
CRYSTAL_INDEX="$HOME/.mother/crystals/INDEX.md"
```

Append to INDEX.md (create if needed):

```markdown
| {date} | {strategy_name} | {signal_type} | CAGR:{X}% Sharpe:{X} | {crystal_filename} |
```

## Step 4 — Cross-Reference

Check if this strategy should be logged to project backtest results:
- If `knowledge/backtest_results_log.md` exists in current project → offer to update it
- If similar crystal exists → show comparison table (old vs new performance)

## Step 5 — Report

```
CRYSTAL CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Strategy:    {name} v{version}
Signal:      {1-line summary}
Performance: CAGR {X}% | Sharpe {X} | MaxDD {X}%
File:        .mother/crystals/{filename}
Size:        ~{N} tokens (vs ~{original_size} raw)
Compression: {X}% reduction

Cross-project reuse:
  Load with: "Check .mother/crystals/{filename}"
  Search:    /crystal-search {keyword}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Quant Rules (enforced)

- NEVER crystallize with raw close — must be adjusted_close
- NEVER include quarter_date — filing_date only
- ALWAYS include the invariants section — this prevents future sessions from repeating mistakes
- If performance looks unrealistic (Sharpe >3, CAGR >50%), flag it with a warning in the crystal
