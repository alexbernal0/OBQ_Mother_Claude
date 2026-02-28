---
name: quant-backtest
description: "OBQ quantitative backtesting patterns — VectorBT strategy structure, L+S implementation, ATR risk sizing, performance metrics, and the standard OBQ strategy file template. Use when building or reviewing any VBT backtest."
---

## OBQ Quantitative Backtesting Patterns (VectorBT 0.28.4)

---

## 1. STANDARD STRATEGY FILE STRUCTURE

Every strategy in `pwb_strategies/STRATEGY_vbt.py` must contain these components in order:

```
PARAMS dict           — all tunable parameters with defaults
DATASET_MAP dict      — maps asset classes to symbol lists
load_universe()       — loads OHLCV data for all assets
load_benchmark()      — loads SPX as benchmark
compute_indicators()  — SMA, ATR, etc. (returns indicator DataFrames)
compute_signals()     — long/short entry/exit signals (returns bool DataFrames)
run_backtest()        — builds Portfolio via from_order_func
print_metrics()       — prints standard performance table
plot_results()        — tearsheet and equity curve
run_STRATEGY_NAME()   — main entry point that calls all of the above
```

---

## 2. PARAMS DICT STANDARD

```python
PARAMS = {
    'leverage': 5,
    'risk_factor': 0.002,
    'atr_period': 20,
    'ma_short': 50,
    'ma_long': 100,
    'breakout_period': 50,
    'atr_multiplier': 3.0,
    'commission': 0.0002,
    'max_size_pct': 0.99,
    'init_cash': 100_000,
}
```

---

## 3. DATA LOADING PATTERN

```python
import sys
sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")
from PWB_tools import data_loader as dl

# Wide format (date × symbol) — preferred for VBT
close = dl.get_pricing("Commodities", symbols=SYMBOLS, field="close")
high  = dl.get_pricing("Commodities", symbols=SYMBOLS, field="high")
low   = dl.get_pricing("Commodities", symbols=SYMBOLS, field="low")

# Single-symbol OHLCV
ohlcv = dl.get_ohlcv("Commodities", "GC1")

# Benchmark
benchmark = dl.get_pricing("Indices", symbols=["SPX"], field="close")["SPX"]
```

Available datasets: Bonds, Commodities, ETFs, Forex, Indices, Cryptocurrencies, Universe

---

## 4. VBT KNOWN BUGS (0.28.4) — CRITICAL

**Bug 1**: `size_type="percent"` raises `ValueError: SizeType.Percent does not support position reversal` with `cash_sharing=True` — even with zero actual reversals.
**Fix**: Use `from_order_func` with Numba (see section 5).

**Bug 2**: `size_type="percent"` sizes off cash balance only, not total portfolio value — no compounding.
**Fix**: Use `c.value_now` inside `from_order_func` (equals cash + unrealized P&L).

**Bug 3**: `order.price must be finite and greater than 0` — negative bond yields and CL1 Apr 2020 (-$37) crash the backtest.
**Fix**:
```python
valid_price = close.notna() & (close > 0)   # compute BEFORE clipping
close = close.clip(lower=0.0001)             # clip AFTER
entries = entries & valid_price              # block entries on bad prices
```

---

## 5. FROM_ORDER_FUNC PATTERN (L+S, cash_sharing — the ONLY correct sizing approach)

