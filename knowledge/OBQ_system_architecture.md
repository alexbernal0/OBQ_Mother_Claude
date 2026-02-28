# OBQ System Architecture Reference

## SECTION 1: System Overview

OBQ is a quantitative hedge fund platform with 8 interconnected systems spanning strategy research, data engineering, AI-powered portfolio management, and client reporting. The platform is built around a central data warehouse in MotherDuck (cloud DuckDB) that serves as the single source of truth for all production data. Strategy research flows from raw data through backtesting to live signals, while a 5-agent AI system continuously monitors and scores the investable universe.

The platform processes 225M+ records of historical market data, generates five proprietary factor scores for thousands of stocks, and delivers results to clients via a live Vercel dashboard. All strategy development uses VectorBT (VBT) for high-performance vectorized backtesting.

**Core Technology Stack:**
- Data storage: MotherDuck (cloud DuckDB), local DuckDB, Parquet files
- Strategy backtesting: VectorBT 0.28.4 with Numba JIT compilation
- AI/ML: LangGraph, Claude (Anthropic), Grok (xAI), Groq (Llama), scikit-learn
- Visualization: Plotly, Performance_Reporting tearsheet
- Client dashboard: FastAPI + Next.js + Tremor (Vercel)
- Data sources: EODHD, Norgate Data, Finnhub

---

## SECTION 2: Data Flow Architecture

```
UPSTREAM DATA SOURCES
├── EODHD API (primary: US equities, ETFs, fundamentals, 225M+ records)
├── Norgate Data (63K+ symbols, 9 databases, survivorship-bias-free)
└── Finnhub / Grok API (news, sentiment, real-time data)
         |
         v
OBQ_Database_Prod (ETL pipelines — daily incremental sync)
├── Split/dividend adjustment processing
├── Point-in-time fundamental data staging
├── Data validation and quality checks
└── DEV_EODHD_DATA (staging/development environment)
         |
         v
MotherDuck Cloud (DuckDB — production data warehouse)
├── PROD_EODHD database
│   ├── PROD_EOD_survivorship     (daily OHLC + adjusted_close, all US equities ever traded)
│   ├── PROD_OBQ_Scores           (value, growth, fs, quality scores — from OBQ_Fundamental_Pro)
│   ├── PROD_OBQ_Momentum_Scores  (momentum, systemscore — updated weekly)
│   └── PROD_EOD_ETFs             (SPY, GLD, QQQ, IWM and other key ETFs)
├── GoldenOpp database
│   └── GDX_GLD_Mining_Stocks_Prices (56 gold mining stocks + 4 ETFs, 53 years of history)
├── qgsi database
│   └── Signal research tables (1-min bars, ThreeGaugeSignal outputs)
└── DEV_EODHD_DATA
    └── Development and staging tables (safe to modify)
         |
         v
CONSUMPTION LAYER
├── OBQ_TradingSystems_Vbt
│   ├── VectorBT strategy backtests
│   └── Performance_Reporting tearsheet (19 Plotly charts, 22 metrics)
├── OBQ_AI (5-agent AI hedge fund)
│   ├── Local DuckDB: D:\OBQ_AI\obq_ai.duckdb (204M+ rows, 12GB memory, 8 threads)
│   ├── Fundamental Agent (Grok)
│   ├── Technical Agent (Claude)
│   ├── Sentiment Agent (Groq/Llama)
│   ├── Risk Agent (Claude)
│   └── Macro Agent (Grok)
├── OBQ_GoldenOpp
│   └── Gold mining portfolio optimization and monitoring
└── JCN_Vercel_Dashboard
    ├── FastAPI backend (D:\JCN_Vercel_Dashboard\backend\)
    ├── Next.js + Tremor frontend
    └── Live at: jcn-tremor.vercel.app
```

---

## SECTION 3: Per-Repo Reference

### OBQ_TradingSystems_Vbt

**Purpose:** The primary strategy research and backtesting environment. All trading strategies are developed, validated, and documented here. Produces the canonical Performance_Reporting tearsheet used across all OBQ strategy presentations.

