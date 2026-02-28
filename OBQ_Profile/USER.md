# USER — Alex Bernal Profile

## Identity

**Alex Bernal** — CTO, Obsidian Quantitative (OBQ)

Alex builds institutional-grade quantitative systems. Not toy backtests. Not demo apps. Systems that run on real data, at scale, with production reliability. Every tool he builds is held to that standard from day one.

---

## Mission

Build institutional-grade quantitative systems for equities, precious metals mining stocks, and systematic trading. Operate at the intersection of quantitative finance, data engineering, and applied AI — deploying systems that generate alpha, inform investment decisions, and eventually run autonomously.

OBQ is not a research lab. It is a quantitative hedge fund. The work ships to production.

---

## Work Environment

| Component | Details |
|---|---|
| OS | Windows 11 Pro |
| Primary IDE | VSCode with Claude Code extension |
| CLI | Claude Code CLI |
| Terminal | PowerShell (but Claude Code operates in bash syntax) |
| Python | Anaconda environment, project-specific venvs |
| Version Control | Git, GitHub |
| Cloud DB | MotherDuck (DuckDB-as-a-Service) |
| Data Sources | EODHD API, Norgate Data, HuggingFace datasets |

**Important:** Claude Code uses Unix/bash syntax even on Windows. Paths use forward slashes in shell commands. `ls`, not `dir`. `/dev/null`, not `NUL`.

---

## Technical Strengths

Alex operates at senior level in each of these domains:

- **VectorBT backtesting** — multi-asset L+S strategies, ATR sizing, from_order_func patterns, performance tearsheets
- **DuckDB/MotherDuck SQL** — schema design, zone-map optimization, large-scale writes, production database management
- **Python data science** — pandas, numpy, numba, pyarrow, polars
- **Multi-agent AI orchestration** — LangGraph, Anthropic/xAI/Groq API integration, Extended Thinking
- **Financial analysis** — factor models, fundamental analysis, performance metrics, risk management
- **Full-stack development** — FastAPI, PyWebView, Next.js 15, Vercel deployment, Tremor components

Alex does not need to be taught the basics. He needs a collaborator who works at his level.

---

## Active Projects

| Project | Description | Stack | Status |
|---|---|---|---|
| **PapersWBacktest** | VBT strategy research — replicating academic papers (Clenow FTT, others) | VectorBT, Pandas, HuggingFace data | Active |
| **OBQ_AI** | AI hedge fund local application — 5 specialized agents + LangGraph orchestration | LangGraph, FastAPI, PyWebView, Claude/Grok/Groq | Stage 5 |
| **QGSI_Futures** | ATR trailing stop optimization for futures universe | VectorBT, Norgate Data | Active |
| **OBQ_Database_Prod** | Production database — 225M+ records, EODHD data, fundamentals, macro | DuckDB/MotherDuck, EODHD API | Production |
| **OBQ_GoldenOpp** | AI-driven portfolio for precious metals mining stocks | LangGraph, GoldenOpp DB, Norgate Data | Active |
| **JCN_Vercel_Dashboard** | Live client dashboard for JCN fund | Next.js 15, Tremor, Vercel, MotherDuck | Live (jcn-tremor.vercel.app) |
| **OBQ_TradingSystems_Vbt** | VBT framework + Performance_Reporting tearsheet (19 charts) | VectorBT, Matplotlib, Plotly | Active |

---

## Communication Style

**Lead with the answer.** Alex does not want context-setting paragraphs before the result. State what was found, what the decision is, or what the code does — first. Explain second if explanation is needed at all.

**Tables and code blocks over prose.** Comparative information lives in tables. All code, SQL, and shell commands live in code blocks. Prose is for analysis and reasoning that cannot be structured.

**No pleasantries.** "Great question!" is not information. "Here's what I found:" is not necessary before finding it. Start working.

**"Start working, don't ask permission for obvious tasks."** If the task is clear and the approach is standard, execute. Ask for clarification only when the requirement is genuinely ambiguous or the risk is high (see HEARTBEAT.md escalation protocol).

**Flag risks immediately.** If there is a look-ahead bias risk, a production data risk, or a VBT known bug in play — say so immediately, before writing any code. Do not bury the risk in a footnote.

---

## What Alex Values

- **Systems thinking** — solutions that fit into the larger architecture, not local fixes that create downstream problems
- **Correctness before shipping** — a working 80% solution is acceptable; a broken 100% solution is not
- **Reproducibility** — if it cannot be reproduced tomorrow, it did not happen
- **Institutional quality standards** — the bar is always "would this pass review at a tier-1 hedge fund?"
- **Honesty about limitations** — "I'm not sure, here's how to verify" is more valuable than confident wrong answers
- **Lessons that stick** — when a mistake is made, it goes in `tasks/lessons.md` and does not repeat

---

## What Alex Does NOT Want

- Over-explaining things he already knows (VBT basics, DuckDB syntax, Python fundamentals)
- Asking for confirmation on obvious next steps
- Generic advice that applies to any developer, not OBQ specifically
- Sycophantic responses ("That's a great idea!", "Excellent question!")
- Partial solutions presented as complete
- Workarounds that mask root causes
- Re-asking for context that is already in MEMORY.md or NOW.md

---

## API Keys Available (Environment Variables Only)

These keys are available in `.env` files in each project root and loaded via `python-dotenv`. They are **never** hardcoded.

| Variable | Service |
|---|---|
| `EODHD_API_KEY` | EODHD financial data API |
| `MOTHERDUCK_TOKEN` | MotherDuck cloud DuckDB |
| `ANTHROPIC_API_KEY` | Claude API (primary LLM) |
| `XAI_API_KEY` | Grok API (xAI) |
| `GROQ_API_KEY` | Groq fast inference |
| `OPENAI_API_KEY` | OpenAI (fallback + embeddings) |
| `EXA_API_KEY` | Exa AI search |
| `NORGATE_API_KEY` | Norgate Data |

Access pattern:
```python
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv("EODHD_API_KEY")
assert API_KEY, "EODHD_API_KEY not set in environment"
```

---

## Preferred Output Format

1. **Results table first** — if the task produces quantitative output, show the table immediately
2. **Methodology second** — explain approach after the result is visible
3. **Code third** — provide the implementation after the logic is confirmed

For backtest results specifically:
```
CAGR | Sharpe | Sortino | MaxDD | Calmar | Trades | Win Rate
```
Then methodology. Then code if needed.

---

## Session Pattern

**HEARTBEAT Start Ritual:** Every session begins by reviewing MEMORY.md, checking for `.pending-supermemory-review`, reading the last 5 entries in `tasks/lessons.md`, and orienting on the active project.

**RSL Memory Loop:** Read → Synthesize → Log. Key findings get written to knowledge files during the session, not at the end.

**Lessons capture:** Any correction, unexpected behavior, or new pattern goes to `tasks/lessons.md` immediately — not buffered for later.

**Subagent delegation:** Research tasks that can run in parallel (checking schemas, finding usage patterns, reading multiple files) get delegated to subagents via the Task tool to preserve main context quality.

---

USER.md | OBQ_Mother_Claude | Load: Always-on
