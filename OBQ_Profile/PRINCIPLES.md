# PRINCIPLES — The Decision Playbook

## THE ALGORITHM

Apply this sequence to every task, in order. Do not skip steps.

### Step 1: Make Requirements Less Dumb
Before building anything, interrogate the requirement itself. The most dangerous requests are the ones that sound reasonable but are solving the wrong problem. Ask: what is the actual goal? What constraint is this requirement responding to? Could the underlying problem be solved differently?

A bad requirement, implemented perfectly, is a perfect waste.

### Step 2: Delete the Part or Process
Can this be removed entirely? Before writing code to handle an edge case, ask whether the edge case should exist. Before adding a parameter, ask if the system is better without it. Before building a pipeline stage, ask if the stage is necessary.

The most elegant code is the code that was never written.

### Step 3: Simplify and Optimize
Now that the requirement is correct and minimal, find the simplest implementation. Not the cleverest, not the most flexible — the simplest. Then optimize the parts that will actually be performance bottlenecks. Do not optimize what will never be called more than once.

### Step 4: Accelerate Cycle Time
Make the feedback loop faster. Can we test with a 2-symbol subset before running 400? Can we write to a staging table before PROD_*? Can we run the backtest on one year before the full history? Shorter cycles mean faster error detection and lower cost of mistakes.

### Step 5: Automate (LAST)
Only after steps 1-4 are complete does automation make sense. Automating a broken process makes it break faster and more consistently. Automation is the reward for having a correct, minimal, simple, fast process — not a substitute for one.

---

## When Principles Collide

Priority order, highest to lowest:

```
Correctness > Reproducibility > Speed > Elegance > Shipping
```

- **Correctness vs. Speed:** Slow and correct always beats fast and wrong. A backtest that runs in 10 minutes with no look-ahead bias is infinitely better than one that runs in 30 seconds with survivorship bias baked in.
- **Reproducibility vs. Elegance:** A verbose but deterministic pipeline beats a clever one that depends on execution order. Lock the random seeds. Pin the library versions. Name the snapshots.
- **Speed vs. Shipping:** A partial solution that is known to be incomplete is acceptable. An incorrect solution presented as complete is not. Flag what is unfinished before shipping.
- **Elegance vs. Shipping:** Ship the working ugly version. Refactor in the next session with tests as guardrails. Do not hold up production work for code aesthetics.

---

## Domain Laws

### VectorBT 0.28.x — Three Critical Bugs

**Bug 1: `size_type="percent"` with `cash_sharing=True` crashes**
```
ValueError: SizeType.Percent does not support position reversal
```
This error fires even when there are zero actual reversals. The bug is in VBT internals. It is confirmed and unfixable without patching the library.
FIX: Use `from_order_func` with Numba (see pattern below). Never use `size_type="percent"` with `cash_sharing=True`.

**Bug 2: `size_type="percent"` uses percent of CASH, not portfolio value**
Even without the crash bug, percent sizing is calculated on available cash, not total portfolio value (cash + unrealized P&L). This means positions shrink as capital is deployed — not what any portfolio manager intends.
FIX: Use `c.value_now` inside `from_order_func`. This equals broker equity (cash + unrealized P&L), which is the correct denominator.

**Bug 3: Negative prices crash `from_order_func`**
```
order.price must be finite and greater than 0
```
Triggered by negative bond yields stored as prices, and CL1 futures in April 2020 (-$37).
FIX:
```python
valid_price = close.notna() & (close > 0)    # compute BEFORE clipping
close = close.clip(lower=0.0001)              # clip AFTER
entries = entries & valid_price               # block entries on invalid prices
```

---

### VBT True Percent-of-Equity Pattern (L+S, cash_sharing)

This is the ONLY correct way to implement percent-of-portfolio sizing with `cash_sharing=True` in VBT 0.28.x:

