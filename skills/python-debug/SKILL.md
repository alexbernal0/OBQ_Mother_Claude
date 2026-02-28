---
name: python-debug
description: "Systematic debug protocol for Python errors in OBQ work — Numba JIT, VectorBT, DuckDB/MotherDuck, pandas, and async agent errors. Use when encountering any traceback or unexpected behavior."
---

# OBQ Python Debug Protocol

Follow these steps in order. Most errors in OBQ work fall into a small set of known categories. Check those first before exploring unknown territory.

---

## CORE DEBUG PROTOCOL

Always follow this sequence — do not skip to step 5 because you have a hypothesis:

```
1. Read the FULL traceback (bottom-up: bottom = proximate cause, top = call site)
2. Reproduce minimally — smallest example that still fails
3. Check shapes and dtypes BEFORE the failing line
4. Add a debug print right before the failing line
5. Test the fix in isolation before integrating back
6. After the fix: add a comment in the code explaining what was wrong and why
7. If the bug is non-obvious: add a line to tasks/lessons.md
```

---

## NUMBA / VECTORBT ERRORS

### `TypingError: Failed in nopython mode pipeline execution`

**Cause:** Type mismatch between what you passed and what Numba expected.

**Most common OBQ causes:**
- Passing a pandas DataFrame where Numba expects a numpy array
- Passing Python `bool` array where Numba expects `np.bool_`
- Passing Python `float` where Numba expects `np.float64`

**Fix:**
```python
# Before passing to from_order_func:
le_arr   = entries_long.values.astype(np.bool_)     # not bool, not object
lx_arr   = exits_long.values.astype(np.bool_)
se_arr   = entries_short.values.astype(np.bool_)
sx_arr   = exits_short.values.astype(np.bool_)
spct_arr = size_pct.values.astype(np.float64)       # not float32
fees     = np.float64(commission)                    # not Python float

# Debug dtype check:
print(le_arr.dtype, lx_arr.dtype, spct_arr.dtype, type(fees))
# Expected: bool bool float64 <class 'numpy.float64'>
```

### `cannot determine Numba type of <class 'pandas.DataFrame'>`

**Cause:** A pandas DataFrame or Series is being passed directly to a `@nb.njit` function.

**Fix:** Convert with `.values` before passing. Numba only accepts numpy arrays, Python scalars, and Numba-compatible types.

```python
# Wrong:
result = my_numba_func(df, series, python_list)

# Correct:
result = my_numba_func(df.values.astype(np.float64),
                       series.values.astype(np.bool_),
                       np.array(python_list, dtype=np.float64))
```

### `@nb.njit function cannot be defined inside another function`

**Cause:** Numba JIT functions must be at module scope. Defining them inside a class method or another function causes reflection errors and can silently corrupt the cache.

**Fix:** Move the `@nb.njit` decorated function to module level (top of file, outside all classes and functions). This is a hard requirement — there is no workaround.

```python
# Wrong:
def run_backtest():
    @nb.njit(cache=True)          # ERROR: inside a function
    def _order_func_nb(c, ...):
        ...

# Correct:
@nb.njit(cache=True)              # OK: at module level
def _order_func_nb(c, ...):
    ...

def run_backtest():
    pf = vbt.Portfolio.from_order_func(..., _order_func_nb, ...)
```

### Stale `cache=True` behavior (function changed but old behavior persists)

**Symptom:** You changed a `@nb.njit(cache=True)` function but the old behavior is still running.

**Cause:** Numba caches compiled kernels in `__pycache__`. If the cache invalidation logic misses your change, the old compiled version runs.

**Fix:** Delete the `__pycache__` folder in the directory containing the strategy file, then rerun.

```bash
# In bash (from the strategy file directory):
rm -rf __pycache__

# Or in Python:
import shutil, pathlib
for p in pathlib.Path(".").rglob("__pycache__"):
    shutil.rmtree(p)
```

### `ValueError: SizeType.Percent does not support position reversal`

**Cause:** VBT 0.28.x Bug #1. `size_type="percent"` + `cash_sharing=True` crashes even with zero actual reversals.

**Fix:** Switch to `from_order_func` pattern. See `vbt-patterns` skill for the complete implementation.

