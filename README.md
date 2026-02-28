# OBQ_Mother_Claude

> Persistent identity, governance, and productivity system for Claude Code at Obsidian Quantitative.

Built specifically for Claude Code (Anthropic CLI + VSCode extension). Not compatible with OpenCode
or Cursor without adaptation.

---

## What This Is

OBQ_Mother_Claude is the configuration layer that gives Claude a persistent, consistent identity
across all OBQ development sessions. It provides:

- **Soul files** — who Claude is, how it thinks, how Alex works
- **Domain laws** — the non-negotiable rules for OBQ quant work
- **Skills** — domain-specific capabilities (VBT, DuckDB, backtesting, data quality)
- **Agents** — specialized subagents (backtest reviewer, paper analyst)
- **Commands** — slash commands (/session-start, /log-results, /new-strategy)
- **Hooks** — session protection (sensitive file blocking, syntax checks)
- **MCP servers** — direct database and documentation access

---

## Quick Install (New Machine)

```bash
# 1. Clone this repo to Desktop
cd ~/Desktop
git clone https://github.com/alexbernal0/OBQ_Mother_Claude

# 2. Run full deployment
cd OBQ_Mother_Claude
python deploy.py all

# 3. Install MCP servers (follow prompts from deploy.py)
python deploy.py mcp

# 4. Restart Claude Code
```

That's it. Claude Code will load the global identity on next launch.

---

## Folder Structure

```
OBQ_Mother_Claude/
├── deploy.py                    ← Run this to install everything
├── README.md                    ← This file
├── DEPLOY.md                    ← Detailed install guide
│
├── soul/                        ← 6-file persistent identity system
│   ├── SOUL.md                  ← Core character and values
│   ├── IDENTITY.md              ← Role, expertise, 10 operating principles
│   ├── PRINCIPLES.md            ← Decision playbook + domain laws
│   ├── USER.md                  ← Alex's profile and preferences
│   ├── HEARTBEAT.md             ← Session start/end rituals
│   └── NOW.md                   ← Live state template
│
├── prime_directive/
│   └── constitution.md          ← Immutable OBQ governance rules
│
├── Personalities/               ← Character reference (Mother/TARS/JARVIS)
│   ├── mother.md
│   ├── tars.md
│   └── jarvis.md
│
├── claude_md/
│   ├── global_CLAUDE.md         ← Deploys to ~/.claude/CLAUDE.md (MOST IMPORTANT)
│   └── templates/               ← Project CLAUDE.md templates
│       ├── vbt_strategy.md      ← For PapersWBacktest-type projects
│       ├── data_pipeline.md     ← For OBQ_Database_Prod-type projects
│       ├── flask_app.md         ← For OBQ_AI-type projects
│       └── research_notebook.md ← For QGSI/Hex.tech-type projects
│
├── skills/                      ← Claude Code SKILL.md format
│   ├── vbt-patterns/            ← VBT 0.28.x bugs + from_order_func template
│   ├── data-quality/            ← Validation before every backtest/pipeline
│   ├── backtest-review/         ← Post-run quality checklist
│   ├── heartbeat/               ← Session start ritual
│   ├── paper-to-strategy/       ← Academic paper → VBT strategy protocol
│   ├── python-debug/            ← Debug protocol for Numba/VBT/DuckDB errors
│   ├── obq-governance/          ← Background governance (auto-applies)
│   ├── jcn-dashboard/           ← JCN FastAPI + Next.js + Vercel patterns
│   ├── quant-backtest/          ← VBT strategy structure and patterns
│   ├── pandas-analytics/        ← Financial data processing
│   ├── duckdb-data-eng/         ← MotherDuck + DuckDB patterns
│   ├── market-data-api/         ← EODHD + Norgate integration
│   ├── jupyter-research/        ← Notebook + Hex.tech workflows
│   └── test-generator/          ← pytest patterns for OBQ work
│
├── agents/
│   ├── backtest-reviewer.md     ← Post-backtest audit agent
│   └── paper-analyst.md        ← Research paper extraction agent
│
├── commands/
│   ├── session-start.md         ← /session-start
│   ├── log-results.md           ← /log-results
│   ├── new-strategy.md          ← /new-strategy [name]
│   └── update-knowledge.md      ← /update-knowledge
│
├── hooks/
│   ├── block-sensitive-files.py ← PreToolUse: block .env writes
│   └── syntax-check.sh         ← PostToolUse: Python syntax validation
│
├── mcp/
│   ├── mcp_additions.json       ← Ready-to-merge MCP config
│   └── INSTALL.md               ← MCP install commands
│
├── knowledge/
│   ├── OBQ_system_architecture.md
│   ├── dataset_schemas.md
│   ├── api_reference.md
│   └── vbt_gotchas.md
│
└── governance/
    └── overrides.log            ← Append-only override audit trail
```

