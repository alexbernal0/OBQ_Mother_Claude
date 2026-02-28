---
name: recursive-self-learning
description: "OBQ Recursive Self-Learning (RSL) system — the full loop: auto-capture lessons from session errors/corrections, crystallize repeated workflows into skills (auto-skill) and tools (auto-tool), synthesize memory monthly, propagate to SuperMemory. Use when explaining the RSL system, running /rsl-status, or onboarding to the OBQ learning loop."
---

# Recursive Self-Learning (RSL) — OBQ Intelligence Loop

> The system that transforms every session's errors, corrections, and discoveries into permanent improvements to OBQ's intelligence. Not theoretical — active on every session.

---

## What RSL Is

RSL is the closed feedback loop that makes OBQ's AI get better over time without human discipline. Each session automatically captures what was learned, promotes high-value discoveries to long-term memory, crystallizes repeated patterns into reusable skills and tools, and synthesizes accumulated knowledge monthly.

**The Gap RSL Fills:** The community has SuperMemory, basic-memory MCP, and the Ralph Loop — but no system automatically watches what Claude does, detects repeated workflows, and proposes crystallizing them into skills. OBQ built the crystallization layer that doesn't exist elsewhere.

---

## The Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: CAPTURE (automatic, session-level)                │
│  • auto-lesson: errors, corrections, surprises → lessons.md │
│  • auto-skill: repeated workflows → SKILL.md candidate       │
│  • auto-tool: repeated commands/scripts → tool candidate     │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: FLAG (Stop hook → session-checkpoint.sh)          │
│  • Creates .pending-supermemory-review in project root      │
│  • Preserved across context windows via filesystem          │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: REVIEW (next session HEARTBEAT Step 2)            │
│  • Was this session a breakthrough? New pattern? Template?  │
│  • Yes → /super-save to SuperMemory (cross-project memory)  │
│  • No → delete flag, continue                               │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: CRYSTALLIZE (auto-skill + auto-tool)              │
│  • Repeated workflow → SKILL.md (user or project level)     │
│  • Repeated command/script → tool in ~/.claude/tools/       │
│  • User approves before any file is written                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: SYNTHESIZE (monthly /synthesize-memory)           │
│  • Compress lessons.md → MEMORY.md higher-order insights    │
│  • Remove outdated patterns                                 │
│  • Cross-project pattern aggregation                        │
└─────────────────────────────────────────────────────────────┘
```

---

## The RSL Loop (Full Flow)

```
Session Work
    ↓
[mid-session] Errors, corrections, new patterns appear
    ↓ CLAUDE always does this at session end:
Write to tasks/lessons.md (standard format — date, symptom, root cause, fix, prevention)
    ↓
[task end] auto-skill silent check: Is this a crystallizable workflow?
           auto-tool silent check: Any commands/scripts repeated 3+ times?
    ↓
[Stop hook fires] session-checkpoint.sh creates .pending-supermemory-review
    ↓
[Next session HEARTBEAT Step 2]
Review .pending-supermemory-review:
  - Breakthrough / new pattern / corrected approach / template? → /super-save → delete flag
  - Routine session → delete flag → continue
    ↓
[Monthly] /synthesize-memory
  - Read last 20+ lessons.md entries
  - Compress into MEMORY.md higher-order patterns
  - Remove superseded or outdated entries
  - Update cross-project knowledge in SuperMemory
