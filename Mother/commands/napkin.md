---
description: "Create or update a per-project napkin runbook with architecture, gotchas, state, and conventions."
argument-hint: "[init | show | add \"note\" | prune]"
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /napkin — Project Napkin Runbook

A `.claude/napkin.md` per project — curated context the AI needs. Max 10 items per category. Under 500 tokens.

## Setup

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
PROJECT_NAME=$(basename "$PROJECT_ROOT")
NAPKIN="$PROJECT_ROOT/.claude/napkin.md"
```

## init — Create Napkin

Analyze project (package.json, pyproject.toml, README, git log, directory structure), then write:

```markdown
# Napkin — [project-name]
<!-- Updated: YYYY-MM-DD | Keep under 500 tokens -->

## Architecture
- [Key stack and service structure]

## Active Gotchas
- [Things that will bite you]

## Current State
- [Branch, in-progress work, blockers]

## Conventions
- [Coding standards, naming, file organization]
```

Save to `$NAPKIN`.

## show (default) — Display current napkin

## add "note" — Add to appropriate category, flag if >10 items

## prune — Review and remove stale/redundant items

## Usage
```bash
/napkin              # Show current napkin
/napkin init         # Create napkin for this project
/napkin add "note"   # Add note to napkin
/napkin prune        # Remove stale items
```
