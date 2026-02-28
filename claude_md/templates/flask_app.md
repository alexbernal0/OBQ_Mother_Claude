# CLAUDE.md — Flask / FastAPI Application Project

<!-- This is a template for Flask or FastAPI application projects in the OBQ_AI / JCN_Vercel_Dashboard style.
     Copy this file to your project root as CLAUDE.md and fill in the specifics. -->

## App Purpose and Architecture

[Describe the application. Include: what it does, who uses it, which OBQ data it consumes, whether it has a UI and what kind (PyWebView desktop, Vercel web, CLI), and any real-time or scheduled components.]

Example (OBQ_AI style): 5-agent AI portfolio analysis system. Desktop application using PyWebView to wrap a FastAPI server. Each agent (Fundamental, Technical, Sentiment, Risk, Macro) queries a local DuckDB database and calls LLM APIs to produce a portfolio recommendation. Not deployed externally — runs locally at http://127.0.0.1:8000.

Example (JCN_Vercel_Dashboard style): Client-facing quant dashboard. FastAPI backend deployed on Railway (or local), Next.js + Tremor frontend deployed on Vercel. Reads OBQ factor scores and portfolio positions from MotherDuck, serves them as REST endpoints, displays as interactive charts.

---

## Project Structure

```
[project_root]/
├── main.py             # Entry point — starts the server (or PyWebView app)
├── app.py              # FastAPI / Flask app factory (create_app() function)
├── routers/            # FastAPI: one router file per domain
│   ├── scores.py       #   GET /scores, GET /scores/{symbol}
│   ├── portfolio.py    #   GET /portfolio, POST /portfolio/rebalance
│   └── market.py       #   GET /market/summary
├── agents/             # (OBQ_AI style) one file per AI agent
│   ├── fundamental.py
│   ├── technical.py
│   ├── sentiment.py
│   ├── risk.py
│   └── macro.py
├── graph/              # (OBQ_AI style) LangGraph workflow
│   └── workflow.py
├── ui/                 # (PyWebView style) HTML/JS frontend
│   ├── index.html
│   └── static/
├── frontend/           # (Next.js style) if separate frontend in same repo
├── database/
│   ├── connection.py   # DuckDB connection factory
│   └── queries.py      # SQL query functions
├── .env                # Environment variables (NEVER commit)
├── .env.example        # Variable names only (safe to commit)
└── requirements.txt
```

---

## Entry Points

### FastAPI Application (main.py)

```python
# main.py — FastAPI entry point
import uvicorn
from app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,   # False in production
        log_level="info"
    )
```

### Flask Application (main.py)

```python
# main.py — Flask entry point
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

### PyWebView Desktop App (main.py)

```python
# main.py — PyWebView entry point (OBQ_AI style)
import threading
import webview
import uvicorn
from app import create_app

app = create_app()

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    # Start FastAPI in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait briefly for server to start
    import time
    time.sleep(1)

    # Launch desktop window
    webview.create_window(
        title="OBQ AI Dashboard",
        url="http://127.0.0.1:8000",
        width=1400,
        height=900,
        resizable=True
    )
    webview.start()
```

---

## App Factory Pattern

```python
# app.py — application factory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import scores, portfolio, market

def create_app() -> FastAPI:
    app = FastAPI(
        title="OBQ API",
        description="OBQ quantitative finance platform",
        version="1.0.0"
    )

    # CORS for Vercel frontend or local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",       # local Next.js dev
            "https://jcn-tremor.vercel.app"  # production frontend
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(scores.router, prefix="/scores", tags=["Scores"])
    app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
    app.include_router(market.router, prefix="/market", tags=["Market"])

    # Health check
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
```

---

## DuckDB Connection Pattern

### MotherDuck (JCN_Vercel_Dashboard style)

```python
# database/connection.py
import duckdb
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def get_motherduck_connection() -> duckdb.DuckDBPyConnection:
    """
    Singleton MotherDuck connection.
    Cached for the lifetime of the process.
    Thread-safe for read-only workloads.
    """
    token = os.getenv("MOTHERDUCK_TOKEN")
    if not token:
        raise RuntimeError("MOTHERDUCK_TOKEN environment variable not set")

    conn = duckdb.connect(f"md:?motherduck_token={token}")
    return conn

def execute_query(sql: str, params=None) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    conn = get_motherduck_connection()
    if params:
        result = conn.execute(sql, params).df()
    else:
        result = conn.execute(sql).df()
    return result.to_dict(orient="records")
```

### Local DuckDB (OBQ_AI style)

```python
# database/connection.py
import duckdb
import os
from pathlib import Path

DB_PATH = os.getenv("LOCAL_DB_PATH", r"D:\OBQ_AI\obq_ai.duckdb")

_connection = None

def get_local_connection() -> duckdb.DuckDBPyConnection:
    """
    Singleton local DuckDB connection with performance settings.
    """
    global _connection
    if _connection is None:
        if not Path(DB_PATH).exists():
            raise FileNotFoundError(f"Local database not found: {DB_PATH}")

        _connection = duckdb.connect(DB_PATH)
        _connection.execute("SET memory_limit='12GB'")
        _connection.execute("SET threads=8")
        print(f"Connected to local DuckDB: {DB_PATH}")

    return _connection
