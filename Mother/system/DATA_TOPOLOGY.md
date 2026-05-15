# OBQ Data Topology — Immutable Source of Truth
# ============================================================
# HUMAN-ONLY — AI reads this file. Never modifies it.
# Update only when a data source intentionally changes.
# Last verified: 2026-04-12
# ============================================================

## The Cardinal Rule

> **Every app owns its data source. No app writes to another app's database. Ever.**
> Cross-database reads require explicit spec entry. Cross-database writes are PROHIBITED.

---

## Verified Data Sources Per App

### JCN Financial Dashboard
```
Source:   EODHD API → MotherDuck PROD_EODHD (canonical pipeline)
Pipeline: api/sync_stage0.py → stage1 (ingest) → stage2 (promote) → stage3 (audit)
Writes:   DEV_EODHD_DATA.* (staging) → PROD_EODHD.main.PROD_* (production)
Reads:    PROD_EODHD.main.PROD_* | GoldenOpp.* | qgsi.* | PROD_SYNC_LOG
Token:    MOTHERDUCK_TOKEN (env only)
NEVER:    Write to EODHD_Options.* | Write to any other app's schema
```

### OBQ_AI_OptionsApp
```
Source:   LOCAL DuckDB ONLY — no MotherDuck, no live API sync
Primary:  D:/OBQ_AI/obq_options_data.duckdb
          Tables: options_sorted (416M rows), stage1/2/3_results, sweep_runs,
                  spy_regime_daily, universe_iv_regime
Secondary: D:/OBQ_AI/obq_ai.duckdb
          Tables: vix_curve, underlying OHLCV
Origin:   Historical EODHD bulk download (one-time). Not a daily sync.
          options_sorted was built from EODHD Marketplace options data.
NEVER:    Connect to MotherDuck | Write to JCN's PROD_EODHD | Write to EODHD_Options.*
NEVER:    Read from Muthr.ai's EODHD_Options — use local options_sorted instead
```

### Muthr.ai
```
Source:   EODHD Marketplace API → MotherDuck EODHD_Options database
Pipeline: scripts/download_options.py (local run) → MotherDuck EODHD_Options
Writes:   EODHD_Options.main.EODHD_OPTIONS_EOD
          EODHD_Options.main.EODHD_OPTIONS_CONTRACTS
          EODHD_Options.main.EODHD_OPTIONS_SYNC_LOG
Reads:    EODHD_Options.* (own schema only)
API:      api/options_sync.py — READ-ONLY monitoring layer
Token:    MOTHERDUCK_TOKEN (env only)
NEVER:    Write to PROD_EODHD.* | Write to GoldenOpp.* | Write to qgsi.*
NEVER:    Read from D:/OBQ_AI/*.duckdb (OptionsApp local files)
```

### OBQ_AI_DeepResearch
```
Source:   Web/API/GitHub/Financial news (fetched at research time)
Memory:   LanceDB local — D:/OBQ_AI/deep_research_kb/lancedb/
          SuperMemory API (cross-session agent improvement)
Output:   knowledge/ folder (research docs), PDF reports
NEVER:    Write to PROD_EODHD.* | Write to EODHD_Options.* | Touch OptionsApp local DBs
NEVER:    Touch JCN's MotherDuck pipeline tables
```

### OBQ_EH_v1
```
Status:   ARCHITECTURE BEING REBUILT — do not integrate data sources with other apps
          Until rebuild complete: treat as isolated/experimental
NEVER:    Feed EH data to any other app until explicitly spec'd
```

---

## MotherDuck Schema Ownership Map