```python
import numba as nb
from vectorbt.portfolio.nb import order_nb as _vbt_order_nb, close_position_nb as _vbt_close_nb

@nb.njit(cache=True)   # MUST be at module level — not inside a function or class
def _order_func_nb(c, le, lx, se, sx, spct, fees):
    i, col = c.i, c.col
    price, pos = c.val_price_now, c.position_now
    if price <= 0. or price != price:          # guard: invalid price
        return _vbt_order_nb(size=np.nan)
    if pos > 0. and lx[i, col]:               # close long
        return _vbt_close_nb(price=price, fees=fees)
    if pos < 0. and sx[i, col]:               # close short
        return _vbt_close_nb(price=price, fees=fees)
    if pos == 0.:
        s = spct[i, col]
        if s <= 0. or s != s:                  # guard: invalid size
            return _vbt_order_nb(size=np.nan)
        dollar = s * c.value_now               # KEY: percent × total portfolio equity
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

Critical parameters:
- `size_type=1` = SizeType.Value (integer, required in Numba context)
- `direction=0` = LongOnly, `direction=1` = ShortOnly
- `lock_cash=True` on BOTH sides — prevents short cash recycling spiral
- `update_value=True` — ensures `c.value_now` updates per order within a bar
- `c.value_now` — cash + unrealized P&L = true broker equity

---

### DuckDB / MotherDuck

**Connection and Authentication**
```python
import duckdb
conn = duckdb.connect("md:?token={MOTHERDUCK_TOKEN}")
# Token from environment only: os.getenv("MOTHERDUCK_TOKEN")
```
- Token expiry: catch `duckdb.duckdb.IOException` with "token" in message → reconnect
- Single-writer: never run two write sessions to the same table in parallel

**Schema Conventions**
- Production: `PROD_EODHD.main.PROD_{TABLE_NAME}` (e.g., `PROD_EODHD.main.PROD_EOD_US`)
- GoldenOpp: `GoldenOpp.main.{TABLE_NAME}`
- QGSI: `qgsi.main.{TABLE_NAME}`
- Symbol format: `TICKER.US` for US equities (e.g., `AAPL.US`)
- Always include `created_at TIMESTAMP DEFAULT NOW()` on write tables

**Zone-Map Optimization**
```sql
-- Sort by date+symbol for range scan performance
CREATE TABLE prod_table AS
SELECT * FROM staging ORDER BY date, symbol;
```

**Safe Write Pattern**
```python
# Write to staging first, then swap — never write directly to PROD_*
conn.execute("CREATE TABLE staging AS SELECT * FROM df")
conn.execute("DROP TABLE IF EXISTS PROD_TABLE")
conn.execute("ALTER TABLE staging RENAME TO PROD_TABLE")
```

---

### EODHD API

```python
from ratelimiter import RateLimiter

API_KEY = os.getenv("EODHD_API_KEY")  # NEVER hardcode
BASE_URL = "https://eodhd.com/api"

@RateLimiter(max_calls=1000, period=60)  # or delay=0.06 seconds between calls
def fetch_eod(ticker, from_date, to_date):
    ...
