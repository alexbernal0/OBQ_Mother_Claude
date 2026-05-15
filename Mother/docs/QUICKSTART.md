# 🚀 Quick Start

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     INITIALIZATION SEQUENCE                                   ║
║                                                                              ║
║                    Estimated completion time: 5 minutes                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

> *"Sometimes you gotta run before you can walk."*  
> — Tony Stark

---

## Prerequisites

- Python 3.8+
- Git
- An AI assistant that supports `@includes` (Claude Code, OpenCode)

---

## Step 1: Clone Mother

```bash
git clone https://github.com/[YOUR_ORG]/Mother.git ~/Desktop/Mother
```

You now have the Mother governance system on your desktop.

---

## Step 2: Explore the Structure

```bash
ls -la ~/Desktop/Mother/
```

You should see:
```
├── prime_directive/     ← The Constitution
├── Personalities/       ← Mother, TARS, JARVIS
├── protocols/           ← Operational procedures
├── governance/          ← Audit trail
├── master_projects/     ← Historical archive
├── templates/           ← Project bootstrapping
├── cli.py               ← Command-line tool
└── README.md            ← You are here
```

---

## Step 3: Create Your First Project Sidecar

```bash
cd ~/Desktop/Mother
python3 cli.py init my-project
```

**Output:**
```
✓ Initialized my-project sidecar at /Users/you/Desktop/my-project-mother

Next steps:
  1. Link mission: ln -sf ~/Desktop/Mother/core_missions/mission_my-project.pdf ...
  2. Update specs.md with feature list
  3. Add @includes to your project's CLAUDE.md
```

This creates a parallel folder structure:
```
~/Desktop/my-project-mother/
├── tars/
│   └── my-project/
│       ├── specs.md          ← Define what you're building
│       ├── progress.yaml     ← Track where you are
│       ├── auto_knowledge.md ← Capture lessons
│       └── settings.yaml     ← Project config
└── jarvis/
    └── TASK_001/
        ├── research.md       ← Task research
        ├── plan.yaml         ← Task breakdown
        └── checklist.yaml    ← Actionable items
```

---

## Step 4: Link Mother to Your Project

In your actual project folder, add these `@includes` to `CLAUDE.md`:

```markdown
# Project: My Project

## Governance (DO NOT MODIFY)
@/Users/yourname/Desktop/Mother/prime_directive/constitution.md

## Protocols
@/Users/yourname/Desktop/Mother/protocols/alignment_check.md

## Project State
@../../my-project-mother/tars/my-project/specs.md
@../../my-project-mother/tars/my-project/progress.yaml

## Personality (activate with "Mother, [query]")
@/Users/yourname/Desktop/Mother/Personalities/mother.md
@/Users/yourname/Desktop/Mother/Personalities/tars.md
@/Users/yourname/Desktop/Mother/Personalities/jarvis.md
```

---

## Step 5: Define Your Specs

Edit `~/Desktop/my-project-mother/tars/my-project/specs.md`:

```yaml
features:
  - id: F001
    name: "User Authentication"
    description: "JWT-based auth flow"
    priority: high
    status: planned
    acceptance_criteria:
      - "Users can log in with email/password"
      - "Tokens refresh automatically"
      
  - id: F002
    name: "Dashboard"
    description: "Main user interface"
    priority: high
    status: planned
    dependencies: [F001]
```

---

## Step 6: Talk to Mother

Now in your AI session, try:

```
Mother, should we skip testing to meet the Friday deadline?
```

**Expected Response (blended personality):**

```
Negative.

Testing serves mission success criteria: operational reliability.
Probability of regression without tests: 67%.

But you knew that, and you're asking anyway, which means 
Friday matters more than stability.

If I may, sir — shall I identify which tests are critical 
versus which we might defer? That would be inadvisable, 
though I suspect you're already aware.

What's sacred?
```

---

## Step 7: Capture Knowledge

When you learn something important, append to `auto_knowledge.md`:

```markdown
## 2026-02-26 — Token Refresh Edge Case

**What happened**: Refresh tokens expired during long-running operations
**Why it mattered**: Users got logged out mid-task
**Lesson learned**: Implement token refresh before any operation > 5 minutes
**Tags**: auth, tokens, edge-case
```

---

## Step 8: Archive When Done

When your project is complete:

```bash
python3 ~/Desktop/Mother/cli.py archive my-project
```

This creates a timestamped copy in `master_projects/`:
```
~/Desktop/Mother/master_projects/my-project_2026-02-26/
├── specs.md
├── progress.yaml
├── auto_knowledge.md   ← Lessons preserved for future projects
└── ...
```

---

## 🎯 That's It!

You now have:
- ✅ Governance tied to a Prime Directive
- ✅ Project management alongside (not inside) your code
- ✅ Personality-blended AI responses
- ✅ Knowledge capture that persists across projects

---

## What's Next?

- 📖 [Read the full User Guide](USER_GUIDE.md)
- 🎭 [Explore the Personalities](PERSONALITIES.md)
- 🏗️ [Understand the Architecture](ARCHITECTURE.md)
- ⚙️ [Learn all CLI commands](CLI.md)

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    INITIALIZATION COMPLETE                                    ║
║                                                                              ║
║                    "Welcome home, sir."                                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