```python
import numba as nb
import numpy as np
import vectorbt as vbt
from vectorbt.portfolio.nb import order_nb as _vbt_order_nb, close_position_nb as _vbt_close_nb

# MUST be defined at module level (not inside a function) for Numba caching
@nb.njit(cache=True)
def _order_func_nb(c, le, lx, se, sx, spct, fees):
    i, col = c.i, c.col
    price = c.val_price_now
    pos   = c.position_now

    # Guard: skip bad prices
    if price <= 0. or price != price:
        return _vbt_order_nb(size=np.nan)

    # Exits first — close existing position
    if pos > 0. and lx[i, col]:
        return _vbt_close_nb(price=price, fees=fees)
    if pos < 0. and sx[i, col]:
        return _vbt_close_nb(price=price, fees=fees)

    # New entries only when flat
    if pos == 0.:
        s = spct[i, col]
        if s <= 0. or s != s:
            return _vbt_order_nb(size=np.nan)
        dollar = s * c.value_now  # KEY: percent × total portfolio value (cash + unrealized)
        if le[i, col]:
            return _vbt_order_nb(size=dollar, price=price, size_type=1,
                                 direction=0, fees=fees, lock_cash=True)
        if se[i, col]:
            return _vbt_order_nb(size=dollar, price=price, size_type=1,
                                 direction=1, fees=fees, lock_cash=True)

    return _vbt_order_nb(size=np.nan)


# Build portfolio
pf = vbt.Portfolio.from_order_func(
    close_clean, _order_func_nb,
    le.values.astype(np.bool_),    # long entries
    lx.values.astype(np.bool_),    # long exits
    se.values.astype(np.bool_),    # short entries
    sx.values.astype(np.bool_),    # short exits
    spct.values.astype(np.float64),  # position size as fraction of equity
    np.float64(PARAMS['commission']),
    init_cash=PARAMS['init_cash'],
    cash_sharing=True,
    group_by=True,
    freq="D",
    ffill_val_price=True,
    update_value=True,   # REQUIRED: ensures c.value_now updates per order within a bar
)
nav = pf.value().iloc[:, 0]
```

Key notes:
- `lock_cash=True` on both long and short prevents the short cash recycling spiral
- `update_value=True` is mandatory for correct intra-bar value accounting
- `size_type=1` = `SizeType.Value` (integer enum in Numba context)
- `direction=0` = `LongOnly`, `direction=1` = `ShortOnly`

---

## 6. ATR POSITION SIZING FORMULA

```python
# ATR-based risk sizing (Clenow / turtle-style)
atr = ind.atr(high, low, close, period=PARAMS['atr_period'])  # ATR in price units

# Position size as fraction of equity
# size = (equity × risk_factor × leverage) / (ATR × price)
# In practice, compute as percent: spct = risk_factor × leverage / (atr / close)
atr_pct = atr / close  # ATR as fraction of price
spct = (PARAMS['risk_factor'] * PARAMS['leverage'] / atr_pct).clip(upper=PARAMS['max_size_pct'])
spct = spct.shift(1)  # CRITICAL: use prior-bar ATR to avoid look-ahead
```

---

## 7. METRICS OUTPUT STANDARD

```python
def print_metrics(pf, nav, benchmark_nav):
    total_ret = (nav.iloc[-1] / nav.iloc[0]) - 1
    n_years   = len(nav) / 252
    cagr      = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1
    returns   = nav.pct_change().dropna()
    sharpe    = returns.mean() / returns.std() * np.sqrt(252)
    neg_ret   = returns[returns < 0]
    sortino   = returns.mean() / neg_ret.std() * np.sqrt(252)
    mdd       = ((nav / nav.cummax()) - 1).min()
    calmar    = cagr / abs(mdd) if mdd != 0 else np.nan
    vol       = returns.std() * np.sqrt(252)

    bm_total  = (benchmark_nav.iloc[-1] / benchmark_nav.iloc[0]) - 1
    bm_cagr   = (benchmark_nav.iloc[-1] / benchmark_nav.iloc[0]) ** (1 / n_years) - 1

    print(f"Period:       {nav.index[0].date()} to {nav.index[-1].date()}")
    print(f"Total Return: {total_ret*100:.1f}%")
    print(f"CAGR:         {cagr*100:.1f}%")
    print(f"Sharpe:       {sharpe:.2f}")
    print(f"Sortino:      {sortino:.2f}")
    print(f"Max DD:       {mdd*100:.1f}%")
    print(f"Calmar:       {calmar:.2f}")
    print(f"Volatility:   {vol*100:.1f}%")
    print(f"Trades:       {pf.orders.count()}")
    print(f"SPX CAGR:     {bm_cagr*100:.1f}%  (Total: {bm_total*100:.1f}%)")
```

---

## 8. REALISTIC PERFORMANCE RANGES

Flag for look-ahead bias review if results exceed these ranges without clear justification:

| Metric | Realistic Range | Investigate If |
|--------|----------------|----------------|
| CAGR | 5–25% | > 40% |
| Sharpe | 0.3–1.5 | > 3.0 |
| Max DD | -15% to -60% | < -5% with high CAGR |
| Win Rate | 35–65% | > 80% |
