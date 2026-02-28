---
name: heartbeat
description: "OBQ session start ritual — checks RSL memory loop flag, surfaces last session state from NOW.md, reads recent lessons, and orients to the active project. Run at the start of any OBQ development session."
disable-model-invocation: true
---

## Session Context
- Current date: !`date /t`
- Active branch (if in git repo): !`git branch --show-current 2>/dev/null || echo "not a git repo"`
- Pending SuperMemory flag: !`test -f "$HOME/.pending-supermemory-review" && echo "YES - review needed" || echo "none"`

## Heartbeat Ritual

Follow these steps in order:

### Step 1: Check Pending SuperMemory Flag

Check whether the file `$HOME/.pending-supermemory-review` exists (shown in Session Context above as "YES - review needed" or "none").

- If **YES**: Review the most recent session output, strategy results, or lessons for any insights worthy of long-term retention in SuperMemory. Run `/super-save` if you find anything significant. Then delete the flag file.
- If **none**: Continue to step 2.

### Step 2: Surface Recent Lessons

Look for `tasks/lessons.md` in the current working directory.

- If it exists: Read the last 5 entries. Identify any patterns or warnings that are relevant to the current project context. Briefly surface them to Alex.
- If it does not exist: Note that no lessons file was found and move on.

### Step 3: Read NOW.md

Look for `NOW.md` in the current working directory.

- If it exists: Read it and extract: (a) current project state, (b) open questions or blockers, (c) next steps.
- If it does not exist: Note that no NOW.md was found — suggest Alex create one at session end.

### Step 4: Orient and Confirm

Present Alex with a single concise brief in this format:

> "Ready. Working on **[PROJECT NAME]**. [One sentence summary of last session state from NOW.md]. Next: [next steps from NOW.md or best inference]. Confirm or redirect?"

Wait for Alex's response before proceeding with any work.
