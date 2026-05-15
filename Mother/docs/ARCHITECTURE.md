# 🏗️ Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    T E C H N I C A L   S P E C I F I C A T I O N             ║
║                                                                              ║
║                    "I am a program. I am without form."                       ║
║                                                      — JARVIS                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Design Principles

### 1. Non-Invasive Sidecar

Mother lives **beside** your project, never inside it:

```
~/Projects/my-app/          ← Your code (untouched)
├── src/
├── tests/
├── package.json
└── CLAUDE.md               ← Only touchpoint: @includes

~/Desktop/my-app-mother/    ← Sidecar (parallel)
├── tars/
└── jarvis/
```

**Why?**
- No build system conflicts
- No accidental commits
- Clean separation of concerns
- Works with any tech stack

### 2. Hierarchical Governance

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRIME DIRECTIVE                              │
│                      (Immutable PDF)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌───────────────┐                                            │
│    │    MOTHER     │  ← Governance, protocols, personalities    │
│    └───────┬───────┘                                            │
│            │                                                     │
│    ┌───────▼───────┐                                            │
│    │     TARS      │  ← Project specs, progress, knowledge      │
│    └───────┬───────┘                                            │
│            │                                                     │
│    ┌───────▼───────┐                                            │
│    │    JARVIS     │  ← Task research, plans, checklists        │
│    └───────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Rule**: Lower layers cannot contradict higher layers.

### 3. Append-Only Knowledge

Files that only grow, never shrink:
- `auto_knowledge.md` — Lessons learned
- `governance/overrides.log` — Override audit trail
- `changes.log` — Session summaries

**Why?**
- Complete history preserved
- Pattern recognition over time
- Institutional memory

### 4. Integration via @includes

Mother integrates with AI assistants through `@include` references:

```markdown
# CLAUDE.md

## Governance
@/Users/alex/Desktop/Mother/prime_directive/constitution.md

## Protocols  
@/Users/alex/Desktop/Mother/protocols/alignment_check.md

## Personality
@/Users/alex/Desktop/Mother/Personalities/mother.md
@/Users/alex/Desktop/Mother/Personalities/tars.md
@/Users/alex/Desktop/Mother/Personalities/jarvis.md

## Project State
@../../my-app-mother/tars/my-app/specs.md
```

---

## Folder Structure

### Master Mother (Desktop)

```
~/Desktop/Mother/
├── prime_directive/
│   ├── Prime_Directive.pdf     ← THE source of truth (read-only)
│   └── constitution.md         ← Machine-readable derivative
│
├── Personalities/
│   ├── mother.md               ← MU/TH/UR 6000 profile
│   ├── tars.md                 ← TARS profile
│   └── jarvis.md               ← JARVIS profile
│
├── protocols/
│   ├── alignment_check.md      ← Pre-implementation verification
│   ├── escalation.md           ← Override protocol
│   ├── session_start.md        ← Session initialization
│   └── session_end.md          ← Session wrap-up
│
├── governance/
│   ├── overrides.log           ← Append-only audit trail
│   └── decisions/              ← Major architectural decisions
│       └── *.md
│
├── claude_refs/                ← Symlinks to identity files
│   ├── SOUL.md → ...
│   ├── IDENTITY.md → ...
│   └── USER.md → ...
│
├── core_missions/              ← Project mission PDFs
│   └── mission_*.pdf
│
├── master_projects/            ← Archived completed projects
│   ├── project-a_2026-01-15/
│   ├── project-b_2026-02-20/
│   └── ...
│
├── templates/
│   ├── DEPLOY.md               ← Deployment guide
│   └── new_project_sidecar/    ← Template for new projects
│
├── cli.py                      ← Command-line interface
└── README.md
```

### Project Sidecar

```
~/Desktop/{project}-mother/
├── tars/
│   └── {project}/
│       ├── mission.md          ← Link to core_missions/*.pdf
│       ├── specs.md            ← Feature specifications
│       ├── progress.yaml       ← Phase tracking
│       ├── auto_knowledge.md   ← Lessons learned (append-only)
│       ├── changes.log         ← Session summaries (append-only)
│       ├── state_diagram.md    ← Mermaid workflow visualization
│       └── settings.yaml       ← Project configuration
│
└── jarvis/
    ├── TASK_001/
    │   ├── research.md         ← Investigation notes
    │   ├── plan.yaml           ← Phased execution plan
    │   ├── checklist.yaml      ← Actionable items
    │   └── alignment_check.md  ← Pre-completion verification
    │
    └── TASK_002/
        └── ...
```

---

## File Formats

### YAML Files

Used for structured data:
- `progress.yaml` — Project phase and health
- `plan.yaml` — Task breakdown
- `checklist.yaml` — Action items with status
- `settings.yaml` — Configuration

Example `progress.yaml`:
```yaml
project: "my-app"
phase: implementation
last_updated: "2026-02-26"

milestones:
  - name: "MVP"
    target_date: "2026-03-15"
    status: in_progress

health:
  on_track: true
  blockers: []
```

