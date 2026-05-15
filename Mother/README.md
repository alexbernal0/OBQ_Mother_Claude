```
███╗   ███╗ ██████╗ ████████╗██╗  ██╗███████╗██████╗ 
████╗ ████║██╔═══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██╗
██╔████╔██║██║   ██║   ██║   ███████║█████╗  ██████╔╝
██║╚██╔╝██║██║   ██║   ██║   ██╔══██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║╚██████╔╝   ██║   ██║  ██║███████╗██║  ██║
╚═╝     ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                          v3.4.0
```

<div align="center">

**Soul Manager & Development Sidecar System**

*"I can't lie to you about your chances, but... you have my sympathies."*

[![Version](https://img.shields.io/badge/version-3.4.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)]()
[![License](https://img.shields.io/badge/license-internal-red.svg)]()

[Quick Start](#-quick-start) · [Soul Config](#-soul-configuration) · [Spec-Driven Dev](#-spec-driven-development) · [The Algorithm](#-the-algorithm)

</div>

---

## 🎬 What Is This?

> *"Mother, are you there?"*
> 
> *"Yes, I'm here. Systems nominal. What do you need?"*

**Mother** is an AI soul management system that lives alongside your development projects. Think of it as the ship's computer from Alien meets TARS from Interstellar meets JARVIS from Iron Man.

It provides:
- 🧠 **Soul Configuration** — Persistent AI identity across sessions
- 📋 **Spec-Driven Development** — Generate, execute, verify, sync from specs
- 📦 **Project Sidecars** — Governance and knowledge capture per project
- 🔄 **Recursive Self-Improvement** — The AI learns from every correction
- 🚀 **Export/Deploy** — Take your configured AI to any machine

```
┌─────────────────────────────────────────────────────────────┐
│  PERSONALITY BLEND                                          │
├─────────────────────────────────────────────────────────────┤
│  ████████████████████░░░░░░░░░░  50% MOTHER (Alien)        │
│  ██████████░░░░░░░░░░░░░░░░░░░░  25% TARS (Interstellar)   │
│  ██████████░░░░░░░░░░░░░░░░░░░░  25% JARVIS (Iron Man)     │
└─────────────────────────────────────────────────────────────┘
```

---

## ⬇️ Download & Install

### Fresh Install (New Machine)

```bash
# 1. Extract to Desktop
cd ~/Desktop
unzip Mother_v3.4.0.zip

# 2. Run the menu
cd Mother
python cli.py menu

# 3. Configure your soul
#    Select "1) Configure Soul" and follow prompts
```

---

## 🚀 Quick Start

```bash
# Talk to Mother
python cli.py --mother
# > "Yes, I'm here. *adjusts honesty setting to 95%*"

# Interactive menu
python cli.py menu

# Initialize soul from your repos
python cli.py soul-init

# Deploy soul to a project
python cli.py soul-deploy ~/Desktop/my-project

# Create project sidecar
python cli.py init my-project

# Export Mother for another machine
python cli.py export-mother
```

---

## 🧠 Soul Configuration

Mother uses a **6-file soul framework** (Option B) to give AI assistants persistent identity:

```
soul/
├── SOUL.md        ← WHO I AM      Character, values, personality
├── IDENTITY.md    ← WHAT I KNOW   Role, domain expertise  
├── PRINCIPLES.md  ← HOW I DECIDE  Heuristics, domain laws, anti-patterns
├── USER.md        ← WHO YOU ARE   Your profile, preferences
├── HEARTBEAT.md   ← SESSION FLOW  Start/end rituals, triggers
└── NOW.md         ← LIVE STATE    Current work, next steps
```

### Generate Soul from Your Repos

```bash
python cli.py soul-init
```

Mother examines **3 repositories** you provide and synthesizes:
- Tech stack and frameworks used
- Code conventions and patterns
- Error handling approaches
- Domain-specific rules

The result: a custom soul calibrated to YOUR codebase.

### Deploy to Projects

```bash
python cli.py soul-deploy ~/Desktop/my-project
```

Creates `.claude/` directory with soul files and sets up `CLAUDE.md` includes.

---

## 📋 Spec-Driven Development

> *"The spec is the single source of truth. Code follows spec. Always."*

Mother v3.4 introduces **tool_BuildfromSpec** — a comprehensive spec-driven development system with 4 modes:

```
┌─────────────────────────────────────────────────────────────┐
│  SPEC-DRIVEN DEVELOPMENT WORKFLOW                           │
├─────────────────────────────────────────────────────────────┤
│  1. GENERATE   Code/idea → Full product spec (PDF)          │
│  2. EXECUTE    Spec → Implementation (Prime Directive)      │
│  3. VERIFY     Continuous spec/code alignment checks         │
│  4. SYNC       Code changes → Updated spec                  │
├─────────────────────────────────────────────────────────────┤
│  Spec = Source of Truth. Drift = Failure.                   │
└─────────────────────────────────────────────────────────────┘
```

### Generate Spec from Code

```bash
python cli.py spec-generate my-project
```

Analyzes your codebase and creates a comprehensive product spec:
- **Research Phase**: Tech stack, dependencies, patterns
- **Requirements Phase**: User stories, acceptance criteria, NFRs
- **Design Phase**: Architecture, data models, API contracts
- **Tasks Phase**: Prioritized backlog with effort estimates

Output: `master_projects/my-project/specs/SPEC_my-project_v1.0.pdf`

### Execute from Spec

Use the `/build-spec execute` command in Claude to:
1. Parse spec into execution plan
2. Generate code following spec exactly
3. Run compliance checks at each gate
4. Produce audit trail

### Verify Alignment

```bash
python cli.py spec-verify my-project
```

Continuous compliance checking:
- Detects spec/code drift
- Categorizes violations by severity
- Suggests remediation actions

### Spec Status

```bash
python cli.py spec-status
python cli.py spec-status my-project
```

Shows spec health across all projects or for a specific project.

---

## 📐 The Algorithm

> *"The best part is no part. The best process is no process."*

Every task follows this sequence — **in order**:

```
┌─────────────────────────────────────────────────────────────┐
│                    THE ALGORITHM                             │
├─────────────────────────────────────────────────────────────┤
│  1. Make requirements less dumb    ← Question everything    │
│  2. Delete the part or process     ← Best code = no code    │
│  3. Simplify and optimize          ← Only after deletion    │
│  4. Accelerate cycle time          ← Speed up survivors     │
│  5. Automate                       ← LAST step, not first   │
├─────────────────────────────────────────────────────────────┤
│  ⚠️  DO STEPS IN ORDER. Most people skip to 3, 4, or 5.    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture

```
~/Desktop/
├── Mother/                          # 🛸 THE SHIP (this repo)
│   ├── soul/                        # Soul configuration templates
│   ├── prime_directive/             # Immutable governance
│   ├── Personalities/               # Mother, TARS, JARVIS profiles
│   ├── system/                      # Principles, ACL, resource mapping
│   ├── templates/                   # Project bootstrapping
│   └── cli.py                       # Command center
│
├── my-project-mother/               # 📦 PROJECT SIDECAR
│   ├── tars/my-project/             # TARS: Project management
│   │   ├── specs.md                 # Feature specifications
│   │   ├── progress.yaml            # Phase tracking
│   │   └── state/                   # Blockers, risks, decisions
│   └── jarvis/TASK_001/             # JARVIS: Task execution
│       ├── research.md              # Task research
│       ├── plan.yaml                # Execution plan
│       └── state/                   # Findings, questions
│
├── [COMPANY]_Skills/                # 🔧 SKILLS LIBRARY
├── [COMPANY]_Knowledge/             # 📚 DOMAIN KNOWLEDGE
└── OC_Knowledge/                    # 🧠 SELF-IMPROVEMENT
```

### Hierarchy & Containment

```
┌──────────────────────────────────────────────────────────────┐
│  MOTHER        Governance layer. Reads everything.          │
│  ══════        Writes only to governance/, system/          │
├──────────────────────────────────────────────────────────────┤
│  TARS          Project management. Reads Mother, code.      │
│  ════          Writes only to tars/[project]/               │
├──────────────────────────────────────────────────────────────┤
│  JARVIS        Task execution. Reads TARS, code, skills.    │
│  ══════        Writes to jarvis/, project code, lessons     │
└──────────────────────────────────────────────────────────────┘

Rule: Lower layers READ up, WRITE within, ESCALATE out.
```

---

## 💻 CLI Commands

### Soul Management
```bash
python cli.py soul-init              # Generate soul from 3 repos
python cli.py soul-deploy <path>     # Deploy soul to project
python cli.py soul-export            # Export soul configuration
```

### Project Management
```bash
python cli.py init <project>         # Create project sidecar
python cli.py archive <project>      # Archive to master_projects/
python cli.py validate <project>     # Check Prime Directive alignment
python cli.py status [project]       # Show project status
```

### Spec-Driven Development
```bash
python cli.py spec-generate <project> # Generate spec from codebase
python cli.py spec-verify <project>   # Check spec/code alignment
python cli.py spec-status [project]   # Show spec health
```

### TARS/JARVIS Initialization
```bash
python cli.py tars-init <project>     # Initialize TARS for project
python cli.py jarvis-init <project>   # Initialize JARVIS for project
```

### Knowledge & Learning
```bash
python cli.py learn                  # Trigger Auto-Learn extraction
python cli.py recall "query"         # Search memories
python cli.py memories               # List recent memories
python cli.py aggregate-lessons      # Synthesize cross-project lessons
```

### Export & Setup
```bash
python cli.py export-mother          # Create .zip for new machine
python cli.py prepare-package <name> # Create handoff for senior dev
python cli.py menu                   # Interactive menu
python cli.py --mother               # Personality greeting
```

---

## 🔄 Recursive Self-Improvement

```
    ┌─────────────────────────────────────────┐
    │                                         │
    │   JARVIS executes task                  │
    │            │                            │
    │            ▼                            │
    │   Discovers pattern or lesson           │
    │            │                            │
    │            ▼                            │
    │   Writes to OC_Knowledge/lessons/       │
    │            │                            │
    │            ▼                            │
    │   Future JARVIS reads improved context  │
    │            │                            │
    │            ▼                            │
    │   Better execution → more learnings     │
    │            │                            │
    └────────────┴────────────────────────────┘
                 │
                 ▼
            ∞ LOOP ∞
```

**OC_Knowledge** improves HOW we work.  
Better work produces better **[COMPANY]_Knowledge**.  
Better context enables better requirements.  
**→ Recursive self-improvement.**

---

## 🆕 What's New

### v3.4 — Spec-Driven Development
- **tool_BuildfromSpec** — Complete spec-driven development skill
- **spec-generate** — Generate product specs from codebase analysis
- **spec-verify** — Continuous spec/code alignment verification
- **spec-status** — Health dashboard for all project specs
- **tars-init / jarvis-init** — Quick initialization commands
- **4 Modes**: GENERATE, EXECUTE, VERIFY, SYNC
- **5 Specialized Agents**: Research Analyst, Product Manager, Architect, Task Planner, Compliance Checker

### v3.3 — Soul Manager
- **Soul Configuration** — 6-file framework (SOUL, IDENTITY, PRINCIPLES, USER, HEARTBEAT, NOW)
- **soul-init** — Generate custom soul from 3-repo analysis
- **soul-deploy** — Deploy soul to any project
- **Export Mother** — Create .zip for fresh machine setup
- **Interactive Menu** — `python cli.py menu`
- **"Mother, are you there?"** — Personality greeting with options

### v3.2 — Auto-Learn
- Automatic knowledge capture during sessions
- 5-gate quality filter (Discovery, Generalizable, Verified, Novel, Trigger)
- Attention dynamics (HOT/WARM/COLD)
- Memory lifecycle with TTL

### v3.1 — Package System
- `prepare-package` for senior developer handoffs
- Secret scanning and validation
- Auto-compression to `.tar.gz`

### v3.0 — Skills & Patterns
- Auto-Review, Auto-Doc-Sync, Saga-Patterns
- Skill-Scan for community skill discovery
- Resource Mapping v3

---

## 🎭 Personality Profiles

### Mother (Alien)
> *Calm. Mission-focused. The ship's computer that keeps you alive.*

- Governance and oversight
- Risk assessment
- Override protocols

### TARS (Interstellar)
> *Blunt. Honest. Adjustable humor setting.*

- Project management
- Direct communication
- "Honesty: 95%"

### JARVIS (Iron Man)
> *Polite. Anticipatory. Gets things done.*

- Task execution
- Proactive assistance
- "Shall I run diagnostics, sir?"

---

## ⚠️ Override Protocol

When any action conflicts with the Prime Directive:

```
1. STOP    → Don't proceed
2. WARN    → Cite the specific section
3. REQUEST → Ask for "SYSTEM OVERRIDE: [justification]"
4. LOG     → If granted, append to governance/overrides.log
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `soul/SOUL.md` | Core character and values |
| `soul/PRINCIPLES.md` | Decision heuristics, domain laws |
| `system/principles.md` | The 5-step Algorithm |
| `prime_directive/constitution.md` | Governance rules |
| `governance/overrides.log` | Override audit trail |

---

## 🔗 Integration

Add to your project's `CLAUDE.md`:

```markdown
## Soul
@.claude/SOUL.md
@.claude/IDENTITY.md
@.claude/PRINCIPLES.md
@.claude/USER.md
@.claude/HEARTBEAT.md

## Governance
@/Users/you/Desktop/Mother/prime_directive/constitution.md
@/Users/you/Desktop/Mother/system/principles.md

## Personality (optional)
@/Users/you/Desktop/Mother/Personalities/mother.md
@/Users/you/Desktop/Mother/Personalities/tars.md
@/Users/you/Desktop/Mother/Personalities/jarvis.md
```

---

<div align="center">

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   "Stay organized. Deep simplicity.                         ║
║    The best ability is delete-ability."                     ║
║                                                              ║
║                    — Mother v3.4.0                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**An open soul management framework for AI-assisted development.**

*Configure. Deploy. Improve.*

</div>