---

## What Gets Deployed Where

| File | Deploys To | Effect |
|------|-----------|--------|
| `claude_md/global_CLAUDE.md` | `~/.claude/CLAUDE.md` | Loaded every session, all projects |
| `skills/*/SKILL.md` | `~/.claude/skills/` | Available as Claude skills globally |
| `agents/*.md` | `~/.claude/agents/` | Available as subagents globally |
| `commands/*.md` | `~/.claude/commands/` | Available as `/commands` globally |
| `hooks/*.py|sh` | `~/.claude/hooks/` | Active on file writes and session stops |
| Hook config | `~/.claude/settings.json` | Wires up all hook events |

**Note**: Soul files, constitution, and knowledge files stay in Mother_Claude — they are reference
documents. Only CLAUDE.md (the compiled identity) gets deployed to ~/.claude/.

---

## Deployment Commands

```bash
python deploy.py all              # Full deployment (recommended)
python deploy.py soul             # CLAUDE.md only
python deploy.py skills           # Skills only
python deploy.py agents           # Agents only
python deploy.py commands         # Commands only
python deploy.py hooks            # Hooks + settings.json
python deploy.py mcp              # Print MCP install commands
python deploy.py project <path>   # Add CLAUDE.md to a project
python deploy.py status           # Check what's deployed
```

---

## MCP Servers (Install Separately)

```bash
# MotherDuck — query your databases directly in conversation
claude mcp add --scope user duckdb --transport stdio -- \
  uvx mcp-server-motherduck --db-path :memory: --read-write --allow-switch-databases

# Memory graph — structured cross-session knowledge
claude mcp add --scope user memory --transport stdio -- \
  npx -y @modelcontextprotocol/server-memory

# Fetch — web content and paper retrieval
claude mcp add --scope user fetch --transport stdio -- \
  npx -y @modelcontextprotocol/server-fetch

# Context7 — live VBT/pandas/numpy docs (via Claude Code plugin)
# In Claude Code session: /plugin install context7
```

---

## Key Design Decisions

**Why no @include in CLAUDE.md?**
Claude Code does not support `@include` or `@import` directives in CLAUDE.md. The global
`~/.claude/CLAUDE.md` is loaded directly. Soul files are reference documents; their essence
is compiled into `global_CLAUDE.md`.

**Why no cli.py?**
Claude Code has no runtime boot process. `deploy.py` is just file management — copy the right
files to the right places. Simple and auditable.

**Why lock_cash=True in VBT?**
Confirmed via diagnostic: VBT 0.28.x's `size_type="percent"` + `cash_sharing=True` always
raises a reversal error even with zero actual reversals. This is a VBT bug, not user error.
`from_order_func` with `c.value_now` is the only correct approach.

---

## Updating

When soul files, principles, or domain laws change:
1. Edit the source files in `soul/`, `prime_directive/`, or `claude_md/global_CLAUDE.md`
2. Run `python deploy.py soul` to redeploy
3. Push changes to GitHub for backup
4. Restart Claude Code

---

## Repository

https://github.com/alexbernal0/OBQ_Mother_Claude

*OBQ_Mother_Claude | Version 1.0 | 2026-02-28*
