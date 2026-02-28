---
name: paper-to-strategy
description: "Protocol for translating an academic research paper into a VectorBT strategy implementation. Use when given a PDF paper or paper description to build a new backtest from. Extracts signal logic, parameters, universe, and maps to OBQ datasets."
---

# Paper-to-Strategy Implementation Protocol

Use this protocol every time you receive an academic paper and need to build a backtest. Following these steps in order prevents re-work caused by discovering a missing symbol in step 6 that you should have caught in step 2.

---

## STEP 1: EXTRACTION CHECKLIST

Read the paper and extract these 8 items before writing any code. Write them out explicitly — ambiguities you gloss over now become bugs later.

```
[ ] 1. UNIVERSE
        What assets? Be specific:
        - Equity indices? (e.g., S&P 500, NASDAQ, international?)
        - Futures? (commodity, financial, equity index?)
        - Individual stocks? (which market, which index members?)
        - ETFs? FX? Crypto?
        - How many assets total?
        - Any exclusions (illiquid, penny stocks, short history)?

[ ] 2. SIGNAL LOGIC — ENTRY
        Write as a boolean expression if possible:
        - MA crossover? (which MAs, which periods?)
        - Momentum? (which lookback, raw return or risk-adjusted?)
        - Breakout? (N-bar high/low, N-bar ATR channel?)
        - Factor? (value, quality, low-vol? — how scored, how ranked?)
        - Fundamental trigger? (earnings surprise, revenue growth?)

[ ] 3. SIGNAL LOGIC — EXIT
        - Fixed stop loss? (% or ATR multiple?)
        - Trailing stop? (ATR-based? High-water mark?)
        - MA crossover reversal? (same or different MA than entry?)
        - Time-based? (hold N days, then exit regardless)
        - Target profit? (take-profit level)

[ ] 4. POSITION SIZING
        - Equal weight? (1/N, where N = open positions)
        - Fixed fractional? (e.g., always 2% per trade)
        - Volatility-scaled? (target vol / current vol)
        - ATR-based? (risk_factor / ATR)
        - Kelly criterion? (from win rate and payoff ratio)
        - Paper-specified leverage?

[ ] 5. REBALANCING FREQUENCY
        - Daily (VBT default — simplest to implement)
        - Weekly (use resample + forward-fill for non-weekly signal)
        - Monthly (common for factor strategies)
        - Event-driven (on signal change only)

[ ] 6. ALL PARAMETERS WITH VALUES
        Document every numerical parameter the paper specifies:
        - Lookback periods (MA windows, ATR period, momentum period)
        - Thresholds (breakout period, z-score cutoff)
        - Risk/sizing params (risk per trade, max position %, leverage)
        - Transaction costs assumed in the paper

[ ] 7. TIME PERIOD AND SAMPLE
        - In-sample period used in paper
        - Out-of-sample period if shown
        - Note any subperiod analysis

[ ] 8. BENCHMARK AND COMPARISON
        - What does the paper compare against?
        - Buy-and-hold? Risk parity? 60/40?
        - Standard benchmark: use SPX for OBQ
```

---

## STEP 2: DATASET MAPPING

Map the paper's universe to available OBQ data sources before writing any code.

### Available Datasets

| Source | Contents | Access Method |
|---|---|---|
| PWBBacktest_Data/Bonds | 8 bond instruments (US2Y, US10Y, US30Y, etc.) | `dl.get_pricing("Bonds")` |
| PWBBacktest_Data/Commodities | 20 front-month futures (GC1, CL1, etc.) | `dl.get_pricing("Commodities")` |
| PWBBacktest_Data/ETFs | Major ETFs (SPY, GLD, TLT, etc.) | `dl.get_pricing("ETFs")` |
| PWBBacktest_Data/Forex | 7 pairs (EURUSD, GBPUSD, USDJPY, etc.) | `dl.get_pricing("Forex")` |
| PWBBacktest_Data/Indices | 10 global indices (SPX, NKY, DAX, etc.) | `dl.get_pricing("Indices")` |
| PWBBacktest_Data/Cryptocurrencies | BTC, ETH, etc. | `dl.get_pricing("Cryptocurrencies")` |
| PWBBacktest_Data/Universe | Daily OHLCV for broad universe | `dl.load_dataset("Universe")` |
| MotherDuck PROD_EODHD | 225M+ US equity records, adjusted | DuckDB query |
| MotherDuck GoldenOpp | 56 gold miners + 4 ETFs, 53yr history | DuckDB query |

