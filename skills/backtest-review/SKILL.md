---
name: backtest-review
description: "Post-backtest quality review checklist. Use after completing any VBT backtest to validate results are realistic, check for biases, verify methodology, and log results. Also triggers run_tearsheet for institutional reporting."
---

# Post-Backtest Quality Review

Run this checklist every time a backtest completes. A result that clears all checks is a result you can discuss with confidence. A result that fails a check is not yet a result.

---

## 1. RESULTS SANITY CHECKS

Compare your output metrics against these reference ranges. Numbers outside these ranges are not automatically wrong — but they require an explanation before you move on.

### Return Metrics

| Strategy Type | Typical CAGR | Suspicious Threshold | Notes |
|---|---|---|---|
| Trend following (L+S) | 8–20% | >35% | Clenow v3a 36.5% is explained by leverage=5 |
| Momentum factor | 10–25% | >40% | Survivorship bias inflates above this |
| Mean reversion | 6–15% | >30% | |
| Factor (HML, SMB etc.) | 5–12% | >20% | Long-only factor long-run |
| Pure long equity | 8–12% | >20% (unleveraged) | Matches market CAGR roughly |

### Risk Metrics

| Metric | Good Range | Red Flag |
|---|---|---|
| Sharpe ratio | 0.5–1.5 | >2.5 without leverage explanation |
| Sortino ratio | 0.7–2.0 | >3.5 |
| Max Drawdown | 15–40% | <5% (too good) or >60% (leverage/bug) |
| Calmar ratio | 0.3–1.0 | >2.0 |
| Annualized vol | 8–25% | <3% (suspect smoothing) or >40% (excess leverage) |

### Trade Statistics

| Metric | Good Range | Red Flag |
|---|---|---|
| Trade count | 50–2000 per 10yr / 50 assets | <30 = statistically thin; >5000 on 50 assets = logic bug |
| Win rate (trend following) | 38–52% | >65% (look-ahead) or <30% (check exits) |
| Win rate (momentum) | 55–68% | >75% |
| Profit factor | 1.2–2.5 | >3.5 or <1.0 (net loss) |
| Avg holding period | 10–100 days (trend) | <2 days on daily bars (check for off-by-one) |

### Quick Sanity Print

```python
# Print full sanity summary after any backtest
def print_sanity_summary(pf, nav, strategy_name="Strategy"):
    """Quick post-run sanity output."""
    import vectorbt as vbt
    import numpy as np

    returns = nav.pct_change().dropna()
    n_years = len(nav) / 252.0

    cagr      = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1
    ann_vol   = returns.std() * np.sqrt(252)
    sharpe    = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
    max_dd    = ((nav / nav.cummax()) - 1).min()
    calmar    = cagr / abs(max_dd) if max_dd != 0 else np.nan

    # Trade stats from portfolio object
    trades = pf.trades.records_readable
    n_trades  = len(trades)
    win_rate  = (trades['PnL'] > 0).mean() if n_trades > 0 else np.nan

    print(f"\n{'='*50}")
    print(f"  {strategy_name}")
    print(f"{'='*50}")
    print(f"  Period:      {nav.index[0].date()} – {nav.index[-1].date()} ({n_years:.1f}yr)")
    print(f"  CAGR:        {cagr*100:.1f}%")
    print(f"  Sharpe:      {sharpe:.2f}")
    print(f"  MaxDD:       {max_dd*100:.1f}%")
    print(f"  Calmar:      {calmar:.2f}")
    print(f"  Ann Vol:     {ann_vol*100:.1f}%")
    print(f"  N Trades:    {n_trades}")
    print(f"  Win Rate:    {win_rate*100:.1f}%" if not np.isnan(win_rate) else "  Win Rate:    N/A")
    print(f"{'='*50}\n")
```

---

## 2. LOOK-AHEAD BIAS CHECKLIST

Look-ahead bias is the most common and most damaging error in backtesting. Check each item explicitly — do not assume.

### Signal Timing

```
[ ] All entry signals use .shift(1) before being passed to the backtest
    WHY: today's signal fires on close data available at end of day.
         You can only act on it at the NEXT day's open (or next close).
    CHECK: if entries_long uses today's SMA cross, and from_order_func
           executes at today's close, you are using future information.
    FIX:  entries_long_shifted = entries_long.shift(1).fillna(False)

[ ] ATR trailing stops use yesterday's stop level
    CHECK: exits_long = close < stop_long.shift(1)  ← correct
           exits_long = close < stop_long           ← look-ahead
    WHY:  stop_long on day T is computed using close[T]. Comparing
          close[T] against stop[T] = circular reference.

[ ] Rolling max/min for breakout uses expanding window ending at current bar
    CHECK: close.rolling(N).max() includes ONLY past N bars, not future
    VBT note: rolling() in pandas is correct by default (trailing window)

[ ] All `.shift(1)` calls are on SIGNAL DataFrames, not on price data
    (shifting prices changes the signal semantics entirely)
```

### Fundamental Data Joins

