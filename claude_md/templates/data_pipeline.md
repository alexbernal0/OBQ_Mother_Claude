# CLAUDE.md — Data Pipeline Project

<!-- This is a template for data pipeline and ETL projects in the OBQ_Database_Prod style.
     Copy this file to your project root as CLAUDE.md and fill in the specifics. -->

## Pipeline Purpose

[Describe what this pipeline does. Include: data source(s), transformation logic, destination tables, schedule/frequency, approximate row counts, and what downstream systems depend on this data.]

Example: Daily incremental sync of EODHD end-of-day prices for all US equities into MotherDuck PROD_EODHD. Downloads new records since last sync date, applies split/dividend adjustments, validates quality, stages in DEV, then promotes to PROD. Feeds OBQ_AI, OBQ_TradingSystems_Vbt, and JCN_Vercel_Dashboard.

---

## Project Structure

```
[project_root]/
├── etl/
│   ├── daily_sync.py          # Main incremental sync script
│   ├── bulk_loader.py         # Full historical load (run once)
│   ├── adjustment_processor.py # Split/dividend adjustment pipeline
│   └── fundamental_loader.py  # Financial statement ingestion
├── validation/
│   └── data_quality.py        # Pre-production validation checks
├── scripts/
│   ├── promote_dev_to_prod.py  # Controlled DEV → PROD promotion
│   └── backfill.py            # Backfill missing date ranges
├── logs/                       # Pipeline run logs (auto-created)
├── .env                        # Environment variables (NEVER commit)
├── .env.example                # Template with variable names (safe to commit)
└── requirements.txt
```

---

## MotherDuck Connection Pattern

**Always use environment variables — never hardcode tokens.**

```python
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()  # loads from .env file

def get_motherduck_connection(database: str = None) -> duckdb.DuckDBPyConnection:
    """
    Get authenticated MotherDuck connection.
    Raises RuntimeError with clear message if token is missing or expired.
    """
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise RuntimeError(
            "MOTHERDUCK_TOKEN not set. Add to .env file or system environment."
        )

    db_path = f"md:{database}" if database else "md:"
    conn_str = f"{db_path}?motherduck_token={token}"

    try:
        conn = duckdb.connect(conn_str)
        conn.execute("SELECT 1").fetchone()  # verify connection
        return conn
    except Exception as e:
        if "catalog" in str(e).lower() or "token" in str(e).lower() or "auth" in str(e).lower():
            raise RuntimeError(
                f"MotherDuck authentication failed. Refresh MOTHERDUCK_TOKEN.\nOriginal error: {e}"
            ) from e
        raise

# Usage
conn = get_motherduck_connection()  # connects to MotherDuck root
conn = get_motherduck_connection("PROD_EODHD")  # connects to specific database
```

---

## Production Write Safety Rules

**These rules implement OBQ Constitution Articles I.5, I.6, II.1, and II.4.**

### Rule 1: Always write to DEV first

```python
DEV_TABLE = "DEV_EODHD_DATA.main.DEV_prices_staging"
PROD_TABLE = "PROD_EODHD.main.PROD_EOD_survivorship"

# Step 1: Write to DEV
conn.execute(f"""
    INSERT INTO {DEV_TABLE}
    SELECT * FROM new_records_df
""")

# Step 2: Validate DEV (see validation section below)
validate_staging(conn, DEV_TABLE, expected_count=len(new_records_df))

# Step 3: Only promote after validation passes
# See: scripts/promote_dev_to_prod.py
```

### Rule 2: Never drop or truncate PROD tables without explicit confirmation

```python
def safe_truncate_prod(conn, table_name: str, confirmed: bool = False):
    """
    Truncate a production table. Requires explicit confirmation parameter.
    In interactive mode, also prompts for typed confirmation.
    """
    if not confirmed:
        raise RuntimeError(
            f"BLOCKED: Attempt to truncate {table_name} without confirmation.\n"
            f"This operation requires OBQ Constitution Article II.1 override.\n"
            f"Pass confirmed=True only after explicit approval from Alex Bernal."
        )

    if "PROD_" in table_name and confirmed:
        # Double-check — log the override
        print(f"[WARNING] Truncating PROD table: {table_name}")
        print(f"[WARNING] This action is logged as an Article II.1 override.")
        conn.execute(f"TRUNCATE TABLE {table_name}")
```

