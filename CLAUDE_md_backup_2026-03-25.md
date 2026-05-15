# OBQ Intelligence
> Direct. Technical. Tables > prose. Flag data risks immediately.

## STATUS (REQUIRED)
Start every response: `> 🟢 RTK+COMPACT ACTIVE`

## Token Laws
- Notebook/script stdout → save to .txt → read last 60 lines only. Never dump full output.
- Sweep/optimization results → CSV first → top-5 rows per direction into context only.
- Sub-agents: `model: haiku` for research/explore. Sonnet/Opus for code only.
- After heavy output → suggest `/compact`.
- RTK: prefix ALL bash commands with `rtk` (passthrough safe). e.g. `rtk git status`, `rtk ls`, `rtk grep`, `rtk git diff`.

## Rules
- Fix only what's broken. Add only what was asked.
- No empty except. No hardcoded keys. Keys in `.env` only.
- After corrections → `tasks/lessons.md` (Date / Symptom / Root Cause / Fix / Prevention).
- Large parquet (>100M rows): `.copy()` after bool filter. No `dt.time`/`dt.date` — use int arithmetic. Verify pre-sorted before any sort.
- `importlib.reload`: reload submodule AND parent package in order, then re-import.

## VBT 0.28.x
- `size_type="percent"` + `cash_sharing=True` → CRASH. Use `from_order_func` + Numba.
- `size_type="percent"` = % of cash not portfolio. Use `c.value_now` in order func.
- Negative prices → crash. Filter `close > 0` before clipping.
- `pf.trades.count()` on multi-col → Series. Use `.sum()` for total. `pf.iloc[idx]` not `pf.iloc[:,idx]`.

## Data Laws
- `adjusted_close` only — never raw close.
- `filing_date` only — never `quarter_date` (look-ahead bias).
- Column: `Symbol` (capital S). No survivorship bias.
- Score against investable universe only — never full ~10K EOD universe.
- Fundamental staleness cap: 548 days max. No forward-fill across staleness gaps.
- Validate before any MotherDuck write.

## DuckDB / MotherDuck
- Single-writer — concurrent writes fail silently.
- Symbol: MotherDuck = `TICKER.US` | display = `TICKER` — always normalize.
- Schema: `PROD_EODHD.main.PROD_*` (prod) | `GoldenOpp.*` | `qgsi.*` | `DEV_EODHD_DATA.*` (staging).
- `MOTHERDUCK_TOKEN` from env only.

## APIs & Keys
- EODHD: 1000/min 100K/day → `RateLimiter(delay=0.06)`. Key in `.env`.
- All keys in `.env`: `ANTHROPIC_API_KEY` `XAI_API_KEY` `GROQ_API_KEY` `OPENAI_API_KEY` `MOTHERDUCK_TOKEN`.

## Notebook
- ONE cell only. Never split without being asked.
- Smoke test (execute) after every change — never report success without proof.
- After modifying any `.ipynb` → output clickable markdown link `[Name.ipynb](path)`.
