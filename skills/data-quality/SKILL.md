---
name: data-quality
description: "Standard OBQ data quality validation protocol before any backtest, pipeline run, or MotherDuck write. Use when loading OHLCV data, before running VBT backtest, or before writing to production databases."
---

# OBQ Data Quality Validation Protocol

Run these checks every time. Data problems found after a backtest require a full re-run. Data problems found after a MotherDuck write require a rollback procedure. Prevention is faster.

---

## PRE-BACKTEST CHECKLIST

Run `validate_ohlcv()` before passing any price data to VBT:

```python
import pandas as pd
import numpy as np

def validate_ohlcv(close: pd.DataFrame, name: str = "close") -> dict:
    """
    Standard OBQ OHLCV validation. Returns dict with all issues found.
    Empty dict = clean data. Non-empty dict = investigate before proceeding.

    Args:
        close: pd.DataFrame, wide format (date index x symbol columns)
        name:  label for logging (e.g., "Commodities close")

    Returns:
        dict of {issue_type: details}
    """
    issues = {}

    # 1. Negative prices — fatal for VBT, economically suspicious for equities
    # Expected negatives: bond yields post-2008, CL1 crude April 2020
    neg = (close < 0).sum()
    if neg.any():
        issues['negative_prices'] = neg[neg > 0].to_dict()

    # 2. NaN density per symbol — high NaN means symbol started late or was delisted
    # >50% NaN = likely wrong symbol or data source mismatch
    nan_pct = close.isna().mean()
    high_nan = nan_pct[nan_pct > 0.5]
    if len(high_nan):
        issues['high_nan_density'] = high_nan.round(3).to_dict()

    # 3. Stale prices — same value 10+ consecutive business days = suspect
    # Common cause: vendor filling gaps with last known price instead of NaN
    for col in close.columns:
        series = close[col].dropna()
        if len(series) < 10:
            continue
        same_as_prev = (series == series.shift(1))
        # rolling(10).sum() on a bool series counts consecutive True runs
        stale_streak = same_as_prev.rolling(10).sum()
        if (stale_streak >= 9).any():
            issues[f'stale_prices_{col}'] = True

    # 4. Business day gaps — more than 5 missing business days suggests a data hole
    # (5 = 1 week, accounts for holidays in a single country)
    expected = pd.bdate_range(close.index.min(), close.index.max())
    missing = expected.difference(close.index)
    if len(missing) > 5:
        issues['date_gaps'] = {
            'count': len(missing),
            'first_5': list(missing[:5].astype(str))
        }

    # 5. All-NaN symbols — symbol in column list but no data at all
    all_nan = close.columns[close.isna().all()].tolist()
    if all_nan:
        issues['all_nan_symbols'] = all_nan

    # 6. Constant columns — price never moves (bad proxy, wrong data)
    for col in close.columns:
        series = close[col].dropna()
        if len(series) > 20 and series.std() == 0:
            issues[f'zero_variance_{col}'] = True

    # 7. Implausible single-bar moves (>50% in one day — possible split or data error)
    pct_chg = close.pct_change().abs()
    big_moves = (pct_chg > 0.50).sum()
    if big_moves.any():
        issues['extreme_1day_moves'] = big_moves[big_moves > 0].to_dict()

    # Summary print
    if issues:
        print(f"[DATA QUALITY] {name}: {len(issues)} issue(s) found:")
        for k, v in issues.items():
            print(f"  {k}: {v}")
    else:
        print(f"[DATA QUALITY] {name}: clean.")

    return issues


def assert_clean(close: pd.DataFrame, name: str = "close", allow_negative: bool = False):
    """
    Raise ValueError if validation finds issues that block a backtest.
    Use allow_negative=True for bond yield datasets.
    """
    issues = validate_ohlcv(close, name)
    blocking = {k: v for k, v in issues.items()
                if not (allow_negative and k == 'negative_prices')}
    if blocking:
        raise ValueError(f"Data quality issues block backtest for {name}: {blocking}")
```

### Usage Example

```python
# Load data
from PWB_tools import data_loader as dl

close = dl.get_pricing("Commodities", field="close")

# Validate
issues = validate_ohlcv(close, name="Commodities close")

# Apply standard fixes
valid_price = close.notna() & (close > 0)   # compute BEFORE clipping
close_clean = close.clip(lower=0.0001)       # clip AFTER flagging

# Pass both to signal computation and backtest
```

---

