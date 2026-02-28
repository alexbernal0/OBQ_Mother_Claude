#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
OBQ_Mother_Claude — Deployment Script
Deploys soul files, skills, agents, commands, and hooks to ~/.claude/

Usage:
    python deploy.py all              # Full deployment
    python deploy.py soul             # Deploy global CLAUDE.md only
    python deploy.py skills           # Deploy all skills to ~/.claude/skills/
    python deploy.py agents           # Deploy agents to ~/.claude/agents/
    python deploy.py commands         # Deploy commands to ~/.claude/commands/
    python deploy.py hooks            # Deploy hooks to ~/.claude/hooks/ + update settings.json
    python deploy.py mcp              # Print MCP install commands
    python deploy.py project <path>   # Deploy project CLAUDE.md template to <path>
    python deploy.py status           # Show deployment status
"""

import sys
import os
import shutil
import json
from pathlib import Path

# Paths
MOTHER_DIR = Path(__file__).parent
CLAUDE_DIR = Path.home() / ".claude"
SKILLS_SRC = MOTHER_DIR / "skills"
SKILLS_DST = CLAUDE_DIR / "skills"
AGENTS_SRC = MOTHER_DIR / "agents"
AGENTS_DST = CLAUDE_DIR / "agents"
COMMANDS_SRC = MOTHER_DIR / "commands"
COMMANDS_DST = CLAUDE_DIR / "commands"
HOOKS_SRC = MOTHER_DIR / "hooks"
HOOKS_DST = CLAUDE_DIR / "hooks"
GLOBAL_CLAUDE_SRC = MOTHER_DIR / "claude_md" / "global_CLAUDE.md"
GLOBAL_CLAUDE_DST = CLAUDE_DIR / "CLAUDE.md"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def deploy_soul():
    """Deploy global CLAUDE.md to ~/.claude/CLAUDE.md"""
    print_header("Deploying Global CLAUDE.md")
    if not GLOBAL_CLAUDE_SRC.exists():
        print(f"  ERROR: Source not found: {GLOBAL_CLAUDE_SRC}")
        return False

    # Backup existing
    if GLOBAL_CLAUDE_DST.exists():
        backup = GLOBAL_CLAUDE_DST.with_suffix(".md.backup")
        shutil.copy2(GLOBAL_CLAUDE_DST, backup)
        print(f"  Backed up existing: {backup}")

    shutil.copy2(GLOBAL_CLAUDE_SRC, GLOBAL_CLAUDE_DST)
    print(f"  ✓ Deployed: {GLOBAL_CLAUDE_DST}")
    return True


def deploy_skills():
    """Deploy all skills to ~/.claude/skills/"""
    print_header("Deploying Skills")
    SKILLS_DST.mkdir(parents=True, exist_ok=True)

    deployed = []
    for skill_dir in SKILLS_SRC.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            dst = SKILLS_DST / skill_dir.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(skill_dir, dst)
            deployed.append(skill_dir.name)
            print(f"  ✓ {skill_dir.name}")

    print(f"\n  Total: {len(deployed)} skills deployed")
    return True


def deploy_agents():
    """Deploy agents to ~/.claude/agents/"""
    print_header("Deploying Agents")
    AGENTS_DST.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in AGENTS_SRC.glob("*.md"):
        shutil.copy2(f, AGENTS_DST / f.name)
        print(f"  ✓ {f.name}")
        count += 1
    print(f"\n  Total: {count} agents deployed")
    return True


def deploy_commands():
    """Deploy commands to ~/.claude/commands/"""
    print_header("Deploying Commands")
    COMMANDS_DST.mkdir(parents=True, exist_ok=True)

    count = 0
    for f in COMMANDS_SRC.glob("*.md"):
        shutil.copy2(f, COMMANDS_DST / f.name)
        print(f"  ✓ {f.name}")
        count += 1
    print(f"\n  Total: {count} commands deployed")
    return True


def deploy_hooks():
    """Deploy hook scripts + update settings.json"""
    print_header("Deploying Hooks")
    HOOKS_DST.mkdir(parents=True, exist_ok=True)

    # Copy hook scripts
    for f in HOOKS_SRC.iterdir():
        if f.is_file():
            dst = HOOKS_DST / f.name
            shutil.copy2(f, dst)
            # Make executable on Unix-like systems
            if f.suffix == '.sh':
                os.chmod(dst, 0o755)
            print(f"  ✓ {f.name}")

    # Update settings.json
    print("\n  Updating settings.json...")
    settings = {}
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH) as f:
            settings = json.load(f)

    hooks_home = str(HOOKS_DST).replace(str(Path.home()), "$HOME").replace("\\", "/")

    new_hooks = {
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "$HOME/.claude/skills/taskmaster/hooks/check-completion.sh",
                        "timeout": 10
                    },
                    {
                        "type": "command",
                        "command": "bash $HOME/.claude/hooks/session-checkpoint.sh",
                        "timeout": 10
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python {hooks_home}/block-sensitive-files.py",
                        "timeout": 5
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"bash {hooks_home}/syntax-check.sh",
                        "timeout": 15
                    }
                ]
            }
        ],
        "Notification": [
            {
                "matcher": "idle_prompt",
                "hooks": [
                    {
                        "type": "command",
                        "command": "powershell -Command \"[System.Console]::Beep(1000, 300)\"",
                        "timeout": 5
                    }
                ]
            }
        ]
    }

    settings["hooks"] = new_hooks
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {"claude-supermemory@supermemory-plugins": True}

    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
    print(f"  ✓ Updated: {SETTINGS_PATH}")
    return True


def show_mcp():
    """Print MCP server install commands"""
    print_header("MCP Server Installation Commands")
    print("""
  Run these commands to install MCP servers:

  # 1. MotherDuck/DuckDB (CRITICAL — direct DB queries in conversation)
  pip install uv  # if not installed
  claude mcp add --scope user duckdb --transport stdio -- uvx mcp-server-motherduck \\
    --db-path :memory: --read-write --allow-switch-databases

  # 2. Memory Graph (structured cross-session knowledge)
  claude mcp add --scope user memory --transport stdio -- \\
    npx -y @modelcontextprotocol/server-memory

  # 3. Fetch (web content, paper retrieval)
  claude mcp add --scope user fetch --transport stdio -- \\
    npx -y @modelcontextprotocol/server-fetch

  # 4. Context7 (live library documentation — VBT, pandas, numpy)
  # Via Claude Code plugin system:
  # Run in Claude Code: /plugin install context7

  Note: Jupyter MCP servers already configured in mcp_config.json.