---

## MOTHERDUCK / DUCKDB ERRORS

### `MotherDuckCatalogException: Token expired` or `Authentication failed`

**Fix:** Reconnect with a fresh token. The token expires; don't cache the connection across long sessions.

```python
import duckdb, os

# Standard MotherDuck reconnect:
token = os.environ.get("MOTHERDUCK_TOKEN") or "your-token-here"
conn = duckdb.connect(f"md:?motherduck_token={token}")

# Verify connection:
conn.execute("SELECT 1").fetchone()
```

### `IO Error: Could not open file` or `Database is locked`

**Cause:** DuckDB enforces single-writer access. If another notebook/process has the `.duckdb` file open, new connections fail.

**Fix:**
1. Find and close all other connections to the database file
2. In Jupyter: restart the kernel that holds the open connection
3. Check for zombie processes: `lsof | grep ".duckdb"` (Linux/Mac) or Task Manager (Windows)

```python
# Defensive pattern: always use a context manager for file-based DuckDB
import duckdb

with duckdb.connect("my_database.duckdb") as conn:
    result = conn.execute("SELECT count(*) FROM my_table").fetchone()
# Connection is automatically released on exit
```

### `Binder Error: Referenced column ... could not be found`

**Cause:** DuckDB column names are case-sensitive. `Date` != `date` != `DATE`.

**Fix:**
```python
# Check actual column names:
conn.execute("DESCRIBE my_table").fetchdf()

# Or:
conn.execute("SELECT * FROM my_table LIMIT 1").fetchdf().columns.tolist()

# Use exact case in queries:
# Wrong:  SELECT date, symbol FROM prices
# Right:  SELECT Date, Symbol FROM prices (if that's how they were created)
```

### `Conversion Error: Could not convert float to int` (or similar type cast)

**Fix:** Add explicit CAST in SQL. DuckDB is strict about implicit type conversions.

```sql
-- Wrong:
SELECT year FROM my_table WHERE year = 2023.0

-- Right:
SELECT year FROM my_table WHERE year = CAST(2023 AS INTEGER)

-- Or in Python:
df['year'] = df['year'].astype(int)  # fix before writing to DuckDB
```

### `OutOfMemoryError` on large MotherDuck queries

**Fix:** Never SELECT * on large tables. Always push filtering to SQL before pulling to Python.

```python
# Wrong — pulls all 225M rows:
df = conn.execute("SELECT * FROM prices").fetchdf()

# Correct — filter first in SQL:
df = conn.execute("""
    SELECT Date, Symbol, close, volume
    FROM prices
    WHERE Symbol IN ('AAPL.US', 'MSFT.US', 'GLD.US')
      AND Date >= '2010-01-01'
""").fetchdf()
```

---

## PANDAS ERRORS

### `FutureWarning: DataFrame.applymap has been renamed to DataFrame.map`

**Cause:** pandas 2.2 renamed `applymap` to `map`.

**Fix:**
```python
# Old (pandas < 2.2):
df = df.applymap(lambda x: x * 2)

# New (pandas >= 2.2):
df = df.map(lambda x: x * 2)
```

### `KeyError: 'symbol'` when you meant `'Symbol'`

**Cause:** OBQ convention is `Symbol` (capital S) in all MotherDuck tables. Pandas doesn't auto-correct case.

**Fix:**
```python
# Check what you actually have:
print(df.columns.tolist())

# Defensive normalization at load time:
df.columns = [c.strip() for c in df.columns]   # strip whitespace
# Do NOT lowercase — OBQ tables use Title Case (Date, Symbol, Close)
```

### `ValueError: cannot reindex from a duplicate axis`

**Cause:** Attempting to pivot a DataFrame that has duplicate `(date, symbol)` rows. Common when joining two data sources that both have the same date range.

**Fix:**
```python
# Find the duplicates first:
dupes = df.duplicated(subset=['Date', 'Symbol'], keep=False)
print(df[dupes].head(20))

# Common resolution: take the last value per (date, symbol)
df = df.sort_values('Date').groupby(['Date', 'Symbol']).last().reset_index()

# Then pivot safely:
wide = df.pivot(index='Date', columns='Symbol', values='close')
```

