# VBT Gotchas — OBQ Knowledge Base

Confirmed bugs and workarounds for VectorBT 0.28.x used across OBQ projects.
This file is the authoritative reference — update whenever a new VBT bug is confirmed.

---

## BUG 1: size_type="percent" + cash_sharing=True → Always Crashes

**Error**: `ValueError: SizeType.Percent does not support position reversal using signals.`

**When**: Any call to `vbt.Portfolio.from_signals()` with `size_type="percent"` and
`cash_sharing=True`. Crashes even when there are ZERO actual position reversals in the data.

**Root Cause**: VBT 0.28.x internally processes reversal logic before checking whether
reversals actually exist. The error is raised preemptively.

**Confirmed via diagnostic**: Running a single-asset, long-only strategy with no exits and
no reversals still triggers this error when cash_sharing=True.

**Fix**: Use `from_order_func` with Numba. Full working pattern:

```python
import numba as nb
import numpy as np
from vectorbt.portfolio.nb import order_nb as _vbt_order_nb, close_position_nb as _vbt_close_nb

@nb.njit(cache=True)   # MUST be at module level
def _order_func_nb(c, le, lx, se, sx, spct, fees):
    i, col = c.i, c.col
    price, pos = c.val_price_now, c.position_now
    if price <= 0. or price != price: return _vbt_order_nb(size=np.nan)
    if pos > 0. and lx[i, col]: return _vbt_close_nb(price=price, fees=fees)
    if pos < 0. and sx[i, col]: return _vbt_close_nb(price=price, fees=fees)
    if pos == 0.:
        s = spct[i, col]
        if s <= 0. or s != s: return _vbt_order_nb(size=np.nan)
        dollar = s * c.value_now
        if le[i, col]: return _vbt_order_nb(size=dollar, price=price, size_type=1, direction=0, fees=fees, lock_cash=True)
        if se[i, col]: return _vbt_order_nb(size=dollar, price=price, size_type=1, direction=1, fees=fees, lock_cash=True)
    return _vbt_order_nb(size=np.nan)

pf = vbt.Portfolio.from_order_func(
    close_clean, _order_func_nb,
    le.values.astype(np.bool_), lx.values.astype(np.bool_),
    se.values.astype(np.bool_), sx.values.astype(np.bool_),
    spct.values.astype(np.float64), np.float64(commission),
    init_cash=100_000, cash_sharing=True, group_by=True,
    freq="D", ffill_val_price=True, update_value=True,
)
```

**Key integer constants in Numba context**:
- `size_type=1` = SizeType.Value (NOT SizeType.Percent)
- `direction=0` = LongOnly
- `direction=1` = ShortOnly

**Do NOT** use `size_type="value"` as a "long-term fix" — it gives no compounding.

---

## BUG 2: size_type="percent" Uses % of CASH, Not Portfolio Value