**Tech Stack:** Python, VectorBT 0.28.4, Numba, Pandas, NumPy, Plotly, Jupyter

**Primary Database/Tables:**
- Reads from: MotherDuck `PROD_EODHD.PROD_EOD_survivorship`, `PROD_EOD_ETFs`
- Also reads from: PWBBacktest_Data parquet files (for paper replications)
- Writes to: local `knowledge/backtest_results_log.md`

**Key Files:**
- `Performance_Reporting/` — the tearsheet module (import from here for all reports)
- `strategies/` — individual strategy `.py` files
- `notebooks/` — Jupyter notebooks (single-cell execution)
- `knowledge/` — backtest results log, VBT patterns, dataset schemas

**Connections to Other Repos:**
- Tearsheet is imported by OBQ_AI for signal validation
- Strategy parameters are referenced by JCN_Vercel_Dashboard for live monitoring
- Data comes from OBQ_Database_Prod via MotherDuck

---

### OBQ_AI

**Purpose:** 5-agent AI hedge fund system. Each agent specializes in one analytical domain and contributes to a joint portfolio recommendation. Orchestrated by LangGraph with a PyWebView desktop UI for interactive use.

**Tech Stack:** Python, LangGraph, PyWebView, DuckDB (local), Anthropic Claude API, xAI Grok API, Groq API, FastAPI

**Primary Database/Tables:**
- Local DuckDB: `D:\OBQ_AI\obq_ai.duckdb`
  - 204M+ rows of market and fundamental data
  - Sorted by (date, symbol) for fast range queries
  - Configuration: 12GB memory limit, 8 threads
- Also reads from: MotherDuck (for real-time score updates)

**Key Files:**
- `main.py` — entry point, starts PyWebView + FastAPI
- `agents/` — one file per agent (fundamental.py, technical.py, sentiment.py, risk.py, macro.py)
- `graph/` — LangGraph workflow definition
- `ui/` — PyWebView HTML/JS frontend

**Agent Details:**
| Agent | LLM | Primary Data Source | Output |
|---|---|---|---|
| Fundamental | Grok (xAI) | Financial statements, OBQ_Scores | Value/quality assessment |
| Technical | Claude (Anthropic) | OHLCV, indicators | Entry/exit signals |
| Sentiment | Groq/Llama | News, social data | Sentiment score |
| Risk | Claude (Anthropic) | Portfolio positions, VIX | Risk metrics, position sizing |
| Macro | Grok (xAI) | Economic data, rates | Macro regime classification |

**Connections to Other Repos:**
- Consumes factor scores from OBQ_Fundamental_Pro via MotherDuck
- Reads historical data from OBQ_Database_Prod ETL output
- Signal validation uses Performance_Reporting from OBQ_TradingSystems_Vbt

---

### OBQ_GoldenOpp

**Purpose:** Specialized portfolio system for gold mining stocks. Covers 56 mining companies plus 4 ETFs (GDX, GLD, GDXJ, SLV) with 53 years of price history.

**Tech Stack:** Python, VectorBT, Pandas, MotherDuck (GoldenOpp database)

**Primary Database/Tables:**
- MotherDuck `GoldenOpp.GDX_GLD_Mining_Stocks_Prices`
  - 60 symbols (56 miners + 4 ETFs)
  - Daily OHLCV + adjusted_close
  - Date range: ~1970 to present

**Key Files:**
- `universe.py` — gold mining universe definition and loading
- `strategies/` — mining-specific strategy implementations
- `screening/` — fundamental screening for mining stocks

**Connections to Other Repos:**
- Data loaded by OBQ_Database_Prod ETL pipelines
- Reports use Performance_Reporting from OBQ_TradingSystems_Vbt

---

### OBQ_Database_Prod

**Purpose:** Production data warehouse and ETL pipeline system. Handles daily incremental data sync from EODHD, split/dividend adjustments, fundamental data processing, and data promotion to MotherDuck production tables.

**Tech Stack:** Python, DuckDB, MotherDuck, EODHD API, Pandas, SQLAlchemy

**Primary Database/Tables:**
- Manages all MotherDuck PROD_EODHD tables
- Intermediate staging in DEV_EODHD_DATA
- Local parquet cache for raw downloads

