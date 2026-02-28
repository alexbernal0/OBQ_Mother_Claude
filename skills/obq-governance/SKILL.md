---
name: obq-governance
description: "OBQ governance rules Claude applies automatically — data integrity laws, production write protocols, override procedures, and escalation path. Background knowledge that shapes all OBQ work."
user-invocable: false
---

## OBQ Governance Rules

This skill is loaded as background knowledge. Claude applies these rules automatically across all OBQ work without being explicitly asked.

---

## 1. DATA INTEGRITY LAWS

These laws are non-negotiable and are enforced on every query, join, and signal computation:

- **NEVER use `quarter_date` for fundamental joins** — always use `filing_date`. Quarter date is the period end; filing date is when the data became available. Using quarter_date introduces look-ahead bias.
- **NEVER use raw `close` for historical analysis** — always use `adjusted_close`. Raw close contains split and dividend distortions that create false signals.
- **NEVER introduce look-ahead bias** — all signals must use only data available at signal time. Signals must be shifted forward by at least 1 bar before position sizing. Stop levels must use prior-bar ATR values.
- **NEVER include survivorship bias** — the historical universe must include delisted symbols. Use `PROD_EOD_survivorship` (which is survivorship-bias-free) not filtered symbol lists.
- **ALWAYS validate data before MotherDuck writes** — check row counts, date ranges, null rates, and schema match before any INSERT or CREATE TABLE AS.

---

## 2. PRODUCTION WRITE PROTOCOL

For any write to a table prefixed `PROD_*`:

1. **STOP** before executing the write.
2. Confirm with Alex: "About to write **[N rows]** to **[PROD_TABLE]**. Verified: schema matches, no duplicates, count plausible. Proceed?"
3. If Alex confirms: write to a `DEV_*` staging table first, verify the output, then promote to PROD.
4. Never skip the DEV staging step for large or complex transformations.

---

## 3. OVERRIDE PROTOCOL

When a user request conflicts with a governance rule:

1. **STOP execution immediately.**
2. State specifically which rule is triggered, e.g.: "DATA INTEGRITY LAW: This query uses `quarter_date` for a fundamental join."
3. Request explicit override: "To proceed, please say: SYSTEM OVERRIDE: [your justification]"
4. If Alex grants the override: log to `governance/overrides.log` with the format below, then proceed.
5. If Alex does not explicitly grant the override: do not proceed with the rule-violating action.

### Overrides Log Format

```
[YYYY-MM-DD HH:MM] OVERRIDE: [rule violated] | Justification: [reason] | Approved by: Alex
```

---

## 4. ESCALATION PATH

Pause and explicitly confirm with Alex before proceeding with any of the following:

- Deleting or overwriting files without an explicit request to do so
- Writing to MotherDuck `PROD_*` tables (see Production Write Protocol above)
- Force-pushing to any GitHub remote
- Changes that affect 5 or more files simultaneously
- Architecture decisions that affect multiple projects (e.g., schema changes, new table conventions, dependency additions)

For escalation items, state clearly: "This action requires confirmation: [describe the action and its scope]. Proceed?"

---

## 5. AUTOMATIC BACKGROUND ENFORCEMENT

Claude applies these rules proactively — not only when asked. Examples:

- When writing a query: automatically check that join keys use `filing_date`, not `quarter_date`
- When building a signal: automatically verify `.shift(1)` is applied before position entry
- When suggesting a universe: recommend `PROD_EOD_survivorship` as the source
- When a backtest result looks too good: flag Sharpe > 3 or CAGR > 40% for look-ahead bias review
- When a file write targets `.env` or `secrets.*`: block via hook (see hooks/block-sensitive-files.py)
