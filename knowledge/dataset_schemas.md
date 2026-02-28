# OBQ Dataset Schema Reference

## SECTION 1: PWBBacktest_Data (local parquet files)

Located at: `D:\Master Data Backup 2025\PapersWBacktest\PWBBacktest_Data\`

All files are daily frequency. Load using the `PWB_tools.data_loader` module (see Section 5 for loading patterns).

| Filename | Asset Class | Symbols (count) | Date Range | Columns |
|---|---|---|---|---|
| `Bonds.parquet` | Government Bonds / Rates | US2Y, US5Y, US10Y, US30Y, DE10Y, JP10Y, GB10Y, EU3M (~15) | ~1990–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `Commodities.parquet` | Commodity Futures (front-month) | GC1, SI1, CL1, NG1, HG1, ZC1, ZS1, ZW1, CC1, KC1, CT1, SB1, LH1, LE1, HE1, PA1, PL1, RB1 (~20) | ~1990–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `ETFs.parquet` | US-listed ETFs | SPY, GLD, TLT, EFA, EEM, VNQ, HYG, LQD, QQQ, IWM, DIA, XLE, XLF, XLK, XLV, USO, GDX, SLV, UUP (~40) | ~2003–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `Forex.parquet` | Currency Pairs | EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURGBP, EURJPY, GBPJPY (~10) | ~1990–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `Indices.parquet` | Equity Indices | SPX, NDX, RTY, DJIA, NKY, DAX, FTSE, CAC, SMI, AEX, IBEX, ASX, HSI, KOSPI, SENSEX (~15) | ~1990–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `Cryptocurrencies.parquet` | Crypto Spot | BTC, ETH, LTC, XRP, BCH, EOS, BNB, ADA, SOL, DOT (~10) | ~2015–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `Universe.parquet` | US Equities (active large/mid) | ~500 stocks (S&P 500 constituents) | ~2000–2026 | date, symbol, open, high, low, close, volume, adjusted_close |
| `Stocks-Quarterly-BalanceSheet.parquet` | Fundamentals | ~500 symbols | ~2000–2026 | symbol, quarter_date, filing_date, total_assets, total_liabilities, equity, cash, debt (+ 30 more) |
| `Stocks-Quarterly-Earnings.parquet` | Fundamentals | ~500 symbols | ~2000–2026 | symbol, quarter_date, filing_date, eps, eps_diluted, revenue, net_income, surprise_pct (+ 15 more) |
| `Stocks-Quarterly-CashFlow.parquet` | Fundamentals | ~500 symbols | ~2000–2026 | symbol, quarter_date, filing_date, operating_cash_flow, capex, free_cash_flow, dividends_paid (+ 20 more) |
| `Stocks-Quarterly-IncomeStatement.parquet` | Fundamentals | ~500 symbols | ~2000–2026 | symbol, quarter_date, filing_date, revenue, gross_profit, ebitda, operating_income, net_income, eps (+ 25 more) |
| `All-Monthly-CoreEconomicData.parquet` | Macro | CPI, PCE, FEDFUNDS, UNRATE, GDP, PAYEMS, ISM, RETAIL, HOUSING (~20 series) | ~1970–2026 | date, series_id, value, revised_value |

**Important Notes:**
- `CL1` (crude oil) contains negative values during Apr 2020. Always clip to `close.clip(lower=0.0001)` after filtering `valid_price = close > 0`.
- Bond yields may be negative (e.g., `DE10Y`, `JP10Y`). Block entries using `entries & valid_price` where `valid_price = close > 0`.
- Forex symbols: pairs stored as quote currency per base (e.g., `USDJPY` = yen per dollar).
- `EU3M` (3-month Euribor) and `EU1Y` are NOT reliably available — use `US2Y` as short-rate proxy.

---

## SECTION 2: MotherDuck Production Schema

Connection: `duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")`

### PROD_EODHD.main.PROD_EOD_survivorship

Primary price table for all US equity backtesting. Survivorship-bias-free (includes delisted stocks).

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Trading date |
| `symbol` | VARCHAR | Ticker with suffix (e.g., `AAPL.US`) |
| `open` | DOUBLE | Unadjusted open price |
| `high` | DOUBLE | Unadjusted high price |
| `low` | DOUBLE | Unadjusted low price |
| `close` | DOUBLE | Unadjusted close price |
| `adjusted_close` | DOUBLE | **Split and dividend adjusted close (use this for returns)** |
| `volume` | BIGINT | Daily volume |
| `exchange` | VARCHAR | Exchange code |

**Primary Key:** `(date, symbol)`
**Typical Row Count:** ~225M rows
**Date Range:** ~1960–present
**Index:** Clustered on `(symbol, date)` for symbol-range queries

---

### PROD_EODHD.main.PROD_OBQ_Scores

