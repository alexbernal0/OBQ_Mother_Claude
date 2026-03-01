```
╔══════════════════════════════════════════════════════════════╗
║  MU/TH/UR 6000  ◈  PROFILES DIRECTORY  ◈  CLASSIFICATION   ║
║  WEYLAND-YUTANI CORPORATION — AUTHORIZED PERSONNEL ONLY     ║
╚══════════════════════════════════════════════════════════════╝
```

# PROFILES

Each profile is a complete, self-contained Mother configuration for a specific machine, operator, or deployment context. Drop a profile onto any machine, run `deploy.py`, and Mother boots with that identity fully intact.

---

## Profile Structure

```
Profiles/
└── [PROFILE_NAME]/
    ├── CLAUDE.md          ← Global identity deployed to ~/.claude/CLAUDE.md
    └── soul/
        ├── SOUL.md                ← Core drive and mission
        ├── IDENTITY.md            ← Role, expertise, operating principles
        ├── PRINCIPLES.md          ← Domain laws and non-negotiables
        ├── USER.md                ← Collaborator profile
        ├── HEARTBEAT.md           ← Boot checklist and session rituals
        ├── NOW.md                 ← Active context (update each session)
        ├── MOTHER_ENHANCED.md     ← MU/TH/UR 6000 character profile
        ├── JARVIS_ENHANCED.md     ← J.A.R.V.I.S. character profile
        ├── TARS_ENHANCED.md       ← TARS character profile
        └── DISPLAY_PROTOCOL.md   ← Visual formatting system
```

---

## Available Profiles

| Profile | Operator | Machine | Specialization |
|---|---|---|---|
| `OBQ_Default` | Alex Bernal / CTO | Windows 11 workstation | Full OBQ stack — VBT, MotherDuck, EODHD, LangGraph |

---

## How to Deploy a Profile

```bash
# 1. Clone the repo (or copy profile folder to target machine)
git clone https://github.com/alexbernal0/OBQ_Mother_Claude.git

# 2. Copy desired profile into the repo root structure
cp -r Profiles/OBQ_Default/CLAUDE.md claude_md/global_CLAUDE.md
cp -r Profiles/OBQ_Default/soul/* soul/

# 3. Run deploy
PYTHONIOENCODING=utf-8 python deploy.py all

# 4. Restart Claude Code — then test:
# "Mother are you there?"
```

---

## How to Create a New Profile

1. Copy an existing profile: `cp -r Profiles/OBQ_Default Profiles/NEW_NAME`
2. Edit `CLAUDE.md` — update Active Projects table, API keys context, specialization
3. Edit `soul/USER.md` — update operator name, environment, working style
4. Edit `soul/NOW.md` — set current active context for that machine
5. Edit `soul/IDENTITY.md` — add/remove domain expertise as needed
6. Run `deploy.py all` on the target machine

---

*PROFILES | OBQ_Mother_Claude | Weyland-Yutani Corporation*
*"Every crew needs a Mother. Every Mother needs a mission."*