### Rule 3: Upsert pattern for incremental loads

```python
def upsert_to_staging(conn, table: str, df: pd.DataFrame, key_cols: list):
    """
    Insert new records, update existing ones. Never blind-append.
    Uses DuckDB INSERT OR REPLACE pattern.
    """
    # Register DataFrame as a view
    conn.register("new_data", df)

    # Build key condition
    key_condition = " AND ".join([f"t.{col} = n.{col}" for col in key_cols])

    conn.execute(f"""
        INSERT INTO {table}
        SELECT n.*
        FROM new_data n
        WHERE NOT EXISTS (
            SELECT 1 FROM {table} t
            WHERE {key_condition}
        )
    """)

    # Return insert count
    return conn.execute(f"SELECT changes()").fetchone()[0]
```

---

## Incremental Sync Patterns

### Get last sync date

```python
def get_last_sync_date(conn, table: str, date_col: str = "date") -> str:
    """Get the most recent date in the table to determine sync start point."""
    result = conn.execute(f"SELECT MAX({date_col}) FROM {table}").fetchone()
    if result[0] is None:
        return "1990-01-01"  # full history load
    # Add one day to avoid re-downloading last date
    last = pd.Timestamp(result[0]) + pd.Timedelta(days=1)
    return last.strftime("%Y-%m-%d")

# Usage
last_date = get_last_sync_date(conn, "PROD_EODHD.main.PROD_EOD_survivorship")
print(f"Syncing from: {last_date}")
```

### Incremental batch sync

```python
import time
from datetime import date

def incremental_sync(symbols: list, from_date: str, batch_size: int = 50):
    """
    Sync new data for all symbols since from_date.
    Processes in batches to respect rate limits.
    """
    conn = get_motherduck_connection()
    total_rows = 0
    errors = []

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size

        print(f"Processing batch {batch_num}/{total_batches}: {batch[:3]}...")

        for symbol in batch:
            try:
                # Fetch from source (e.g., EODHD)
                raw_data = fetch_eod_data(symbol, from_date=from_date)
                if not raw_data:
                    continue

                df = pd.DataFrame(raw_data)
                df["symbol"] = symbol

                # Write to DEV staging
                conn.register("batch_data", df)
                conn.execute("""
                    INSERT INTO DEV_EODHD_DATA.main.DEV_prices_staging
                    SELECT * FROM batch_data
                """)
                total_rows += len(df)

            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})
                print(f"  ERROR {symbol}: {e}")
                continue

        # Rate limit pause between batches
        time.sleep(0.1)  # 100ms between batches

    print(f"\nSync complete: {total_rows} rows loaded, {len(errors)} errors")
    if errors:
        print("Errors:", errors)

    return total_rows, errors
```

---

## Data Validation Requirement

**Run these checks before any PROD write. Article I.5 mandates validation.**

