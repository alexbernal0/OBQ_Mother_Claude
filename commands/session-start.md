---
description: Orient to current OBQ project — check memory state, surface last session, review active tasks
---

Run the OBQ session start ritual:

1. Check if `$HOME/.pending-supermemory-review` flag exists. If yes: review recent session context for SuperMemory-worthy insights and suggest /super-save if applicable.

2. Look for `tasks/lessons.md` in the current working directory. If it exists, read the last 5 entries and flag any that are relevant to the current work.

3. Look for `NOW.md` in the current working directory. If it exists, read it and summarize current project state, open questions, and next steps.

4. Look for any `.ipynb` or `.py` files modified in the last 24 hours: `!find . -name "*.py" -o -name "*.ipynb" | xargs ls -t 2>/dev/null | head -10`

5. Provide a concise brief: "Working on [PROJECT]. Last: [what was done]. Next: [what to do]. Any blockers: [list or 'none']."
