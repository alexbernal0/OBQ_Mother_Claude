# Mother System Session Handoff
**Date:** 2026-04-15  
**Session:** Full Mother upgrade + SDD system + DeepResearch reorganization  
**Status:** Partially complete — DeepResearch test run NOT yet done

---

## What Was Completed This Session

### 1. Mother v4.1 Upgrades (all live, restart required for hooks)

| Component | Location | Status |
|---|---|---|
| `auto-review` skill | `~/.claude/skills/auto-review/` | ✅ Live |
| `skill-scan` skill | `~/.claude/skills/skill-scan/` | ✅ Live |
| `harden-code` skill + command | `~/.claude/skills/harden-code/` + `~/.claude/commands/harden-code.md` | ✅ Live |
| `compound-knowledge` skill | `~/.claude/skills/compound-knowledge/` | ✅ Live |
| `housekeeping` command | `~/.claude/commands/housekeeping.md` | ✅ Live |
| `napkin` command (prune mode) | `~/.claude/commands/napkin.md` | ✅ Live |
| `durable-plans` skill (SDD enforcer) | `~/.claude/skills/durable-plans/` | ✅ Live |
| `run-deep-research` skill | `~/.claude/skills/run-deep-research/` | ✅ Live |

### 2. Hooks (activate after OpenCode restart)

| Hook | Event | File | Status |
|---|---|---|---|
| `block-sensitive-files.py` | PreToolUse | `~/.claude/hooks/` | ✅ Registered |
| `capture_error_fix.py` | PostToolUse | `~/.claude/hooks/` | ✅ Registered |
| `detect_learning_signal.py` | UserPromptSubmit | `~/.claude/hooks/` | ✅ Registered |
| `session_checkpoint.py` | Stop | `~/.claude/hooks/` | ✅ Registered |

### 3. SDD Spec System (all 4 projects)

| Project | Spec Location | Status |
|---|---|---|
| JCN Dashboard | `JCNDashboardApp/.spec/` | ✅ Full spec (config.yaml + ARCHITECTURE.md) |
| OBQ_AI_OptionsApp | `OBQ_AI/OBQ_AI_OptionsApp/.spec/` | ✅ Full spec |
| Muthr.ai | `Muthr.ai/.spec/` | ✅ Full spec |
| OBQ_AI_DeepResearch | `OBQ_AI/OBQ_AI_DeepResearch/.spec/` | ✅ Full spec |

Spec commands: `/spec:propose`, `/spec:design`, `/spec:apply`, `/spec:archive`

### 4. Data Topology (immutable guardrails)

`~/Desktop/MotherV4/Mother/system/DATA_TOPOLOGY.md` — verified data sources per app.
Key finding: **OBQ_AI_OptionsApp has ZERO MotherDuck connections** (100% local DuckDB).
`block-sensitive-files.py` enforces cross-app DB write prohibitions at hook level.

### 5. Mother Widget (v4.1)

`~/Desktop/MotherV4/Mother/system/mother_widget.py`  
Launch: `pythonw ~/Desktop/MotherV4/Mother/system/mother_widget.py`  
OR: `~/Desktop/MotherV4/Mother/system/launch_mother_widget.bat`

New sections: SDD SPECS (4 projects, green/yellow/red), Persistent Systems, all 12 commands panel.

### 6. DeepResearch Reorganization (PARTIAL — test run pending)

**Completed:**
- Archived 39 `_*.py` scripts → `_archive/research_scripts/`
- Archived 7 `knowledge/` utility scripts → `_archive/knowledge_utils/`
- Archived 2 unused graphs → `_archive/unused_graphs/`
- Deleted nested duplicate `OBQ_AI/OBQ_AI_DeepResearch/` (47 dead files)
- Added 3 quality modules: `agents/claim_verifier.py`, `agents/report_scorer.py`, `agents/iterative_deepener.py`
- Fixed 3 pre-existing syntax errors (synthesizer.py, dd_graph.py, quant_research_graph.py)
- Removed `langgraph` from requirements.txt (not used)
- Restored LangChain as LLM adapter layer (correct — `llm.invoke()` pattern throughout graphs)
- 62 files syntax clean, 0 errors

**NOT completed (next session):**
- Wire claim_verifier + report_scorer into `gui/api/research_api.py` post-synthesis
- Test run on-demand research via `run-deep-research` skill
- Archive spec change (`/spec:archive cleanup-langchain-reorganize`)

---

## Active Spec Changes

| Project | Slug | Status |
|---|---|---|
| OBQ_AI_DeepResearch | `cleanup-langchain-reorganize` | ✅ Applied, needs `/spec:archive` |

---

## Next Session — Immediate Actions

1. **Launch widget:** say "launch widget"
2. **Wire quality modules into research_api.py** — find the synthesis completion point and add:
   ```python
   # After synthesis completes, in research_api.py
   try:
       from agents.report_scorer import ReportScorer
       scorer = ReportScorer()
       score = await scorer.score_report(query=topic, report=synthesis_text, sources=sources)
       # Add score to run result / event stream
   except Exception as e:
       logger.warning(f"Scoring failed (non-fatal): {e}")
   ```
3. **Test run:** "research: what are the best iron condor entry timing signals using VIX term structure"
4. **Archive spec:** `/spec:archive cleanup-langchain-reorganize`

---

## Key File Locations

```
Mother widget:          ~/Desktop/MotherV4/Mother/system/mother_widget.py
DATA_TOPOLOGY:          ~/Desktop/MotherV4/Mother/system/DATA_TOPOLOGY.md
All skills:             ~/.claude/skills/
All commands:           ~/.claude/commands/
settings.json (hooks):  ~/.claude/settings.json
JCN spec:               ~/Desktop/JCNDashboardApp/.spec/
OptionsApp spec:        ~/Desktop/OBQ_AI/OBQ_AI_OptionsApp/.spec/
Muthr.ai spec:          ~/Desktop/Muthr.ai/.spec/
DeepResearch spec:      ~/Desktop/OBQ_AI/OBQ_AI_DeepResearch/.spec/
run-deep-research skill:~/.claude/skills/run-deep-research/SKILL.md
DeepResearch app:       ~/Desktop/OBQ_AI/OBQ_AI_DeepResearch/
  Quality modules:      .../agents/claim_verifier.py
                        .../agents/report_scorer.py
                        .../agents/iterative_deepener.py
  Archive:              .../archive/  (39 scripts, 7 utils, 2 graphs)
This handoff:           ~/Desktop/MotherV4/Mother/system/SESSION_HANDOFF_2026-04-15.md
```

---

## Skills Now Available (full list)

```
auto-review          — code review with OBQ data law enforcement
skill-scan           — community skill discovery
harden-code          — 3-agent adversarial code audit
compound-knowledge   — capture solved problems to docs/solutions/
durable-plans        — SDD enforcer (reads .spec/ before any code task)
run-deep-research    — on-demand research from any chat
housekeeping         — weekly/daily maintenance
napkin               — per-project runbook with prune mode
(+ all original 30 OBQ skills)
```

---

## How to Use run-deep-research in Next Chat

Simply say in any OpenCode session:
> "Research: what are the best iron condor entry timing signals using VIX term structure"

Or:
> "Deep research on OBQ factor momentum strategies — STANDARD mode"

The `run-deep-research` skill auto-loads and handles everything.
Requires: OBQ_AI_DeepResearch app running at :5001 OR will attempt headless subprocess.

**Skill location:** `~/.claude/skills/run-deep-research/SKILL.md`
