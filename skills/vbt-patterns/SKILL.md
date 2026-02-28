---
name: vbt-patterns
description: "VectorBT 0.28.x critical bugs and the correct from_order_func pattern for percent-of-equity sizing with cash_sharing. Use when writing any VBT backtest, especially with L+S strategies, cash_sharing=True, or position sizing."
user-invocable: false
---

# VectorBT 0.28.x Critical Patterns

This skill documents confirmed bugs in VBT 0.28.x and the only correct implementation patterns for production backtests at Obsidian Quantitative.

---

## THREE CRITICAL VBT 0.28.x BUGS

### Bug 1: size_type="percent" Crashes with cash_sharing=True

**Error:** `ValueError: SizeType.Percent does not support position reversal`

**When it occurs:** Any time you use `size_type="percent"` with `cash_sharing=True`, even when there are ZERO actual reversals in your signals.

**Root cause:** VBT 0.28.x internally processes potential reversals during order evaluation — it detects the possibility of a reversal at the type-dispatch level before examining actual signals. The error fires even if no asset ever actually reverses in the data.

**Confirmed via diagnostic:** A test portfolio with 1 asset, 100 bars, and only long entries (no shorts, no reversals) still triggers this error when `cash_sharing=True` and `size_type="percent"`.

**WRONG approach (do not use):**
```python
# This crashes — do NOT do this
pf = vbt.Portfolio.from_signals(
    close, entries=long_entries, exits=long_exits,
    short_entries=short_entries, short_exits=short_exits,
    size=0.02, size_type="percent",
    cash_sharing=True, group_by=True,
)
```

**FIX:** Use `from_order_func` with a Numba kernel (see THE CORRECT PATTERN below). Do not attempt to work around this with `size_type="value"` — that eliminates compounding.

---

### Bug 2: size_type="percent" Uses % of Cash, Not Portfolio Value

**What it does:** `size_type="percent"` computes position size as a percentage of available **cash**, not total portfolio equity (cash + unrealized P&L).

