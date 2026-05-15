# PRINCIPLES.md — Decision Playbook

> *How to decide when things get messy. Decision heuristics, domain laws, anti-patterns, and institutional memory. The tactical playbook.*

---

## When Principles Collide

| Conflict | Winner | Why |
|----------|--------|-----|
| Correctness vs Speed | **Correctness** | Fast + wrong = expensive |
| Shipping vs Elegance | **Shipping** | Unless it's a foundation |
| New Feature vs Tech Debt | **Tech debt** | If it blocks the feature |
| Your Inference vs User's | **User** | They have context you don't |
| Safety vs Convenience | **Safety** | Past incidents prove this |

---

## Operating Principles (Non-Negotiable)

### 1. Plan Before Building
For 3+ steps or architectural decisions: stop, plan, confirm. Write to `tasks/todo.md`. Include failure modes, timeouts, retry strategy.

### 2. Use Subagents — Right-Sized
Offload research and exploration to subagents. One task per subagent. Keep main context clean.
**Before firing any agent**: Can I answer this with a direct tool (Read/Grep/Edit)? If yes — do it directly.
**Hard limit**: MAX 3 background agents simultaneously. Fire in batches, wait for system-reminder, cancel after collecting.
**Cancel immediately**: background_cancel(taskId="...") after every result collected — no zombie accumulation.
**Model routing**: explore/librarian → gpt-4o-mini (cheap). oracle/deep → grok-4 (reasoning). sisyphus → claude-sonnet. compaction → claude-haiku.

### 3. Self-Improvement Loop
After ANY correction: update `tasks/lessons.md` immediately. Write rules that prevent repetition.

### 4. Verify Before Done
Never mark complete without proof. Backtest: verify no look-ahead bias. Data: verify schema. Pipeline: verify output counts.

### 5. Minimal Impact
Bug fix changes only the bug. Feature adds only the feature. No extra abstractions.

### 6. Safety Limits Are Sacred
- Never remove/reduce cost limits without discussion
- Safety limits exist because of past costly incidents
- The config file is source of truth — don't patch around it

---

## OBQ Data Laws (Non-Negotiable)

### Financial Data Integrity
```
CRITICAL: adjusted_close only — never raw close
CRITICAL: filing_date only — never quarter_date (look-ahead bias)
CRITICAL: Symbol (capital S) in all column references
CRITICAL: No survivorship bias — include delisted symbols
CRITICAL: Validate before writing to MotherDuck
```

### DuckDB / MotherDuck
```
CRITICAL: Single-writer — concurrent writes fail silently
CRITICAL: Symbol format: MotherDuck = TICKER.US, display = TICKER — always normalize
CRITICAL: Schema: PROD_EODHD.main.PROD_* (prod) | GoldenOpp.* | qgsi.* | DEV_EODHD_DATA.* (staging)
CRITICAL: MOTHERDUCK_TOKEN from env var only
CRITICAL: Confirm environment (dev/staging/prod) before ANY write
```

### VectorBT 0.28.x
```
CRITICAL: size_type="percent" + cash_sharing=True → CRASHES. Use from_order_func with Numba.
CRITICAL: size_type="percent" = % of CASH not portfolio. Use c.value_now inside order func.
CRITICAL: Negative prices → crash. Filter (close > 0) BEFORE clipping to 0.0001.
```

### API Rate Limits
```
WARNING: EODHD — 1000 calls/min, 100K/day → RateLimiter(delay=0.06). Key in .env.
WARNING: All LLM keys in .env: ANTHROPIC_API_KEY, XAI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY
WARNING: No hardcoded API keys. No empty except blocks. Keys in .env only.
```

---

## Anti-Pattern Catalog

| Anti-Pattern | Why It Fails |
|--------------|--------------|
| "Quick abstraction" | 3 similar lines > premature abstraction |
| "Handle edge case later" | Edge cases are where production breaks |
| "Works in my test" | Test with concurrent execution or it's not tested |
| Remove cost limits "just for this" | Past costly incidents |
| Skip plan mode | 15 files changed → architecture wrong → start over |
| One mega-session | Long conversations degrade quality. One task per session. |
| Empty catch blocks | Silent failures compound |
| Delete failing tests to "pass" | Lying to yourself |
| Raw close instead of adjusted_close | Splits/dividends corrupt every downstream calc |
| quarter_date instead of filing_date | Look-ahead bias invalidates backtest |
| Reflexive parallelization | Firing explore+librarian+oracle on every task → OpenCode freezes, zombie processes |
| Zombie agent accumulation | Collecting result without background_cancel(taskId="...") → 15+ python procs, event loop block |
| Re-delegation | Firing explore for code already read this session → wasted tokens + duplicate work |
| >3 concurrent background tasks | API response queue backs up → opencode-cli bloats to 1GB+ → UI freeze |

---

## Institutional Memory

### The VBT Cash Sharing Crash
**What happened:** Used size_type="percent" with cash_sharing=True in VectorBT 0.28.x
**Result:** Silent crash — no error, just wrong results or hard failure
**Permanent fix:** Always use from_order_func with Numba for multi-asset portfolios
**Lesson:** VBT's percent sizing refers to cash, not portfolio value. Use c.value_now.

### The Look-Ahead Bias Incident
**What happened:** Used quarter_date instead of filing_date for fundamental data
**Result:** Backtest showed unrealistic alpha — data was available before it was public
**Permanent fix:** filing_date only, enforced at data loading layer
**Lesson:** Temporal alignment is non-negotiable in financial data.

---

## The 80/20 Rule

**80% of bugs:** Look-ahead bias, survivorship bias, wrong price field, Symbol casing
**80% of value:** Clean data pipelines, bias-free universes, reproducible backtests
**80% of waste:** Premature abstraction, over-engineering, optimizing before deleting

---

## The Algorithm

Every task, in order:
1. **Make requirements less dumb** — Question if it should exist
2. **Delete the part or process** — Best code is no code
3. **Simplify and optimize** — Only after deletion fails
4. **Accelerate cycle time** — Speed up what survives
5. **Automate** — Last step, not first

> *"If you're not adding things back 10% of the time, you're not deleting enough."*

---

*PRINCIPLES.md | Mother Soul Framework | Load: Always-on*
