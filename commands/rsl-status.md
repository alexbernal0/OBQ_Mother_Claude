# /rsl-status

Show the current state of the OBQ Recursive Self-Learning loop.

## What to Check

Run these checks in order and present a structured status report.

### 1. Pending Flags

Look for `.pending-supermemory-review` in:
- The current working directory
- The active project root (from MEMORY.md Active Project)
- `C:\Users\admin\Desktop\Mother_Claude\OBQ_Mother_Claude\`

Report: found / not found. If found — how old (check file mtime). Remind: this should be resolved at session start.

### 2. lessons.md State

Check `tasks/lessons.md` in the active project (or `~/.claude/projects/*/lessons.md` if no active project).

Report:
- Total entry count
- Last 3 entries (date + title only)
- Days since last entry
- If >20 entries and no recent synthesis: flag "Synthesis overdue — run /synthesize-memory"

### 3. Skills Added Recently

Check `~/.claude/skills/` for directories modified in the last 7 days.

Report each new/modified skill: name + date modified.

### 4. Tools Crystallized

Check `~/.claude/tools/` directory (may not exist yet — create if not):
- List all `.py` and `.sh` files
- Show file count and last modified

### 5. SuperMemory Activity

Report:
- Last `/super-save` call from session history (if determinable from context)
- Reminder: check SuperMemory via `/super-search "recent OBQ work"` to verify what's been persisted

### 6. Synthesis Schedule

Check the date of the last `/synthesize-memory` run (look for synthesis timestamps in MEMORY.md or lessons.md).

If last synthesis was >30 days ago: flag "Monthly synthesis due — run /synthesize-memory"

### 7. auto-tool Candidates (if session is active)

List any auto-tool candidates detected this session that haven't been extracted or skipped.

---

## Output Format

```
RSL STATUS — [DATE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PENDING FLAGS
  .pending-supermemory-review   → [found: X days old / not found]

LESSONS.MD  (active project: [PROJECT])
  Total entries: [N]
  Last entry:    [DATE] — [TITLE]
  Status:        [OK / SYNTHESIS OVERDUE (N entries)]

SKILLS (last 7 days)
  [skill-name]  [date]
  [No new skills added]

TOOLS (~/.claude/tools/)
  [N files]  last modified: [DATE]
  [No tools directory yet]

SUPERMEMORY
  [Check manually: /super-search "recent OBQ work"]

SYNTHESIS SCHEDULE
  Last synthesize-memory: [DATE / unknown]
  Status: [OK / OVERDUE — run /synthesize-memory]

AUTO-TOOL CANDIDATES (this session)
  [N candidates pending] or [None detected]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT ACTION: [most urgent RSL action — one line]
```

---

## Also Do

After showing the report:

1. If synthesis is overdue: ask "Want to run /synthesize-memory now?"
2. If .pending-supermemory-review is old (>24h): ask "Want to review this and decide on /super-save?"
3. If no tools directory: suggest "Want me to create ~/.claude/tools/ now?"
4. If no recent lessons: ask "No lessons logged recently — did anything interesting happen last session?"
