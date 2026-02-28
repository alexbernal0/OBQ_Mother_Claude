# OBQ API Reference

## EODHD API

**Base URL:** `https://eodhd.com/api/`

**Rate Limits:**
- 1,000 API calls per minute
- 100,000 API calls per day
- Burst limit: 20 calls/second

**Authentication:**
API key passed as query parameter `api_token` or as `Authorization: Bearer <key>` header. Store in environment variable `EODHD_API_KEY`.

### Key Endpoints

**End-of-Day Prices:**
```
GET https://eodhd.com/api/eod/{TICKER}.{EXCHANGE}
    ?api_token={KEY}
    &from=2020-01-01
    &to=2026-02-28
    &period=d          # d=daily, w=weekly, m=monthly
    &adjusted=1        # 1 = return adjusted_close column
    &fmt=json
```

**Bulk EOD (all symbols for an exchange — more efficient):**
```
GET https://eodhd.com/api/eod-bulk-last-day/{EXCHANGE}
    ?api_token={KEY}
    &date=2026-02-27
    &fmt=json
```

**Fundamental Data:**
```
GET https://eodhd.com/api/fundamentals/{TICKER}.{EXCHANGE}
    ?api_token={KEY}
    &filter=Financials  # or General, Highlights, Valuation
    &fmt=json
```

**Exchange Symbol List:**
```
GET https://eodhd.com/api/exchange-symbol-list/{EXCHANGE}
    ?api_token={KEY}
    &fmt=json
    &type=common_stock  # filter to common stocks only
```

**Python Pattern with Rate Limiting:**
```python
import os
import time
import requests
from ratelimit import limits, sleep_and_retry

EODHD_API_KEY = os.getenv("EODHD_API_KEY")
BASE_URL = "https://eodhd.com/api"

@sleep_and_retry
@limits(calls=1000, period=60)  # 1000 calls per minute
def eodhd_get(endpoint: str, params: dict) -> dict:
    """Rate-limited EODHD API call."""
    params["api_token"] = EODHD_API_KEY
    params.setdefault("fmt", "json")

    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# Example: fetch adjusted EOD prices
def get_eod_prices(ticker: str, exchange: str = "US",
                    from_date: str = "2000-01-01", to_date: str = "2026-02-28") -> list:
    return eodhd_get(
        f"eod/{ticker}.{exchange}",
        {"from": from_date, "to": to_date, "period": "d", "adjusted": 1}
    )

# Example: fetch fundamentals
def get_fundamentals(ticker: str, exchange: str = "US") -> dict:
    return eodhd_get(f"fundamentals/{ticker}.{exchange}", {"filter": "Financials"})

# Batch processing with incremental sync
def sync_symbols_batch(symbols: list, batch_size: int = 50):
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        for symbol in batch:
            try:
                data = get_eod_prices(symbol)
                # process data...
            except requests.HTTPError as e:
                print(f"Error fetching {symbol}: {e}")
                continue
        print(f"Processed batch {i // batch_size + 1} of {len(symbols) // batch_size + 1}")
```

**Important Notes:**
- Always request `adjusted=1` to get `adjusted_close` column — raw close contains unadjusted prices
- For historical survivorship-bias-free data, use the `exchange-symbol-list` endpoint with `delisted=1`
- Store raw JSON responses locally before processing — re-fetching is rate-limited and counted toward daily quota
- EODHD format for symbols: `AAPL.US`, `GLD.US`, `BTC-USD.CC` (crypto uses `.CC` exchange)

---

## Norgate Data

**Type:** Local Python API (installed package, no HTTP calls)
**Package:** `norgatedata` (install via Norgate Data Updater application)
**Data Location:** Local machine, managed by Norgate Data Updater

### 9 Available Databases

| Database Name | Description | Approx. Symbols |
|---|---|---|
| `ASX` | Australian Securities Exchange | ~3,000 |
| `Canada` | Canadian stocks (TSX, TSXV) | ~4,000 |
| `India` | Indian stocks (NSE, BSE) | ~5,000 |
| `Japan` | Japanese stocks (TSE) | ~4,000 |
| `KoreanStockExchange` | Korean stocks (KSE) | ~2,500 |
| `NYSE` | US stocks (NYSE, NASDAQ, AMEX, current) | ~10,000 |
| `US_Delisted` | US stocks that have been delisted | ~20,000 |
| `USFutures` | US futures contracts (continuous + roll-adjusted) | ~500 |
| `USMutualFunds` | US mutual funds | ~15,000 |