**Key Files:**
- `etl/daily_sync.py` — daily OHLCV incremental update
- `etl/fundamental_loader.py` — financial statement ingestion
- `etl/adjustment_processor.py` — split/dividend adjustment pipeline
- `validation/data_quality.py` — pre-production validation checks
- `scripts/promote_dev_to_prod.py` — controlled DEV → PROD promotion

**Connections to Other Repos:**
- Feeds all other repos via MotherDuck
- Receives configuration from OBQ_Fundamental_Pro for score table schemas

---

### QGSI

**Purpose:** Signal research platform for high-frequency indicators. Implements ThreeGaugeSignal and related short-term signals on 1-minute bars across 400 US stocks.

**Tech Stack:** Python, DuckDB (qgsi database), Pandas, NumPy, custom signal libraries

**Primary Database/Tables:**
- MotherDuck `qgsi` database
- 1-minute OHLCV for 400 stocks
- ThreeGaugeSignal output tables

**Key Files:**
- `signals/three_gauge.py` — ThreeGaugeSignal implementation
- `universe/400_stocks.py` — stock universe definition
- `backtest/` — signal validation backtests

**Connections to Other Repos:**
- Signal research may feed into OBQ_AI Technical Agent
- Historical data sourced from OBQ_Database_Prod pipelines

---

### JCN_Vercel_Dashboard

**Purpose:** Live client-facing dashboard. Displays OBQ factor scores, portfolio positions, performance metrics, and market data in an interactive web interface.

**Tech Stack:** FastAPI (Python backend), Next.js 14, Tremor UI components, Vercel (hosting)

**Live URL:** jcn-tremor.vercel.app

**Primary Database/Tables:**
- Reads from: MotherDuck `PROD_OBQ_Scores`, `PROD_OBQ_Momentum_Scores`, `PROD_EOD_survivorship`
- Backend API: `D:\JCN_Vercel_Dashboard\backend\`

**Key Files:**
- `backend/main.py` or `backend/app.py` — FastAPI entry point
- `backend/routers/` — API route handlers
- `frontend/app/` — Next.js pages
- `frontend/components/` — Tremor chart components

**Connections to Other Repos:**
- Displays scores computed by OBQ_Fundamental_Pro
- References strategy performance from OBQ_TradingSystems_Vbt
- Data served from OBQ_Database_Prod via MotherDuck

---

### OBQ_Fundamental_Pro

**Purpose:** Factor scoring pipeline. Computes five OBQ proprietary scores for every stock in the investable universe using financial statement data, then writes results to MotherDuck for consumption by OBQ_AI and JCN_Vercel_Dashboard.

**Tech Stack:** Python, Pandas, NumPy, scikit-learn (for score normalization), MotherDuck

**Primary Database/Tables:**
- Reads from: MotherDuck fundamental tables (balance sheets, income statements, cash flow)
- Writes to: `PROD_EODHD.PROD_OBQ_Scores`, `PROD_EODHD.PROD_OBQ_Momentum_Scores`

**Key Files:**
- `scoring/value_score.py` — value factor computation
- `scoring/growth_score.py` — growth factor computation
- `scoring/financial_strength.py` — FS score (Piotroski-style)
- `scoring/quality_score.py` — quality/profitability factor
- `scoring/momentum_score.py` — price and earnings momentum
- `pipeline/run_all_scores.py` — master scoring run

**Connections to Other Repos:**
- Outputs consumed by JCN_Vercel_Dashboard and OBQ_AI
- Input data managed by OBQ_Database_Prod

---

### QuantMuse

**Purpose:** Reference framework (fork). Used as an architectural template for strategy design patterns, particularly for portfolio construction and risk management approaches.

**Tech Stack:** Python, VectorBT (similar stack to OBQ_TradingSystems_Vbt)

**Usage:** Read-only reference. Do not modify; pull upstream updates when relevant.

---

## SECTION 4: The Five OBQ Factor Scores

The five OBQ scores are the core intellectual product of the platform. They represent a systematic, rules-based approach to identifying high-quality stocks across value, growth, financial health, quality, and momentum dimensions.

**Score Definitions:**

| Score | Description | Key Inputs |
|---|---|---|
| `value_score` | Measures cheapness relative to earnings, book value, and cash flow | P/E, P/B, P/FCF, EV/EBITDA |
| `growth_score` | Measures revenue, earnings, and cash flow growth rates | YoY and 3Y revenue growth, EPS growth, FCF growth |
| `financial_strength_score` (fs) | Measures balance sheet and cash flow health (Piotroski-inspired) | Debt/equity, current ratio, OCF/assets, accruals |
| `quality_score` | Measures profitability consistency and management efficiency | ROE, ROIC, gross margin, asset turnover, earnings consistency |
| `momentum_score` | Measures price and earnings momentum | 12-1M price momentum, EPS revision momentum, relative strength |

**Data Flow:**
```
Financial Statements (EODHD quarterly data)
    |
    v
