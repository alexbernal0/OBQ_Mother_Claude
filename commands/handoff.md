---
description: "Generate a session handoff summary for continuing work in a new session."
argument-hint: "[--save | --show]"
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /handoff — Session Handoff

Generate a compressed context summary so the next session picks up exactly where this one left off.

## Step 1 — Gather Context

```bash
echo "=== Git State ==="
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "not a git repo")
COMMIT=$(git log -1 --format='%h %s' 2>/dev/null || echo "N/A")
AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "?")
echo "Branch: $BRANCH | Last: $COMMIT | Ahead: $AHEAD"
git diff --stat HEAD 2>/dev/null
git ls-files --others --exclude-standard 2>/dev/null | head -10
echo "Machine: $(hostname) | $(date '+%Y-%m-%d %H:%M') | $(pwd)"
```

## Step 2 — Generate Handoff

Analyze the conversation + git data. Write this structure:

```markdown
# Session Handoff
<!-- Generated: YYYY-MM-DD HH:MM | Machine: hostname -->

## What Was Done
- [Accomplishments — specific files, features, fixes]

## Current State
- **Branch:** name (N ahead) | **Last commit:** hash — msg
- **Tests/Build:** status

## Next Steps (Start Here)
1. [First thing to do — specific enough to start cold]
2. [Second priority]
3. [Third priority]

## Files Modified
[git diff --stat or manual list]

## Context for Next Session
- [Env vars, running services, gotchas discovered]
```

## Step 3 — Save or Display

**--show**: Print to terminal only.

**--save** (default):
```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
mkdir -p "$PROJECT_ROOT/.claude"
```
Write handoff to `$PROJECT_ROOT/.claude/handoff.md`.

Also update `soul/NOW.md` with current task state and next steps.

If session produced significant learnings, trigger Supermemory save.

## Usage
```bash
/handoff          # Save handoff (default)
/handoff --show   # Display without saving
```
