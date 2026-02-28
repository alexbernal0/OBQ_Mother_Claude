# OBQ_Profile — Active Profile Backup

This folder contains a snapshot of the currently deployed OBQ Claude identity files.

Use this to:
- Back up your current profile before making changes
- Review what's currently deployed
- Restore a previous profile if needed
- Transfer the profile to another machine

## Files

| File | Deployed To | Purpose |
|------|------------|---------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Global identity — loaded every session |
| `SOUL.md` | Reference (Mother_Claude) | Core character and values |
| `IDENTITY.md` | Reference (Mother_Claude) | Role, expertise, operating principles |
| `PRINCIPLES.md` | Reference (Mother_Claude) | Decision playbook + domain laws |
| `USER.md` | Reference (Mother_Claude) | Alex's profile and preferences |
| `HEARTBEAT.md` | Reference (Mother_Claude) | Session start/end rituals |
| `NOW.md` | Reference (Mother_Claude) | Live state template |

## Restoring from Backup

```bash
# Restore global CLAUDE.md
cp OBQ_Profile/CLAUDE.md ~/.claude/CLAUDE.md

# Restore all soul files
cp OBQ_Profile/*.md ../soul/

# Redeploy everything from Mother_Claude
cd ..
python deploy.py all
```

## Updating This Backup

After making changes to soul files or CLAUDE.md, update this folder:

```bash
cd OBQ_Mother_Claude
cp ~/.claude/CLAUDE.md OBQ_Profile/CLAUDE.md
cp soul/*.md OBQ_Profile/
git add OBQ_Profile/
git commit -m "Update OBQ_Profile snapshot: [what changed]"
git push
```

*OBQ_Profile | Snapshot: 2026-02-28 | Version: 1.0*
