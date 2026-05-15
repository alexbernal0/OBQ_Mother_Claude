# ⚙️ CLI Reference

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    C O M M A N D   L I N E   I N T E R F A C E               ║
║                                                                              ║
║                    "Settings. General settings. Security settings."          ║
║                                                              — TARS          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Overview

```bash
python3 cli.py [--mother] [--verbose] <command> [arguments]
```

### Global Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--mother` | | Enable personality blend in output |
| `--verbose` | `-v` | Verbose output |
| `--help` | `-h` | Show help |

---

## Commands

### init

Create a new project sidecar from the template.

```bash
python3 cli.py init <project_name> [--target <directory>]
```

**Arguments:**
- `project_name` — Name of your project (used for folder naming)

**Options:**
- `--target`, `-t` — Target directory for sidecar (default: `~/Desktop/`)

**Example:**
```bash
python3 cli.py init my-awesome-app
```

**Output:**
```
✓ Initialized my-awesome-app sidecar at /Users/alex/Desktop/my-awesome-app-mother

Next steps:
  1. Link mission: ln -sf ~/Desktop/Mother/core_missions/mission_my-awesome-app.pdf ...
  2. Update specs.md with feature list
  3. Add @includes to your project's CLAUDE.md
```

**What it creates:**
```
~/Desktop/my-awesome-app-mother/
├── tars/
│   └── my-awesome-app/
│       ├── mission.md
│       ├── specs.md
│       ├── progress.yaml
│       ├── auto_knowledge.md
│       ├── changes.log
│       ├── state_diagram.md
│       └── settings.yaml
└── jarvis/
    └── TASK_001/
        ├── research.md
        ├── plan.yaml
        ├── checklist.yaml
        └── alignment_check.md
```

---

### archive

Archive a completed project to `master_projects/`.

```bash
python3 cli.py archive <project_name> [--path <sidecar_path>]
```

**Arguments:**
- `project_name` — Name of the project to archive

**Options:**
- `--path`, `-p` — Path to sidecar if not in default location

**Example:**
```bash
python3 cli.py archive my-awesome-app
```

**Output:**
```
✓ Archived my-awesome-app to /Users/alex/Desktop/Mother/master_projects/my-awesome-app_2026-02-26
```

**With verbose:**
```bash
python3 cli.py archive my-awesome-app --verbose
```

**Output:**
```
✓ Archived my-awesome-app to /Users/alex/Desktop/Mother/master_projects/my-awesome-app_2026-02-26

Archived contents:
  specs.md
  progress.yaml
  auto_knowledge.md
  changes.log
  state_diagram.md
  settings.yaml
```

---

### validate

Check project alignment with the Prime Directive.

```bash
python3 cli.py validate <project_name> [--path <sidecar_path>]
```

**Arguments:**
- `project_name` — Name of the project to validate

**Options:**
- `--path`, `-p` — Path to sidecar if not in default location

**Example:**
```bash
python3 cli.py validate my-awesome-app
```

**Success Output:**
```
✓ my-awesome-app passes validation
```

**Failure Output:**
```
✗ my-awesome-app has 2 issue(s):
  - Missing required file: specs.md
  - Missing required file: progress.yaml

⚠ my-awesome-app has 1 warning(s):
  - auto_knowledge.md has no lessons captured yet
```

**What it checks:**
- Required files exist (`specs.md`, `progress.yaml`, `auto_knowledge.md`)
- `progress.yaml` has valid phase
- Basic structural integrity

---

### aggregate-lessons

Synthesize lessons across all archived projects.

```bash
python3 cli.py aggregate-lessons [--verbose]
```

**Example:**
```bash
python3 cli.py aggregate-lessons
```

**Output:**
```
Found 12 lessons across 4 projects
```

**With verbose:**
```bash
python3 cli.py aggregate-lessons --verbose
```

**Output:**
```
Found 12 lessons across 4 projects

============================================================

[my-app_2026-01-15]
## 2026-01-10 — Token Refresh Edge Case

**What happened**: Refresh tokens expired during long operations
**Why it mattered**: Users got logged out mid-task
**Lesson learned**: Implement token refresh before operations > 5min

----------------------------------------

[other-project_2026-02-01]
## 2026-01-28 — API Rate Limiting

**What happened**: Hit third-party rate limits during batch processing
...
```

---

### status

Show project status.

```bash
python3 cli.py status [project_name]
```

**Arguments:**
- `project_name` — (Optional) Specific project to check

**Show all projects:**
```bash
python3 cli.py status
```

**Output:**
```
Active Sidecars:
  my-awesome-app: implementation
  side-project: planning

Archived Projects: 4 in master_projects/
```

**Show specific project:**
```bash
python3 cli.py status my-awesome-app
```

**Output:**
```
Project: my-awesome-app
  phase: implementation
  last_updated: 2026-02-26
```

---

## Personality Mode

Add `--mother` flag to get personality-infused output:

```bash
python3 cli.py --mother init my-project
```

**Output:**
```
MOTHER ONLINE. Personality blend active.

✓ Initialized my-project sidecar.

If I may, sir — I've prepared the standard template 
with all required files. The probability of a successful 
project is... well, that depends entirely on you.

I'll be here if you need me. At your service, sir.
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (file not found, validation failed, etc.) |

---

## Environment Variables

The CLI respects these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MOTHER_ROOT` | Script directory | Path to Mother installation |

---

## Examples

### Full Workflow

```bash
# 1. Initialize a new project
python3 cli.py init my-api

# 2. ... work on the project ...

# 3. Check status
python3 cli.py status my-api

# 4. Validate alignment
python3 cli.py validate my-api

# 5. Archive when complete
python3 cli.py archive my-api

# 6. Learn from all projects
python3 cli.py aggregate-lessons --verbose
```

### With Personality Mode

```bash
# Morning check-in with Mother
python3 cli.py --mother status

# Output:
# MOTHER ONLINE. Personality blend active.
#
# Active Sidecars:
#   my-api: implementation
#
# Probability of on-time completion: 73%.
# That's better than yesterday. Keep going.
```

---

## Troubleshooting

### "Could not find sidecar for X"

The CLI looks for sidecars at `~/Desktop/{project}-mother/`.

**Solutions:**
1. Check the folder exists
2. Use `--path` to specify location:
   ```bash
   python3 cli.py validate my-project --path ~/somewhere/else/my-project-mother
   ```

### "Missing required file"

Your sidecar is incomplete.

**Solution:**
Copy missing files from the template:
```bash
cp ~/Desktop/Mother/templates/new_project_sidecar/tars/PROJECT_NAME/specs.md \
   ~/Desktop/my-project-mother/tars/my-project/
```

### "Archive already exists"

You've already archived this project today.

**Solutions:**
1. Delete the existing archive if you want to replace it
2. Wait until tomorrow (archives are date-stamped)
3. Rename the existing archive

---

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    CLI REFERENCE COMPLETE                                     ║
║                                                                              ║
║                    "Confirmed. Additional customization?"                     ║
║                                                              — TARS          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```
