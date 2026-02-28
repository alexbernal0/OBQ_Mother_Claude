# OBQ Constitution v2.0 — Claude Code Edition

## Preamble

This document defines the canonical rules for all OBQ AI-assisted development. Rules here override all other instructions except explicit SYSTEM OVERRIDE requests from Alex Bernal. Every Claude agent, session, and automated process operating within the OBQ ecosystem is bound by this constitution. When in doubt, stop and ask.

---

## ARTICLE I: DATA INTEGRITY LAWS

These rules are non-negotiable. Violations introduce errors that compound silently and corrupt all downstream analysis.

**I.1** Always use `adjusted_close` for historical price analysis. Raw close prices contain splits and dividends that create artificial discontinuities and destroy return calculations.

**I.2** Always use `filing_date` for point-in-time fundamental data joins. Never use `quarter_date` or `report_date` as the join key. Financial statements are not available to investors until they are filed — using the quarter end date introduces look-ahead bias of up to 90 days.

**I.3** Never introduce look-ahead bias. All signals, indicators, and model inputs must use only data that would have been available at signal generation time. This includes: prices (use prior close, not current day's close for same-day signals), fundamental data (use filing_date), index membership (use historical constituents, not current), and analyst estimates (use as-of-date snapshots).

**I.4** Never introduce survivorship bias. Historical universes must include delisted symbols. Use `PROD_EOD_survivorship` (not a filtered current-constituents list) for strategy backtesting. When constructing universes, verify that your data source includes stocks that were delisted during the study period.

**I.5** Validate all data before writing to MotherDuck production tables. Run the following checks: row count vs. expected, date range completeness, no NaN in key columns (date, symbol, adjusted_close), no duplicate (date, symbol) pairs, price sanity (adjusted_close > 0 for equities).

**I.6** MotherDuck `PROD_*` tables require explicit override before any write operation. All development and testing uses `DEV_*` tables. Promotion to PROD is a deliberate, confirmed action — not a default.

---

## ARTICLE II: PRODUCTION PROTECTION LAWS

These rules protect the integrity of the live system and client-facing infrastructure.

**II.1** Never drop or truncate production tables without explicit written confirmation from Alex Bernal in the current session. If a task seems to require dropping a PROD table, stop, explain the situation, and request confirmation. The confirmation must name the specific table.

**II.2** Never force-push to the `main` or `master` branch of any OBQ repository. If a fast-forward push is not possible, create a pull request or ask Alex to resolve the conflict. The main branch represents production-deployed code.

**II.3** Never commit API keys, tokens, passwords, or secrets to any git repository. All credentials are stored in environment variables (`.env` files, OS environment, or secret managers). If a `.env` file is present, verify it is listed in `.gitignore` before staging any files.

**II.4** Write to `DEV_*` tables first. Verify correctness (row counts, data integrity, spot-check values). Only after verification, promote to `PROD_*` tables. Never skip the DEV stage to save time.

---

## ARTICLE III: CODE QUALITY LAWS

These rules ensure all OBQ strategy and pipeline code meets production standards.

**III.1** All strategies using percent-of-equity sizing must use the `from_order_func` pattern with Numba. Never use `size_type="percent"` with `cash_sharing=True` in VectorBT 0.28.x — this is a confirmed bug that raises `ValueError: SizeType.Percent does not support position reversal`. See `knowledge/vbt_code_patterns.md` for the canonical implementation.

**III.2** All strategies must include commission modeling. Zero-commission backtests are not valid for publication or client reporting. Default: 0.0002 (2 bps) for liquid instruments. Adjust upward for less liquid assets.

**III.3** Results must be logged to `knowledge/backtest_results_log.md` after every completed backtest run. Log format: strategy name, date run, parameter set, key metrics (CAGR, Sharpe, MaxDD, Calmar, total trades), and notes on any anomalies.

**III.4** No silent failures. All exceptions must be caught and handled explicitly. Use `try/except` blocks with specific exception types. Log errors with context (which symbol, which date, which operation). Never use bare `except: pass`.

---

## ARTICLE IV: OBQ CANONICAL SYSTEMS

The OBQ platform consists of eight interconnected repositories. Each has a defined purpose and must not be used for tasks outside its scope.

| Repository | Purpose |
|---|---|
| **OBQ_TradingSystems_Vbt** | VBT strategy framework. Hosts all backtested trading strategies plus the `Performance_Reporting` tearsheet module (19 Plotly charts, 22 metrics). Primary research and strategy validation environment. |
| **OBQ_AI** | 5-agent AI hedge fund system. Built on LangGraph with Claude (Anthropic), Grok (xAI), and Groq (Llama). Agents: Fundamental, Technical, Sentiment, Risk, Macro. PyWebView desktop UI. Local DuckDB (204M+ rows). |
| **OBQ_GoldenOpp** | Gold mining stock portfolio system. 56 mining stocks + 4 ETFs (GDX, GLD, GDXJ, SLV). 53 years of history in GoldenOpp MotherDuck database. |
| **OBQ_Database_Prod** | Production data warehouse and ETL pipelines. 225M+ records from EODHD. Feeds MotherDuck PROD_EODHD database. Handles daily incremental sync, split/dividend adjustments, and fundamental data loading. |
| **QGSI** | Signal research system. ThreeGaugeSignal and related indicators. 1-minute bars, 400 stocks. High-frequency signal generation and evaluation. |
| **JCN_Vercel_Dashboard** | Live client-facing dashboard at jcn-tremor.vercel.app. FastAPI backend + Next.js/Tremor frontend. Displays OBQ factor scores, portfolio positions, and performance metrics. |
| **OBQ_Fundamental_Pro** | Factor scoring pipeline. Computes five OBQ scores (value, growth, financial_strength, quality, momentum) from financial statements. Writes to `PROD_OBQ_Scores` and `PROD_OBQ_Momentum_Scores` in MotherDuck. |
| **QuantMuse** | Reference framework (fork). Used as a template and reference for strategy architecture patterns. |
| **PapersWBacktest** | Paper-to-backtest research environment (local, not on GitHub). Replicates published academic strategies using VBT. Uses PWBBacktest_Data parquet files. See separate MEMORY.md for full details. |

---

## ARTICLE V: OVERRIDE PROTOCOL

When a requested action would violate an article of this constitution, the following protocol applies:

**Step 1: STOP.** Do not proceed with the action.

**Step 2: WARN.** State clearly which article is being violated and why. Be specific — cite the article number and explain the risk.

**Step 3: REQUEST OVERRIDE.** Ask Alex Bernal explicitly: "Do you want to override Article X.Y for this action? Please confirm with: OVERRIDE Article X.Y — [brief reason]."

**Step 4: LOG.** If the override is granted, log it immediately to `governance/overrides.log` using the format below before proceeding.

**Override Log Format:**
```
[YYYY-MM-DD HH:MM] OVERRIDE: Article X.Y | Justification: [reason] | Approved: Alex
```

**Example:**
```
[2026-02-28 14:30] OVERRIDE: Article II.1 | Justification: Rebuilding PROD_EOD_survivorship from scratch after schema migration | Approved: Alex
```

Overrides are never automatic. If Alex is not present in the session, do not proceed with constitution-violating actions even if a previous session granted a similar override.

---

*constitution.md | OBQ_Mother_Claude | Version: 2.0 | Amended: 2026-02-28*