```
PROD_EODHD.main.PROD_*        OWNER: JCN Dashboard (sync pipeline)
                               READERS: JCN API only
                               WRITERS: JCN sync_stage1/2/3 ONLY
                               PROHIBITED WRITERS: Muthr.ai, OptionsApp, DeepResearch

GoldenOpp.*                   OWNER: OBQ scoring system (external scripts)
                               READERS: JCN API (factor scores)
                               WRITERS: OBQ scoring pipeline ONLY
                               PROHIBITED WRITERS: All apps

qgsi.*                        OWNER: QGSI research pipeline
                               READERS: JCN API (composite blends)
                               WRITERS: QGSI pipeline ONLY
                               PROHIBITED WRITERS: All apps

DEV_EODHD_DATA.*              OWNER: JCN sync pipeline (staging)
                               WRITERS: JCN sync_stage1 ONLY
                               PROHIBITED WRITERS: All other apps

EODHD_Options.*               OWNER: Muthr.ai (scripts/download_options.py)
                               READERS: Muthr.ai API only
                               WRITERS: Muthr.ai download script ONLY
                               PROHIBITED WRITERS: JCN, OptionsApp, DeepResearch

PROD_SYNC_LOG                 OWNER: JCN sync pipeline audit trail
                               WRITERS: JCN sync_stage3 ONLY
```

---

## Local File Ownership Map

```
D:/OBQ_AI/obq_options_data.duckdb   OWNER: OBQ_AI_OptionsApp
                                    WRITERS: OptionsApp sweep pipeline ONLY
                                    READERS: OptionsApp modules ONLY
                                    PROHIBITED: All other apps, all network access

D:/OBQ_AI/obq_ai.duckdb            OWNER: OBQ_AI_OptionsApp (OHLCV)
                                    WRITERS: Data build scripts ONLY
                                    READERS: OptionsApp modules ONLY

D:/OBQ_AI/deep_research_kb/         OWNER: OBQ_AI_DeepResearch
                                    WRITERS: DeepResearch agents ONLY
                                    READERS: DeepResearch modules ONLY
```

---

## Cross-App Data Flow (APPROVED — future roadmap only)

These flows do NOT exist yet. They require a spec proposal when the time comes.

```
APPROVED FUTURE FLOWS (spec required before implementation):
  OptionsApp Knowledge/ outputs → Muthr.ai (read-only intelligence feed)
  JCN portfolio data → Muthr.ai (read-only portfolio views)
  DeepResearch reports → Muthr.ai (read-only report display)

PERMANENTLY PROHIBITED:
  Any app → PROD_EODHD.* (JCN owns this absolutely)
  Any app → EODHD_Options.* (Muthr.ai owns this absolutely)
  Any app → D:/OBQ_AI/*.duckdb (OptionsApp owns this absolutely)
  Any app writing to another app's primary data store
```

---

## Data Contamination Risk Matrix

| Risk | Scenario | Guard |
|---|---|---|
| 🔴 CRITICAL | Any app writes to PROD_EODHD | MotherDuck schema-level — only JCN token has write |
| 🔴 CRITICAL | OptionsApp connects to MotherDuck | No md: connection string exists — confirmed |
| 🔴 CRITICAL | JCN sync accidentally writes to EODHD_Options | JCN code never references EODHD_Options — spec guard |
| 🟠 HIGH | New Muthr.ai feature reads OptionsApp local DuckDB | Physical impossibility (local file, different machine path) |
| 🟠 HIGH | DeepResearch agent writes to any DB table | memory/ module spec-protected |
| 🟡 MEDIUM | New JCN endpoint reads from wrong schema | Spec module boundary check |
| 🟡 MEDIUM | Muthr.ai download script runs against wrong token | MOTHERDUCK_TOKEN env check |

---

## AI Enforcement Rules

When working in any spec-enabled project:

1. **Before any DB connection code** — check this file. Is the target DB owned by this app?
2. **Before any MotherDuck write** — which schema? Is this app the owner of that schema?
3. **Before any new data source** — does it appear in this topology? If not, raise a spec proposal.
4. **If asked to "sync data from X to Y"** — verify both X and Y are owned by the same app. Cross-app sync requires human spec approval.
5. **MOTHERDUCK_TOKEN** — from env only. Single token may have access to multiple schemas. Ownership is enforced by code, not token permissions.

---

## How to Update This File

Only update when:
- A new data source is added to an existing app (spec required first)
- A new app is added to the platform (spec required first)
- A data source is decommissioned (spec required first)

Never update to "temporarily" allow a cross-app write. If cross-app data flow is needed, spec it properly.