```
[ ] Joined on filing_date, not quarter_date or report_date
    RULE: the quarterly earnings for Q1 2023 might be FILED in May 2023.
          Joining on quarter_date = March 31, 2023 would use data
          that wasn't publicly available until May 2023.

[ ] No forward-fill of fundamentals beyond 6 months
    RULE: if a company hasn't filed in 6+ months, treat as missing,
          not as still-valid.

[ ] Test: pick any row in your backtest output, find its date D.
    For each fundamental feature in that row, verify it was PUBLIC
    (i.e., filing_date <= D) on date D.
```

### Universe Selection

```
[ ] Universe is defined as of each backtest date (not survivorship-biased)
    WRONG: "S&P 500 current constituents" — includes hindsight (only survivors)
    BETTER: use point-in-time constituent data or note survivorship as a limitation

[ ] No symbols included that didn't exist at the start of the backtest
    CHECK: for each symbol, confirm data starts before your backtest start date
    VBT behavior: symbols with NaN at start are fine — VBT skips them until
                  data begins, so early NaN is handled correctly
```

---

## 3. COMMISSION AND COST CHECK

```
[ ] Commission is included in the backtest
    STANDARD: 0.0002 (2 bps) for liquid futures/ETFs
    STANDARD: 0.0005–0.001 for equity strategies
    NOTE: zero commission = not a production-ready result

[ ] Leverage impact is documented in the result notes
    STANDARD: Clenow uses leverage=5. Document explicitly so results
              are not misread as unleveraged.

[ ] Slippage: note in results whether modeled or not
    ACCEPTABLE: not modeling slippage on daily strategies with liquid assets
    REQUIRED NOTE: "No slippage modeled — results are optimistic for illiquid assets"

[ ] Commission formula used:
    fees = commission * dollar_value
    e.g., 0.0002 * $10,000 = $2 per trade
    This is what lock_cash=True and the fees parameter in from_order_func implement.
```

---

## 4. STANDARD TEARSHEET CALL

Generate the OBQ institutional tearsheet after every completed backtest. This is the deliverable format for internal review.

```python
import sys
sys.path.insert(0, r"C:\Users\admin\Desktop\OBQ_TradingSystems_Vbt")
from Performance_Reporting import run_tearsheet

results = run_tearsheet(
    nav=nav,                            # pd.Series: portfolio NAV (daily values)
    benchmark=spx_nav,                  # pd.Series: SPX close prices for comparison
    pf=pf,                              # vbt.Portfolio object (trade-level stats)
    strategy_name="FTT Clenow v3a",     # shown in tearsheet header
    initial_capital=100_000,
)
# results dict contains: cagr, sharpe, sortino, max_dd, calmar, vol, etc.
```

If `spx_nav` is not already loaded:
```python
from PWB_tools import data_loader as dl
spx_close = dl.get_pricing("Indices", symbols=["SPX"], field="close")
spx_nav = spx_close["SPX"].dropna()
```

---

## 5. RESULTS LOGGING — MANDATORY AFTER EVERY RUN

Every completed backtest must be logged. This is non-negotiable — it's how we track progress across strategy versions and avoid re-running experiments.

**Step 1: Print the log line**
```python
from datetime import date
import numpy as np

def log_result(strategy_name, pf, nav, n_assets, commission, leverage=1.0):
    """Print a formatted log line for backtest_results_log.md"""
    returns = nav.pct_change().dropna()
    n_years = len(nav) / 252.0

    cagr    = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1
    vol     = returns.std() * np.sqrt(252)
    sharpe  = (returns.mean() * 252) / vol if vol > 0 else np.nan
    neg_ret = returns[returns < 0]
    sortino = (returns.mean() * 252) / (neg_ret.std() * np.sqrt(252)) if len(neg_ret) > 0 else np.nan
    mdd     = ((nav / nav.cummax()) - 1).min()
    calmar  = cagr / abs(mdd) if mdd != 0 else np.nan

    start = nav.index[0].strftime("%Y-%m-%d")
    end   = nav.index[-1].strftime("%Y-%m-%d")

    print(
        f"| {strategy_name} | {date.today()} | {n_assets} | {start} | {end} | "
        f"{cagr*100:.1f}% | {sharpe:.2f} | {sortino:.2f} | {mdd*100:.1f}% | "
        f"{calmar:.2f} | {vol*100:.1f}% | leverage={leverage}, comm={commission} |"
    )
```

**Step 2: Copy the output line to `knowledge/backtest_results_log.md`**

Table header for the log:
```
| Strategy | Date | N Assets | Start | End | CAGR | Sharpe | Sortino | MaxDD | Calmar | Vol | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
```

---

## 6. BEFORE SHARING RESULTS — FINAL SIGN-OFF

Before presenting results to anyone (internal review, paper draft, client):

```
[ ] All 5 sanity ranges checked and any outliers explained
[ ] All 6 look-ahead bias items verified (signed off, not "probably fine")
[ ] Commission included, leverage documented
[ ] run_tearsheet() output reviewed (not just printed)
[ ] Results logged to knowledge/backtest_results_log.md
[ ] Any known limitations noted (survivorship, no slippage, data coverage gaps)
```
