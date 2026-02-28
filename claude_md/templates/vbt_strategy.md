# CLAUDE.md — VBT Strategy Project

<!-- This is a template for VBT strategy projects in the PapersWBacktest / OBQ_TradingSystems_Vbt style.
     Copy this file to your project root as CLAUDE.md and fill in the specifics. -->

## Project Purpose

[Describe the strategy being implemented. Include: paper/source being replicated, asset universe, strategy type (trend-following, mean-reversion, factor, etc.), long/short/L+S, frequency.]

Example: Replication of Clenow's FTT trend-following strategy across 45 futures contracts (bonds, commodities, forex, indices). ATR-based position sizing, dual MA entry, ATR trailing stop exit.

---

## Project Structure

```
[project_root]/
├── [StrategyName].ipynb         # Single-cell notebook — runs all code in one shot
├── pwb_strategies/
│   └── [strategy_name]_vbt.py  # VBT implementation (PARAMS, signals, backtest, metrics)
├── knowledge/
│   ├── backtest_results_log.md  # MUST be updated after every run
│   ├── vbt_code_patterns.md     # VBT-specific patterns and known bugs
│   └── dataset_schemas.md       # Data schema reference
├── PWBBacktest_Data/            # Parquet files (local, do not modify)
└── PWB_tools/                   # Shared toolbox (do not modify)
```

---

## Standard Import Pattern

**Always use this sys.path pattern — do not install PWB_tools as a package.**

```python
import sys
sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")

import numpy as np
import pandas as pd
import vectorbt as vbt
import numba as nb

from PWB_tools import data_loader as dl
from PWB_tools import indicators as ind
from PWB_tools import signals as sig
from PWB_tools import metrics as met
from PWB_tools import plots as plt_tools
from PWB_tools import universe as uni
from PWB_tools import commission as comm
```

---

## PARAMS Dict Reference

Every strategy file must have a top-level `PARAMS` dict. Standard structure:

```python
PARAMS = {
    # Universe
    "datasets": ["Commodities", "Bonds", "Forex", "Indices"],  # which PWBBacktest_Data files
    "symbols": {
        "Commodities": ["GC1", "CL1", "NG1"],   # symbols per dataset
        "Bonds":       ["US10Y", "US30Y"],
        # ...
    },
    "benchmark_symbol": "SPX",
    "benchmark_dataset": "Indices",

    # Date range
    "start_date": "1990-01-01",
    "end_date": "2026-02-28",

    # Strategy parameters
    "ma_short":         50,
    "ma_long":          100,
    "breakout_period":  50,
    "atr_period":       20,
    "atr_multiplier":   3.0,

    # Sizing
    "risk_factor":      0.002,
    "leverage":         5.0,
    "max_size_pct":     0.99,

    # Costs
    "commission":       0.0002,   # 2 bps per side

    # Portfolio
    "init_cash":        100_000,
}
```

---

## Standard Strategy File Structure

Every file in `pwb_strategies/` must implement these functions:

```python
PARAMS = { ... }          # top-level parameter dict (see above)
DATASET_MAP = { ... }     # maps dataset name → list of symbols

def load_universe() -> pd.DataFrame:
    """Load and align all price data. Returns wide DataFrame (date × symbol)."""

def load_benchmark() -> pd.Series:
    """Load benchmark price series."""

def compute_indicators(close: pd.DataFrame) -> dict:
    """Compute all technical indicators. Returns dict of DataFrames."""

def compute_signals(close: pd.DataFrame, indicators: dict) -> dict:
    """Compute entry/exit signals. Returns dict with keys: le, lx, se, sx, spct."""

def run_backtest(close: pd.DataFrame, signals: dict) -> vbt.Portfolio:
    """Run VBT backtest. Must use from_order_func for percent sizing."""

def print_metrics(pf: vbt.Portfolio, benchmark: pd.Series) -> None:
    """Print standard metrics table using met.summary_report()."""

def plot_results(pf: vbt.Portfolio, benchmark: pd.Series) -> None:
    """Generate tearsheet using Performance_Reporting or plt_tools."""

def run_[STRATEGY_NAME]() -> vbt.Portfolio:
    """Master function that calls all above in order. Returns portfolio."""

if __name__ == "__main__":
    pf = run_[STRATEGY_NAME]()
```

---

## Common Commands

```bash
# Run the notebook (from project root)
jupyter nbconvert --to notebook --execute [StrategyName].ipynb --output [StrategyName]_output.ipynb

# Run strategy file directly
python pwb_strategies/[strategy_name]_vbt.py

# Check available symbols in a dataset
python -c "
import sys; sys.path.insert(0, r'D:\Master Data Backup 2025\PapersWBacktest')
from PWB_tools import data_loader as dl
df = dl.load_dataset('Commodities')
print(df['symbol'].unique())
"

# Verify parquet files exist
python -c "
import pathlib
p = pathlib.Path(r'D:\Master Data Backup 2025\PapersWBacktest\PWBBacktest_Data')
for f in sorted(p.glob('*.parquet')): print(f.name)
"
```