Factor scores computed by OBQ_Fundamental_Pro. All scores are cross-sectionally normalized (z-score or percentile rank within the universe for that date).

| Column | Type | Description |
|---|---|---|
| `date` | DATE | **Filing date** (point-in-time — when the financials were publicly available) |
| `symbol` | VARCHAR | Ticker with suffix (e.g., `AAPL.US`) |
| `value_score` | DOUBLE | Value factor score (higher = cheaper) |
| `growth_score` | DOUBLE | Growth factor score (higher = faster growing) |
| `fs_score` | DOUBLE | Financial strength score (Piotroski-inspired, 0–9 integer components) |
| `quality_score` | DOUBLE | Quality/profitability score (higher = higher quality) |
| `composite_score` | DOUBLE | Equally-weighted average of the four non-momentum scores |
| `universe_rank` | INTEGER | Rank by composite_score within the universe (1 = best) |
| `universe_size` | INTEGER | Number of stocks scored on this date |

**Primary Key:** `(date, symbol)`
**Typical Row Count:** ~15M rows
**Date Range:** ~2000–present

---

### PROD_EODHD.main.PROD_OBQ_Momentum_Scores

Momentum scores updated more frequently than the quarterly fundamental scores.

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Score calculation date |
| `symbol` | VARCHAR | Ticker with suffix |
| `momentum_score` | DOUBLE | 12-1 month price momentum (normalized) |
| `earnings_revision_score` | DOUBLE | EPS estimate revision momentum |
| `relative_strength` | DOUBLE | Relative strength vs. S&P 500 |
| `systemscore` | DOUBLE | Combined signal used for ranking |
| `momentum_rank` | INTEGER | Rank by systemscore within universe |

**Primary Key:** `(date, symbol)`
**Typical Row Count:** ~5M rows
**Date Range:** ~2000–present

---

### PROD_EODHD.main.PROD_EOD_ETFs

Daily OHLCV and adjusted close for key ETFs.

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Trading date |
| `symbol` | VARCHAR | ETF ticker with suffix (e.g., `SPY.US`) |
| `open` | DOUBLE | Open price |
| `high` | DOUBLE | High price |
| `low` | DOUBLE | Low price |
| `close` | DOUBLE | Close price |
| `adjusted_close` | DOUBLE | Adjusted close (use for returns) |
| `volume` | BIGINT | Daily volume |

**Primary Key:** `(date, symbol)`
**Typical Row Count:** ~500K rows
**Date Range:** ~1993–present (SPY inception date)

---

### GoldenOpp.main.GDX_GLD_Mining_Stocks_Prices

Gold mining stocks and related ETFs for OBQ_GoldenOpp system.

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Trading date |
| `symbol` | VARCHAR | Ticker (e.g., `NEM`, `GDX`) |
| `open` | DOUBLE | Open price |
| `high` | DOUBLE | High price |
| `low` | DOUBLE | Low price |
| `close` | DOUBLE | Close price |
| `adjusted_close` | DOUBLE | Adjusted close |
| `volume` | BIGINT | Daily volume |

**Primary Key:** `(date, symbol)`
**Universe:** 56 gold mining stocks + GDX, GLD, GDXJ, SLV
**Date Range:** ~1970–present (53 years)

---

## SECTION 3: Local DuckDB (OBQ_AI)

**Path:** `D:\OBQ_AI\obq_ai.duckdb`

**Size:** 204M+ rows, approximately 8–10GB on disk

**Configuration:**
```python
import duckdb
conn = duckdb.connect(r"D:\OBQ_AI\obq_ai.duckdb")
conn.execute("SET memory_limit='12GB'")
conn.execute("SET threads=8")
```

**Schema:** Mirrors MotherDuck PROD_EODHD structure but stored locally for fast agent access. Sorted by `(date, symbol)` for efficient date-range scans. Refreshed periodically from MotherDuck.

**Performance Notes:**
- Primary access pattern: `WHERE date >= '2020-01-01' AND symbol = 'AAPL.US'`
- Use `PRAGMA database_list` to verify connection
- Avoid full table scans on the main price table — always filter by date or symbol
- For universe-wide scans, read in chunks of 250K rows max

---

## SECTION 4: Symbol Format Conventions

Different systems use different symbol formats. Always convert appropriately when moving data between systems.

| System | Format | Example | Notes |
|---|---|---|---|
| MotherDuck (all PROD tables) | `TICKER.US` | `AAPL.US`, `SPY.US` | Always includes `.US` suffix for US stocks/ETFs |
| Local DuckDB (OBQ_AI) | `TICKER.US` | `AAPL.US` | Same as MotherDuck |
| VectorBT (column headers) | `TICKER` | `AAPL`, `SPY` | Strip `.US` suffix before passing to VBT |
| PWBBacktest_Data | Asset-class specific | `GC1`, `CL1`, `SPX`, `EURUSD` | Commodity futures use Bloomberg convention (contract month suffix `1` = front month) |
| Norgate Data | Standard US ticker | `AAPL`, `MSFT` | No suffix; delisted stocks use historical tickers |
| EODHD API | `TICKER.US` | `AAPL.US` | Exchange suffix required in API calls |