### Symbol Mapping Process

```python
# Check which paper symbols are available in each dataset
from PWB_tools import data_loader as dl

# Get available symbols for each dataset
bonds_df      = dl.load_dataset("Bonds")
commodities_df = dl.load_dataset("Commodities")
forex_df      = dl.load_dataset("Forex")
indices_df    = dl.load_dataset("Indices")

bonds_symbols      = bonds_df['Symbol'].unique().tolist()
commodities_symbols = commodities_df['Symbol'].unique().tolist()
forex_symbols      = forex_df['Symbol'].unique().tolist()
indices_symbols    = indices_df['Symbol'].unique().tolist()

# Map paper symbols to available data
paper_symbols = ["SP500", "GOLD", "CRUDE", "10Y_BOND", "EURUSD"]

mapping = {
    "SP500":    "SPX (Indices)",
    "GOLD":     "GC1 (Commodities)",
    "CRUDE":    "CL1 (Commodities) — NOTE: hit -$37 Apr 2020, needs valid_price mask",
    "10Y_BOND": "US10Y (Bonds) — NOTE: may have negative yields post-2008",
    "EURUSD":   "EURUSD (Forex)",
}

# Known problem symbols (do not use without special handling):
# EU1Y: not in dataset (removed)
# EU10Y: only 2 rows of data (removed)
# NIKKEI: use NKY not NIKKEI
# JPYUSD, CHFUSD, CADUSD: inverted — use USDJPY, USDCHF, USDCAD instead
```

### Missing Symbol Protocol

If a paper requires a symbol not available in OBQ data:
1. Note it explicitly in the strategy file header comment
2. Find the best available proxy (document the proxy and why)
3. Check if symbol can be sourced from MotherDuck PROD_EODHD
4. If no proxy available, exclude and note the impact on universe coverage

---

## STEP 3: IMPLEMENTATION PLAN

Generate this plan before writing code. Review it once before starting.

```python
"""
STRATEGY: [Name from paper]
PAPER:     [Author, Year, Title, SSRN/DOI if available]
UNIVERSE:  [N assets: X bonds, Y commodities, Z forex, W indices]
PERIOD:    [Start] to [End] (paper: [paper period])
MISSING:   [Any symbols not available — proxies used]
LEVERAGE:  [If any]
COSTS:     [Commission assumed]
STATUS:    [Building | Complete | Under Review]

PARAMS:
  ma_short = X
  ma_long = Y
  ... (all params with paper-specified values)
"""
```

---

## STEP 4: STANDARD STRATEGY FILE TEMPLATE

All strategy files live in `pwb_strategies/` and follow this exact structure. Consistency makes it easy to run any strategy from the notebook with a single call.