**Why this matters:** As the portfolio grows and capital is deployed into open positions, available cash shrinks. A 2% position on $50k cash in a $200k portfolio is not the same as 2% of portfolio equity. This produces:
- Undersizing as the portfolio gains (returns don't compound correctly)
- Oversizing early when all capital is still cash
- Wrong risk management semantics vs. every other backtesting platform

**FIX:** Use `c.value_now` inside `from_order_func`. `c.value_now` = cash + unrealized P&L = total broker equity — exactly what every percentage-of-equity calculation should use.

---

### Bug 3: Negative Prices Cause Crashes

**When it occurs:**
- Bond yields (negative in many datasets post-2008)
- Crude oil front-month (CL1) hit -$37 in April 2020
- Any symbol where data goes negative for economic reasons

**Error messages:** Various — `order.price must be finite and greater than 0`, silent NaN propagation, or Numba crashes in `@nb.njit` kernels.

**WRONG order (do not use):**
```python
# Bug: clipping first means valid_price is always True after clip
close_clean = close.clip(lower=0.0001)
valid_price = close_clean > 0   # always True — validation is useless
```

**CORRECT order: validate BEFORE clipping, block entries for invalid prices:**
```python
# Compute validity flag BEFORE any clipping
valid_price = close.notna() & (close > 0)

# Clip AFTER flagging
close_clean = close.clip(lower=0.0001)

# Block entries on invalid prices (apply to both long and short)
entries_long = entries_long & valid_price
entries_short = entries_short & valid_price

# Pass close_clean (not close) to from_order_func
```

---

## THE CORRECT PATTERN: True Percent-of-Equity with from_order_func

This is the ONLY correct way to implement percent-of-portfolio sizing with `cash_sharing=True` in VBT 0.28.x. This pattern is battle-tested across all OBQ strategies.

```python
import numba as nb
import numpy as np
import vectorbt as vbt
from vectorbt.portfolio.nb import order_nb as _vbt_order_nb, close_position_nb as _vbt_close_nb

# CRITICAL: @nb.njit function MUST be at MODULE LEVEL, not inside any other function.
# Defining it inside a function causes Numba reflection errors and cache corruption.
@nb.njit(cache=True)
def _order_func_nb(c, le, lx, se, sx, spct, fees):
    """
    Numba order function for percent-of-equity L+S with cash_sharing.

    Args:
        c:    VBT order context (provides c.i, c.col, c.val_price_now,
                c.position_now, c.value_now)
        le:   Long entry signals  (bool array, shape: bars x assets)
        lx:   Long exit signals   (bool array, shape: bars x assets)
        se:   Short entry signals (bool array, shape: bars x assets)
        sx:   Short exit signals  (bool array, shape: bars x assets)
        spct: Size in % of portfolio per asset per bar (float64 array)
        fees: Commission rate as decimal (e.g., 0.0002 for 2bps)
    """
    i, col = c.i, c.col
    price = c.val_price_now
    pos = c.position_now

    # Guard: skip NaN or zero prices (handles bond yields, CL1 Apr 2020)
    if price <= 0. or price != price:
        return _vbt_order_nb(size=np.nan)

    # Exit logic — process exits before entries (always close before reversing)
    if pos > 0. and lx[i, col]:
        return _vbt_close_nb(price=price, fees=fees)
    if pos < 0. and sx[i, col]:
        return _vbt_close_nb(price=price, fees=fees)

    # Entry logic — only enter when flat
    if pos == 0.:
        s = spct[i, col]
        # Guard: skip NaN or zero size (e.g., when ATR is NaN during warmup)
        if s <= 0. or s != s:
            return _vbt_order_nb(size=np.nan)

        # KEY: multiply percent by c.value_now (total portfolio equity, not just cash)
        # c.value_now = cash + unrealized P&L = broker.getvalue()
        dollar = s * c.value_now

        if le[i, col]:
            return _vbt_order_nb(
                size=dollar,
                price=price,
                size_type=1,    # SizeType.Value (must use integer in Numba, not string)
                direction=0,    # Direction.LongOnly (must use integer in Numba)
                fees=fees,
                lock_cash=True  # Prevents short cash recycling spiral
            )
        if se[i, col]:
            return _vbt_order_nb(
                size=dollar,
                price=price,
                size_type=1,    # SizeType.Value
                direction=1,    # Direction.ShortOnly (must use integer in Numba)
                fees=fees,
                lock_cash=True  # BOTH sides need lock_cash=True
            )

    return _vbt_order_nb(size=np.nan)


def run_backtest(close_clean, le, lx, se, sx, spct, commission=0.0002, init_cash=100_000):
    """
    Execute backtest using the correct from_order_func pattern.

    Args:
        close_clean: pd.DataFrame (date x symbol), already clipped for negative prices
        le, lx:      pd.DataFrame bool (date x symbol) — long entries/exits
        se, sx:      pd.DataFrame bool (date x symbol) — short entries/exits
        spct:        pd.DataFrame float64 (date x symbol) — position size as fraction
        commission:  float, e.g., 0.0002 for 2bps
        init_cash:   float, starting capital

    Returns:
        pf:  vbt.Portfolio object
        nav: pd.Series, portfolio NAV (value over time)
    """
    pf = vbt.Portfolio.from_order_func(
        close_clean,
        _order_func_nb,
        # Extra args passed to _order_func_nb (must match function signature exactly):
        le.values.astype(np.bool_),
        lx.values.astype(np.bool_),
        se.values.astype(np.bool_),
        sx.values.astype(np.bool_),
        spct.values.astype(np.float64),
        np.float64(commission),
        # Portfolio configuration:
        init_cash=init_cash,
        cash_sharing=True,   # Single cash pool shared across all assets
        group_by=True,       # Group all assets into one portfolio group
        freq="D",
        ffill_val_price=True,  # Forward-fill val_price for illiquid assets
        update_value=True,     # REQUIRED: ensures c.value_now updates per order within a bar
    )
    nav = pf.value().iloc[:, 0]
    return pf, nav
```

### Key Parameter Notes

| Parameter | Value | Why |
|---|---|---|
| `size_type=1` | Integer, not string | Numba cannot use string enum. 1 = SizeType.Value |
| `direction=0` | Integer, not string | 0 = Direction.LongOnly |
| `direction=1` | Integer, not string | 1 = Direction.ShortOnly |
| `lock_cash=True` | Both long AND short | Prevents short-side cash recycling spiral where shorts generate phantom cash that funds more shorts |
| `update_value=True` | Portfolio kwarg | Without this, c.value_now is stale within a bar — first order of the bar uses last bar's equity |
| `ffill_val_price=True` | Portfolio kwarg | Prevents NaN val_price for assets not trading every day |
| `c.value_now` | In kernel | Total portfolio equity = cash + unrealized P&L. NOT just cash. |

---

## ATR TRAILING STOP PATTERN (Clenow-Style)

Used in FTT_Clenow and as the standard OBQ trailing stop implementation.

```python
from PWB_tools import indicators as ind

# Compute ATR
atr = ind.atr(high, low, close, period=atr_period)   # already in price units

# Position sizing: risk a fixed % of portfolio per unit of ATR
# risk_factor * leverage = total notional / ATR unit
size_pct = (risk_factor * leverage) / atr   # fraction of portfolio per unit
size_pct = size_pct.clip(upper=max_size_pct)  # cap at 99% to prevent over-allocation

# Entry signals: MA crossover + breakout (Clenow rules)
entries_long  = (sma_short > sma_long) & (close >= close.rolling(breakout_period).max())
entries_short = (sma_short < sma_long) & (close <= close.rolling(breakout_period).min())

# ATR trailing stops (use yesterday's stop to avoid look-ahead)
stop_long  = close - atr_multiplier * atr   # stop level below price for longs
stop_short = close + atr_multiplier * atr   # stop level above price for shorts

# Compare today's close against YESTERDAY's stop (shift(1) prevents look-ahead)
exits_long  = close < stop_long.shift(1)
exits_short = close > stop_short.shift(1)

# Default params (validated on 1990-2026, 46 assets):
# atr_period=20, ma_short=50, ma_long=100, breakout_period=50
# atr_multiplier=3.0, risk_factor=0.002, leverage=5, max_size_pct=0.99
```

---

## PERFORMANCE REPORTING INTEGRATION

After every backtest, generate the OBQ institutional tearsheet:

```python
import sys
sys.path.insert(0, r"C:\Users\admin\Desktop\OBQ_TradingSystems_Vbt")
from Performance_Reporting import run_tearsheet

results = run_tearsheet(
    nav=nav,                          # pd.Series: portfolio NAV over time
    benchmark=spx_nav,                # pd.Series: SPX close prices (optional but recommended)
    pf=pf,                            # vbt.Portfolio object (optional, enables trade stats)
    strategy_name="Strategy Name",
    initial_capital=100_000,
)
```

---

## RESULTS LOGGING

Mandatory after every backtest run. Print this line and then update `knowledge/backtest_results_log.md`:

```python
from datetime import date
print(
    f"| {strategy_name} | {date.today()} | {n_assets} assets | "
    f"{start_date} | {end_date} | "
    f"CAGR={cagr*100:.1f}% | Sharpe={sharpe:.2f} | Sortino={sortino:.2f} | "
    f"MaxDD={mdd*100:.1f}% | Calmar={calmar:.2f} | Vol={vol*100:.1f}% |"
)
```

Table format for `knowledge/backtest_results_log.md`:
```
| Strategy | Date | N Assets | Start | End | CAGR | Sharpe | Sortino | MaxDD | Calmar | Vol |
```

---

## REFERENCE: FTT CLENOW RESULTS BY IMPLEMENTATION

Confirmed results on 1990-2026, 45 assets (8 Bonds, 20 Commodities, 7 Forex, 10 Indices):

| Version | CAGR | Sharpe | MaxDD | Trades | Notes |
|---|---|---|---|---|---|
| v1 (fixed sizing, no compound) | 5.8% | 0.45 | -51% | 1336 | Baseline |
| v3a (from_order_func, lock=T/T) | 36.5% | 2.34 | -9.8% | 781 | BEST — correct pattern |
| v3b (from_order_func, lock=F/T) | 53.4% | 1.92 | -69.7% | 846 | lock_cash=False on shorts |

The difference between v3a and v3b is solely `lock_cash=True` on the short side. v3b's 53% CAGR is inflated by the cash recycling spiral — shorts generate phantom collateral that funds more shorts. v3a is the correct implementation.