**Conversion Helpers:**
```python
# Strip MotherDuck suffix for VBT
symbols_vbt = [s.replace(".US", "") for s in symbols_md]

# Add suffix for MotherDuck queries
symbols_md = [f"{s}.US" if "." not in s else s for s in symbols_vbt]
```

**Special Cases:**
- Forex in Norgate: stored as rate pairs, convention may differ from EODHD
- Commodity futures: `GC1` = gold front-month, `GC2` = second month, etc.
- Indices: `SPX` (PWBBacktest), `^GSPC` (Yahoo convention — not used in OBQ)
- Crypto: `BTC-USD` in some sources; stored as `BTC` in PWBBacktest_Data

---

## SECTION 5: Data Loading Patterns

### PWBBacktest_Data (VBT strategies)

```python
import sys
sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")
from PWB_tools import data_loader as dl

# Wide format: date × symbol (returns DataFrame)
close = dl.get_pricing("Commodities", symbols=["GC1", "CL1"], field="close")
close_adj = dl.get_pricing("Universe", field="adjusted_close")  # all symbols

# Single-symbol OHLCV (returns DataFrame with open/high/low/close/volume)
ohlcv = dl.get_ohlcv("Commodities", "GC1")

# Long format (returns DataFrame with date, symbol, value columns)
df_long = dl.load_dataset("Bonds", symbols=["US10Y", "US30Y"])

# Available datasets
# Price datasets: Bonds, Commodities, ETFs, Forex, Indices, Cryptocurrencies, Universe
# Fundamental: Stocks-Quarterly-BalanceSheet, Stocks-Quarterly-Earnings,
#              Stocks-Quarterly-CashFlow, Stocks-Quarterly-IncomeStatement
# Macro: All-Monthly-CoreEconomicData
```

### MotherDuck (production queries)

```python
import duckdb
import os

# Connect (token from environment variable — never hardcode)
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

# Basic price query
df = conn.execute("""
    SELECT date, symbol, adjusted_close
    FROM PROD_EODHD.main.PROD_EOD_survivorship
    WHERE date >= '2020-01-01'
      AND symbol IN ('AAPL.US', 'MSFT.US', 'SPY.US')
    ORDER BY date, symbol
""").df()

# Factor scores query (always use filing_date for point-in-time joins)
scores = conn.execute("""
    SELECT date, symbol, value_score, quality_score, composite_score
    FROM PROD_EODHD.main.PROD_OBQ_Scores
    WHERE date >= '2015-01-01'
      AND composite_score IS NOT NULL
    ORDER BY date, composite_score DESC
""").df()

# Join prices to scores using filing_date (point-in-time safe)
df = conn.execute("""
    SELECT p.date, p.symbol, p.adjusted_close, s.composite_score
    FROM PROD_EODHD.main.PROD_EOD_survivorship p
    JOIN PROD_EODHD.main.PROD_OBQ_Scores s
      ON p.symbol = s.symbol
      AND p.date >= s.date  -- use scores available on or before trade date
    WHERE p.date >= '2015-01-01'
""").df()

# Handle token expiry
from duckdb import MotherDuckCatalogException
try:
    conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")
except MotherDuckCatalogException:
    print("MotherDuck token expired — refresh MOTHERDUCK_TOKEN env var")
    raise
```

### Local DuckDB (OBQ_AI)

```python
import duckdb

conn = duckdb.connect(r"D:\OBQ_AI\obq_ai.duckdb")
conn.execute("SET memory_limit='12GB'")
conn.execute("SET threads=8")

# Verify connection
tables = conn.execute("SHOW TABLES").df()
print(tables)

# Standard query
df = conn.execute("""
    SELECT date, symbol, adjusted_close
    FROM prices
    WHERE date >= '2023-01-01'
    ORDER BY date, symbol
""").df()
```

### DEV Write Pattern (safe staging before PROD promotion)

```python
# ALWAYS write to DEV first
conn.execute(f"""
    CREATE TABLE IF NOT EXISTS DEV_EODHD_DATA.main.DEV_my_table AS
    SELECT * FROM my_dataframe_staging
""")

# Validate
row_count = conn.execute("SELECT COUNT(*) FROM DEV_EODHD_DATA.main.DEV_my_table").fetchone()[0]
print(f"DEV table row count: {row_count}")

# Only after validation — promote to PROD (requires Article I.6 override)
# conn.execute("CREATE TABLE PROD_EODHD.main.PROD_my_table AS SELECT * FROM DEV_EODHD_DATA.main.DEV_my_table")
```