```python
def validate_staging(conn, table: str, expected_count: int,
                     date_col: str = "date", price_col: str = "adjusted_close",
                     symbol_col: str = "symbol") -> bool:
    """
    Standard OBQ data quality checks.
    Returns True if all checks pass, raises ValueError on failure.
    """
    errors = []

    # Check 1: Row count
    actual_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if actual_count < expected_count * 0.95:  # allow 5% tolerance
        errors.append(f"Row count too low: {actual_count} vs expected {expected_count}")

    # Check 2: No NaN in key columns
    null_counts = conn.execute(f"""
        SELECT
            COUNT(*) FILTER (WHERE {date_col} IS NULL) AS null_dates,
            COUNT(*) FILTER (WHERE {symbol_col} IS NULL) AS null_symbols,
            COUNT(*) FILTER (WHERE {price_col} IS NULL) AS null_prices
        FROM {table}
    """).fetchone()
    if any(null_counts):
        errors.append(f"Null values found: dates={null_counts[0]}, symbols={null_counts[1]}, prices={null_counts[2]}")

    # Check 3: No duplicate (date, symbol) pairs
    dupe_count = conn.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT {date_col}, {symbol_col}, COUNT(*) as cnt
            FROM {table}
            GROUP BY {date_col}, {symbol_col}
            HAVING cnt > 1
        )
    """).fetchone()[0]
    if dupe_count > 0:
        errors.append(f"Duplicate (date, symbol) pairs: {dupe_count}")

    # Check 4: Price sanity (positive prices for equities)
    negative_price_count = conn.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE {price_col} <= 0
    """).fetchone()[0]
    if negative_price_count > 0:
        errors.append(f"Non-positive prices found: {negative_price_count} rows")

    # Check 5: Date range completeness (no large gaps)
    date_gaps = conn.execute(f"""
        WITH dates AS (
            SELECT DISTINCT {date_col}::DATE AS d
            FROM {table}
            ORDER BY d
        ),
        gaps AS (
            SELECT d, LAG(d) OVER (ORDER BY d) AS prev_d,
                   d - LAG(d) OVER (ORDER BY d) AS gap_days
            FROM dates
        )
        SELECT COUNT(*) FROM gaps WHERE gap_days > 7  -- flag weekend-crossing gaps > 7 days
    """).fetchone()[0]
    if date_gaps > 0:
        errors.append(f"Potential date gaps found: {date_gaps} gaps > 7 days")

    if errors:
        raise ValueError(f"Data validation FAILED for {table}:\n" + "\n".join(f"  - {e}" for e in errors))

    print(f"Validation PASSED for {table} ({actual_count:,} rows)")
    return True
```

---

## Rate Limiting Reminder

**Always respect API rate limits. EODHD limits: 1,000 calls/min, 100K/day.**

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=900, period=60)   # stay under 1000/min limit with buffer
def rate_limited_api_call(url: str, params: dict) -> dict:
    """Wrapped API call with automatic rate limiting."""
    import requests
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()
```

---

## Environment Variables Required

Create a `.env` file in the project root (NEVER commit this file — verify `.gitignore`):

```bash
# .env — DO NOT COMMIT
MOTHERDUCK_TOKEN=your_motherduck_token_here
EODHD_API_KEY=your_eodhd_api_key_here
NORGATE_ENABLED=true    # set to false if Norgate is not installed
```

Create a `.env.example` file (safe to commit):

```bash
# .env.example — copy to .env and fill in values
MOTHERDUCK_TOKEN=
EODHD_API_KEY=
NORGATE_ENABLED=true
```

Verify `.gitignore` contains:
```
.env
*.env
logs/
__pycache__/
*.pyc
```

---

## Schema Validation Requirement

Before creating a new PROD table, define and validate its schema explicitly:

```python
SCHEMA = {
    "PROD_EOD_survivorship": {
        "date":           "DATE NOT NULL",
        "symbol":         "VARCHAR NOT NULL",
        "open":           "DOUBLE",
        "high":           "DOUBLE",
        "low":            "DOUBLE",
        "close":          "DOUBLE",
        "adjusted_close": "DOUBLE NOT NULL",
        "volume":         "BIGINT",
        "PRIMARY KEY":    "(date, symbol)",
    }
}

def create_table_from_schema(conn, table_name: str, schema: dict):
    """Create table with explicit schema. Fails fast on type mismatches."""
    columns = [f"{col} {dtype}" for col, dtype in schema.items()
               if col != "PRIMARY KEY"]
    pk = schema.get("PRIMARY KEY", "")
    pk_clause = f", PRIMARY KEY {pk}" if pk else ""

    ddl = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(columns)}{pk_clause}
        )
    """
    conn.execute(ddl)
    print(f"Table created/verified: {table_name}")
```
