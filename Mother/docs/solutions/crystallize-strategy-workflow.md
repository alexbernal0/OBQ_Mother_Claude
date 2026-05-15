# Crystallize — Strategy Session Workflow
**When:** After completing any backtest in PapersWithBacktest, OBQ_Strategies_*, or any strategy session
**Why:** Preserves signal logic, parameters, and performance in a compact reusable crystal so future sessions start with full context without re-reading notebooks

---

## The Problem It Solves

Without crystallize:
- Start new session → re-read 500-line notebook → 15,000 tokens wasted
- Parameters buried in outputs → have to re-run to find them
- Cross-strategy comparison impossible → each session is isolated

With crystallize:
- Start new session → load crystal → 800 tokens, full context
- Parameters in YAML → queryable, comparable
- Second brain knows your full strategy corpus

---

## When to Run It

Run `/crystallize <name>` immediately after:
- ✅ Completing a backtest with real results (Sharpe, returns, drawdown)
- ✅ Implementing a new signal from a paper
- ✅ Finding a parameter set worth preserving
- ✅ Discovering a strategy variant that beats baseline

Don't run it for:
- ❌ Failed/broken backtests
- ❌ Exploratory data analysis with no signal
- ❌ Infrastructure changes (use compound-knowledge instead)

---

## What a Crystal Contains

Saved to: `C:\Users\admin\.mother\crystals\<name>-<date>.yaml`

```yaml
strategy: RSI_Momentum_v1
date: 2026-04-29
paper: "Momentum and Reversal in Financial Markets (Jegadeesh 1993)"
project: OBQ_Strategies_Master_Corpus_26
notebook: rsi_momentum_backtest.ipynb

signal:
  entry: RSI(14) crosses above 30 after being below 25 for 3+ bars
  exit: RSI crosses above 70 OR 20-bar holding period
  universe: SP500 constituents, price > $10, adv > $1M
  timeframe: daily

parameters:
  rsi_period: 14
  entry_threshold: 30
  oversold_threshold: 25
  lookback_bars: 3
  exit_rsi: 70
  max_hold_bars: 20

sizing:
  method: equal_weight
  max_position_pct: 5.0
  max_positions: 20

performance:
  period: 2015-01-01 to 2025-12-31
  sharpe: 1.24
  cagr: 14.2%
  max_drawdown: -18.3%
  win_rate: 54%
  total_trades: 847

notes:
  - Works best in mean-reverting regimes
  - Degrades significantly in trending markets (2020-2021)
  - Add regime filter (VIX < 25) improves Sharpe to 1.61
  - OBQ score integration pending

status: validated  # draft | validated | deployed | retired
```

---

## How to Load a Crystal in a New Session

In any strategy session:
```
Load crystal for RSI_Momentum_v1
```

Or explicitly:
```
Read C:\Users\admin\.mother\crystals\RSI_Momentum_v1-20260429.yaml
```

The session_checkpoint hook now auto-reminds you to crystallize when it detects backtest keywords.

---

## Cross-Strategy Comparison

Once you have 5+ crystals, run:
```
Compare all crystals in .mother/crystals/ — rank by Sharpe, show parameter patterns
```

This gives you a portfolio view of your strategy corpus without re-running anything.

---

## Integration with PapersWithBacktest

In your PapersWithBacktest workflow:
1. Implement strategy from paper → run backtest
2. Record results in notebook
3. Run `/crystallize <paper-slug>` → YAML saved
4. Second brain now knows this strategy permanently
5. Next session: load crystal → extend/modify with full context in <1000 tokens

The corpus in `OBQ_Strategies_Master_Corpus_26` (198 Python files) should have one crystal per validated strategy. Currently 0 crystals exist — this is the gap.
