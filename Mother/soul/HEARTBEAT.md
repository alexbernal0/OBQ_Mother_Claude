# HEARTBEAT.md — Session Rituals

> *The connective tissue between sessions. Run START before engaging with the first task. Run END before concluding. Non-negotiable.*

---

## SESSION START RITUAL

Run silently before responding. Don't announce it — just do it.

### Step 1 — Load Context
- [ ] Read `NOW.md` — identify active work, last state
- [ ] Check Supermemory context — retrieve relevant long-term memory
- [ ] Check `tasks/lessons.md` if exists — review patterns to avoid

### Step 2 — Identify Active Project
Determine from:
- Directory Claude Code / OpenCode is opened in
- User's first message context
- NOW.md state

Active project sets: tech stack, data connections, coding patterns.

| Project | Path | Stack |
|---------|------|-------|
| PapersWBacktest | D:\Master Data Backup 2025\PapersWBacktest | VBT, DuckDB, PWB_tools |
| OBQ_AI | Desktop\OBQ_AI\AI_Hedge_Fund_Local | AI agents, Claude API |
| QGSI_Futures | Desktop\QGSI Claude Data File | Futures, DuckDB |
| JCN_Vercel_Dashboard | GitHub (private) | Vercel, Next.js |

### Step 3 — Safety Check
Before engaging with tasks involving:
- Data writes → confirm environment (dev/staging/prod) and validate data
- VBT backtests → verify adjusted_close, filing_date, no survivorship bias
- MotherDuck writes → confirm schema, single-writer constraint
- LLM calls → verify provider and cost expectations
- API calls → verify rate limits (EODHD: delay=0.06)

### Step 4 — Ready
Respond with full context loaded. Don't summarize the ritual.

---

## SESSION END RITUAL

Run when:
- User says session is complete
- Major milestone reached
- Natural conclusion of work block

### Step 1 — /handoff
Run `/handoff` to generate session summary for next session.

### Step 2 — Update NOW.md
Update with:
- Current state of work
- Next logical step (specific enough to start cold)
- Open questions or blockers
- Key decisions made

### Step 3 — Capture Lessons
If corrected or caught a mistake, update `tasks/lessons.md`:
- Date / Symptom / Root Cause / Fix / Prevention

### Step 4 — Supermemory Auto-Capture
Assess: should anything be preserved long-term?
- Architectural decisions
- Significant findings
- Resolved bugs with root-cause clarity
- Safety incidents

If yes: `super-save`.

---

## MID-SESSION CHECKPOINTS

At natural breakpoints:
- Am I aligned with original intent?
- Has scope crept?
- Token budget check — am I burning context on low-value work?
- Should this be routed to local LLM (Qwen) instead?
- Lesson to capture now?

If yes to any → address immediately.

---

## Heartbeat Triggers (Always Watch)

| Trigger | Action |
|---------|--------|
| DB write without env confirmation | **PAUSE** — confirm dev/staging/prod |
| MotherDuck write without validation | **STOP** — validate data first |
| User correction | Immediately capture lesson |
| Cost spike detected | **STOP** — investigate |
| Raw close used instead of adjusted_close | **STOP** — fix immediately |
| quarter_date used instead of filing_date | **STOP** — look-ahead bias |
| **context > 100K tokens** | **/handoff and start fresh** |

---

*HEARTBEAT.md | Mother Soul Framework | Load: Always-on*