```

---

## Blueprint / Router Registration Pattern

### FastAPI Router (one per domain)

```python
# routers/scores.py
from fastapi import APIRouter, Query, HTTPException
from database.connection import execute_query
from typing import Optional

router = APIRouter()

@router.get("/")
def get_scores(
    date: Optional[str] = Query(None, description="Score date (YYYY-MM-DD). Defaults to latest."),
    limit: int = Query(100, ge=1, le=1000),
    min_composite: Optional[float] = Query(None)
):
    """Get OBQ factor scores for the most recent scoring date."""
    date_filter = f"AND date = '{date}'" if date else "AND date = (SELECT MAX(date) FROM PROD_EODHD.main.PROD_OBQ_Scores)"
    composite_filter = f"AND composite_score >= {min_composite}" if min_composite else ""

    sql = f"""
        SELECT date, symbol, value_score, growth_score, fs_score, quality_score,
               momentum_score, composite_score, universe_rank
        FROM PROD_EODHD.main.PROD_OBQ_Scores
        WHERE 1=1
        {date_filter}
        {composite_filter}
        ORDER BY composite_score DESC NULLS LAST
        LIMIT {limit}
    """

    try:
        return execute_query(sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{symbol}")
def get_scores_for_symbol(symbol: str, periods: int = Query(12, ge=1, le=120)):
    """Get score history for a specific symbol."""
    sql = f"""
        SELECT date, value_score, growth_score, fs_score, quality_score,
               composite_score, universe_rank
        FROM PROD_EODHD.main.PROD_OBQ_Scores
        WHERE symbol = '{symbol}.US'
        ORDER BY date DESC
        LIMIT {periods}
    """
    results = execute_query(sql)
    if not results:
        raise HTTPException(status_code=404, detail=f"No scores found for {symbol}")
    return results
```

---

## Environment Variables Required

Create a `.env` file in the project root (NEVER commit this file):

```bash
# .env — DO NOT COMMIT
# MotherDuck
MOTHERDUCK_TOKEN=your_motherduck_token_here

# Local database (OBQ_AI style)
LOCAL_DB_PATH=D:\OBQ_AI\obq_ai.duckdb

# LLM APIs (OBQ_AI style)
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_xai_key_here
GROQ_API_KEY=your_groq_key_here

# App settings
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://jcn-tremor.vercel.app
```

Create a `.env.example` file (safe to commit):

```bash
# .env.example — copy to .env and fill in real values
MOTHERDUCK_TOKEN=
LOCAL_DB_PATH=D:\OBQ_AI\obq_ai.duckdb
ANTHROPIC_API_KEY=
XAI_API_KEY=
GROQ_API_KEY=
DEBUG=false
PORT=8000
```

Load in app:
```python
from dotenv import load_dotenv
load_dotenv()  # call before any os.getenv() calls
```

---

## Deployment Commands

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI with hot reload
uvicorn main:app --reload --port 8000

# Run Flask
python main.py

# Run PyWebView desktop app
python main.py

# View API docs (FastAPI auto-generates)
# Open: http://127.0.0.1:8000/docs
```

### Production (FastAPI on Railway)

```bash
# Deploy to Railway (from project root)
railway login
railway init
railway up

# Set environment variables on Railway
railway env set MOTHERDUCK_TOKEN=your_token
railway env set ANTHROPIC_API_KEY=your_key

# View logs
railway logs
```

### Frontend (Next.js on Vercel)

```bash
# From frontend/ directory
npm install

# Local development
npm run dev  # starts at http://localhost:3000

# Deploy to Vercel
vercel

# Set environment variables on Vercel dashboard
# NEXT_PUBLIC_API_URL = https://your-railway-app.railway.app
```

### Docker (if containerized)

```bash
# Build image
docker build -t obq-api .

# Run container
docker run -p 8000:8000 \
  -e MOTHERDUCK_TOKEN=$MOTHERDUCK_TOKEN \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  obq-api
```

---

## Common Development Tasks

```bash
# Check all routes are registered (FastAPI)
python -c "from app import create_app; app = create_app(); [print(r.path) for r in app.routes]"

# Test a specific endpoint
curl http://127.0.0.1:8000/scores?limit=5

# Verify database connection
python -c "
from database.connection import get_motherduck_connection
conn = get_motherduck_connection()
result = conn.execute('SELECT COUNT(*) FROM PROD_EODHD.main.PROD_EOD_survivorship').fetchone()
print(f'Row count: {result[0]:,}')
"

# Check environment variables are loaded
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
keys = ['MOTHERDUCK_TOKEN', 'ANTHROPIC_API_KEY', 'XAI_API_KEY', 'GROQ_API_KEY']
for k in keys:
    v = os.getenv(k)
    print(f'{k}: {\"SET\" if v else \"MISSING\"} ({len(v) if v else 0} chars)')
"
```
