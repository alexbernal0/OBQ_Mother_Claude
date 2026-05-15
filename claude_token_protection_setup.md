# Claude Code Token Protection Setup
**Date:** 2026-03-25  
**Author:** Alex Bernal, CTO — Obsidian Quantitative

---

## Problem
$3,000/month API bills from Claude Code (Opus 4.6) due to:
- Notebook stdout dumps (3–8K tokens each) injected raw into context
- Large sweep/optimization tables pulled into context in full
- Sub-agents running at Sonnet/Opus when Haiku would suffice
- Context bloat compounding across every turn in long sessions

---

## Solution Stack

### 1. RTK v0.33.1 (Rust Token Killer)
Compresses Bash command output 53–90% before Claude sees it.

**Installed at:** `C:\Users\admin\.local\bin\rtk.exe`  
**Repo:** https://github.com/rtk-ai/rtk  
**Mode:** CLAUDE.md injection (Windows — hook mode requires Unix)  
**PATH:** `C:\Users\admin\.local\bin` added to Windows user PATH permanently

**Reinstall steps:**
```powershell
# Download rtk-x86_64-pc-windows-msvc.zip from github.com/rtk-ai/rtk/releases
# Extract rtk.exe to C:\Users\admin\.local\bin\
rtk init -g --auto-patch   # re-inject CLAUDE.md instructions
```

**Verify:**
```bash
rtk --version        # should print version
rtk gain             # shows token savings history
rtk git status       # test compression (~60% savings)
```

---

### 2. CLAUDE.md Rules (Global — `C:\Users\admin\.claude\CLAUDE.md`)

Two sections added:

#### RESPONSE HEADER (NON-NEGOTIABLE)
Every response starts with: `> 🟢 RTK+COMPACT ACTIVE`  
Confirms token protection is running each turn.

#### Output Discipline (Token Laws)
- **Notebook stdout**: Execute → capture to `.txt` → read last ~60 lines only
- **Sweep tables**: Save to CSV first → read top-5 rows per direction only
- **Large reads**: Relevant section only, never full logs
- **Sub-agents**: `model: haiku` for research/explore — Sonnet/Opus for code only
- **After heavy output**: Suggest `/compact` immediately

---

### 3. Feedback Memory (Persistent)
Saved to: `C:\Users\admin\.claude\projects\c--Users-admin-Desktop-QGSI-Claude-Data-File\memory\feedback_notebook_output_discipline.md`  
Loaded automatically at session start — enforces output discipline rules across all future conversations.

---

## Cost Impact

| Model | Input | Output |
|---|---|---|
| Opus 4.6 (main) | $15/1M tokens | $75/1M tokens |
| Sonnet 4.6 (sub-agents) | $3/1M | $15/1M |
| Haiku 4.5 (research agents) | $0.80/1M | $4/1M |

| Driver | Before | After | Saving |
|---|---|---|---|
| Notebook stdout | ~40K tokens/session | ~2K (summary only) | -95% |
| Bash output (RTK) | raw | compressed ~55% | -55% |
| Sub-agent model | Sonnet | Haiku for research | -70% |
| Context bloat | compounding | cut at source | -65% |
| **Monthly estimate** | **~$3,000** | **~$750–1,050** | **~65–75%** |

---

## Settings Reference (`C:\Users\admin\.claude\settings.json`)

Key entries:
- `"model": "claude-opus-4-6"` — main model
- `"CLAUDE_CODE_SUBAGENT_MODEL": "claude-sonnet-4-6"` — sub-agents (override to haiku for research)
- `PostToolUse` hook: `compressor.py` on Bash/Read/Grep/Glob/WebFetch (already existed)
- `Stop` hooks: `taskmaster` + `session-checkpoint.sh`

---

## Maintenance

```bash
rtk gain              # check cumulative savings
rtk discover          # find commands where RTK wasn't used (missed savings)
/compact              # run manually when context feels heavy
```

Check Anthropic usage dashboard monthly: https://console.anthropic.com → Usage