```python
# pwb_strategies/STRATEGY_NAME_vbt.py
"""
[Strategy Name] — VBT Implementation
Paper: [Author, Year]
Universe: [Description]
Status: [Building | Complete]
"""

import sys
import numpy as np
import pandas as pd
import vectorbt as vbt
import numba as nb
from vectorbt.portfolio.nb import order_nb as _vbt_order_nb, close_position_nb as _vbt_close_nb

sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")
from PWB_tools import data_loader as dl
from PWB_tools import indicators as ind

# ============================================================
# PARAMETERS — all tunable values in one place
# ============================================================
PARAMS = {
    # Signal parameters (from paper)
    "ma_short":        50,
    "ma_long":         100,
    "breakout_period": 50,
    "atr_period":      20,
    "atr_multiplier":  3.0,
    # Sizing parameters
    "leverage":        5,
    "risk_factor":     0.002,
    "max_size_pct":    0.99,
    # Execution parameters
    "commission":      0.0002,
    "init_cash":       100_000,
}

# ============================================================
# DATASET MAP — asset class to data source mapping
# ============================================================
DATASET_MAP = {
    "Bonds":       ["US2Y", "US5Y", "US10Y", "US30Y"],
    "Commodities": ["GC1", "SI1", "CL1", "NG1"],
    "Forex":       ["EURUSD", "GBPUSD", "USDJPY"],
    "Indices":     ["SPX", "NKY", "DAX"],
}


# ============================================================
# DATA LOADING
# ============================================================
def load_universe() -> tuple:
    """Load OHLCV for all assets. Returns (close, high, low) DataFrames."""
    close_parts, high_parts, low_parts = [], [], []

    for dataset, symbols in DATASET_MAP.items():
        for sym in symbols:
            try:
                ohlcv = dl.get_ohlcv(dataset, sym)
                close_parts.append(ohlcv[['close']].rename(columns={'close': sym}))
                high_parts.append(ohlcv[['high']].rename(columns={'high': sym}))
                low_parts.append(ohlcv[['low']].rename(columns={'low': sym}))
            except Exception as e:
                print(f"  WARNING: could not load {dataset}/{sym}: {e}")

    close = pd.concat(close_parts, axis=1).sort_index()
    high  = pd.concat(high_parts,  axis=1).sort_index()
    low   = pd.concat(low_parts,   axis=1).sort_index()

    return close, high, low


def load_benchmark():
    """Load SPX as benchmark NAV."""
    spx = dl.get_pricing("Indices", symbols=["SPX"], field="close")["SPX"].dropna()
    return spx / spx.iloc[0] * PARAMS["init_cash"]


# ============================================================
# INDICATORS
# ============================================================
def compute_indicators(close, high, low):
    """Compute all technical indicators. Returns dict."""
    sma_short = close.rolling(PARAMS["ma_short"]).mean()
    sma_long  = close.rolling(PARAMS["ma_long"]).mean()
    atr       = ind.atr(high, low, close, period=PARAMS["atr_period"])

    return {
        "sma_short": sma_short,
        "sma_long":  sma_long,
        "atr":       atr,
    }


# ============================================================
# SIGNALS
# ============================================================
def compute_signals(close, indicators):
    """Compute entry/exit boolean matrices. Returns dict."""
    sma_short = indicators["sma_short"]
    sma_long  = indicators["sma_long"]
    atr       = indicators["atr"]

    # Negative price mask — compute BEFORE clipping
    valid_price = close.notna() & (close > 0)

    # Entry signals
    entries_long  = (sma_short > sma_long) & (close >= close.rolling(PARAMS["breakout_period"]).max())
    entries_short = (sma_short < sma_long) & (close <= close.rolling(PARAMS["breakout_period"]).min())

    # Apply validity mask
    entries_long  = entries_long & valid_price
    entries_short = entries_short & valid_price

    # Exit signals (ATR trailing stop)
    stop_long  = close - PARAMS["atr_multiplier"] * atr
    stop_short = close + PARAMS["atr_multiplier"] * atr
    exits_long  = close < stop_long.shift(1)
    exits_short = close > stop_short.shift(1)

    # Position sizing
    size_pct = (PARAMS["risk_factor"] * PARAMS["leverage"]) / atr
    size_pct = size_pct.clip(upper=PARAMS["max_size_pct"])

    # Shift signals by 1 bar (signal on close[T] → trade on close[T+1])
    entries_long  = entries_long.shift(1).fillna(False)
    entries_short = entries_short.shift(1).fillna(False)
    exits_long    = exits_long.shift(1).fillna(False)
    exits_short   = exits_short.shift(1).fillna(False)

    # Clip prices (AFTER computing valid_price mask)
    close_clean = close.clip(lower=0.0001)

    return {
        "entries_long":  entries_long,
        "entries_short": entries_short,
        "exits_long":    exits_long,
        "exits_short":   exits_short,
        "size_pct":      size_pct,
        "close_clean":   close_clean,
    }


# ============================================================
# NUMBA ORDER FUNCTION (module level — required for @nb.njit)
# ============================================================
@nb.njit(cache=True)
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
        if le[i, col]:
            return _vbt_order_nb(size=dollar, price=price, size_type=1,
                                 direction=0, fees=fees, lock_cash=True)
        if se[i, col]:
            return _vbt_order_nb(size=dollar, price=price, size_type=1,
                                 direction=1, fees=fees, lock_cash=True)
    return _vbt_order_nb(size=np.nan)


# ============================================================
# BACKTEST
# ============================================================
def run_backtest(signals):
    """Execute backtest. Returns (pf, nav)."""
    p = PARAMS
    pf = vbt.Portfolio.from_order_func(
        signals["close_clean"],
        _order_func_nb,
        signals["entries_long"].values.astype(np.bool_),
        signals["exits_long"].values.astype(np.bool_),
        signals["entries_short"].values.astype(np.bool_),
        signals["exits_short"].values.astype(np.bool_),
        signals["size_pct"].values.astype(np.float64),
        np.float64(p["commission"]),
        init_cash=p["init_cash"],
        cash_sharing=True,
        group_by=True,
        freq="D",
        ffill_val_price=True,
        update_value=True,
    )
    nav = pf.value().iloc[:, 0]
    return pf, nav


# ============================================================
# REPORTING
# ============================================================
def print_metrics(pf, nav):
    """Print standard OBQ metrics summary."""
    import numpy as np
    from datetime import date

    returns = nav.pct_change().dropna()
    n_years = len(nav) / 252.0
    cagr    = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1
    vol     = returns.std() * np.sqrt(252)
    sharpe  = (returns.mean() * 252) / vol
    mdd     = ((nav / nav.cummax()) - 1).min()
    calmar  = cagr / abs(mdd)

    print(f"\nCAGR:   {cagr*100:.1f}%  |  Sharpe: {sharpe:.2f}  |  MaxDD: {mdd*100:.1f}%  |  Calmar: {calmar:.2f}")
    print(f"Vol:    {vol*100:.1f}%  |  Trades: {len(pf.trades.records)}")


def plot_results(nav, benchmark=None):
    """Plot equity curve vs benchmark."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(14, 6))
    (nav / nav.iloc[0]).plot(ax=ax, label="Strategy", linewidth=2)
    if benchmark is not None:
        (benchmark / benchmark.iloc[0]).plot(ax=ax, label="SPX", linewidth=1, alpha=0.7)
    ax.set_title("Equity Curve")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def run_STRATEGY_NAME(verbose=True):
    """Run complete strategy pipeline. Returns (pf, nav)."""
    print("Loading universe...")
    close, high, low = load_universe()
    benchmark = load_benchmark()

    print("Computing indicators...")
    indicators = compute_indicators(close, high, low)

    print("Computing signals...")
    signals = compute_signals(close, indicators)

    print("Running backtest...")
    pf, nav = run_backtest(signals)

    print_metrics(pf, nav)
    plot_results(nav, benchmark)

    return pf, nav
```

