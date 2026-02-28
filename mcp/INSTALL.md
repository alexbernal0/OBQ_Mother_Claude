# MCP Server Installation Guide

This guide covers installation and verification of all MCP servers used by OBQ_Mother_Claude.

---

## Prerequisites

### Node.js (required for memory and fetch servers)

```bash
# Check if Node.js is installed (need 18+)
node --version

# If not installed, download from https://nodejs.org/
# Or via winget on Windows:
winget install OpenJS.NodeJS.LTS
```

### uv / uvx (required for DuckDB/MotherDuck server)

```bash
# Check if uv is installed
uvx --version

# Install uv (Windows)
winget install astral-sh.uv

# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify uvx is available
uvx --version
```

---

## Step 1: Set the MotherDuck Token Environment Variable

The DuckDB MCP server requires `MOTHERDUCK_TOKEN` to be set as a system environment variable.

**Windows (PowerShell — persistent, requires restart):**
```powershell
[System.Environment]::SetEnvironmentVariable("MOTHERDUCK_TOKEN", "your_token_here", "User")
```

**Windows (current session only):**
```powershell
$env:MOTHERDUCK_TOKEN = "your_token_here"
```

**macOS/Linux (add to ~/.bashrc or ~/.zshrc):**
```bash
export MOTHERDUCK_TOKEN="your_token_here"
```

To find your MotherDuck token: log in at https://app.motherduck.com → Settings → Tokens.

**Verify the variable is set:**
```bash
# Windows PowerShell
echo $env:MOTHERDUCK_TOKEN

# macOS/Linux
echo $MOTHERDUCK_TOKEN
```

---

## Step 2: Merge MCP Configuration into ~/.claude/mcp_config.json

**Locate your existing config:**
```bash
# Windows
cat "C:\Users\admin\.claude\mcp_config.json"

# macOS/Linux
cat ~/.claude/mcp_config.json
```

**Merge the servers from `mcp_additions.json`:**

Open `~/.claude/mcp_config.json` in your editor and add the three server entries from `mcp_additions.json` into the existing `mcpServers` object. Do NOT replace the entire file — only add the new keys.

Example final structure:
```json
{
  "mcpServers": {
    "existing-server": { "...": "..." },
    "duckdb": {
      "command": "uvx",
      "args": ["mcp-server-motherduck", "--db-path", ":memory:", "--read-write", "--allow-switch-databases"],
      "env": { "motherduck_token": "${MOTHERDUCK_TOKEN}" },
      "transport": "stdio"
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "transport": "stdio"
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "transport": "stdio"
    }
  }
}
```

---

## Step 3: Pre-download MCP Server Packages (optional but recommended)

These commands pre-install the packages so the first Claude session does not have download latency.

```bash
# Pre-install memory server
npx -y @modelcontextprotocol/server-memory --version

# Pre-install fetch server
npx -y @modelcontextprotocol/server-fetch --version

# Pre-install MotherDuck MCP server via uvx
uvx mcp-server-motherduck --help
```

---

## Step 4: Restart Claude Code

After updating `mcp_config.json`, restart Claude Code completely (not just the session) so it picks up the new server configuration.

```bash
# Close Claude Code and reopen, or if running as CLI:
claude --restart
```

---

## Step 5: Verification

After restarting Claude Code, verify each server is connected.

### Verify DuckDB/MotherDuck Server

In a Claude Code session, ask:
```
Run a DuckDB query: SELECT current_date AS today
```

If the server is working, Claude will return the current date from DuckDB.

Then verify MotherDuck connectivity:
```
Connect to MotherDuck and run: SHOW DATABASES
```

Expected output: list of databases including `PROD_EODHD`, `GoldenOpp`, `qgsi`, `DEV_EODHD_DATA`.

### Verify Memory Server

In a Claude Code session, ask:
```
Create a memory entity: OBQ_Test with observation "MCP memory server is working"
```

Then in a new session, ask:
```
What do you know about OBQ_Test?
```

It should recall the observation from the previous session.

### Verify Fetch Server

In a Claude Code session, ask:
```
Fetch the content of https://duckdb.org/docs/api/python/overview and summarize it.
```

---

## Troubleshooting

### "uvx command not found"
- Ensure uv is installed and on the PATH
- On Windows, check: `C:\Users\admin\.local\bin\` is in PATH
- Restart terminal after installing uv

### "MOTHERDUCK_TOKEN not set" error
- Verify the environment variable is set in the same shell that runs Claude Code
- On Windows, set it as a User environment variable (Control Panel → System → Advanced → Environment Variables) then restart Claude Code

### "Cannot find module @modelcontextprotocol/server-memory"
- npx will auto-install on first run — this is normal
- If it fails, manually install: `npm install -g @modelcontextprotocol/server-memory`

### DuckDB server connects but MotherDuck queries fail
- Token may have expired — generate a new token at https://app.motherduck.com
- Update the `MOTHERDUCK_TOKEN` environment variable and restart Claude Code

### "JSON parse error in mcp_config.json"
- Validate your JSON with: `python -c "import json; json.load(open(r'C:\Users\admin\.claude\mcp_config.json'))"`
- Common issue: trailing commas in the JSON (not valid JSON)

---

## Server Reference

| Server | Package | Transport | Purpose |
|---|---|---|---|
| `duckdb` | `mcp-server-motherduck` (via uvx) | stdio | SQL queries against MotherDuck and local DuckDB |
| `memory` | `@modelcontextprotocol/server-memory` (via npx) | stdio | Cross-session knowledge graph persistence |
| `fetch` | `@modelcontextprotocol/server-fetch` (via npx) | stdio | Web content retrieval (papers, docs, APIs) |