**Total:** 63,000+ symbols across all databases. Survivorship-bias-free when combining `NYSE` + `US_Delisted`.

### Python Usage

```python
import norgatedata as ng
import pandas as pd

# List all symbols in a database
symbols = ng.symbols("NYSE")  # returns list of symbol strings

# Get OHLCV data for a symbol
# priceadjust: 0=unadjusted, 1=dividend+split adjusted, 2=split-only adjusted
df = ng.price_timeseries(
    "AAPL",
    stock_price_adjust=ng.StockPriceAdjust.TotalReturn,  # dividend + split adjusted
    start_date="2000-01-01",
    end_date="2026-02-28",
    format=ng.Format.DataFrame
)
# Returns DataFrame with columns: Date, Open, High, Low, Close, Volume, Unadjusted Close, Dividend, Capital Gain

# Check if a symbol is in the delisted database
is_active = ng.security_name("ENRNQ") is not None  # Enron was delisted

# Get all symbols that were in S&P 500 at a specific date (point-in-time index membership)
# This is Norgate's key advantage for survivorship-bias-free index backtesting
sp500_at_date = ng.index_constituent_timeseries("$SPX", start_date="2015-01-01")

# Batch processing — 100 symbols at a time for memory efficiency
def load_norgate_batch(symbols: list, start_date: str, batch_size: int = 100) -> dict:
    results = {}
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        for symbol in batch:
            try:
                df = ng.price_timeseries(
                    symbol,
                    stock_price_adjust=ng.StockPriceAdjust.TotalReturn,
                    start_date=start_date,
                    format=ng.Format.DataFrame
                )
                results[symbol] = df
            except Exception as e:
                print(f"Norgate error for {symbol}: {e}")
        print(f"Loaded batch {i // batch_size + 1}")
    return results
```

**Important Notes:**
- Norgate requires the Norgate Data Updater application to be installed and licensed
- Data is stored locally — no API keys needed at runtime, but license must be active
- Use `US_Delisted` + `NYSE` together for survivorship-bias-free US equity backtests
- Point-in-time index membership is available via `index_constituent_timeseries` — critical for realistic S&P 500 backtests

---

## Claude API (Anthropic)

**Python SDK:** `anthropic` (install: `pip install anthropic`)
**Environment Variable:** `ANTHROPIC_API_KEY`

### Model IDs

| Model | ID | Best For |
|---|---|---|
| Claude Opus 4.6 | `claude-opus-4-6` | Complex analysis, extended thinking, strategy research |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Balanced performance and cost (current Claude Code model) |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Fast, low-cost tasks (classification, formatting) |

### Standard Usage Pattern

```python
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Standard message
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    messages=[
        {"role": "user", "content": "Analyze this earnings report..."}
    ]
)
text = response.content[0].text

# Extended Thinking (for complex multi-step analysis)
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # tokens allocated to internal reasoning
    },
    messages=[
        {"role": "user", "content": "Perform a deep fundamental analysis..."}
    ]
)
# Access thinking blocks
for block in response.content:
    if block.type == "thinking":
        reasoning = block.thinking
    elif block.type == "text":
        analysis = block.text

# Prompt Caching (for repeated system prompts — reduces cost and latency)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    system=[
        {
            "type": "text",
            "text": "You are an OBQ quantitative analyst...[long system prompt]",
            "cache_control": {"type": "ephemeral"}  # cache this prefix
        }
    ],
    messages=[
        {"role": "user", "content": f"Analyze {symbol}..."}
    ]
)
```

**Used by:** OBQ_AI Technical Agent, Risk Agent; Claude Code for development

---

## xAI Grok API

**Base URL:** `https://api.x.ai/v1`
**Python SDK:** Compatible with OpenAI Python SDK (`openai` package with custom base_url)
**Environment Variable:** `XAI_API_KEY`

### Models

| Model | ID | Best For |
|---|---|---|
| Grok 4 | `grok-4` | Deep fundamental analysis, complex financial reasoning |
| Grok 3 | `grok-3` | General analysis tasks |
| Grok 3 Mini | `grok-3-mini` | Fast, cost-efficient tasks |

### Python Usage Pattern

