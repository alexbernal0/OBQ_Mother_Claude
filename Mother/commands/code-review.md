---
description: "Index a codebase and run a full senior-engineer code audit with RAG-assisted context."
argument-hint: "<project-path> [--reindex] [--audit-only] [--index-only]"
allowed-tools: "Bash, Read, Write, Edit, Glob, Grep"
---

# /code-review — RAG-Assisted Codebase Audit

Full senior-engineer audit powered by codebase indexing. Indexes once, reviews
with full context, minimal token burn.

## Arguments

- `<project-path>` — Path to the project root (required)
- `--reindex` — Force re-index even if `.code_index.json` exists
- `--audit-only` — Skip indexing, use existing index
- `--index-only` — Index only, don't run audit

## Workflow

### Step 1: Index (or verify existing index)

```bash
PROJECT_PATH="$1"
INDEX_FILE="$PROJECT_PATH/.code_index.json"
INDEXER="C:\Users\admin\Desktop\MotherV4\Mother\tools\codebase_indexer.py"
```

Check if index exists and is less than 24h old:
- If missing or stale or `--reindex` flag: run `python $INDEXER --project $PROJECT_PATH`
- If fresh: skip, report "Using existing index (N chunks, indexed at T)"

### Step 2: Load Architecture Map

Read `.code_index.json` and build a summary:
- Total files, total functions/classes, total lines
- Top 10 largest files (by line count)
- Top 10 most-connected functions (most imports/calls)
- Any functions over 50 lines (refactor candidates)
- Any files with no docstrings (documentation gaps)

Present this as the **Architecture Map** before auditing.

### Step 3: Audit (phased)

Load the `python-debug` and `options-scanner-arch` skills (or equivalent for the target project).

**Phase 1 — Critical Path Audit:**
Identify the 5 most important files (by connectivity + size) from the index.
For each: read the file, check for:
- BUGS: unhandled exceptions, None access, incorrect math, race conditions
- EDGE CASES: division by zero, empty data handling, missing column checks
- DEAD CODE: unused functions, unreachable branches
- HARDENING: missing try/except on I/O, input validation, SQL injection
- PERFORMANCE: unnecessary copies, N+1 queries
- TYPE SAFETY: variables that could be None but aren't checked
- RESOURCE LEAKS: unclosed connections, file handles

**Phase 2 — Secondary Files:**
Audit remaining files with lighter touch — focus on:
- Resource leaks
- Error handling
- Dead code

**Phase 3 — Test Coverage Gap Analysis:**
Cross-reference index with test files:
- Which functions have tests?
- Which functions are untested?
- Which tests are stale (testing functions that no longer exist)?

### Step 4: Report

Write `{project}/AUDIT_REPORT.md`:

```markdown
# Code Audit Report — {project_name}
**Date:** YYYY-MM-DD
**Indexed:** N files, M functions, L lines

## Architecture Summary
[from index]

## Critical Bugs (fix immediately)
| File | Line | Issue |
|------|------|-------|

## Warnings (fix soon)
| File | Line | Issue |
|------|------|-------|

## Info / Improvements
| File | Line | Issue |
|------|------|-------|

## Dead Code
| File | Function | Lines |
|------|----------|-------|

## Test Coverage Gaps
| Function | File | Status |
|----------|------|--------|

## Refactor Candidates (>50 lines)
| Function | File | Lines | Reason |
|----------|------|-------|--------|
```

### Step 5: Confirm

Report summary to user:
- N critical bugs, M warnings, K info items
- X functions untested
- Y functions need refactoring
- Ask: "Ready for Phase 2 fixes, or review the report first?"
