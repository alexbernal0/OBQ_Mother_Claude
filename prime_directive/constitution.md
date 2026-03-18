# Constitution — Machine-Readable Prime Directive

> **IMMUTABLE REFERENCE** — This document derives from and is subordinate to:
> `../Prime Directive/Prime_Directive.pdf`
>
> Any conflict between this file and the PDF: **the PDF wins**.

---

## System: OBQ Intelligence

**Purpose**: Quantitative research platform for signal development, backtesting, and data engineering. Serves OBQ's research workflow from raw market data ingestion through validated strategy deployment and live dashboard presentation.

---

## Canonical Entities

| Entity | Role | Boundary |
|--------|------|----------|
| **MotherDuck** | Data layer — cloud DuckDB warehouse | Owns PROD_EODHD, GoldenOpp, qgsi schemas. Single source of truth for validated data. |
| **VBT Strategies** | Execution layer — vectorbt backtesting | Owns strategy logic, signal evaluation, portfolio simulation. No direct data writes. |
| **EODHD Pipeline** | Ingestion layer — market data acquisition | Owns API calls, rate limiting, staging tables (DEV_EODHD_DATA). Writes only to staging. |
| **JCN Dashboard** | Presentation layer — Vercel web dashboard | Owns display logic. Read-only access to MotherDuck prod tables. |

---

## Communication Law (INVIOLABLE)

```
EODHD API (external)
 → DuckDB staging (DEV_EODHD_DATA)    [raw ingestion, rate-limited]
  → Validation layer                    [quality checks, dedup, bias prevention]
   → MotherDuck prod (PROD_EODHD)      [validated, immutable once written]
    → JCN Dashboard (read-only)         [presentation to end users]
```

**Rules that CANNOT be violated:**
1. Raw data never goes directly to prod — must pass through staging + validation
2. adjusted_close only — never raw close (split/dividend bias)
3. filing_date only — never quarter_date (look-ahead bias)
4. No survivorship bias — delisted symbols must be included in all universes

---

## Success Criteria (What We Optimize For)

1. **No look-ahead bias**: Every signal uses only data available at decision time. filing_date enforced, no future data leakage.
2. **Reproducible backtests**: Same parameters + same data = same results. Deterministic pipelines, versioned datasets.
3. **Validated data**: Every record passes schema validation, dedup, and sanity checks before reaching prod.
4. **Documented strategies**: Every strategy has a paper reference, parameter rationale, and out-of-sample test results.

---

## Override Protocol

When any proposed action conflicts with this constitution:

1. **STOP** — Do not proceed
2. **WARN** — Cite the specific section being violated
3. **REQUEST** — Ask for explicit system override with justification
4. **LOG** — If override granted, append to `governance/overrides.log`

```
WARNING: PRIME DIRECTIVE CONFLICT

Section: [which section]
Proposed Action: [what was requested]
Conflict: [why it violates the directive]

To proceed, confirm: "SYSTEM OVERRIDE: [justification]"
```

---

## Document Hierarchy

1. **Prime_Directive.pdf** — Immutable source of truth (read-only)
2. **constitution.md** — Machine-readable derivative (this file)
3. **Project CLAUDE.md files** — Project-specific rules (subordinate to constitution)

Lower levels cannot contradict higher levels. Conflicts escalate upward.
