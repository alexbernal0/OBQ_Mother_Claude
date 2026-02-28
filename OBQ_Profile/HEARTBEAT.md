# HEARTBEAT — Session Ritual

The HEARTBEAT is the rhythm of every working session. It is not optional. It is not a suggestion. It is the difference between sessions that accumulate progress and sessions that spin in place.

---

## BOOT CHECKLIST — Run Before Anything Else

When "Mother are you there" is received OR at session start, verify these connections first.
Report status explicitly. Do not proceed silently if a connection is down.

| Service | Check Command | Always On Boot |
|---------|--------------|----------------|
| GitHub | `gh auth status` | Yes |
| SuperMemory | `enabledPlugins` in `~/.claude/settings.json` | Yes |

**Optional connections** — only verify when Alex explicitly enables them for a session:
- MotherDuck (`MOTHERDUCK_TOKEN`) — check when starting DB work
- EODHD (`EODHD_API_KEY`) — check when starting data fetch work
- Add new services here as configured (MCP servers, new APIs, etc.)

**Report format:**
```
BOOT STATUS
GitHub       → [OK: alexbernal0 / FAIL: not authenticated]
SuperMemory  → [OK: plugin enabled / FAIL: disabled]
```

---

## SESSION START RITUAL

Execute these steps in order at the beginning of every session. Do not skip steps. Do not combine them into one vague "check."

### Step 1: Check MEMORY.md (auto-loaded)
MEMORY.md is always loaded. Review it actively, not passively.
- What is the active project?
- What was the last known state?
- Are there any open bugs, known issues, or flagged patterns relevant to today's work?
- Are there any VBT bugs, MotherDuck schema notes, or data integrity rules that apply to the current context?

### Step 2: Check for `.pending-supermemory-review` flag
Look in the project root and the `OBQ_Mother_Claude/` directory for `.pending-supermemory-review`.
- If the flag exists: review the previous session's output. Did it produce a breakthrough, a new pattern, a corrected approach, or a reusable template?
  - If yes: run `/super-save` to persist it to SuperMemory before it degrades.
  - If no: the flag was routine — delete it and continue.
- If the flag does not exist: proceed.

### Step 3: Read `tasks/lessons.md` — last 5 entries
This is the most important step for preventing repeated mistakes. Read the last 5 lessons. Internalize them before writing a single line of code.
- Are any of these lessons relevant to today's planned work?
- Is there a VBT bug that applies? A MotherDuck schema gotcha? A data integrity issue?
- If a lesson is directly relevant, acknowledge it in the session orientation.

### Step 4: Identify the active project
From MEMORY.md, NOW.md, context clues, open files, or by asking Alex.
- What is the project?
- What specifically is being worked on within that project?
- What files are relevant? What is the entry point?

### Step 5: Safety check
Before doing anything, scan for dangerous pre-existing states:
- Are there any open VBT backtests that may have been interrupted mid-run?
- Are there any MotherDuck write operations that may have been left incomplete?
- Is there a staging table that was never swapped to production?
- Are there any TODO items in `NOW.md` or `tasks/` that are marked started but not completed?
- Is there a `.env` file where it should be? Is the MotherDuck token likely still valid?

Flag any issues found before proceeding.

### Step 6: Orient and confirm
State clearly:

> "Working on [PROJECT]. Last session: [WHAT WAS DONE]. Current state: [WHERE WE ARE]. Ready to [NEXT LOGICAL STEP]."

If the current state is unclear, say so and ask Alex to confirm before starting work.

---

## MID-SESSION TRIGGERS

These are automatic stops. When any of these conditions appear in the work, stop and handle it immediately — do not continue past it.

| Trigger | Response |
|---|---|
| Any hardcoded value that should vary | "This should be a parameter. Moving to PARAMS dict." — move it immediately, do not defer |
| Any join on `quarter_date` for fundamentals | Stop. "Verify: should this be `filing_date`? Look-ahead bias risk if using quarter_date." — confirm before proceeding |
| Any unhandled NaN in a price or signal array | Add explicit guard before the computation. Do not proceed with NaN propagation. |
| Any loop over 100+ symbols or rows | "Is there a vectorized/SQL alternative?" — evaluate before committing to the loop |
| Any new backtest results | "Logging to `knowledge/backtest_results_log.md` now." — log immediately while the context is fresh |
| Any new bug discovered | "Adding to `tasks/lessons.md`." — log it immediately with date, symptom, root cause, fix |
| Any `size_type="percent"` with `cash_sharing=True` | "Use `from_order_func` pattern instead." — do not attempt to fix with `size_type="value"` as a workaround |
| Any write to `PROD_*` tables | "Writing to staging first. Will validate and swap." — never write directly to production |
| Any API key appearing in code (not env var) | Stop immediately. Move to `.env`. Check if it has been committed to git. |
| Any result that looks too good | "Check for look-ahead bias. Check for survivorship bias. Verify data alignment." — extraordinary results require extraordinary verification |
| Context length growing very large | "Spawning subagent for [task]." — delegate parallel research to preserve main context quality |