```

---

## Three Active Components

### 1. auto-lesson (behavioral rule — no skill file needed)

**What it does:** At session end, before stopping, Claude checks:
> "Were there any errors, corrections, unexpected behaviors, or new discoveries this session?"

If yes → write to `tasks/lessons.md` in standard format.

**Standard format:**
```markdown
## [DATE] — [BRIEF TITLE]
**Symptom:** What happened
**Root Cause:** Why it happened
**Fix:** What resolved it
**Prevention:** How to avoid it next time
```

**This is non-negotiable.** If it's in CLAUDE.md as a rule, it fires without being asked.

### 2. auto-skill (skill: `~/.claude/skills/auto-skill/`)

**What it does:** Silently monitors at every task completion for crystallizable workflows. Only surfaces the 4-option modal when a genuine candidate is found.

**Always-on mode:** Even without `/autoskill-on`, Claude performs the silent checklist at task end. The modal only appears if a clear candidate is detected. (The explicit `/autoskill-on` command makes it more aggressive — offers for borderline cases too.)

**Trigger criteria:**
- Multi-step workflow (3+ distinct steps) executed with clear inputs, outputs, and a nameable goal
- Pattern appeared 2+ times in this session or described as habitual by user
- Domain-specific procedure tied to project tools or conventions
- Complex enough that a new developer would need instructions to reproduce it

**Output:** SKILL.md written to `~/.claude/skills/` (user) or `.claude/skills/` (project)

### 3. auto-tool (skill: `~/.claude/skills/auto-tool/`)

**What it does:** Detects repeated commands, scripts, and processes that are candidates for extraction into reusable tools.

**Trigger criteria:**
- Same bash command or command pattern executed 3+ times in a session
- Same Python snippet (semantically equivalent) across 2+ files
- Same SQL query structure reused across 2+ contexts
- API call wrapper pattern repeated without abstraction

**Output:** Python script in `~/.claude/tools/[tool-name].py` (user-level) or `project/scripts/[tool-name].py` (project-level)

---

## Memory Hierarchy

| Memory Layer | What It Stores | Retention |
|---|---|---|
| `tasks/lessons.md` | Session-level errors, corrections, discoveries | Permanent until synthesized |
| `MEMORY.md` (auto-loaded) | Synthesized project-level patterns and decisions | Permanent |
| `~/.claude/CLAUDE.md` | Cross-project domain laws and anti-patterns | Permanent (manually updated) |
| SuperMemory (cloud) | High-value breakthroughs, reusable templates | Permanent, cross-project |
| `~/.claude/skills/` | Crystallized workflows as SKILL.md files | Permanent |
| `~/.claude/tools/` | Crystallized scripts and utilities | Permanent |

---

## What Gets Promoted to SuperMemory

Use `/super-save` when a session produces any of:

| Type | Example |
|---|---|
| New VBT workaround | `from_order_func` pattern that fixes a VBT bug |
| Corrected approach | Filing date vs quarter date for fundamental joins |
| Significant backtest | New strategy with CAGR/Sharpe/MaxDD results |
| Reusable template | New SKILL.md, new conftest.py, new data loader |
| Data schema insight | New MotherDuck table structure or join pattern |
| Architecture decision | Chose X over Y for Z reason |

Do NOT super-save: routine questions, minor fixes, one-time actions, anything project-specific that won't generalize.

---

## RSL Status Check — Run /rsl-status

The `/rsl-status` command shows:
- `.pending-supermemory-review` flag status
- `tasks/lessons.md` — entry count + last 3 entries
- Skills added this week
- Tools crystallized this month
- Days since last `/synthesize-memory`
- SuperMemory: last save date

---

## The Community Gap OBQ Fills

Based on deep research into the Claude Code ecosystem (February 2026):

| What the Community Has | What OBQ Built |
|---|---|
| SuperMemory (manual save) | auto-lesson capture (automatic) |
| basic-memory MCP (write-when-prompted) | RSL loop (structured, automatic at edges) |
| Ralph Loop (human-maintained AGENTS.md) | auto-skill + auto-tool (automated crystallization) |
| recall/session-restore (raw search) | synthesize-memory (semantic compression) |

The **crystallization layer** — automatically detecting repeated patterns and proposing skill/tool extraction with user approval — does not exist in open source. OBQ's auto-skill + auto-tool combination is the community's missing layer.

---

## Integration With OBQ Projects

All OBQ projects gain RSL when they have:
1. `tasks/lessons.md` — lesson capture target
2. `tasks/` folder — RSL control plane
3. Project-level MEMORY.md — synthesized output destination

RSL fires across all projects in the Active Projects table in CLAUDE.md.

---

*RSL | OBQ_Mother_Claude | v1.0 | 2026-02-28*