---

## Dataset Locations

All parquet files: `D:\Master Data Backup 2025\PapersWBacktest\PWBBacktest_Data\`

| Dataset Name | File | Asset Class |
|---|---|---|
| `Bonds` | Bonds.parquet | Government bond yields/futures |
| `Commodities` | Commodities.parquet | Commodity futures (front-month) |
| `ETFs` | ETFs.parquet | US-listed ETFs |
| `Forex` | Forex.parquet | Currency pairs |
| `Indices` | Indices.parquet | Equity indices |
| `Cryptocurrencies` | Cryptocurrencies.parquet | Crypto spot prices |
| `Universe` | Universe.parquet | US equity universe (~500 stocks) |

For full schema details, see `knowledge/dataset_schemas.md`.

---

## VBT Critical Bugs — Quick Reference

### BUG 1: size_type="percent" with cash_sharing=True

**Symptom:** `ValueError: SizeType.Percent does not support position reversal`

**Fix:** Use `from_order_func` with Numba. The only correct pattern for percent-of-equity with L+S and cash_sharing:

```python
import numba as nb
from vectorbt.portfolio.nb import order_nb as _vbt_order_nb, close_position_nb as _vbt_close_nb

@nb.njit(cache=True)   # MUST be at module level, not inside a function
def _order_func_nb(c, le, lx, se, sx, spct, fees):
    i, col = c.i, c.col
    price, pos = c.val_price_now, c.position_now
    if price <= 0. or price != price: return _vbt_order_nb(size=np.nan)
    if pos > 0. and lx[i, col]: return _vbt_close_nb(price=price, fees=fees)
    if pos < 0. and sx[i, col]: return _vbt_close_nb(price=price, fees=fees)
    if pos == 0.:
        s = spct[i, col]
        if s <= 0. or s != s: return _vbt_order_nb(size=np.nan)
        dollar = s * c.value_now   # percent * total portfolio value
        if le[i, col]:
            return _vbt_order_nb(size=dollar, price=price, size_type=1,
                                 direction=0, fees=fees, lock_cash=True)
        if se[i, col]:
            return _vbt_order_nb(size=dollar, price=price, size_type=1,
                                 direction=1, fees=fees, lock_cash=True)
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

**Key points:**
- `size_type=1` = SizeType.Value (integer — required inside Numba)
- `direction=0/1` = LongOnly/ShortOnly (integer)
- `lock_cash=True` on BOTH sides prevents short cash recycling spiral
- `update_value=True` ensures `c.value_now` updates within a bar
- `c.value_now` = cash + unrealized P&L = broker.getvalue() equivalent

### BUG 2: size_type="percent" uses % of cash, not portfolio value

**Symptom:** Sizing is based on cash only, not total portfolio value — no compounding on unrealized gains.

**Fix:** Use `c.value_now` inside `from_order_func` (shown in BUG 1 fix).

### BUG 3: Negative prices crash backtests

**Symptom:** `order.price must be finite and greater than 0` — caused by negative bond yields or CL1 Apr 2020 (-$37).

**Fix:**
```python
# Compute valid_price BEFORE clipping
valid_price = close.notna() & (close > 0)

# Clip AFTER computing valid_price
close_clean = close.clip(lower=0.0001)

# Block entries on invalid prices
le = le & valid_price
se = se & valid_price
```

---

## Results Logging Requirement

**After every completed backtest run, update `knowledge/backtest_results_log.md`.**

Required fields per entry:
```markdown
## [Strategy Name] — [YYYY-MM-DD]

**Parameters:** [key params]
**Date Range:** [start] to [end]
**Universe:** [N assets, asset classes]

| Metric | Value |
|---|---|
| CAGR | X% |
| Sharpe | X.XX |
| MaxDD | -X% |
| Calmar | X.XX |
| Total Trades | XXXX |
| Win Rate | XX% |

**Notes:** [any anomalies, implementation choices, comparison to paper results]
```

---

## Development Workflow

1. Load data and inspect: check date ranges, missing values, symbol availability
2. Implement indicators in `compute_indicators()` — validate output shapes
3. Implement signals in `compute_signals()` — check signal counts before running full backtest
4. Run backtest on a single asset first to validate sizing logic
5. Run full backtest
6. Compare metrics to paper results — document discrepancies
7. Update `knowledge/backtest_results_log.md`
8. Commit strategy file and results log
