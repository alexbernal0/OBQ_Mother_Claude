---
name: duckdb-data-eng
description: "OBQ DuckDB and MotherDuck data engineering patterns — connection management, schema conventions, zone-map optimization, symbol format handling, ETL patterns, and production write protocol. Use for any DuckDB or MotherDuck work."
---

## OBQ DuckDB and MotherDuck Data Engineering Patterns

---

## 1. CONNECTION PATTERNS

```python
import duckdb
import os

# MotherDuck cloud connection
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")
conn.execute("USE PROD_EODHD")  # set active database for subsequent queries

# Local DuckDB (analytics / staging)
conn = duckdb.connect(r"D:\OBQ_AI\obq_ai.duckdb")
conn.execute("PRAGMA memory_limit='12GB'; PRAGMA threads=8;")

# In-memory (temporary computation)
conn = duckdb.connect()
```

Always use `os.getenv('MOTHERDUCK_TOKEN')` — never hardcode the token.

---

## 2. PRODUCTION SCHEMA MAP

```
PROD_EODHD.main.PROD_EOD_survivorship
    Columns: date, symbol, open, high, low, close, adjusted_close, volume, sector, industry
    Note:    Survivorship-bias-free daily OHLC. USE adjusted_close for analysis.

PROD_EODHD.main.PROD_OBQ_Scores
    Columns: date, symbol, value_score, growth_score, fs_score, quality_score
    Note:    Composite factor scores. All scores are percentile-ranked (0–100).

PROD_EODHD.main.PROD_OBQ_Momentum_Scores
    Columns: date, symbol, obq_momentum_score, systemscore
    Note:    Momentum factor score per symbol per date.

PROD_EODHD.main.PROD_EOD_ETFs
    Columns: date, symbol, open, high, low, close, adjusted_close, volume
    Note:    ETF pricing. SPY.US = equity benchmark. GLD.US = gold benchmark.

GoldenOpp.GDX_GLD_Mining_Stocks_Prices
    Columns: date, symbol, adjusted_close, ...
    Note:    56 gold mining stocks + 4 ETFs, 53 years of history.

qgsi.*
    Note:    QGSI signal research data (separate database).

DEV_EODHD_DATA.*
    Note:    Development / staging database — safe to write without escalation.
```

---

## 3. PRODUCTION WRITE PROTOCOL

Before writing to any `PROD_*` table, follow this sequence (see also obq-governance skill):

```python
# Step 1: Validate before write
print(f"Rows to write: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Symbols: {df['symbol'].nunique()} unique")
print(f"Null rate: {df.isnull().mean().to_dict()}")

# Step 2: Write to DEV first
conn.execute("CREATE OR REPLACE TABLE DEV_EODHD_DATA.main.DEV_STAGING AS SELECT * FROM df")

# Step 3: Verify DEV output
result = conn.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM DEV_EODHD_DATA.main.DEV_STAGING").fetchdf()
print(result)

# Step 4: Confirm with Alex, then promote to PROD
# conn.execute("INSERT INTO PROD_EODHD.main.PROD_TARGET SELECT * FROM DEV_EODHD_DATA.main.DEV_STAGING")
```

---

## 4. ZONE-MAP OPTIMIZATION

DuckDB uses zone maps (min/max metadata per row group) for fast predicate pushdown. Always sort on write:

```python
# Critical for query performance — sort by date then symbol before every write
df = df.sort_values(['date', 'symbol']).reset_index(drop=True)

# Register and insert
conn.register('df_view', df)
conn.execute("INSERT INTO target_table SELECT * FROM df_view")
```

This ensures date-range and symbol filters skip entire row groups rather than scanning all data.

---

## 5. SYMBOL FORMAT HANDLING

MotherDuck stores symbols as `TICKER.US`. VectorBT and display layers use bare `TICKER`. Normalize at every boundary:

```python
# Convert display → MotherDuck form
symbols_md = [f"{s}.US" for s in symbols]

# Convert MotherDuck → display form
symbols_clean = [s.replace('.US', '') for s in symbols_md]

# Defensive query — handle inconsistency in historical data
all_forms = symbols_md + symbols_clean
placeholders = ','.join([f"'{s}'" for s in all_forms])
query = f"SELECT * FROM PROD_EOD_survivorship WHERE symbol IN ({placeholders})"
```

---

## 6. LONG → WIDE TRANSFORMATION (for VectorBT)

MotherDuck returns long format. VectorBT expects wide (date × symbol):

```python
# Query returns: date, symbol, adjusted_close
df_long = conn.execute("""
    SELECT date, symbol, adjusted_close
    FROM PROD_EODHD.main.PROD_EOD_survivorship
    WHERE symbol IN ({placeholders})
    ORDER BY date, symbol
""").fetchdf()

# Transform to wide format
df_wide = df_long.pivot(index='date', columns='symbol', values='adjusted_close')
df_wide.index = pd.to_datetime(df_wide.index)
df_wide = df_wide.sort_index()
df_wide.columns.name = None  # clean up column axis name
```

---

## 7. DATA INTEGRITY CHECKS (run before any analysis)

```python
def validate_price_data(df: pd.DataFrame, name: str = "data") -> None:
    """Run standard OBQ data integrity checks."""
    issues = []

    # Check for future dates
    if df.index.max() > pd.Timestamp.today():
        issues.append(f"Future dates present: max={df.index.max()}")

    # Check for negative prices
    neg_mask = (df < 0) & df.notna()
    if neg_mask.any().any():
        neg_cols = df.columns[neg_mask.any()].tolist()
        issues.append(f"Negative prices in: {neg_cols}")

    # Check for extreme gaps (possible split artifacts)
    pct_change = df.pct_change().abs()
    extreme = (pct_change > 0.5) & pct_change.notna()
    if extreme.any().any():
        issues.append(f"Day-over-day moves > 50% detected — verify adjusted_close used")

    if issues:
        for issue in issues:
            print(f"WARNING [{name}]: {issue}")
    else:
        print(f"OK [{name}]: {len(df)} rows, {len(df.columns)} symbols, {df.index.min()} to {df.index.max()}")
```

---

## 8. COMMON QUERY PATTERNS

```python
# Latest scores per symbol
conn.execute("""
    SELECT symbol, value_score, growth_score, quality_score
    FROM PROD_EODHD.main.PROD_OBQ_Scores
    WHERE date = (SELECT MAX(date) FROM PROD_EODHD.main.PROD_OBQ_Scores)
    ORDER BY value_score DESC
""").fetchdf()

# Rolling window with DuckDB
conn.execute("""
    SELECT date, symbol,
           AVG(adjusted_close) OVER (
               PARTITION BY symbol
               ORDER BY date
               ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
           ) AS sma50
    FROM PROD_EODHD.main.PROD_EOD_survivorship
    WHERE symbol = 'AAPL.US'
""").fetchdf()
```