### `PerformanceWarning: DataFrame is highly fragmented`

**Cause:** Building a DataFrame column by column in a loop with `df[new_col] = ...`.

**Fix:**
```python
# Wrong — fragmented:
df = pd.DataFrame()
for sym in symbols:
    df[sym] = some_series

# Correct — build list of Series, concat once:
parts = []
for sym in symbols:
    parts.append(pd.Series(data, name=sym))
df = pd.concat(parts, axis=1)
```

---

## COMMON OBQ SHAPE MISMATCHES

The most frequent class of silent error: the code runs, produces numbers, but the numbers are wrong because of a shape mismatch between systems.

### Long vs. Wide Format Mismatch

VBT requires **wide format** (date × symbol). MotherDuck returns **long format** (Date, Symbol, value per row).

```python
# MotherDuck output (long):
# Date        Symbol   close
# 2023-01-03  AAPL.US  125.07
# 2023-01-03  MSFT.US  239.82
# 2023-01-04  AAPL.US  126.36

# Convert to wide (for VBT):
wide = df.pivot(index='Date', columns='Symbol', values='close')
wide.index = pd.to_datetime(wide.index)
wide = wide.sort_index()

# After pivot: always check coverage
print(f"Shape: {wide.shape}")
print(f"NaN per symbol:\n{wide.isna().sum().sort_values(ascending=False).head(10)}")
```

### Date Index Alignment

Signals and prices must share the same index. Misaligned indices cause silent NaN injection.

```python
# Check alignment before backtest:
assert close.index.equals(entries_long.index), \
    f"Index mismatch: close has {len(close)} bars, signals have {len(entries_long)}"

# If misaligned, reindex signals to match prices:
entries_long = entries_long.reindex(close.index, fill_value=False)
```

### NaN Propagation in Numba

Inside `@nb.njit`, NaN comparisons behave differently than Python:

```python
# In Python: float('nan') == float('nan') is False
# In Numba: same — x != x is the idiomatic NaN check

# Correct NaN guard inside @nb.njit:
if price != price:   # True only if price is NaN (IEEE 754)
    return _vbt_order_nb(size=np.nan)

# Also guard for infinity:
if not np.isfinite(price):
    return _vbt_order_nb(size=np.nan)
```

---

## ASYNC / AGENT FRAMEWORK ERRORS

### `RuntimeError: This event loop is already running`

**Cause:** Jupyter notebooks run an event loop. Calling `asyncio.run()` inside a notebook creates a conflict.

**Fix:**
```python
# Wrong in Jupyter:
result = asyncio.run(my_async_function())

# Correct in Jupyter:
import nest_asyncio
nest_asyncio.apply()
result = asyncio.run(my_async_function())
# or:
result = await my_async_function()  # in a Jupyter cell, await works directly
```

### Agent task hangs indefinitely

**Common causes:**
1. Waiting for user input inside an async task (use timeout)
2. DuckDB connection lock inside a coroutine (DuckDB is synchronous — run in executor)

```python
# Running synchronous DuckDB inside async code:
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def query_motherduck(sql: str):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, conn.execute(sql).fetchdf)
    return result
```

---

## DEBUGGING REFERENCE CARD

```python
# Shape and dtype inspection (run before any failing operation):
print(f"close:          {close.shape}, dtypes: {close.dtypes.unique()}")
print(f"entries_long:   {entries_long.shape}, dtype: {entries_long.values.dtype}")
print(f"size_pct:       {size_pct.shape}, NaN: {size_pct.isna().sum().sum()}")

# Check for unexpected NaN in signals (should be 0 or low after warmup):
for name, df in [("entries_long", entries_long), ("exits_long", exits_long),
                 ("size_pct", size_pct)]:
    print(f"{name}: True={df.values.sum()}, NaN={df.isna().sum().sum()}")

# Quick value range check:
print(f"close range:    [{close.min().min():.4f}, {close.max().max():.2f}]")
print(f"size_pct range: [{size_pct.min().min():.4f}, {size_pct.max().max():.4f}]")
print(f"negative close: {(close < 0).sum().sum()} cells")
```
