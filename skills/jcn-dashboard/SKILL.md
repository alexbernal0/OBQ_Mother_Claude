---
name: jcn-dashboard
description: "JCN Vercel Dashboard development patterns — FastAPI Python serverless functions, Next.js 15 with Tremor UI, MotherDuck integration, Vercel deployment, and symbol format handling. Use when working on JCN_Vercel_Dashboard codebase."
---

## JCN Vercel Dashboard — Development Patterns

---

## 1. ARCHITECTURE

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 + React 19 + Tremor components + ECharts |
| Backend | FastAPI Python serverless functions at `/api/` |
| Database | MotherDuck (PROD_EODHD database) |
| Deployment | Vercel (auto-detects FastAPI `app` variable) |

---

## 2. CRITICAL PATTERNS

### FastAPI Route Prefix Requirement

All FastAPI routes **MUST** include the `/api` prefix:

```python
# CORRECT
@app.get("/api/health")
@app.get("/api/scores/{symbol}")

# WRONG — will 404 in production
@app.get("/health")
@app.get("/scores/{symbol}")
```

### Environment Variables

- `MOTHERDUCK_TOKEN` is stored as a Vercel environment variable — **never hardcode it in source files**
- Access via `os.getenv('MOTHERDUCK_TOKEN')` in Python functions

### Symbol Format Normalization

MotherDuck stores symbols as `TICKER.US`. The frontend displays bare `TICKER`. Always normalize at API boundaries:

```python
def _normalize(s: str) -> str:
    """Strip .US suffix for display."""
    return s.replace('.US', '')

def _add_suffix(s: str) -> str:
    """Add .US suffix for MotherDuck queries."""
    return s if s.endswith('.US') else f"{s}.US"

# Query defensively — handle both forms in WHERE clause
symbols_both = symbols_md + [s.replace('.US', '') for s in symbols_md]
WHERE symbol IN ({','.join([f"'{s}'" for s in symbols_both])})
```

---

## 3. LOCAL DEV SETUP

Run two terminals simultaneously:

```bash
# Terminal 1 — FastAPI backend (port 8000)
cd api && uvicorn index:app --reload --port 8000

# Terminal 2 — Next.js frontend (rewrites /api/* to localhost:8000)
pnpm dev
```

The `next.config.mjs` rewrites proxy `/api/**` to `http://localhost:8000` during development, mirroring the Vercel routing behavior.

---

## 4. PRODUCTION DATABASE SCHEMA

```
PROD_EODHD.main.PROD_EOD_survivorship
    → Daily OHLC + adjusted_close, sector, industry
    → Survivorship-bias-free universe

PROD_EODHD.main.PROD_OBQ_Scores
    → value_score, growth_score, fs_score, quality_score per symbol per date

PROD_EODHD.main.PROD_OBQ_Momentum_Scores
    → obq_momentum_score per symbol per date

PROD_EODHD.main.PROD_EOD_ETFs
    → ETF pricing — SPY.US used as benchmark
```

Always query with `adjusted_close`, never raw `close`. (See obq-governance skill.)

---

## 5. VERCEL DEPLOYMENT

- `vercel.json` routes `/api/**` to the Python serverless functions
- `next.config.mjs` configures rewrites for local dev
- No Mangum or ASGI adapter needed — Vercel natively auto-detects the FastAPI `app` variable
- Always test with `vercel dev` locally before pushing to production
- Environment variables must be set in Vercel dashboard (Settings → Environment Variables) for production deploys

### Deployment Checklist

1. Run `vercel dev` and smoke-test all API endpoints
2. Verify `MOTHERDUCK_TOKEN` is set in Vercel project settings
3. Confirm all routes have `/api` prefix
4. Push — Vercel auto-deploys from main branch

---

## 6. COMMON GOTCHAS

- **Cold start latency**: MotherDuck connections add ~500ms on first request per function instance. Use connection pooling where possible.
- **Symbol inconsistency**: Some historical data has `AAPL`, some has `AAPL.US`. Always query both forms.
- **Tremor version**: Uses Tremor v3 component API — check docs before adding new Tremor components as v3 broke v2 APIs.
- **ECharts with Next.js**: Use dynamic import with `ssr: false` to avoid SSR hydration errors with ECharts canvas.
