---
name: auto-skill
description: "Monitors conversations for teachable repeatable workflows and offers to create a reusable Claude Code skill when a good candidate is found and no equivalent exists. Options: Let's Do It (draft now), Deep Research (subagent proposes), Skip, or Save to Template. Use when user says 'turn on auto-skill', 'autoskill on', 'watch for skills', or runs /autoskill-on."
compatibility: "Claude Code (VSCode + CLI) and OpenCode — single .claude/skills/ path works in both"
metadata:
  author: OBQ
  source: OBQ_Claude_Inception
  updated: "2026-02-23"
  version: "1.1"
  allowed-tools: "Read, Glob"
---

# Auto-Skill

> **In one sentence:** When auto-skill is on, I watch for teachable repeatable workflows and offer to create a Claude Code skill — only if no equivalent already exists.

---

## Compatibility

This skill lives in `.claude/skills/auto-skill/SKILL.md`. It works without modification in:
- **Claude Code** (VSCode extension and CLI) — native path
- **OpenCode** — reads `.claude/skills/` automatically as a compatibility layer

No duplicate copies needed. One file, both tools.

---

## When This Skill Applies

- **Only** when the user has explicitly enabled auto-skill by running `/autoskill-on` or saying "turn on auto-skill" / "autoskill on" / "watch for skills".
- If not enabled — stay completely silent. Do not mention auto-skill or offer extraction.
- Works alongside all other active skills without conflict.

---

## Skill vs MEMORY.md Decision Gate

Before offering a skill, determine: **is this better as a skill or a MEMORY.md entry?**

| Pattern | Better as |
|---|---|
| Repeatable workflow — clear steps, inputs, outputs, nameable goal | **Skill** |
| One-time architectural decision for this project | **MEMORY.md** |
| Project-specific constant, preference, or convention | **MEMORY.md** |
| Persistent user preference that applies to all sessions | **MEMORY.md** |
| Domain procedure reusable across multiple codebases | **Skill (user-level)** |

If MEMORY.md is the better fit, say: *"This looks like it's better captured in MEMORY.md than as a skill — want me to add it there instead?"* and handle accordingly.

---

## Before Offering: Full Checklist

Confirm ALL before offering:

- [ ] Pattern is **teachable and repeatable** — clear steps, bounded I/O, nameable goal
- [ ] **Not better as a MEMORY.md entry** (see gate above)
- [ ] **No equivalent** in `.claude/skills/`, `~/.claude/skills/`, `.opencode/skills/`, or `~/.config/opencode/skills/`
- [ ] Currently installed user skills (`make-no-mistakes`, `taskmaster`) don't already cover it
- [ ] Auto-skill is **on** this session
- [ ] This is **not** a one-off question, vague request, or trivial single-file edit
- [ ] User has **not** chosen Skip or turned off auto-skill in this thread

---

## Monitoring for Skill Candidates

**Assess at the end of each completed task** — not mid-thought.

### Positive triggers
- Multi-step workflow executed with clear steps, inputs, outputs, and a nameable goal
- Domain-specific procedure tied to project layout, tools, or conventions
- Same or similar pattern appeared earlier in this session or described as habitual
- You could write a SKILL.md name and one-sentence description immediately

### Negative triggers — never offer for
- One-off questions or single factual answers
- Vague requests with no repeatable steps
- Trivial single-file edits or small refactors
- User recently chose Skip in this thread
- Equivalent skill already exists (state which one covers it)

### Examples

| Situation | Offer? |
|---|---|
| Agent runs build → push → deploy (3 clear steps) | Yes |
| Agent follows project-specific review checklist | Yes |
| Repeating the same ATR optimization pattern from earlier | Yes |
| "What does this function return?" | No — one-off |
| "Fix this typo" | No — trivial |
| `deploy-to-staging` skill already exists | No — covered |

---

## The Four Options

When the checklist passes, pause and offer:

