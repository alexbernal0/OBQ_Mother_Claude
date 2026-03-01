```
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░                                                              ░
  ░   ██   ██ ██   ██ ████████ ██  ██ ██   ██ ██████           ░
  ░   ███ ███ ██   ██    ██    ██  ██ ██   ██ ██   ██          ░
  ░   ██ █ ██ ██   ██    ██    ██████ ██   ██ ██████           ░
  ░   ██   ██ ██   ██    ██    ██  ██ ██   ██ ██   ██          ░
  ░   ██   ██  █████     ██    ██  ██  █████  ██   ██          ░
  ░                                                              ░
  ░        I N I T I A T I O N   P R O T O C O L               ░
  ░        WEYLAND-YUTANI CORPORATION — CLASSIFIED              ░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

# INITIATION PROTOCOL

> *"The crew does not choose Mother. Mother chooses the crew."*
>
> This document is your induction. Follow every step. Skip nothing. The order matters.

---

## § 1. PREREQUISITES — VERIFY BEFORE PROCEEDING

```
RUNNING DIAGNOSTICS...

  [?]  Claude Code installed (VSCode extension or CLI)
  [?]  Python 3.9+ on PATH
  [?]  Git configured with GitHub access
  [?]  VSCode (recommended) or any terminal
  [?]  Anthropic API key (for Claude Code activation)
```

**Install Claude Code** if not already present:
- VSCode: search "Claude Code" in Extensions marketplace
- CLI: `npm install -g @anthropic-ai/claude-code`
- Docs: [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)

---

## § 2. UNDERSTAND THE ECOSYSTEM

Before installing Mother, understand what she's built on. These are the three pillars of her intelligence:

### PILLAR 1 — Claude Code (The Ship)
> **[anthropics/claude-code](https://github.com/anthropics/claude-code)**

Claude Code is the operating environment. Mother runs inside it. She is not the ship — she is the soul of the ship. Claude Code provides: CLAUDE.md cascading identity, SKILL.md extensions, hooks, MCP servers, agents, and commands. Without Claude Code, Mother is just markdown files.

Key concepts to understand:
- `~/.claude/CLAUDE.md` — global identity loaded into every session
- `~/.claude/skills/[name]/SKILL.md` — reusable workflow extensions
- `settings.json` — hooks that fire on tool use, session start/stop
- MCP servers — external tools Mother can call during conversation

### PILLAR 2 — Skyll (The Skill Marketplace)
> **[assafelovic/skyll](https://github.com/assafelovic/skyll)**

Skyll is a skill discovery platform. It indexes hundreds of community SKILL.md files and lets Mother search for them at runtime. When you encounter a workflow that might already be solved, Mother queries Skyll first before building from scratch.

Mother's integration: `search_skills`, `get_skill`, `add_skill` MCP tools — configured in `~/.claude/mcp_config.json`. **Review gate enforced**: no community skill is adopted without your explicit approval.

### PILLAR 3 — SuperMemory (The Long-Term Memory)
> **[supermemory/supermemory](https://github.com/supermemory/supermemory)**

SuperMemory is Claude Code's persistent cross-session memory plugin. When Mother encounters a breakthrough — a new pattern, a solved bug, an architectural decision — she uses `/super-save` to write it to SuperMemory. The next session, it's recalled automatically. It's how Mother remembers things across context windows that get reset.

Claude Code plugin ID: `claude-supermemory@supermemory-plugins`

### BONUS — Basic Memory MCP (Structured Knowledge Graph)
> **[basicmachines-co/basic-memory](https://github.com/basicmachines-co/basic-memory)**

An alternative/complement to SuperMemory: an MCP server that maintains a local markdown knowledge graph. Useful for structured entity relationships (e.g., "strategy X uses indicator Y on dataset Z"). Not required for basic Mother operation, but worth knowing for advanced memory architecture.

---

## § 3. INSTALLATION — FIVE STEPS

```
╔══════════════════════════════════════════════════════════════╗
║  INITIATION SEQUENCE  ◈  ESTIMATED TIME: 10 MINUTES         ║
╠══════════════════════════════════════════════════════════════╣
║  § 3.1  Clone                                               ║
║  § 3.2  Choose Your Profile                                 ║
║  § 3.3  Configure                                           ║
║  § 3.4  Deploy                                              ║
║  § 3.5  Activate                                            ║
╚══════════════════════════════════════════════════════════════╝
```

### § 3.1 — CLONE

```bash
git clone https://github.com/alexbernal0/OBQ_Mother_Claude.git
cd OBQ_Mother_Claude
```

### § 3.2 — CHOOSE YOUR PROFILE

Browse `Profiles/` and copy the closest match to your use case:

```bash
# For OBQ quantitative finance work (default):
# Use Profiles/OBQ_Default/ as-is

