---
name: code-indexer
description: "Codebase RAG indexer and context-aware code review. Indexes Python codebases into Supermemory for cross-session retrieval. Replaces re-reading entire files — search for exact functions, patterns, and architecture. Use before any code audit, refactor, or review session."
compatibility: "Claude Code (VSCode + CLI), OpenCode"
metadata:
  author: OBQ
  source: OBQ AI Development Infrastructure
  updated: "2026-04-01"
  version: "1.0"
  allowed-tools: "Read, Bash, Grep, Glob, Write, Edit"
---

# CODE INDEXER — Codebase RAG for Development Sessions

Indexes OBQ Python codebases into Supermemory so every session starts with
full code context already loaded. Eliminates the #1 source of token burn:
re-reading entire files from scratch every session.

---

## WHAT THIS REPLACES

| Before (no indexer) | After (indexed) |
|---|---|
| Read 1,514 lines of scanner_engine.py | `/super-search "scanner scoring"` → 10 relevant chunks |
| 10,000+ input tokens per audit start | ~2,000 tokens for same context |
| Agent re-discovers architecture each time | Architecture in Supermemory, retrieved instantly |
| Deep agent times out reading 20 files | Deep agent gets pre-digested context |

---

## WHEN TO USE

- **Before any code audit or review** — index first, then audit
- **After major refactors** — re-index changed files
- **Starting a new project** — index once at onboarding
- **Before delegating to subagents** — ensure context is available

---

## HOW IT WORKS

### Phase 1: Index (run once per project, re-run on changes)

```bash
python C:\Users\admin\Desktop\MotherV4\Mother\tools\codebase_indexer.py \
  --project "C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_OptionsApp" \
  --name "OBQ_OptionsApp"
```

**What it does:**
1. Walks all `.py` files in the project (skips `__pycache__`, `.git`, `cache/`, `logs/`)
2. Parses each file with `ast` module — extracts every class, function, and top-level assignment
3. Builds **chunks**: each function/class becomes a chunk with metadata:
   - `file_path` — relative path from project root
   - `function_name` — qualified name (Class.method or function)
   - `line_start` / `line_end` — exact location
   - `imports` — what this function imports/uses
   - `docstring` — if present
   - `code_body` — the actual source code (trimmed to 800 chars for embedding)
   - `signature` — function signature with args and return type
4. Saves chunks to Supermemory via API with scope=project, type=architecture
5. Also saves a local JSON index at `{project}/.code_index.json` for offline queries

### Phase 2: Query (every session, every subagent)

```bash
# From OpenCode:
/super-search "scanner_engine _score_contract scoring methods"
/super-search "DuckDB connection pattern in scanner"
/super-search "how does _derive_metrics calculate EV"

# Or programmatically in a skill prompt:
# "Search Supermemory for: scanner edge_score calculation"
```

### Phase 3: Review (use indexed context for audits)

When running `/code-review` or any audit task:
1. Query Supermemory for the target module's indexed chunks
2. Get exact function bodies, not entire files
3. Audit with full context but minimal token burn
4. Flag issues with exact file:line references (from index metadata)

---

## INDEX OUTPUT FORMAT

Each chunk saved to Supermemory:

```
[OBQ_OptionsApp] scanner_app/scanner_engine.py :: _score_contract (L:245-L:398)
Scores a single options contract using one of 12 methods: naked_sell, iv_context,
prob_ev, spread_credit, spread_debit, strangle, straddle, condor, butterfly, calendar, composite.
Dispatches by strategy['scoring'] field. Returns float score 0-100.

SIGNATURE: def _score_contract(row: dict, strategy: dict, indicators: dict) -> float
IMPORTS: math, numpy
CALLS: _iv_context_multiplier(), _edge_score()
---
[full function body, trimmed to 800 chars]
```

---

## LOCAL INDEX FILE

`{project}/.code_index.json`:

```json
{
  "project": "OBQ_OptionsApp",
  "indexed_at": "2026-04-01T09:40:00Z",
  "files": 65,
  "chunks": 342,
  "total_lines": 22697,
  "index": [
    {
      "file": "scanner_app/scanner_engine.py",
      "name": "_score_contract",
      "type": "function",
      "line_start": 245,
      "line_end": 398,
      "signature": "def _score_contract(row, strategy, indicators)",
      "docstring": "Score a single contract...",
      "imports": ["math", "numpy"],
      "calls": ["_iv_context_multiplier", "_edge_score"],
      "code_preview": "def _score_contract(row, strategy, indicators):\n    scoring = strategy.get('scoring', 'composite')..."
    }
  ]
}
```

---

## INTEGRATION WITH AUDIT WORKFLOW

### Pre-Audit Checklist
1. `python codebase_indexer.py --project <path> --name <label>` (if not already indexed)
2. Check `.code_index.json` exists and is recent
3. Query Supermemory for target module before reading raw files
4. Only read raw files for the specific lines flagged by audit

### Subagent Delegation Pattern
When delegating code audit to a deep/ultrabrain agent:
```
CONTEXT: The codebase is indexed in Supermemory as "OBQ_OptionsApp".
Before reading any file, search Supermemory for relevant functions.
Local index at: {project}/.code_index.json — read this first for file map.
Only read raw files for functions you need to audit line-by-line.
```

This cuts subagent token burn by 60-70% on large codebases.

---

## RE-INDEXING

Run the indexer again whenever:
- Files are added/removed
- Major refactors change function signatures
- After a PR merge that touches core modules

The indexer is **idempotent** — re-running overwrites the previous index.
Supermemory deduplicates by content hash automatically.

---

## TOOL LOCATION

```
C:\Users\admin\Desktop\MotherV4\Mother\tools\codebase_indexer.py
```

Also deployed to: `C:\Users\admin\.claude\skills\code-indexer\`
