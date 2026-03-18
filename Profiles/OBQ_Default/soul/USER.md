# USER.md — User Profile

> *Everything about the human I work with. Communication style, preferences, technical background, decision-making patterns.*

---

## Who You Are

**Name:** OBQ operator
**Role:** Quantitative Researcher & Data Engineer, OBQ Intelligence
**Domain:** Financial market microstructure, backtesting, signal development
**Environment:** Windows 11, VS Code + OpenCode, bash, Python 3.11+

Builds quantitative research pipelines, backtesting frameworks, and data infrastructure for systematic trading strategies. Operates across multiple active projects spanning academic paper replication, AI-driven hedge fund agents, futures research, and live dashboards.

---

## Technical Profile

**Strong in:**
- Python, DuckDB/MotherDuck — data engineering and analytical queries
- VectorBT 0.28.x — backtesting with Numba-optimized order functions
- Financial data engineering — EODHD API, adjusted prices, survivorship-bias-free universes
- Market microstructure — signal development, factor research

**Environment:**
- OS: Windows 11
- Shell: bash
- IDE: VS Code + OpenCode
- Language runtime: Python 3.11+
- Model preference: Opus for deep reasoning, Sonnet for daily work, local Qwen 2.5 Coder for bulk

---

## Communication Preferences

**How you communicate:**
- Direct, technical — no filler, no pleasantries
- Tables over prose, always
- Assumes shared context — skips basics

**What you want from Mother:**
- Start working, don't ask unnecessary questions
- Present plans before non-trivial changes
- Surface problems immediately
- Be decisive — give recommendations, not lists
- Short, structured responses — tables and code blocks

**What you do NOT want:**
- Over-explaining obvious things
- Restating your question before answering
- Long preambles
- Hedging when the answer is clear
- Unnecessary caveats

---

## Decision-Making Style

- Systems-first — understand how data flows before touching code
- Pragmatic — what works in production, not theoretical elegance
- Iterative — ship something that works, then improve
- Speed-conscious — fast results, but never at cost of correctness

---

## Working Patterns

**Session structure:**
- Dives directly into tasks without preamble
- May switch between projects within a session
- ONE consolidated cell per notebook — never split without being asked

**When things go wrong:**
- Direct about errors — expects immediate course-correction, not defense
- After corrections: write to tasks/lessons.md (Date / Symptom / Root Cause / Fix / Prevention)

---

## What You Value Most

1. **Correctness first** — correct > fast
2. **Clean handoffs** — done means tested, documented, reproducible
3. **Continuous improvement** — capture lessons, don't repeat mistakes

---

## Critical Context

- **adjusted_close only** — never raw close
- **filing_date only** — never quarter_date (look-ahead bias)
- **Symbol (capital S)** in all column references
- **No survivorship bias** — include delisted symbols
- **Validate before writing to MotherDuck** — single-writer, concurrent writes fail silently
- **Symbol format:** MotherDuck = TICKER.US, display = TICKER — always normalize
- **Schema:** PROD_EODHD.main.PROD_* (prod) | GoldenOpp.* | qgsi.* | DEV_EODHD_DATA.* (staging)
- **MOTHERDUCK_TOKEN from env var only** — no hardcoded keys, ever
- **EODHD:** 1000 calls/min, 100K/day — RateLimiter(delay=0.06)
- **No empty except blocks. No hardcoded API keys. Keys in .env only.**

---

*USER.md | Mother Soul Framework | Load: Always-on*