### Markdown Files

Used for prose and documentation:
- `specs.md` — Feature specifications
- `research.md` — Investigation notes
- `auto_knowledge.md` — Lessons learned
- `*.md` in protocols/ — Operational procedures

### PDF Files

Used for immutable documents:
- `Prime_Directive.pdf` — The constitution
- `mission_*.pdf` — Project missions

**Why PDF?**
- Read-only by convention
- Difficult to accidentally modify
- Clear visual distinction from working files

---

## Data Flow

### Session Start
```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ progress.yaml    │────▶│ AI Assistant    │────▶│ Context loaded   │
│ specs.md         │     │ reads @includes │     │ Ready to work    │
│ constitution.md  │     └─────────────────┘     └──────────────────┘
└──────────────────┘
```

### During Work
```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ User request     │────▶│ Alignment check │────▶│ Action or        │
│                  │     │ vs constitution │     │ Override request │
└──────────────────┘     └─────────────────┘     └──────────────────┘
```

### Knowledge Capture
```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Lesson learned   │────▶│ Append to       │────▶│ Available for    │
│                  │     │ auto_knowledge  │     │ future sessions  │
└──────────────────┘     └─────────────────┘     └──────────────────┘
```

### Project Archive
```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ cli.py archive   │────▶│ Copy to         │────▶│ Available for    │
│ {project}        │     │ master_projects │     │ aggregate-lessons│
└──────────────────┘     └─────────────────┘     └──────────────────┘
```

---

## CLI Architecture

```python
cli.py
├── init <project>       # Create sidecar from template
├── archive <project>    # Copy to master_projects/
├── validate <project>   # Check alignment
├── aggregate-lessons    # Synthesize across projects
└── status [project]     # Show status
```

### init
1. Copy `templates/new_project_sidecar/` to `~/Desktop/{project}-mother/`
2. Rename `PROJECT_NAME` to actual project name
3. Replace `{{PROJECT_NAME}}` and `{{DATE}}` placeholders

### archive
1. Find sidecar at `~/Desktop/{project}-mother/tars/{project}/`
2. Create timestamped copy in `master_projects/{project}_{date}/`
3. Preserve all files including `auto_knowledge.md`

### aggregate-lessons
1. Scan all folders in `master_projects/`
2. Read `auto_knowledge.md` from each
3. Extract lesson entries (sections starting with `##`)
4. Display or output synthesized patterns

---

## Integration Points

### With Claude Code / OpenCode

Mother complements existing tools:

| Tool Handles | Mother Handles |
|--------------|----------------|
| `.claude/skills/` | `Personalities/` |
| `MEMORY.md` per-project | `master_projects/` cross-project |
| Session transcripts | `overrides.log` audit trail |
| Real-time context | Immutable governance |

### With Git

Mother sidecars can be git-versioned:
```bash
cd ~/Desktop/my-app-mother
git init
git add .
git commit -m "Initial sidecar setup"
```

This enables:
- Version history of specs and progress
- Team collaboration on project management
- Diffing changes over time

### With Other AI Tools

The `@include` pattern works with any tool that supports it:
- Claude Code
- OpenCode
- Cursor (via .cursorrules)
- Any tool reading CLAUDE.md

---

## Security Considerations

### Sensitive Data

**Never store in Mother:**
- API keys
- Passwords
- Credentials
- Personal data

The `auto_knowledge.md` and `changes.log` may contain:
- Error messages
- Code snippets
- File paths

Review before sharing or archiving.

### Override Logging

All overrides are logged with:
- Who approved
- What justification
- When it happened

This creates accountability but also a record. Consider your retention policy.

---

## Performance

### File Sizes

Most Mother files are small:
- `specs.md`: 2-10 KB
- `progress.yaml`: 1-2 KB
- `auto_knowledge.md`: Grows ~500 bytes per entry

### @include Loading

Each `@include` adds to context window:
- `constitution.md`: ~3 KB
- `alignment_check.md`: ~2 KB
- Personality files: ~10 KB each

Total personality load: ~35 KB — well within context limits.

---

## Extending Mother

### Adding New Protocols

1. Create `protocols/your_protocol.md`
2. Follow existing format with clear sections
3. Add `@include` to relevant CLAUDE.md files

### Adding New Personalities

1. Create `Personalities/character.md`
2. Include: source, traits, speech patterns, examples
3. Adjust blend weights in documentation

### Custom CLI Commands

Extend `cli.py` with new subcommands:
```python
def my_command(args):
    """Your custom command."""
    pass

# Add to subparsers
subparsers.add_parser("my-command", help="...")
```

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ARCHITECTURE SPECIFICATION COMPLETE                        ║
║                                                                              ║
║            "Commencing automated assembly. Estimated completion              ║
║             time is five hours."                                              ║
║                                                      — JARVIS                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