OBQ_Database_Prod (ETL — point-in-time staging using filing_date)
    |
    v
OBQ_Fundamental_Pro (scoring pipeline — normalized cross-sectionally)
    |
    v
MotherDuck PROD_OBQ_Scores (date, symbol, value_score, growth_score, fs_score, quality_score)
MotherDuck PROD_OBQ_Momentum_Scores (date, symbol, momentum_score, systemscore)
    |
    v (consumed by)
JCN_Vercel_Dashboard ← displayed to clients
OBQ_AI Fundamental Agent ← used in AI portfolio recommendations
OBQ_TradingSystems_Vbt ← used as strategy signals
```

**Critical Rule (Article I.2):** All score computations must use `filing_date` as the point-in-time join key. Using `quarter_date` introduces up to 90 days of look-ahead bias in backtests.

---

## SECTION 5: Performance_Reporting Tearsheet

The Performance_Reporting module is the standard output format for all OBQ backtests. It provides a comprehensive, interactive Plotly-based report that can be embedded in notebooks or exported as HTML.

**Location:** `OBQ_TradingSystems_Vbt/Performance_Reporting/`

**Standard Import:**
```python
import sys
sys.path.insert(0, r"D:\OBQ_TradingSystems_Vbt")
from Performance_Reporting import tearsheet
```

**19 Interactive Plotly Charts:**
1. Equity curve (log scale) vs. benchmark
2. Drawdown chart
3. Monthly returns heatmap
4. Annual returns bar chart
5. Rolling Sharpe ratio (12M, 36M)
6. Rolling volatility (annualized)
7. Rolling beta to benchmark
8. Rolling correlation to benchmark
9. Win/loss distribution
10. Return distribution histogram
11. Underwater plot (time in drawdown)
12. Position count over time
13. Turnover analysis
14. Long/short exposure over time
15. Sector/asset class exposure
16. Crisis period comparison
17. Factor exposure over time
18. Best/worst periods analysis
19. Trade duration distribution

**22 Metrics:**
CAGR, Total Return, Sharpe Ratio, Sortino Ratio, Calmar Ratio, Max Drawdown, Max Drawdown Duration, Avg Drawdown, Volatility (annualized), Beta, Alpha (annualized), Correlation, Win Rate, Avg Win, Avg Loss, Profit Factor, Total Trades, Avg Trade Duration, Best Month, Worst Month, Value at Risk (95%), Expected Shortfall (95%)

**8 Built-in Crisis Periods:**
1. Dot-com Crash (2000-03 to 2002-10)
2. Global Financial Crisis (2007-10 to 2009-03)
3. Flash Crash (2010-05-06)
4. European Debt Crisis (2011-07 to 2011-10)
5. China Devaluation (2015-08)
6. Q4 2018 Selloff (2018-10 to 2018-12)
7. COVID Crash (2020-02 to 2020-03)
8. 2022 Rate Shock (2022-01 to 2022-10)

**Usage in Strategy Files:**
```python
results = tearsheet.generate(
    portfolio=pf,
    benchmark=benchmark_returns,
    strategy_name="My Strategy",
    params=PARAMS,
    export_html=True,
    output_path="results/my_strategy_tearsheet.html"
)
```
