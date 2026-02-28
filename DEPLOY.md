# OBQ_Mother_Claude — Complete Installation Guide

## Prerequisites

- Claude Code installed (VSCode extension or CLI)
- Python 3.11+ available
- Git installed
- Windows 11 (primary target) — paths use Windows conventions

---

## Step 1: Get the Repository

```bash
cd ~/Desktop
git clone https://github.com/alexbernal0/OBQ_Mother_Claude
cd OBQ_Mother_Claude
```

---

## Step 2: Run Full Deployment

```bash
python deploy.py all
```

This will:
1. Back up any existing `~/.claude/CLAUDE.md`
2. Deploy `global_CLAUDE.md` → `~/.claude/CLAUDE.md`
3. Copy all 14 skills → `~/.claude/skills/`
4. Copy 2 agents → `~/.claude/agents/`
5. Copy 4 commands → `~/.claude/commands/`
6. Copy hook scripts → `~/.claude/hooks/`
7. Update `~/.claude/settings.json` with hook configuration
8. Print MCP install commands

---

## Step 3: Install MCP Servers

Run these commands in your terminal:

```bash
# Install uv if needed (fast Python package runner)
pip install uv

# 1. MotherDuck/DuckDB — query databases directly in Claude conversations
claude mcp add --scope user duckdb --transport stdio -- \
  uvx mcp-server-motherduck --db-path :memory: --read-write --allow-switch-databases

# 2. Memory Graph — structured cross-session knowledge
claude mcp add --scope user memory --transport stdio -- \
  npx -y @modelcontextprotocol/server-memory

# 3. Fetch — web content and academic paper retrieval
claude mcp add --scope user fetch --transport stdio -- \
  npx -y @modelcontextprotocol/server-fetch
```

Then in a Claude Code session, install Context7 (live docs):
```
/plugin install context7
```

---

## Step 4: Set Environment Variables

Ensure these are in your `.env` or system environment:

```
EODHD_API_KEY=your_key
MOTHERDUCK_TOKEN=your_token
ANTHROPIC_API_KEY=your_key
XAI_API_KEY=your_key
GROQ_API_KEY=your_key
OPENAI_API_KEY=your_key
EXA_API_KEY=your_key
```

The `MOTHERDUCK_TOKEN` env var is especially critical — the DuckDB MCP server uses it.

---

## Step 5: Restart Claude Code

Close and reopen VS Code or restart the Claude Code CLI. The global CLAUDE.md will
be loaded automatically on next session start.

---

## Step 6: Verify Deployment

```bash
python deploy.py status
```

All items should show `✓`. Then open Claude Code and run:
```
/session-start
```

Claude should orient to your active project and confirm it has loaded the OBQ identity.

---

## Step 7: Add Project CLAUDE.md Files (Optional but Recommended)

For each active project, add a project-specific CLAUDE.md:

```bash
# For PapersWBacktest (VBT strategy project)
python deploy.py project "D:/Master Data Backup 2025/PapersWBacktest"

# For OBQ_AI (Flask app project)
python deploy.py project "C:/Users/admin/Desktop/OBQ_AI"
```

Select the appropriate template when prompted.

---

## Updating After Changes

When you modify soul files or add new skills:

```bash
# Redeploy everything
python deploy.py all

# Or redeploy specific components
python deploy.py soul         # CLAUDE.md changed
python deploy.py skills       # Added/modified skills
python deploy.py hooks        # Hook scripts changed
```

Always push changes to GitHub after updating:
```bash
git add -A
git commit -m "Update OBQ_Mother_Claude: [what changed]"
git push
```

---

## File Locations After Deployment

| Component | Location |
|-----------|----------|
| Global CLAUDE.md | `~/.claude/CLAUDE.md` |
| Skills | `~/.claude/skills/<name>/SKILL.md` |
| Agents | `~/.claude/agents/<name>.md` |
| Commands | `~/.claude/commands/<name>.md` |
| Hook scripts | `~/.claude/hooks/` |
| Settings | `~/.claude/settings.json` |
| MCP config | `~/.claude/mcp_config.json` (managed by `claude mcp add`) |
| Auto-memory | `~/.claude/projects/<hash>/memory/MEMORY.md` (auto-managed) |

---

## Troubleshooting

**Skills not appearing:** Check SKILL.md frontmatter — description must be single-line quoted string.
Restart Claude Code after adding skills.

**Hooks not firing:** Check `~/.claude/settings.json` has the hooks array populated.
Hook scripts must exist at the paths referenced in settings.json.

**MotherDuck MCP not connecting:** Ensure `MOTHERDUCK_TOKEN` is set in your environment
(not just in .env file — it must be in the shell environment where Claude Code launches).

**CLAUDE.md not loading:** It must be at exactly `~/.claude/CLAUDE.md` (not a subdirectory).
Run `python deploy.py status` to verify the path.

---

*DEPLOY.md | OBQ_Mother_Claude | 2026-02-28*
