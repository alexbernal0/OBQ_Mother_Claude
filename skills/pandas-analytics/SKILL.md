---
name: pandas-analytics
description: "OBQ pandas and polars financial data processing patterns — time series operations, OHLCV manipulation, rolling windows, cross-sectional ranking, and performance metrics for quantitative finance work."
---

## Core Time Series Patterns

```python
import pandas as pd
import numpy as np

# Ensure datetime index
df.index = pd.to_datetime(df.index)
df = df.sort_index()

# Forward-fill then backfill (standard for OHLCV gaps)
df = df.ffill().bfill()

# Rolling window (use min_periods to handle NaN at edges)
sma_50 = close.rolling(50, min_periods=50).mean()
atr = (high - low).rolling(20, min_periods=1).mean()  # simplified ATR

# Shift for signal timing (today's signal → tomorrow's entry)
signal_shifted = signal.shift(1)

# Percent change (returns)
returns = close.pct_change()
log_returns = np.log(close / close.shift(1))
```

## Long ↔ Wide Format Conversion

```python
# Long format (MotherDuck native): Date, Symbol, value
# Wide format (VectorBT required): date-indexed, symbol columns

# Long → Wide
df_wide = df_long.pivot(index='Date', columns='Symbol', values='adjusted_close')
df_wide.index = pd.to_datetime(df_wide.index)
df_wide = df_wide.sort_index()

# Wide → Long (for MotherDuck writes)
df_long = df_wide.stack().reset_index()
df_long.columns = ['Date', 'Symbol', 'value']
```

## Cross-Sectional Factor Ranking (OBQ Factor Scores)

```python
def percentile_rank_cross_sectional(df: pd.DataFrame) -> pd.DataFrame:
    """Rank each symbol 0-100 within each date cross-section."""
    return df.rank(axis=1, pct=True) * 100

def zscore_cross_sectional(df: pd.DataFrame) -> pd.DataFrame:
    """Z-score normalize each row (date) across symbols."""
    mean = df.mean(axis=1)
    std = df.std(axis=1)
    return df.sub(mean, axis=0).div(std, axis=0)

# Standard OBQ factor score pipeline
raw_factor = compute_raw_factor(df)          # raw metric per symbol per date
percentile = percentile_rank_cross_sectional(raw_factor)  # 0-100 rank
clipped = percentile.clip(lower=5, upper=95) # trim outliers
```

## Performance Metrics

```python
def compute_metrics(nav: pd.Series) -> dict:
    """Standard OBQ performance metrics from NAV series."""
    returns = nav.pct_change().dropna()
    n_years = len(nav) / 252

    cagr = (nav.iloc[-1] / nav.iloc[0]) ** (1 / n_years) - 1
    vol = returns.std() * np.sqrt(252)
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
    sortino_denom = returns[returns < 0].std() * np.sqrt(252)
    sortino = (returns.mean() * 252) / sortino_denom if sortino_denom > 0 else 0

    drawdown = (nav / nav.cummax()) - 1
    max_dd = drawdown.min()
    calmar = cagr / abs(max_dd) if max_dd != 0 else 0

    return {
        'CAGR': cagr, 'Volatility': vol, 'Sharpe': sharpe,
        'Sortino': sortino, 'MaxDD': max_dd, 'Calmar': calmar
    }
```

## Pandas 2.2+ Compatibility (OBQ uses pandas 2.2+)

```python
# WRONG (deprecated in 2.2)
df.applymap(func)     # AttributeError

# CORRECT
df.map(func)          # pandas 2.2+ replacement for applymap

# WRONG (fragmentation warning)
for col in columns:
    df[col] = compute(col)

# CORRECT (assign all at once)
df = df.assign(**{col: compute(col) for col in columns})
```

## Polars (Used in OBQ_AI for performance)

```python
import polars as pl

# DuckDB → Polars (zero-copy via Arrow)
arrow_table = conn.execute("SELECT * FROM prices").arrow()
df_pl = pl.from_arrow(arrow_table)

# Polars → pandas (for VectorBT)
df_pd = df_pl.to_pandas()

# Polars groupby (faster than pandas for large datasets)
result = (
    df_pl
    .group_by(["date", "sector"])
    .agg([
        pl.col("adjusted_close").mean().alias("avg_price"),
        pl.col("Symbol").count().alias("n_symbols"),
    ])
    .sort("date")
)
```

## Always Use Symbol (Capital S)

```python
# WRONG
df['symbol']   # KeyError in most OBQ datasets

# CORRECT
df['Symbol']   # always capital S in OBQ data
```