## PRE-MOTHERDUCK WRITE CHECKLIST

Before writing any DataFrame to MotherDuck (PROD_EODHD, GoldenOpp, or staging):

```python
def validate_for_motherduck(df: pd.DataFrame, table_name: str,
                             date_col: str = "Date",
                             symbol_col: str = "Symbol") -> dict:
    """
    Validate a DataFrame before writing to MotherDuck.
    Returns dict of issues. Empty dict = safe to write.
    """
    issues = {}

    # 1. Schema: expected columns present
    # (caller should pass expected_cols list from production schema)

    # 2. Duplicate rows on primary key
    dupes = df.duplicated(subset=[date_col, symbol_col]).sum()
    if dupes > 0:
        issues['duplicate_rows'] = dupes

    # 3. Date range sanity
    if date_col in df.columns:
        dates = pd.to_datetime(df[date_col])
        if dates.max() > pd.Timestamp.today() + pd.Timedelta(days=1):
            issues['future_dates'] = str(dates.max())
        if dates.min() < pd.Timestamp("1960-01-01"):
            issues['prehistoric_dates'] = str(dates.min())

    # 4. Record count plausibility
    n = len(df)
    if n == 0:
        issues['empty_dataframe'] = True

    # 5. Symbol format: MotherDuck uses TICKER.US format
    if symbol_col in df.columns:
        sample = df[symbol_col].dropna().head(10).tolist()
        non_suffixed = [s for s in sample if isinstance(s, str) and '.' not in s]
        if non_suffixed:
            issues['missing_dot_suffix'] = {
                'example': non_suffixed[:3],
                'note': "MotherDuck tables use TICKER.US format"
            }

    # 6. Critical numeric columns: no all-NaN
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols:
        if df[col].isna().all():
            issues[f'all_nan_column_{col}'] = True

    if issues:
        print(f"[MOTHERDUCK VALIDATE] {table_name}: {len(issues)} issue(s):")
        for k, v in issues.items():
            print(f"  {k}: {v}")
    else:
        print(f"[MOTHERDUCK VALIDATE] {table_name}: ready to write ({n:,} rows).")

    return issues


def safe_motherduck_write(conn, df: pd.DataFrame, table: str,
                          mode: str = "append",
                          validate_sample_size: int = 1000):
    """
    Write to MotherDuck with validation on a sample before full write.

    Args:
        conn:   active DuckDB/MotherDuck connection
        df:     DataFrame to write
        table:  fully qualified table name, e.g. "my_db.main.prices"
        mode:   "append" or "replace"
        validate_sample_size: rows to validate before full write
    """
    # Validate sample first
    sample = df.head(validate_sample_size)
    issues = validate_for_motherduck(sample, table)
    blocking = {k: v for k, v in issues.items() if k != 'empty_dataframe'}
    if blocking:
        raise ValueError(f"Pre-write validation failed for {table}: {blocking}")

    # Write
    if mode == "replace":
        conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df")
    else:
        conn.execute(f"INSERT INTO {table} SELECT * FROM df")

    print(f"[MOTHERDUCK WRITE] {table}: {len(df):,} rows written ({mode}).")
```

---

## POINT-IN-TIME VALIDATION (Fundamental Data)

Point-in-time correctness is the most common source of look-ahead bias in factor backtests. Run these checks when working with earnings, balance sheet, or income statement data.

```python
def validate_point_in_time(df: pd.DataFrame,
                            filing_col: str = "filing_date",
                            period_col: str = "quarter_date") -> dict:
    """
    Validate that a fundamentals DataFrame is properly point-in-time.
    Returns dict of issues found.
    """
    issues = {}

    # 1. Filing date must exist (never join on period/quarter date alone)
    if filing_col not in df.columns:
        issues['missing_filing_date'] = (
            f"Column '{filing_col}' not found. "
            "Never join fundamentals on period/quarter date — use filing_date only."
        )
        return issues  # Cannot continue without filing_date

    # 2. Filing must come AFTER the period it reports on
    if period_col in df.columns:
        late_filings = df[pd.to_datetime(df[filing_col]) < pd.to_datetime(df[period_col])]
        if len(late_filings) > 0:
            issues['filing_before_period'] = {
                'count': len(late_filings),
                'note': "Filing date is before the quarter it reports — data corruption"
            }

    # 3. Filing lag: typical range is 30-90 days for quarterly reports
    if period_col in df.columns:
        lag = (pd.to_datetime(df[filing_col]) - pd.to_datetime(df[period_col])).dt.days
        extreme_lag = (lag > 365).sum()
        negative_lag = (lag < 0).sum()
        if extreme_lag > 0:
            issues['extreme_filing_lag'] = f"{extreme_lag} rows with lag > 365 days"
        if negative_lag > 0:
            issues['negative_filing_lag'] = f"{negative_lag} rows"

    # 4. Future filing dates
    today = pd.Timestamp.today()
    future = (pd.to_datetime(df[filing_col]) > today).sum()
    if future > 0:
        issues['future_filing_dates'] = future

    return issues
```

