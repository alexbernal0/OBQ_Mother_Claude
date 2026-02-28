---
name: market-data-api
description: "OBQ market data integration patterns — EODHD API (primary), Norgate Data (63K+ symbols), and data loading from PWBBacktest_Data parquet files. Use when fetching, syncing, or validating market data."
---

## EODHD API

**Rate limits**: 1000 calls/min, 100K/day. Always use RateLimiter.

```python
import requests, time, os

class RateLimiter:
    def __init__(self, delay=0.06):  # 0.06s = 1000/min
        self.delay = delay
        self._last = 0.0

    def wait(self):
        elapsed = time.time() - self._last
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last = time.time()

limiter = RateLimiter(delay=0.06)

def get_eod_prices(ticker: str, from_date: str = "1990-01-01") -> dict:
    """Fetch EOD prices from EODHD."""
    limiter.wait()
    url = f"https://eodhd.com/api/eod/{ticker}"
    params = {
        "api_token": os.getenv("EODHD_API_KEY"),
        "fmt": "json",
        "from": from_date,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def get_fundamentals(ticker: str) -> dict:
    """Fetch fundamental data from EODHD."""
    limiter.wait()
    url = f"https://eodhd.com/api/fundamentals/{ticker}"
    params = {"api_token": os.getenv("EODHD_API_KEY"), "fmt": "json"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

**Key endpoints**:
- `/api/eod/{TICKER.US}` — daily OHLCV + adjusted_close
- `/api/fundamentals/{TICKER.US}` — balance sheet, earnings, cash flow, income
- `/api/exchange-symbol-list/US` — full US equity universe
- `/api/bulk-eod/US?date=2025-01-15` — bulk daily snapshot

**Always use `adjusted_close`** for historical analysis (splits/dividends adjusted).

## Norgate Data (OBQ_AI — 63K+ Symbols)

```python
import norgatedata

# List available databases
databases = norgatedata.databases()
# Returns: ASX, Canada, India, Japan, KoreanStockExchange, NYSE,
#          US_Delisted, USFutures, USMutualFunds

# Get price data (survivorship-bias-free)
pricedata_array = norgatedata.price_timeseries(
    symbol="AAPL",
    stock_price_adjustment_setting=norgatedata.StockPriceAdjustmentType.TOTALRETURN,
    padding_setting=norgatedata.PaddingType.NONE,
    start_date="2020-01-01",
    end_date="2025-12-31",
    timeseriesformat="pandas-dataframe"
)

# Batch processing (always 100 symbols at a time)
BATCH_SIZE = 100
for i in range(0, len(symbols), BATCH_SIZE):
    batch = symbols[i:i + BATCH_SIZE]
    for sym in batch:
        data = norgatedata.price_timeseries(sym, ...)
        # process...
    print(f"Processed {min(i+BATCH_SIZE, len(symbols))}/{len(symbols)}")
```

**Point-in-time index membership** (critical for avoiding survivorship bias):
```python
# Check if symbol was in index on a specific date
was_in_index = norgatedata.index_constituent_timeseries(
    "AAPL", "S&P 500", start_date="2020-01-01"
)
```

## PWBBacktest_Data (Local Parquet)

```python
import sys
sys.path.insert(0, r"D:\Master Data Backup 2025\PapersWBacktest")
from PWB_tools import data_loader as dl

# Available datasets
datasets = ["Bonds", "Commodities", "ETFs", "Forex", "Indices",
            "Cryptocurrencies", "Universe"]

# Load wide format (date × symbol)
close = dl.get_pricing("Commodities", symbols=["GC1", "CL1", "NG1"], field="close")
high  = dl.get_pricing("Commodities", symbols=["GC1", "CL1", "NG1"], field="high")
low   = dl.get_pricing("Commodities", symbols=["GC1", "CL1", "NG1"], field="low")

# Load single symbol OHLCV
ohlcv = dl.get_ohlcv("Commodities", "GC1")

# Load multiple symbols full OHLCV
multi = dl.get_multi_ohlcv("Bonds", ["US10Y", "US2Y", "DE10Y"])

# Load in long format
df_long = dl.load_dataset("Indices", symbols=["SPX", "NKY"])
```

**Known bad symbols** (removed or proxied):
- `EU1Y` — not in dataset; removed
- `EU10Y` — only 2 rows; removed
- `NIKKEI` → use `NKY`
- `JPYUSD` → use `USDJPY` (inverted)
- `CHFUSD` → use `USDCHF` (inverted)
- `CADUSD` → use `USDCAD` (inverted)

## Incremental Sync Pattern (for pipelines)

```python
import duckdb, os

def get_last_sync_date(conn, table: str, date_col: str = "date") -> str:
    """Get last date in MotherDuck table for incremental sync."""
    try:
        result = conn.execute(f"SELECT MAX({date_col}) FROM {table}").fetchone()
        return str(result[0]) if result[0] else "1990-01-01"
    except Exception:
        return "1990-01-01"

def sync_incremental(symbols: list, table: str):
    conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")
    last_date = get_last_sync_date(conn, table)
    print(f"Syncing from {last_date}")

    limiter = RateLimiter(delay=0.06)
    for symbol in symbols:
        limiter.wait()
        data = get_eod_prices(symbol, from_date=last_date)
        if data:
            df = pd.DataFrame(data)
            df['symbol'] = symbol.replace('.US', '')
            conn.execute(f"INSERT INTO {table} SELECT * FROM df")
    conn.close()
```