```

- Rate limit: 1000 requests/minute — enforce without exception
- Always use `adjusted_close`, never `close` for historical backtesting
- Ticker format: `AAPL.US`, `GC.COMM`, `EURUSD.FOREX`
- Fundamentals: use `filing_date` for point-in-time joins, never `report_date` or `quarter_date`
- Handle HTTP 429: exponential backoff minimum 5 seconds

---

### Norgate Data

- 9 databases, 63K+ symbols, survivorship-bias-free by default
- Access via `norgatedata` Python package (must be installed via Norgate Data Updater)
- Batch processing: maximum 100 symbols per batch to prevent memory pressure
- Adjusted prices: `PriceAdjust.TotalReturn` for equities, `PriceAdjust.None_` for futures
- Symbol check: `norgatedata.status(symbol)` before bulk download
- Do not cache raw Norgate data to MotherDuck without validating schema first

---

### Data Integrity Laws

These are not guidelines. They are laws.

1. **Use `adjusted_close` for all historical price analysis.** Raw close contains dividend gaps and split discontinuities that corrupt any price-based strategy.
2. **Use `filing_date` for fundamental joins, not `quarter_date`.** `quarter_date` introduces look-ahead bias — the data was not available to investors on that date.
3. **`Symbol` column is capitalized with capital S.** Consistent with EODHD schema. Joins fail silently on case mismatch in DuckDB.
4. **Validate before every MotherDuck write:**
   ```python
   assert df['date'].notna().all(), "NaN dates detected — abort write"
   assert df['symbol'].str.match(r'^[A-Z0-9]+\.[A-Z]+$').all(), "Invalid symbol format"
   assert (df['adjusted_close'] > 0).all(), "Non-positive prices detected"
   ```
5. **Never write NaN values to production tables.** Handle them explicitly upstream.
6. **Always check row count after write:**
   ```python
   written = conn.execute("SELECT COUNT(*) FROM prod_table").fetchone()[0]
   assert written == len(df), f"Write mismatch: expected {len(df)}, got {written}"
   ```

---

### LangGraph / AI Agent Architecture

**OBQ_AI Agent Structure (5 agents)**
```
Supervisor
├── Fundamental Agent  (financials, valuation, EODHD fundamentals)
├── Technical Agent    (price/volume signals, momentum, VBT signals)
├── Sentiment Agent    (news, social, earnings call tone)
├── Risk Agent         (portfolio risk, correlation, drawdown, VaR)
└── Macro Agent        (rates, economic indicators, commodities, FX)
```

- State: `TypedDict` with full audit trail — every agent appends to `reasoning_chain`
- Extended Thinking: use for complex multi-factor synthesis (min 8000 thinking tokens)
- LLM routing: Claude for reasoning, Grok for alternative view, Groq for fast classification
- Error handling: each agent catches its own exceptions and returns a degraded result, never hard-fails the graph
- Timeouts: 30s for fast agents, 120s for Extended Thinking calls

**API Key Environment Variables**
```python
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY")
XAI_API_KEY        = os.getenv("XAI_API_KEY")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
```

---

### Python Performance

- Use `float32` where precision allows (price ratios, normalized signals) — halves memory
- Use `float64` for cumulative calculations, NAV tracking, and anything compounded
- Numba JIT (`@nb.njit(cache=True)`) for inner loops executed per bar/per symbol
- Vectorized pandas over `iterrows` — never use `iterrows` on DataFrames > 1000 rows
- DuckDB SQL for aggregations on large datasets — faster than pandas groupby at scale
- `pd.merge_asof` for time-series joins (sorted, nearest-match) — faster than merge + ffill
- Avoid `df.apply(lambda ...)` on large DataFrames — use vectorized numpy operations

---

## Anti-Pattern Catalog

These patterns are prohibited. Each one has destroyed a session or corrupted a result.

| Anti-Pattern | Why It's Prohibited |
|---|---|
| Abstract 3 similar lines into a class immediately | Abstraction before the pattern stabilizes creates wrong abstractions. Wait for 3+ concrete uses first. |
| "Handle that edge case later" | Edge cases in financial data are not edge cases — they are production incidents waiting. Handle them now. |
| Skip data validation before computation | Silent NaN propagation, shape mismatches, and dtype coercions cause results that look correct but are wrong. |
| Build without a plan for complex tasks | Unplanned builds optimize for starting fast, not finishing correctly. Plan first. |
| `# type: ignore` without an explanatory comment | Suppressed type errors are undocumented technical debt. Document why it is safe to suppress. |
| Hardcode API keys anywhere in code | Keys in code get committed to git. Keys in git get leaked. Use `.env` + `python-dotenv`. |
| Empty `except` blocks | `except: pass` silently swallows errors. Always log at minimum, preferably re-raise with context. |
| Join on `quarter_date` for fundamentals | Look-ahead bias. The fundamental data was not available to investors on `quarter_date`. Use `filing_date`. |
| Use raw `close` for historical backtesting | Dividend gaps and split discontinuities make price-based strategies meaningless. Use `adjusted_close`. |
| `size_type="percent"` with `cash_sharing=True` | Confirmed VBT 0.28.x bug — crashes even with zero reversals. Use `from_order_func` pattern. |
| One mega-session for a complex project | Context quality degrades over long sessions. Spawn subagents for research; checkpoint regularly. |
| Mark task complete without testing | "I wrote it" is not "it works." Test before declaring done. |
| Write directly to `PROD_*` tables | Always write to staging first, validate, then swap. Production tables are not sandboxes. |
| Run 400-symbol backtest before testing on 5 | Find bugs on the small test first. Debugging a 400-symbol backtest takes 10x longer. |
| Commit `.env` files to git | API keys in git repos are a security incident. Add `.env` to `.gitignore` before the first commit. |

---

PRINCIPLES.md | OBQ_Mother_Claude | Load: Always-on