---

## STEP 5: COMMON PITFALLS IN PAPER-TO-IMPLEMENTATION

These are the errors that appear most often when translating papers to code:

### Signal Timing
**Paper says:** "signals computed on daily closing prices, positions taken at next open"
**Wrong implementation:** use signal on day T, execute on day T's close
**Correct implementation:** `entries = entries.shift(1)` — signal fires day T, executes day T+1

### Volatility-Scaled Sizing
**Paper says:** "target 10% annual volatility"
**Wrong implementation:** compute annual vol, divide into 10%
**Correct:** `size = (0.10 / (20-day_vol * sqrt(252)))` — this gives daily-adjusted fraction

### Adjusted vs. Unadjusted Returns
**Paper says:** "total return index" or "adjusted for dividends"
**Check:** PWBBacktest_Data commodities are front-month futures (no dividends; roll-adjusted)
**Check:** MotherDuck PROD_EODHD is adjusted close (dividends included in price history)
**Note:** If paper uses unadjusted prices + separate dividend stream, note the difference

### Universe Survivorship
**Paper says:** "S&P 500 universe"
**Problem:** current S&P 500 membership is survivorship-biased (only winners remain)
**Partial fix:** note this as a limitation. Full fix requires historical constituent data.

### Annual Parameters → Daily Implementation
**Paper says:** "12-month momentum" or "252-day lookback"
**In pandas:** `close.pct_change(252)` or `close.rolling(252).mean()`
**Gotcha:** if data has weekends excluded (business days only), 252 ≈ 1 year is correct

### Rebalancing Lag
**Paper says:** "monthly rebalancing"
**Wrong:** use daily signals with monthly signal update — you miss the daily holding period
**Correct pattern:**
```python
# Generate monthly signals, forward-fill to daily
monthly_signal = signal.resample("ME").last()
daily_signal = monthly_signal.reindex(close.index, method="ffill")
```