**Issue**: When `size_type="percent"` is used (in cases where Bug 1 doesn't apply),
the percentage is calculated against available CASH, not total portfolio value (cash +
unrealized P&L). This is semantically wrong for percent-of-equity sizing.

**Example**: If portfolio is $150K (started at $100K), cash=$80K, unrealized=$70K:
- Intended: 2% × $150K = $3K position
- Actual (VBT): 2% × $80K = $1.6K position

**Fix**: Use `c.value_now` inside `from_order_func`:
```python
dollar = spct[i, col] * c.value_now  # c.value_now = cash + unrealized P&L
```
This is equivalent to `broker.getvalue()` in backtrader.

---

## BUG 3: Negative Prices Cause Crashes or Infinite Loops

**Affected instruments**: Bond yields (CH10Y, DE10Y, GB10Y, US2Y) and CL1 crude oil
(April 2020: -$37.63). These legitimately go negative in real markets.

**Symptom**: `ValueError: order.price must be finite and greater than 0` or infinite loop.

**WRONG fix** (common mistake — causes issues):
```python
close = close.clip(lower=0.0001)  # DO NOT do this first
entries = entries  # entries now includes invalid-price bars — bug!
```

**CORRECT fix** (validate BEFORE clipping):
```python
# Step 1: Identify invalid prices BEFORE clipping
valid_price = close.notna() & (close > 0)

# Step 2: Block entries on invalid-price bars
entries_long = entries_long & valid_price
entries_short = entries_short & valid_price

# Step 3: NOW safe to clip for VBT price array
close_clean = close.clip(lower=0.0001)
```

**Symbols requiring this treatment in PWBBacktest_Data**:
- CH10Y (Swiss 10Y yield — went negative 2014-2022)
- DE10Y (German 10Y yield — negative 2019-2022)
- DE2Y (German 2Y yield — deeply negative 2019-2022)
- GB1Y (UK 1Y yield — negative briefly 2020-2021)
- CL1 (Crude oil front contract — April 2020: -$37.63)

---

## KNOWN ISSUE: lock_cash=True Behavior

**Context**: `lock_cash=True` in `_vbt_order_nb` causes entry orders to be rejected when
free cash is insufficient (even if overall portfolio value is ample).

**Behavior with lock_cash=True (both sides)**:
- Acts as an implicit quality/momentum filter for entries
- Only enters when portfolio has ample free cash (post-profit periods)
- Results in fewer trades, higher quality (as confirmed in FTT Clenow v3a)

**Behavior with lock_cash=False (longs) / True (shorts)**:
- Free cash from short exits recycles into long entries
- More trades, more aggressive compounding, higher MaxDD
- Can create leverage-like cash recycling spiral on shorts

**FTT Clenow Results**:
- v3a (lock=T/T): CAGR=36.5%, Sharpe=2.34, MaxDD=-9.8% ← CLEANEST
- v3b (lock=F/T): CAGR=53.4%, Sharpe=1.92, MaxDD=-69.7% ← MORE EXPLOSIVE

**Recommendation**: Use lock=T/T for realistic production-quality backtests.

---

## KNOWN ISSUE: update_value=True Required

When using `from_order_func` with `cash_sharing=True` across multiple assets,
`update_value=True` must be set to ensure `c.value_now` reflects all orders processed
within the same bar (not just the start-of-bar value).

Without it: size calculations for later assets in a bar use stale portfolio value.

```python
pf = vbt.Portfolio.from_order_func(
    ...,
    update_value=True,  # REQUIRED for accurate c.value_now across same-bar orders
)
```

---

## KNOWN ISSUE: @nb.njit at Module Level

Numba `@nb.njit` functions **cannot be defined inside another function**. They must be
at module level (top-level scope in the .py file).

**Will fail**:
```python
def run_backtest(params):
    @nb.njit(cache=True)  # ERROR: nested njit not supported
    def _order_func_nb(c, ...):
        ...
```

**Correct**:
```python
@nb.njit(cache=True)  # module level
def _order_func_nb(c, ...):
    ...

def run_backtest(params):
    pf = vbt.Portfolio.from_order_func(..., _order_func_nb, ...)
```

---

## KNOWN ISSUE: Stale Numba Cache

When `cache=True` is used (recommended for performance) and the function signature changes,
Numba may use the stale cached version, causing silent wrong behavior or type errors.

**Fix**: Delete `__pycache__` folder in the strategy directory:
```bash
rm -rf pwb_strategies/__pycache__
```

---

## PERFORMANCE COMPARISON (FTT Clenow, 1990-2026)

| Version | Sizing | lock_cash | CAGR | Sharpe | MaxDD | Trades |
|---------|--------|-----------|------|--------|-------|--------|
| v1 (fixed, no compound) | value, no compound | N/A | 5.8% | 0.45 | -51.0% | 1,336 |
| v2 (two-pass scaling) | equity-scaled | N/A | ~4.7% | ~0.38 | catastrophic | ABANDONED |
| v3a (from_order_func) | % equity (correct) | T/T | 36.5% | 2.34 | -9.8% | 781 |
| v3b (from_order_func) | % equity (correct) | F/T | 53.4% | 1.92 | -69.7% | 846 |

SPX benchmark (1990-2026): +633.6% total return.

---

*vbt_gotchas.md | OBQ_Mother_Claude | Updated: 2026-02-28*
