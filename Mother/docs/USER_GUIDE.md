# 📖 User Guide

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    M O T H E R   U S E R   G U I D E                         ║
║                                                                              ║
║                    "I can't lie to you about your chances."                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [The Hierarchy](#the-hierarchy)
3. [Session Workflow](#session-workflow)
4. [Working with Tars (Project Management)](#working-with-tars)
5. [Working with Jarvis (Task Management)](#working-with-jarvis)
6. [The Override Protocol](#the-override-protocol)
7. [Knowledge Capture](#knowledge-capture)
8. [Cross-Project Learning](#cross-project-learning)
9. [Personality Activation](#personality-activation)

---

## Philosophy

> *"Deep simplicity with maximum benefit"*

Mother is built on these principles:

### 1. Non-Invasive
Mother lives **beside** your project, not inside it. Your `src/` folder never sees a `.mother/` directory. This means:
- No conflicts with your build system
- No accidental commits of governance files
- Clean separation of concerns

### 2. Hierarchical
```
PRIME DIRECTIVE (immutable)
        ↓
    MOTHER (governance)
        ↓
      TARS (project management)
        ↓
     JARVIS (task management)
```

Lower levels **cannot** contradict higher levels. If your task plan violates the Prime Directive, the task plan loses.

### 3. Append-Only Knowledge
The `auto_knowledge.md` file only grows. You never delete entries. This creates:
- A complete history of lessons learned
- Pattern recognition across projects
- Institutional memory that survives team changes

### 4. Auditable Decisions
Every override is logged. Every major decision is documented. When someone asks "why did we do it this way?", you have the receipts.

---

## The Hierarchy

### Mother (Governance Layer)
Lives at: `~/Desktop/Mother/`

Contains:
- **Prime Directive** — The constitution, immutable
- **Personalities** — Behavioral profiles for AI responses
- **Protocols** — Reusable operational procedures
- **Governance** — Override logs, decision records
- **Master Projects** — Archive of all completed projects

### Tars (Project Layer)
Lives at: `~/Desktop/{project}-mother/tars/{project}/`

Contains:
- **specs.md** — Feature specifications
- **progress.yaml** — Phase and milestone tracking
- **auto_knowledge.md** — Lessons learned
- **state_diagram.md** — Visual workflow
- **changes.log** — Session summaries
- **settings.yaml** — Project configuration

### Jarvis (Task Layer)
Lives at: `~/Desktop/{project}-mother/jarvis/{task_id}/`

Contains:
- **research.md** — Investigation notes
- **plan.yaml** — Phased execution plan
- **checklist.yaml** — Actionable items with status
- **alignment_check.md** — Pre-completion verification

---

## Session Workflow

### Session Start

```
┌─────────────────────────────────────────────────────────────────┐
│ SESSION START PROTOCOL                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Read progress.yaml        → Where are we?                   │
│  2. Read specs.md             → What are we building?           │
│  3. Check jarvis/             → Any in-progress tasks?          │
│  4. Verify alignment          → Still serving Prime Directive?  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Quick version**: Just scan progress.yaml and pick up where you left off.

### During Work

1. **Create task folders** in `jarvis/` for each unit of work
2. **Update checklists** as you progress
3. **Run alignment check** before major changes
4. **Capture knowledge** when you learn something

### Session End

```
┌─────────────────────────────────────────────────────────────────┐
│ SESSION END PROTOCOL                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Mark completed tasks      → Update checklist.yaml           │
│  2. Capture lessons           → Append to auto_knowledge.md     │
│  3. Log changes               → Append to changes.log           │
│  4. Update progress           → Modify progress.yaml if needed  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Working with Tars

> *"I have a cue light I can use when I'm joking, if you like."*

Tars manages the **project level**—specs, progress, and project-wide knowledge.

### specs.md — Define What You're Building

```yaml
features:
  - id: F001
    name: "User Authentication"
    description: "JWT-based auth with refresh tokens"
    priority: high
    status: in_progress
    dependencies: []
    acceptance_criteria:
      - "Users can log in with email/password"
      - "Tokens refresh automatically before expiry"
      - "Failed logins are rate-limited"

  - id: F002
    name: "User Dashboard"
    description: "Main interface after login"
    priority: high
    status: planned
    dependencies: [F001]
    acceptance_criteria:
      - "Shows user profile"
      - "Displays recent activity"
```

### progress.yaml — Track Where You Are

```yaml
project: "my-project"
phase: implementation  # planning | design | implementation | testing | review | done

milestones:
  - name: "MVP Complete"
    target_date: "2026-03-15"
    status: in_progress

health:
  on_track: true
  blockers: []
  risks:
    - description: "Third-party API rate limits"
      likelihood: medium
      mitigation: "Implement caching layer"
```

### settings.yaml — Project Configuration

```yaml
personality:
  enabled: true
  humor_level: 75  # TARS's humor (0-100)

integration:
  project_path: "~/Projects/my-project"
  prime_directive: "~/Desktop/Mother/prime_directive/constitution.md"
```

---

## Working with Jarvis

> *"At your service, sir."*

Jarvis manages the **task level**—individual units of work.

### Creating a New Task

1. Copy the template:
   ```bash
   cp -r ~/Desktop/Mother/templates/new_project_sidecar/jarvis/TASK_001 \
         ~/Desktop/my-project-mother/jarvis/TASK_002
   ```

2. Or manually create:
   ```
   jarvis/
   └── implement-auth/
       ├── research.md
       ├── plan.yaml
       ├── checklist.yaml
       └── alignment_check.md
   ```

### research.md — Capture Investigation

```markdown
# Research: JWT Authentication

## Questions to Answer
- [x] Which JWT library to use?
- [x] Token expiration policy?
- [ ] Refresh token rotation strategy?

## Findings

### JWT Libraries Comparison
**Source**: npm trends, security advisories

| Library | Stars | Last Update | Security Issues |
|---------|-------|-------------|-----------------|
| jsonwebtoken | 14k | 2 months | 0 known |
| jose | 5k | 1 week | 0 known |

**Recommendation**: Use `jose` — more actively maintained.
```

### plan.yaml — Break Down the Work

```yaml
task:
  id: implement-auth
  title: "Implement JWT Authentication"
  status: implementing

phases:
  - phase: brainstorm
    status: done
    outputs: [research.md]
    
  - phase: plan
    status: done
    outputs: [plan.yaml]
    
  - phase: implement
    status: in_progress
    outputs: []

steps:
  - id: 1
    description: "Set up jose library"
    status: done
    
  - id: 2
    description: "Create auth middleware"
    status: in_progress
    
  - id: 3
    description: "Add refresh token endpoint"
    status: pending
```

### checklist.yaml — Track Actions

```yaml
task:
  id: implement-auth
  status: in_progress

items:
  - id: 1
    description: "Install jose"
    status: done
    completed: "2026-02-26"
    
  - id: 2
    description: "Create auth middleware"
    status: in_progress
    
  - id: 3
    description: "Write tests"
    status: pending
    
  - id: 4
    description: "Complete alignment check"
    status: pending
```

---

## The Override Protocol

When you try to do something that conflicts with the Prime Directive:

```
⚠️ PRIME DIRECTIVE CONFLICT

Section: Communication Law (Section 5)
Proposed Action: Call Probe API directly from Dashboard
Conflict: Dashboard talks to AK, not directly to probes

Options:
1. Modify approach to align with directive
2. Request system override

To proceed with override, confirm:
"SYSTEM OVERRIDE: [your justification]"
```

### If You Confirm Override

1. **Logged** to `governance/overrides.log`:
   ```
   ## 2026-02-26 14:32 — Override Granted
   
   **Section Overridden**: Communication Law
   **Action Taken**: Direct probe call for emergency shutdown
   **Justification**: Production incident, AK unresponsive
   **Approver**: [YOUR_GITHUB_USER]
   **Review Status**: pending
   ```

2. **Action proceeds**

3. **Flagged** for retrospective review

### Override Log Format

The `governance/overrides.log` is append-only. Every override lives forever:

```markdown
# Overrides Log

> **DO NOT DELETE ENTRIES** — This is an audit trail.

## 2026-02-26 14:32 — Override Granted

**Section Overridden**: Communication Law
**Proposed Action**: Direct probe call
**Conflict**: Violates canonical communication path
**Justification**: Production emergency
**Approver**: [YOUR_GITHUB_USER]
**Outcome**: Incident resolved
**Review Status**: reviewed — accepted as emergency exception
```

---

## Knowledge Capture

### auto_knowledge.md — Append-Only Lessons

Every time you learn something, append:

```markdown
## 2026-02-26 — Token Refresh Race Condition

**What happened**: Two simultaneous refresh requests caused token invalidation
**Why it mattered**: Users got logged out unexpectedly
**Lesson learned**: Implement refresh token locking or use sliding expiration
**Tags**: auth, tokens, race-condition, edge-case
```

### What to Capture

- **Corrections** — When you fixed a mistake
- **Patterns** — Reusable solutions
- **Gotchas** — Things that surprised you
- **Decisions** — Why you chose A over B
- **Tools** — Useful commands or configurations

### Cross-Project Learning

When you archive a project:
```bash
python3 cli.py archive my-project
```

The `auto_knowledge.md` is preserved in `master_projects/`. 

Then you can synthesize across all projects:
```bash
python3 cli.py aggregate-lessons --verbose
```

This scans all archived projects and shows patterns:
```
Found 47 lessons across 6 projects

Common patterns:
- Token refresh issues (4 projects)
- API rate limiting (3 projects)
- State management complexity (5 projects)
```

---

## Personality Activation

### Activating the Blend

Prefix any query with `"Mother, [question]"`:

```
Mother, should we add caching to this endpoint?
```

### What You Get

The response blends three personalities:

| Source | Weight | Contribution |
|--------|--------|--------------|
| Mother | 50% | Mission focus, clinical precision |
| TARS | 25% | Honest assessment, dry wit |
| JARVIS | 25% | Proactive suggestions, warmth |

### Example Blended Response

**Query**: "Mother, can we skip code review for this hotfix?"

**Blended Response**:
```
Negative. Code review serves mission success criteria.

That said, the probability of introducing regressions 
with a 12-line hotfix is approximately 8%. 
Acceptable risk for production issues.

If I may, sir — I've prepared a minimal review checklist 
for expedited cases. Shall I pull it up?

The alternative is shipping blind. I won't judge. Out loud.
```

This response has:
- **Mother**: "Negative. Code review serves mission success criteria."
- **TARS**: "probability of... 8%" and "I won't judge. Out loud."
- **JARVIS**: "If I may, sir" and "Shall I pull it up?"

### Humor Slider

TARS's humor is configurable in `settings.yaml`:

```yaml
personality:
  humor_level: 75  # 0-100
```

- **0-25**: Almost Mother-like. Just facts.
- **26-50**: Occasional dry observation.
- **51-75**: Regular sardonic commentary. (Default)
- **76-100**: Full TARS mode. Robot colony jokes.

---

## Pro Tips

### 1. Keep specs.md Updated
The specs file is your source of truth for what you're building. When requirements change, update it first.

### 2. Create Tasks for Everything
Even small changes benefit from a `jarvis/` folder. It takes 30 seconds and creates a paper trail.

### 3. Capture Knowledge Immediately
Don't wait until session end. When you learn something, append to `auto_knowledge.md` right away.

### 4. Use the Alignment Check
Before completing any significant task, run through `alignment_check.md`. It catches drift.

### 5. Archive Completed Projects
Even "failed" projects have lessons. Archive everything.

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    END USER GUIDE                                            ║
║                                                                              ║
║                    "See you on the other side, Coop."                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