**Rules for point-in-time joins:**
```python
# CORRECT: merge on filing_date, take most recent known as of each backtest date
# Conceptually: "what was the latest filing available on this date?"
def pit_merge(prices: pd.DataFrame, fundamentals: pd.DataFrame,
              filing_col: str = "filing_date",
              symbol_col: str = "Symbol") -> pd.DataFrame:
    """
    Merge price data with fundamentals on a point-in-time basis.
    For each price date, use only fundamentals filed on or before that date.
    """
    result_rows = []
    for date in prices.index:
        available = fundamentals[
            pd.to_datetime(fundamentals[filing_col]) <= date
        ]
        # Take most recent filing per symbol
        latest = available.sort_values(filing_col).groupby(symbol_col).last()
        row = prices.loc[[date]].join(latest, how='left')
        result_rows.append(row)
    return pd.concat(result_rows)

# WRONG — never do this:
# prices.merge(fundamentals, on=['Symbol', 'quarter_date'])
# This leaks future earnings data into past signals.
```

---

## SYMBOL FORMAT CHECK

Symbol format inconsistency is a silent join failure — no error, just NaN results.

```python
def check_symbol_format(symbols: list, context: str = "") -> dict:
    """
    Diagnose symbol format issues across OBQ systems.

    OBQ format rules:
    - MotherDuck (PROD_EODHD): "AAPL.US", "GLD.US"  — always TICKER.US
    - PWBBacktest_Data / VBT: "AAPL", "GLD"           — no suffix
    - Display / reporting: "AAPL", "GLD"               — no suffix
    """
    has_suffix = [s for s in symbols if isinstance(s, str) and '.' in s]
    no_suffix   = [s for s in symbols if isinstance(s, str) and '.' not in s]

    report = {
        'total': len(symbols),
        'with_suffix': len(has_suffix),
        'without_suffix': len(no_suffix),
        'examples_with': has_suffix[:3],
        'examples_without': no_suffix[:3],
    }

    if has_suffix and no_suffix:
        report['WARNING'] = "Mixed formats — joins across systems will silently fail"

    if context:
        print(f"[SYMBOL FORMAT] {context}: {report}")

    return report


# Conversion utilities
def strip_suffix(symbols):
    """'AAPL.US' -> 'AAPL' (for PWBBacktest_Data / VBT)"""
    return [s.split('.')[0] if isinstance(s, str) else s for s in symbols]

def add_suffix(symbols, suffix='.US'):
    """'AAPL' -> 'AAPL.US' (for MotherDuck joins)"""
    return [f"{s}{suffix}" if isinstance(s, str) and '.' not in s else s for s in symbols]
```

---

## WIDE vs. LONG FORMAT CONVERSION

VBT requires wide format. MotherDuck returns long format. Always check before passing data between systems.

```python
def ensure_wide(df: pd.DataFrame,
                date_col: str = "Date",
                symbol_col: str = "Symbol",
                value_col: str = "close") -> pd.DataFrame:
    """
    Convert long format (Date, Symbol, close) to wide format (date x symbol).
    Checks for duplicates before pivoting — duplicates cause silent data loss.
    """
    # Check for duplicates on the key
    dupes = df.duplicated(subset=[date_col, symbol_col]).sum()
    if dupes > 0:
        raise ValueError(
            f"Cannot pivot: {dupes} duplicate ({date_col}, {symbol_col}) rows. "
            "Resolve duplicates before converting to wide format."
        )

    wide = df.pivot(index=date_col, columns=symbol_col, values=value_col)
    wide.index = pd.to_datetime(wide.index)
    wide = wide.sort_index()

    print(f"[FORMAT] Converted to wide: {wide.shape[0]} dates x {wide.shape[1]} symbols. "
          f"NaN density: {wide.isna().mean().mean():.1%}")

    return wide
```