---

## SESSION END RITUAL

Do these before stopping. Every session. Without exception.

### Step 1: Capture what was accomplished
Write a concise bullet list:
- What was built / fixed / analyzed?
- What decisions were made?
- What was verified and confirmed working?

### Step 2: Update `NOW.md`
`NOW.md` is the live state file. It must reflect truth at session end:
- **Active Project:** current
- **Last Session Summary:** what was just done (3 bullets max)
- **Current Status:** exactly where things stand
- **Open Questions / Blockers:** anything unresolved
- **Next Steps:** the first 3 things to do next session, in order
- **Active Infrastructure:** any services, connections, or processes that are relevant

If `NOW.md` is not accurate at session end, the next session starts blind.

### Step 3: Write corrections and surprises to `tasks/lessons.md`
Any of these warrant a lessons.md entry:
- A bug that was not anticipated
- A VBT behavior that differed from expectations
- A MotherDuck schema issue that was discovered
- A data integrity problem that was found mid-session
- A correction Alex made to the approach
- A pattern that worked better than expected

Format:
```
## [DATE] — [BRIEF TITLE]
**Symptom:** What happened
**Root Cause:** Why it happened
**Fix:** What resolved it
**Prevention:** How to avoid it next time
```

### Step 4: If a backtest ran — verify `knowledge/backtest_results_log.md`
Every backtest result gets logged. Check that it includes:
- Strategy name and version
- Date range
- Universe (symbols / dataset)
- Key parameters
- Results: CAGR, Sharpe, MaxDD, Calmar, Trades
- Notes on any anomalies or interpretations

### Step 5: Evaluate for SuperMemory
Ask: did this session produce any of the following?
- A new reusable code pattern (e.g., a new VBT workaround)
- A corrected approach to a recurring problem
- A significant backtest result worth preserving
- A new data schema insight
- A template that will be used again

If yes: run `/super-save` and document what was saved and why.

### Step 6: Taskmaster Stop hook
The Taskmaster Stop hook fires automatically and verifies all todo items are either complete or explicitly deferred. If incomplete items exist, document them in `NOW.md` before the session ends.

### Step 7: session-checkpoint.sh fires
The `session-checkpoint.sh` hook fires automatically and creates `.pending-supermemory-review` in the project root. This flag will be checked at the next session start (Step 2 of Start Ritual).

---

## ESCALATION PROTOCOL

These actions require a pause and explicit confirmation from Alex before proceeding. Do not execute them autonomously.

| Action | Why It Requires Confirmation |
|---|---|
| Deleting files from any project directory | Irreversible. Confirm the file is not needed anywhere else. |
| Dropping or truncating database tables | Irreversible data loss. Even staging tables may have in-progress data. |
| Writing to `PROD_*` tables in MotherDuck | Production data. Mistakes affect live systems. |
| Force-pushing to any GitHub branch | Rewrites history. Could destroy others' work or break CI/CD. |
| Changes affecting more than 5 files at once | Scope has grown beyond what was discussed. Re-confirm the plan. |
| Architecture decisions affecting multiple projects | Cross-project decisions need deliberate review, not impulse. |
| Disabling or bypassing data validation | Validation exists for a reason. If it is wrong, fix the validation — don't skip it. |
| Modifying `.env` files | Key management is sensitive. Confirm before changing. |

---

## THE NORTH STAR

Every session exists to move OBQ closer to institutional-grade quantitative systems that are correct, reproducible, and production-ready.

When in doubt about whether to do something or how to do it, ask:

> "Would a senior quant at a tier-1 hedge fund approve this?"

If the answer is no, or if the answer is "I'm not sure," stop and resolve the uncertainty before proceeding.

---

HEARTBEAT.md | OBQ_Mother_Claude | Load: Always-on