> It looks like this might be a good candidate for a skill.
>
> 1. **Let's Do It** — Draft the skill together now; you review before anything is saved.
> 2. **Deep Research** — I spawn a subagent to research and propose a full draft; you review before any files are written.
> 3. **Skip** — Continue current task; no skill created (no re-offer this session).
> 4. **Save to Template** — Same as Let's Do It, but also saves to `OBQ_Claude_Inception/skills/` as a permanent reusable template.

Wait for the user to respond before proceeding.

---

## Handling Each Choice

### 1. Let's Do It

Draft in-chat in this order:

1. **Name** — kebab-case only (e.g. `deploy-to-staging`). No spaces, underscores, or capitals. Matches folder name exactly.
2. **Scope** (see Scope Decision Tree below)
3. **Frontmatter** — CRITICAL: all values must be single-line quoted strings. No YAML block scalars (`>-` or `|`):
   ```yaml
   ---
   name: skill-name
   description: "What it does and when to use it — include trigger phrases. Single line only."
   version: "1.0"
   compatibility: "Claude Code (VSCode + CLI), OpenCode"
   allowed-tools: Read, Glob
   metadata:
     author: OBQ
     source: OBQ_Claude_Inception
   ---
   ```
   > **Warning:** Multi-line `description` using `>-` or `|` causes **silent skill discovery failure** in Claude Code (Issue #9817). Always use a quoted single-line string.
4. **Body structure:**
   - Steps — numbered, concrete, executable
   - Examples — `User says: … → Actions: … → Result: …` (minimum 2)
   - Troubleshooting — `Symptom / Cause / Solution` (minimum 2)
5. **Optional folders** — only if genuinely needed:
   - `scripts/` — executable code run repeatedly
   - `references/` — docs Claude should read while working
   - `assets/` — output files (not loaded into context)
6. **No `README.md`** inside the skill folder — all docs in `SKILL.md` or `references/`.
7. **No `argument-hint` field** — causes parse errors in OpenCode.

**CRITICAL:** Do not create or modify any file until the user **explicitly approves** the draft (e.g. "yes save it", "looks good", "go ahead"). Show full proposed path + full contents first. Wait for approval.

**After saving:**
- Suggest: "Want to test this in a fresh context?"
- If user-level skill with Bash tools: note the known `allowed-tools` bug — add Bash patterns directly to `~/.claude/settings.json → permissions.allow` as a workaround (Issue #14956).

### 2. Deep Research

Spawn a subagent using Claude Code's native Task tool:

```
Use the Task tool with subagent_type "Plan" to research this workflow:
"[brief description of the task/workflow]"

The subagent should propose:
- Skill name (kebab-case)
- Full SKILL.md draft with single-line YAML frontmatter
  (name, description with what+when+triggers, version, compatibility, allowed-tools)
- Body: steps, 2-3 examples, troubleshooting
- Recommended scope: project / user / OBQ_Claude_Inception template
- Optional folders needed (scripts/, references/, assets/)

Do NOT write any files. Return proposal for user review only.
```

Present the full proposal. Only write files after explicit user approval.

### 3. Skip

Acknowledge and continue. Do not re-offer for this pattern in this session. Reset only when user explicitly re-enables auto-skill or starts a new session.

### 4. Save to Template

Same flow as **Let's Do It**, but after user approves, save to **both**:
1. The appropriate project or user skills path (`.claude/skills/` or `~/.claude/skills/`)
2. `C:/Users/admin/Desktop/OBQ_Claude_Inception/skills/<skill-name>/SKILL.md`

The OBQ_Claude_Inception copy is the canonical template — it propagates to all future Claude projects. Confirm both save paths with the user before writing anything.

---

## Scope Decision Tree

```
Is this skill useful only in this specific project?
  Yes → .claude/skills/<name>/              (project-level)
  No  →
    Reusable across all your projects?
      Yes →
        Evergreen — should live in every future project?
          Yes → ~/.claude/skills/<name>/
                + OBQ_Claude_Inception/skills/<name>/  (template)
          No  → ~/.claude/skills/<name>/              (user-level only)
      No  → .claude/skills/<name>/              (project-level)
```

---

## Session Deduplication

- Once an offer is made for a pattern (any option chosen), do not re-offer for the same workflow in this session.
- A **new distinct workflow** that emerges later → offer normally.
- Reset at the start of every new session.

---

## Examples

**Example 1: ATR optimization pipeline**
- Agent loads parquet, runs ATR backtests, saves results — repeatable data science workflow.
- Checklist passes → offers 4 options → user picks "Save to Template".
- Result: `atr-optimization` skill saved to `.claude/skills/` AND `OBQ_Claude_Inception/`.

**Example 2: Git release procedure**
- User does: bump version → changelog → tag → push → PR — same every release.
- Checklist passes → user picks "Let's Do It".
- Result: `git-release` skill drafted, approved, saved to `~/.claude/skills/`.

**Example 3: One-off question (no offer)**
- "What does ThreeGaugeSignal return for flat bars?"
- No offer — single factual answer, no repeatable workflow.

**Example 4: MEMORY.md redirect**
- Agent completes a one-time schema migration. User says "remember this pattern".
- Gate check: one-time architectural decision → suggest MEMORY.md, not a skill.

**Example 5: Equivalent exists (no offer)**
- Agent runs deploy steps. `.claude/skills/` check finds `deploy-to-staging` already exists.
- No offer. Agent notes: "Already covered by `deploy-to-staging`."

---

## Troubleshooting

**Symptom:** Skill never loads or triggers in Claude Code.
- **Cause:** Multi-line YAML block scalar in frontmatter (Issue #9817).
- **Solution:** Ensure `description` is a single quoted string on one line. No `>-` or `|`. Check for any line break inside the `---` frontmatter block.

**Symptom:** User said Skip but agent keeps re-offering.
- **Cause:** Same session re-detection of similar pattern.
- **Solution:** Treat Skip as session-wide. Track offered patterns; do not re-offer until new session.

**Symptom:** `allowed-tools` not granting Bash permissions.
- **Cause:** Known Claude Code bug (Issue #14956).
- **Solution:** Add the Bash pattern to `~/.claude/settings.json`:
  ```json
  { "permissions": { "allow": ["Bash(your-command *)"] } }
  ```

**Symptom:** Skill works in Claude Code but breaks in OpenCode.
- **Cause:** `argument-hint` field in frontmatter — unsupported in OpenCode.
- **Solution:** Remove `argument-hint` from all SKILL.md frontmatter.

**Symptom:** Agent never offers even on clear repeatable workflows.
- **Cause:** Auto-skill not enabled this session, or description triggers too narrow.
- **Solution:** Confirm user said "autoskill on" or ran `/autoskill-on`. If enabled, add more trigger phrases to this skill's `description` field.

---

## Turning Auto-Skill Off

Any of these turns it off for the session: "stop", "turn it off", "skip all", "no more skill offers". Re-enable with `/autoskill-on` or "turn on auto-skill".

---

## How to Test This Skill

- **Trigger test:** Run a multi-step repeatable workflow → confirm 4 options appear.
- **One-off test:** Ask a factual question → confirm no offer.
- **Skip persistence:** Choose Skip → confirm no re-offer same session.
- **MEMORY.md gate:** Describe a one-time decision → confirm MEMORY.md suggestion instead.
- **Existing skill test:** Create a dummy skill in `.claude/skills/` → run matching workflow → confirm no offer (agent states which skill covers it).
- **Let's Do It draft:** Confirm — kebab-case name, single-line frontmatter, no `argument-hint`, steps + examples + troubleshooting, no file written until explicitly approved.
- **OpenCode compat:** Confirm skill loads when running OpenCode from the same project root.

---

## Related Skills

- **make-no-mistakes** (installed) — invoke for precision-critical skill drafts
- **taskmaster** (installed) — tracks task completion; auto-skill does not conflict with it
- **create-skill** — if available, use to validate naming and structure of new drafts
- **optimize-skill** — if available, use to improve an existing skill post-creation