""")


def deploy_project(target_path):
    """Deploy appropriate project CLAUDE.md template to target path"""
    print_header(f"Deploying Project CLAUDE.md to {target_path}")
    target = Path(target_path)
    if not target.exists():
        print(f"  ERROR: Target path does not exist: {target}")
        return False

    templates_dir = MOTHER_DIR / "claude_md" / "templates"
    print("\n  Available templates:")
    templates = list(templates_dir.glob("*.md"))
    for i, t in enumerate(templates):
        print(f"  {i+1}. {t.stem}")

    print("\n  Select template number (or press Enter to skip): ", end="")
    choice = input().strip()
    if not choice:
        print("  Skipped.")
        return True

    try:
        idx = int(choice) - 1
        template = templates[idx]
        dst = target / "CLAUDE.md"
        if dst.exists():
            print(f"  WARNING: CLAUDE.md already exists at {dst}. Overwrite? (y/N): ", end="")
            if input().strip().lower() != 'y':
                print("  Skipped.")
                return True
        shutil.copy2(template, dst)
        print(f"  ✓ Deployed {template.name} → {dst}")
        print(f"  Remember to customize CLAUDE.md for your specific project!")
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return False
    return True


def show_status():
    """Show deployment status"""
    print_header("Deployment Status")

    checks = [
        (GLOBAL_CLAUDE_DST, "Global CLAUDE.md"),
        (SETTINGS_PATH, "settings.json"),
    ]

    print("\n  Core files:")
    for path, name in checks:
        status = "✓" if path.exists() else "✗ MISSING"
        print(f"  {status} {name}: {path}")

    print("\n  Skills:")
    if SKILLS_DST.exists():
        installed = [d.name for d in SKILLS_DST.iterdir() if d.is_dir()]
        source = [d.name for d in SKILLS_SRC.iterdir() if d.is_dir()] if SKILLS_SRC.exists() else []
        for s in sorted(set(source)):
            status = "✓" if s in installed else "✗ NOT DEPLOYED"
            print(f"  {status} {s}")
    else:
        print("  ✗ Skills directory does not exist")

    print("\n  Agents:")
    if AGENTS_SRC.exists():
        for f in AGENTS_SRC.glob("*.md"):
            dst = AGENTS_DST / f.name
            status = "✓" if dst.exists() else "✗ NOT DEPLOYED"
            print(f"  {status} {f.name}")

    print("\n  Commands:")
    if COMMANDS_SRC.exists():
        for f in COMMANDS_SRC.glob("*.md"):
            dst = COMMANDS_DST / f.name
            status = "✓" if dst.exists() else "✗ NOT DEPLOYED"
            print(f"  {status} {f.name}")

    print("\n  Hooks:")
    if HOOKS_SRC.exists():
        for f in HOOKS_SRC.iterdir():
            if f.is_file():
                dst = HOOKS_DST / f.name
                status = "✓" if dst.exists() else "✗ NOT DEPLOYED"
                print(f"  {status} {f.name}")


def deploy_all():
    """Full deployment"""
    print_header("OBQ_Mother_Claude — Full Deployment")
    deploy_soul()
    deploy_skills()
    deploy_agents()
    deploy_commands()
    deploy_hooks()
    show_mcp()
    print_header("Deployment Complete")
    print("\n  Restart Claude Code for all changes to take effect.")
    print("  Run 'python deploy.py status' to verify.")
    print("  Run MCP install commands shown above.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "all":
        deploy_all()
    elif cmd == "soul":
        deploy_soul()
    elif cmd == "skills":
        deploy_skills()
    elif cmd == "agents":
        deploy_agents()
    elif cmd == "commands":
        deploy_commands()
    elif cmd == "hooks":
        deploy_hooks()
    elif cmd == "mcp":
        show_mcp()
    elif cmd == "project":
        if len(sys.argv) < 3:
            print("Usage: python deploy.py project <path>")
            sys.exit(1)
        deploy_project(sys.argv[2])
    elif cmd == "status":
        show_status()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