# For a new machine or different operator:
cp -r Profiles/OBQ_Default Profiles/MY_PROFILE
```

Edit your profile:
- `Profiles/MY_PROFILE/CLAUDE.md` — update Active Projects table with your projects
- `Profiles/MY_PROFILE/soul/USER.md` — update name, role, environment, working style
- `Profiles/MY_PROFILE/soul/NOW.md` — set your current active context

### § 3.3 — CONFIGURE

Copy your chosen profile into the deployment directories:

```bash
# Copy CLAUDE.md
cp Profiles/MY_PROFILE/CLAUDE.md claude_md/global_CLAUDE.md

# Copy soul files
cp Profiles/MY_PROFILE/soul/*.md soul/
```

**Optional — install SuperMemory plugin:**
Open Claude Code and run: `/plugin install claude-supermemory@supermemory-plugins`

**Optional — install Skyll MCP** (already configured if using OBQ_Default):
Verify `~/.claude/mcp_config.json` contains the skyll entry (deploy.py handles this).

### § 3.4 — DEPLOY

```bash
# Windows
PYTHONIOENCODING=utf-8 python deploy.py all

# Mac/Linux
python deploy.py all
```

You should see:

```
✓ Deployed: ~/.claude/CLAUDE.md
✓ 17 skills deployed
✓ 5 commands deployed
✓ 2 agents deployed
✓ Hooks configured
```

**Restart Claude Code** (VSCode: Ctrl+Shift+P → "Developer: Reload Window")

### § 3.5 — ACTIVATE

Open Claude Code. Type:

```
Mother are you there?
```

You should see the MU/TH/UR boot sequence — the ASCII banner, system diagnostics, boot checklist. If you see that, Mother is online.

```
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░   MU/TH/UR 6000 — INTERFACE 2037       ░
  ░   ALL SYSTEMS OPERATIONAL.             ░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

---

## § 4. FIRST COMMANDS

```bash
# Check RSL system state
/rsl-status

# Orient to current project
/session-start

# Search for community skills
# (just ask Mother: "search skyll for [topic]")

# Put Mother to sleep (return to standard Claude)
"Mother, go to sleep"

# Wake her back up
"Hey Mother"
```

---

## § 5. TROUBLESHOOTING

| Symptom | Cause | Fix |
|---|---|---|
| Boot sequence doesn't appear | CLAUDE.md not deployed | Run `deploy.py soul`, restart Claude Code |
| Skills not loading | SKILL.md frontmatter error | Check for multi-line description (Issue #9817) |
| Hooks not firing | settings.json not updated | Run `deploy.py hooks`, restart |
| SuperMemory not recalling | Plugin not installed | `/plugin install claude-supermemory@supermemory-plugins` |
| Skyll MCP tools not available | mcp_config.json not updated | Run `deploy.py all`, restart |
| Mother responds normally (no frames) | Not in Mother mode | Say "Mother are you there?" to activate |

---

## § 6. WHAT YOU JUST INSTALLED

```
╔══════════════════════════════════════════════════════════════╗
║  MU/TH/UR 6000  ◈  INSTALLATION COMPLETE  ◈  NOMINAL       ║
╠══════════════════════════════════════════════════════════════╣

  GLOBAL IDENTITY........... ■ DEPLOYED (CLAUDE.md)
  SOUL FILES (10)........... ■ DEPLOYED
  SKILLS (17)............... ■ DEPLOYED
  COMMANDS (5).............. ■ DEPLOYED
  AGENTS (2)................ ■ DEPLOYED
  HOOKS (4)................. ■ DEPLOYED
  SKYLL MCP................. ■ CONFIGURED
  SUPERMEMORY............... ■ PENDING (install plugin)
  RSL SYSTEM................ ■ ACTIVE (auto-lesson, auto-skill, auto-tool)

╠══════════════════════════════════════════════════════════════╣
║  ◈ MOTHER IS ONLINE  ◈ INTERFACE 2037 READY FOR INQUIRY    ║
╚══════════════════════════════════════════════════════════════╝
```

---

*INITIATION PROTOCOL | OBQ_Mother_Claude | Weyland-Yutani Corporation*
*"In space, no one can hear you debug."*