```python
from openai import OpenAI
import os

# Grok uses OpenAI-compatible API
grok_client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

def grok_analyze(prompt: str, system: str = None, model: str = "grok-4") -> str:
    """Call Grok API for fundamental analysis."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = grok_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=4096,
        temperature=0.1  # low temperature for financial analysis
    )
    return response.choices[0].message.content

# Example: fundamental analysis
analysis = grok_analyze(
    prompt=f"Analyze {symbol}'s financial statements: {financial_data}",
    system="You are a senior fundamental analyst. Focus on quality of earnings and balance sheet strength.",
    model="grok-4"
)
```

**Used by:** OBQ_AI Fundamental Agent (primary), Macro Agent

---

## Groq API

**Base URL:** `https://api.groq.com/openai/v1`
**Python SDK:** `groq` (install: `pip install groq`) or OpenAI-compatible
**Environment Variable:** `GROQ_API_KEY`

### Models

| Model | ID | Context | Best For |
|---|---|---|---|
| Llama 3.1 70B | `llama-3.1-70b-versatile` | 128K | Sentiment analysis, fast inference |
| Llama 3.1 8B | `llama-3.1-8b-instant` | 128K | Ultra-fast, high-volume tasks |
| Mixtral 8x7B | `mixtral-8x7b-32768` | 32K | Alternative to Llama |

### Python Usage Pattern

```python
from groq import Groq
import os

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def groq_sentiment(news_items: list[str], symbol: str) -> dict:
    """Fast sentiment analysis using Groq/Llama."""
    news_text = "\n".join(news_items[:20])  # limit to 20 items

    response = groq_client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a financial news sentiment analyzer. Return JSON with sentiment score (-1 to 1), confidence (0-1), and key themes."
            },
            {
                "role": "user",
                "content": f"Analyze sentiment for {symbol}:\n{news_text}"
            }
        ],
        max_tokens=512,
        temperature=0.0,
        response_format={"type": "json_object"}  # force JSON output
    )

    import json
    return json.loads(response.choices[0].message.content)
```

**Key Advantage:** Groq runs on custom LPU hardware — inference is 10–20x faster than standard GPU-based APIs. Ideal for high-volume sentiment processing across large universes.

**Used by:** OBQ_AI Sentiment Agent

---

## MotherDuck

**Type:** Cloud DuckDB
**Python Package:** `duckdb` (install: `pip install duckdb motherduck`)
**Environment Variable:** `MOTHERDUCK_TOKEN`

### Connection Patterns

```python
import duckdb
import os

# Standard connection
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

# Connect to a specific database
conn = duckdb.connect(f"md:PROD_EODHD?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")

# Connection with error handling for token expiry
def get_motherduck_connection(database: str = None) -> duckdb.DuckDBPyConnection:
    """Get MotherDuck connection with graceful error handling."""
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise ValueError("MOTHERDUCK_TOKEN environment variable not set")

    db_str = f"md:{database}" if database else "md:"
    conn_str = f"{db_str}?motherduck_token={token}"

    try:
        conn = duckdb.connect(conn_str)
        # Verify connection with a trivial query
        conn.execute("SELECT 1").fetchone()
        return conn
    except Exception as e:
        if "catalog" in str(e).lower() or "token" in str(e).lower():
            raise RuntimeError(
                "MotherDuck connection failed — check MOTHERDUCK_TOKEN is current"
            ) from e
        raise

# Cross-database queries (use fully qualified table names)
conn = duckdb.connect(f"md:?motherduck_token={os.getenv('MOTHERDUCK_TOKEN')}")
df = conn.execute("""
    SELECT p.date, p.symbol, p.adjusted_close, s.composite_score
    FROM PROD_EODHD.main.PROD_EOD_survivorship p
    JOIN PROD_EODHD.main.PROD_OBQ_Scores s
      ON p.symbol = s.symbol
    WHERE p.date = '2026-02-27'
    ORDER BY s.composite_score DESC
    LIMIT 100
""").df()

# List all databases
databases = conn.execute("SHOW DATABASES").df()
print(databases)

# List tables in a database
tables = conn.execute("SHOW TABLES FROM PROD_EODHD.main").df()
print(tables)
```

**Safety Rules (from Article II):**
- Never write to `PROD_*` tables without explicit Article I.6 override
- Always use `DEV_EODHD_DATA` for development and testing
- Include `IF NOT EXISTS` in CREATE TABLE statements
- Use `INSERT OR REPLACE` or `INSERT OR IGNORE` for upsert operations — never blind inserts that may duplicate rows

**Token Management:**
- Token expires periodically — check MotherDuck dashboard for expiry date
- Store token in `.env` file (verify `.env` is in `.gitignore`)
- For production pipelines (OBQ_Database_Prod), set up automatic token refresh
