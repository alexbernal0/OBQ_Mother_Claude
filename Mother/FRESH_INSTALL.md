# Fresh Install Guide — Mother v3.4

> *"Mother, are you there?"*
> *"Yes. Let's get you set up."*

---

## What Is This?

You've downloaded **Mother** — an AI soul management system that gives your AI assistants persistent identity, governance, and recursive self-improvement capabilities.

This is a **clean template** ready for any team or company to customize.

---

## Quick Setup (5 Minutes)

### Step 1: Extract Mother

```bash
cd ~/Desktop
unzip Mother_v3.4.0.zip
cd Mother
```

### Step 2: Create Supporting Directories

Mother works alongside 3 companion directories. Replace `[COMPANY]` with your organization name:

```bash
mkdir -p ~/Desktop/[COMPANY]_Skills
mkdir -p ~/Desktop/[COMPANY]_Knowledge
mkdir -p ~/Desktop/OC_Knowledge/{guides,patterns,lessons,references}
mkdir -p ~/Desktop/Packages
```

### Step 3: Configure Your Identity

Edit these files to match your organization:

| File | What to Change |
|------|---------------|
| `soul/SOUL.md` | Replace `[YOUR COMPANY]` with your org name |
| `soul/IDENTITY.md` | Add your tech stack, frameworks, domain expertise |
| `soul/PRINCIPLES.md` | Add your domain laws, anti-patterns, safety limits |
| `soul/USER.md` | Replace `[YOUR NAME]`, `[YOUR ROLE]`, preferences |
| `soul/HEARTBEAT.md` | Customize session start/end rituals |

**Or use the interactive wizard:**

```bash
python cli.py soul-init
```

This examines 3 of your repositories and auto-generates customized soul files.

### Step 4: Update CLI Paths

Edit `cli.py` and update the configuration section near the top:

```python
# <!-- CUSTOMIZE: Replace [COMPANY] with your organization name -->
PACKAGES_DIR = Path.home() / "Desktop" / "Packages"
SKILLS_DIR = Path.home() / "Desktop" / "[COMPANY]_Skills"   # <-- change this
KNOWLEDGE_DIR = Path.home() / "Desktop" / "[COMPANY]_Knowledge"  # <-- change this
```

### Step 5: Update Resource Mapping

Edit `system/resource_mapping.md` and replace all `[COMPANY]` placeholders with your organization name.

### Step 6: Deploy to a Project

```bash
python cli.py soul-deploy ~/Desktop/my-project
```

---

## What to Customize

Search for `<!-- CUSTOMIZE -->` and `[COMPANY]` across all files to find every placeholder:

```bash
grep -r "CUSTOMIZE\|\\[COMPANY\\]\|\\[YOUR" ~/Desktop/Mother/ --include="*.md" --include="*.py"
```

### Key Customization Points

| Location | What | Priority |
|----------|------|----------|
| `soul/SOUL.md` | Core character and values | **Required** |
| `soul/IDENTITY.md` | Tech stack, domain expertise | **Required** |
| `soul/USER.md` | User profile and preferences | **Required** |
| `soul/PRINCIPLES.md` | Decision heuristics, domain laws | **Required** |
| `cli.py` (line ~63) | Directory paths | **Required** |
| `system/resource_mapping.md` | Knowledge repository paths | **Required** |
| `prime_directive/constitution.md` | Governance rules | Recommended |
| `system/containment.md` | ACL and access rules | Recommended |
| `debloat-opencode.md` | Protected process list | Optional |
| `skills/Skill-Scan/SKILL.md` | Skill discovery targets | Optional |
| `skills/Saga-Patterns/SKILL.md` | Workflow pattern examples | Optional |

---

## Directory Structure After Setup

```
~/Desktop/
├── Mother/                          # This repo — the governance layer
│   ├── soul/                        # Soul configuration (identity, principles)
│   ├── prime_directive/             # Immutable governance rules
│   ├── Personalities/               # Mother, TARS, JARVIS profiles
│   ├── system/                      # Principles, ACL, resource mapping
│   ├── skills/                      # Bundled skill templates
│   ├── templates/                   # Project bootstrapping templates
│   ├── docs/                        # Guides and documentation
│   └── cli.py                       # Command center
│
├── [COMPANY]_Skills/                # Your skills library
│   ├── Auto-Learn/                  # Automatic knowledge capture
│   ├── Auto-Skill/                  # Skill creation automation
│   └── ...                          # Your custom skills
│
├── [COMPANY]_Knowledge/             # Your domain knowledge
│   ├── products/                    # Product documentation
│   ├── architecture/                # Architecture decisions
│   └── research/                    # Reference materials
│
├── OC_Knowledge/                    # Self-improvement knowledge
│   ├── guides/                      # How-to guides
│   ├── patterns/                    # Reusable patterns
│   ├── lessons/                     # Lessons learned
│   └── references/                  # External references
│
└── Packages/                        # Export packages
```

---

## How It Works

### The Three-Layer System

```
┌──────────────────────────────────────────────────────────────┐
│  MOTHER        Governance layer. Reads everything.           │
│  ══════        Writes only to governance/, system/           │
├──────────────────────────────────────────────────────────────┤
│  TARS          Project management. Reads Mother, code.       │
│  ════          Writes only to tars/[project]/                │
├──────────────────────────────────────────────────────────────┤
│  JARVIS        Task execution. Reads TARS, code, skills.     │
│  ══════        Writes to jarvis/, project code, lessons      │
└──────────────────────────────────────────────────────────────┘

Rule: Lower layers READ up, WRITE within, ESCALATE out.
```

### The Soul Framework (6 Files)

```
soul/
├── SOUL.md        ← WHO I AM      Character, values, personality
├── IDENTITY.md    ← WHAT I KNOW   Role, domain expertise
├── PRINCIPLES.md  ← HOW I DECIDE  Heuristics, domain laws
├── USER.md        ← WHO YOU ARE   Your profile, preferences
├── HEARTBEAT.md   ← SESSION FLOW  Start/end rituals
└── NOW.md         ← LIVE STATE    Current work, next steps
```

### Recursive Self-Improvement

```
JARVIS executes task → Discovers pattern → Writes to OC_Knowledge/lessons/
→ Future JARVIS reads improved context → Better execution → ∞ LOOP
```

---

## CLI Commands

```bash
python cli.py menu                    # Interactive menu
python cli.py soul-init               # Generate soul from repos
python cli.py soul-deploy <path>      # Deploy soul to project
python cli.py init <project>          # Create project sidecar
python cli.py spec-generate <project> # Generate spec from codebase
python cli.py export-mother           # Create .zip for another machine
python cli.py --mother                # "Mother, are you there?"
```

---

## Integration with Claude/AI

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
```

---

## Troubleshooting

**"Command not found" when running cli.py**
- Ensure Python 3.11+ is installed: `python3 --version`
- Run with explicit python: `python3 cli.py menu`

**Soul files have [PLACEHOLDER] text**
- Run `python cli.py soul-init` to auto-generate from your repos
- Or manually edit each soul/*.md file

**Skills directory not found**
- Create the companion directories (Step 2 above)
- Update paths in `cli.py` if using non-default names

---

*FRESH_INSTALL.md | Mother v3.4.0*
