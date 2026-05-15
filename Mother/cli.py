#!/usr/bin/env python3
"""
Mother CLI — Soul Manager & Development Sidecar System

═══════════════════════════════════════════════════════════════════
  "Mother, are you there?"
  > Yes, I'm here. *adjusts settings*
═══════════════════════════════════════════════════════════════════

Commands:
    # Soul Management
    soul-init                   Initialize new soul from 3 repositories
    soul-deploy <project>       Deploy soul files to a project
    soul-export                 Export soul files as package
    
    # Project Management
    init <project_name>         Create a new project sidecar from template
    archive <project_name>      Archive completed project to master_projects/
    validate <project_name>     Check alignment with Prime Directive
    aggregate-lessons           Synthesize lessons across all master_projects/
    status [project_name]       Show project status (or all projects)
    prepare-package <name>      Create handoff package for senior developer
    
    # Auto-Learn
    learn                       Trigger Auto-Learn extraction from current session
    recall <query>              Search Auto-Learn memories
    memories                    List recent Auto-Learn memories
    auto-learn                  Show Auto-Learn status
    
    # Export
    export-mother               Create .zip of Mother for new machine setup
    
    # Interactive
    menu                        Show interactive menu

Flags:
    --mother                    Enable personality blend in output
    --verbose                   Verbose output
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

MOTHER_ROOT = Path(__file__).parent
TEMPLATE_DIR = MOTHER_ROOT / "templates" / "new_project_sidecar"
MASTER_PROJECTS = MOTHER_ROOT / "master_projects"
CONSTITUTION = MOTHER_ROOT / "prime_directive" / "constitution.md"
SOUL_DIR = MOTHER_ROOT / "soul"
# <!-- CUSTOMIZE: Replace [COMPANY] with your organization name -->
PACKAGES_DIR = Path.home() / "Desktop" / "Packages"
SKILLS_DIR = Path.home() / "Desktop" / "Skills"
KNOWLEDGE_DIR = Path.home() / "Desktop" / "Knowledge"
OC_KNOWLEDGE = Path.home() / "Desktop" / "OC_Knowledge"

# Version
VERSION = "3.5.0"

# Auto-Learn paths
AUTO_LEARN_SCRIPTS = SKILLS_DIR / "Auto-Learn" / "scripts"

# Personality responses
GREETINGS = [
    "Yes, I'm here. *adjusts honesty setting to 95%*",
    "Online and calibrated. What do you need?",
    "Present. Systems nominal. *checks heartbeat*",
    "I'm here. Ship's running smooth.",
    "Affirmative. Context loaded, ready to work.",
]

# ═══════════════════════════════════════════════════════════════════
# Menu System
# ═══════════════════════════════════════════════════════════════════

def show_menu(mother_mode: bool = True):
    """Show interactive Mother menu."""
    import random
    
    greeting = random.choice(GREETINGS)
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  MOTHER v{VERSION} — Soul Manager & Spec-Driven Development        ║
╚══════════════════════════════════════════════════════════════════╝

{greeting}

What would you like to do?

  ┌─────────────────────────────────────────────────────────────┐
  │  SOUL MANAGEMENT                                            │
  ├─────────────────────────────────────────────────────────────┤
  │  1) Configure Soul      Initialize or modify soul files     │
  │  2) Deploy Soul         Deploy soul to a project            │
  │                                                             │
  │  SPEC-DRIVEN DEVELOPMENT (Prime Directive)                  │
  ├─────────────────────────────────────────────────────────────┤
  │  3) Generate Spec       Create spec from project code       │
  │  4) Verify Spec         Check code alignment with spec      │
  │  5) Spec Status         Show spec versions & alignment      │
  │  6) Init TARS           Set up spec-driven management       │
  │  7) Init JARVIS         Set up spec-verified execution      │
  │                                                             │
  │  PROJECT MANAGEMENT                                         │
  ├─────────────────────────────────────────────────────────────┤
  │  8) Init Sidecar        Create new project sidecar          │
  │  9) Prepare Package     Create handoff for senior dev       │
  │  10) Archive Project    Archive completed project           │
  │  11) Show Status        Project status overview             │
  │                                                             │
  │  KNOWLEDGE & EXPORT                                         │
  ├─────────────────────────────────────────────────────────────┤
  │  12) Auto-Learn Status  Show learning system status         │
  │  13) Recall Memory      Search stored memories              │
  │  14) Export Mother      Create .zip for new machine setup   │
  │  15) Sync Skills        Pull latest from skills repo         │
  │                                                             │
  │  0) Exit                                                    │
  └─────────────────────────────────────────────────────────────┘
""")
    
    try:
        choice = input("Enter choice (0-15): ").strip()
        
        if choice == "0":
            print("\n*powers down gracefully*\n")
            return
        elif choice == "1":
            soul_init_interactive()
        elif choice == "2":
            soul_deploy_interactive()
        elif choice == "3":  # Generate Spec
            project = input("Project name: ").strip()
            path = input("Project path (or Enter for auto): ").strip() or None
            if project:
                spec_generate(project, path, verbose=True)
        elif choice == "4":  # Verify Spec
            project = input("Project name: ").strip()
            if project:
                spec_verify(project, verbose=True)
        elif choice == "5":  # Spec Status
            project = input("Project name (or Enter for all): ").strip() or None
            spec_status(project, verbose=True)
        elif choice == "6":  # Init TARS
            project = input("Project name: ").strip()
            if project:
                tars_init(project, verbose=True)
        elif choice == "7":  # Init JARVIS
            project = input("Project name: ").strip()
            if project:
                jarvis_init(project, verbose=True)
        elif choice == "8":  # Init Sidecar
            project = input("Project name: ").strip()
            if project:
                init_project(project, verbose=True)
        elif choice == "9":  # Prepare Package
            name = input("Package name: ").strip()
            target = input("Target system (e.g., backend, frontend): ").strip()
            if name and target:
                prepare_package(name, target, verbose=True)
        elif choice == "10":  # Archive
            project = input("Project name to archive: ").strip()
            if project:
                archive_project(project, verbose=True)
        elif choice == "11":  # Status
            show_status(verbose=True)
        elif choice == "12":  # Auto-Learn Status
            auto_learn_status(verbose=True)
        elif choice == "13":  # Recall Memory
            query = input("Search query: ").strip()
            if query:
                auto_learn_recall(query, verbose=True)
        elif choice == "14":  # Export Mother
            export_mother(verbose=True)
        elif choice == "15":  # Sync Skills
            skills_sync(verbose=True)
        else:
            print("Invalid choice. Try again.")
            
    except KeyboardInterrupt:
        print("\n\n*graceful shutdown*\n")
    except EOFError:
        print("\n")


def mother_greeting():
    """Handle 'Mother are you there?' greeting."""
    import random
    greeting = random.choice(GREETINGS)
    print(f"\n{greeting}\n")
    print("Options:")
    print("  1) Configure Soul         python cli.py soul-init")
    print("  2) Modify Skills/Tools    cd ~/Desktop/Skills")
    print("  3) Update Mother Files    cd ~/Desktop/Mother")
    print("  4) Prepare Package        python cli.py prepare-package <name> --target <system>")
    print("  5) Export Mother          python cli.py export-mother")
    print("  6) Show Full Menu         python cli.py menu")
    print()


# ═══════════════════════════════════════════════════════════════════
# Soul Management
# ═══════════════════════════════════════════════════════════════════

def soul_init_interactive():
    """Interactive soul initialization from 3 repositories."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  SOUL INIT — Build AI Soul from Repository Analysis              ║
╚══════════════════════════════════════════════════════════════════╝

I'll examine 3 repositories to understand patterns, conventions,
and domain expertise, then generate a custom soul configuration.

""")
    
    # Gather repository paths
    repos = []
    print("Enter paths to 3 representative repositories:")
    print("  (Primary project, Supporting project, Infrastructure/tooling)")
    print()
    
    for i in range(1, 4):
        while True:
            path = input(f"Repository {i} path: ").strip()
            path = Path(path).expanduser()
            if path.exists() and path.is_dir():
                repos.append(path)
                break
            else:
                print(f"  Error: {path} does not exist or is not a directory")
    
    print()
    
    # Gather user profile
    print("User Profile:")
    user_name = input("  Name: ").strip() or "Developer"
    user_role = input("  Role (e.g., Senior Engineer): ").strip() or "Engineer"
    primary_lang = input("  Primary language (e.g., Python): ").strip() or "Python"
    environment = input("  Environment (e.g., macOS/VSCode/zsh): ").strip() or "macOS/VSCode/zsh"
    
    print()
    
    # Organization context
    print("Organization Context (optional, press Enter to skip):")
    org_name = input("  Organization name: ").strip() or "Organization"
    constraint = input("  Key constraint: ").strip()
    incident = input("  Critical incident to remember: ").strip()
    
    print()
    
    # Output location
    output_default = Path.home() / "Desktop" / f"{org_name}_Soul"
    output_path = input(f"Output directory [{output_default}]: ").strip()
    output_path = Path(output_path).expanduser() if output_path else output_default
    
    print()
    print("Analyzing repositories...")
    
    # Perform analysis
    soul_init_from_repos(
        repos=repos,
        user_name=user_name,
        user_role=user_role,
        primary_lang=primary_lang,
        environment=environment,
        org_name=org_name,
        constraint=constraint,
        incident=incident,
        output_path=output_path,
        verbose=True
    )


def soul_init_from_repos(
    repos: List[Path],
    user_name: str,
    user_role: str,
    primary_lang: str,
    environment: str,
    org_name: str,
    constraint: str,
    incident: str,
    output_path: Path,
    verbose: bool = False
):
    """Generate soul files from repository analysis."""
    
    output_path.mkdir(parents=True, exist_ok=True)
    analysis_dir = output_path / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    
    # Analyze each repo
    all_patterns = {
        'tech_stack': set(),
        'conventions': [],
        'error_handling': [],
        'logging': set(),
        'testing': [],
        'frameworks': set(),
    }
    
    for i, repo in enumerate(repos, 1):
        print(f"  Analyzing {repo.name}...")
        
        patterns = analyze_repository(repo)
        
        # Merge patterns
        all_patterns['tech_stack'].update(patterns.get('tech_stack', []))
        all_patterns['conventions'].extend(patterns.get('conventions', []))
        all_patterns['frameworks'].update(patterns.get('frameworks', []))
        
        # Write individual analysis
        analysis_file = analysis_dir / f"repo{i}_{repo.name}_analysis.md"
        analysis_file.write_text(f"""# Repository Analysis: {repo.name}

## Path
{repo}

## Tech Stack
{chr(10).join('- ' + t for t in patterns.get('tech_stack', []))}

## File Structure
{patterns.get('structure', 'N/A')}

## Patterns Detected
{chr(10).join('- ' + c for c in patterns.get('conventions', []))}
""")
    
    print("  Synthesizing soul files...")
    
    # Generate soul files by copying templates and customizing
    soul_source = SOUL_DIR
    
    # Copy and customize each file
    for soul_file in ['SOUL.md', 'IDENTITY.md', 'PRINCIPLES.md', 'USER.md', 'HEARTBEAT.md', 'NOW.md']:
        source = soul_source / soul_file
        dest = output_path / soul_file
        
        if source.exists():
            content = source.read_text()
            
            # Customize based on gathered info
            content = content.replace("[YOUR COMPANY]", org_name)
            content = content.replace("[YOUR NAME]", user_name)
            content = content.replace("[YOUR ROLE]", user_role)
            content = content.replace("[YOUR ORGANIZATION]", org_name)
            
            if incident and "[YOUR CRITICAL INCIDENT]" in content:
                content = content.replace("[YOUR CRITICAL INCIDENT]", incident)
            
            dest.write_text(content)
            if verbose:
                print(f"    Created {soul_file}")
    
    # Generate README
    readme = output_path / "README.md"
    readme.write_text(f"""# {org_name} Soul Configuration

Generated by Mother v{VERSION} on {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Source Repositories
{chr(10).join(f'- {r.name}: {r}' for r in repos)}

## User Profile
- **Name:** {user_name}
- **Role:** {user_role}
- **Language:** {primary_lang}
- **Environment:** {environment}

## Files
- `SOUL.md` — Core character and values
- `IDENTITY.md` — Role and domain expertise
- `PRINCIPLES.md` — Decision heuristics and domain laws
- `USER.md` — User profile and preferences
- `HEARTBEAT.md` — Session rituals
- `NOW.md` — Live working memory template

## Setup
1. Copy files to your project root or `~/.claude/`
2. Reference in your `CLAUDE.md` with `@` includes
3. Customize as you work — these are living documents

## Customization
After 1-2 weeks of use, run `mother soul-calibrate` to refine based on feedback.
""")
    
    print(f"""
✅ Soul generated at: {output_path}

Files created:
  - SOUL.md (character, values)
  - IDENTITY.md (role, expertise)
  - PRINCIPLES.md (decision heuristics)
  - USER.md (user profile)
  - HEARTBEAT.md (session rituals)
  - NOW.md (live memory template)
  - analysis/ (repository analysis)

Next steps:
  1. Review and customize the generated files
  2. Copy to your project or ~/.claude/
  3. Add @includes to your CLAUDE.md
""")
    
    return output_path


def analyze_repository(repo_path: Path) -> dict:
    """Analyze a repository for patterns and conventions."""
    patterns = {
        'tech_stack': [],
        'conventions': [],
        'structure': '',
        'frameworks': [],
    }
    
    # Check for common config files
    config_checks = {
        'package.json': 'Node.js/JavaScript',
        'pyproject.toml': 'Python (modern)',
        'setup.py': 'Python',
        'Cargo.toml': 'Rust',
        'go.mod': 'Go',
        'tsconfig.json': 'TypeScript',
        'docker-compose.yml': 'Docker Compose',
        'Dockerfile': 'Docker',
        '.github/workflows': 'GitHub Actions',
        'temporal.yaml': 'Temporal.io',
    }
    
    for config, tech in config_checks.items():
        if (repo_path / config).exists():
            patterns['tech_stack'].append(tech)
    
    # Check directory structure
    dirs = [d.name for d in repo_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    patterns['structure'] = ', '.join(dirs[:10])
    
    # Detect frameworks from imports (simplified)
    py_files = list(repo_path.rglob('*.py'))[:20]
    for py_file in py_files:
        try:
            content = py_file.read_text(errors='ignore')
            if 'from fastapi' in content or 'import fastapi' in content:
                patterns['frameworks'].add('FastAPI')
            if 'from temporal' in content:
                patterns['frameworks'].add('Temporal')
            if 'import pytest' in content:
                patterns['frameworks'].add('pytest')
            if 'from pydantic' in content:
                patterns['frameworks'].add('Pydantic')
            if 'loguru' in content:
                patterns['conventions'].append('Uses Loguru for logging')
        except Exception:
            pass
    
    # Check for common patterns
    if (repo_path / 'tests').exists():
        patterns['conventions'].append('Has tests/ directory')
    if (repo_path / 'src').exists():
        patterns['conventions'].append('Uses src/ layout')
    if (repo_path / '.pre-commit-config.yaml').exists():
        patterns['conventions'].append('Uses pre-commit hooks')
    
    return patterns


def soul_deploy_interactive():
    """Deploy soul files to a project."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  SOUL DEPLOY — Deploy Soul Files to Project                      ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    project_path = input("Project path to deploy to: ").strip()
    project_path = Path(project_path).expanduser()
    
    if not project_path.exists():
        print(f"Error: {project_path} does not exist")
        return
    
    soul_source = input(f"Soul source [{SOUL_DIR}]: ").strip()
    soul_source = Path(soul_source).expanduser() if soul_source else SOUL_DIR
    
    if not soul_source.exists():
        print(f"Error: {soul_source} does not exist")
        return
    
    # Create .claude directory in project if needed
    claude_dir = project_path / ".claude"
    claude_dir.mkdir(exist_ok=True)
    
    # Copy soul files
    soul_files = ['SOUL.md', 'IDENTITY.md', 'PRINCIPLES.md', 'USER.md', 'HEARTBEAT.md', 'NOW.md']
    
    for soul_file in soul_files:
        source = soul_source / soul_file
        if source.exists():
            dest = claude_dir / soul_file
            shutil.copy2(source, dest)
            print(f"  Deployed {soul_file}")
    
    # Create CLAUDE.md with includes if it doesn't exist
    claude_md = project_path / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text(f"""# {project_path.name}

## Soul Configuration
@.claude/SOUL.md
@.claude/IDENTITY.md
@.claude/PRINCIPLES.md
@.claude/USER.md
@.claude/HEARTBEAT.md

## Project Context
[Add project-specific context here]
""")
        print(f"  Created CLAUDE.md with soul includes")
    
    print(f"\n✅ Soul deployed to {project_path}")


def soul_deploy(project_path: str, soul_source: str = None, verbose: bool = False):
    """Deploy soul files to a project (non-interactive)."""
    project_path = Path(project_path).expanduser()
    soul_source = Path(soul_source).expanduser() if soul_source else SOUL_DIR
    
    if not project_path.exists():
        print(f"Error: {project_path} does not exist")
        sys.exit(1)
    
    claude_dir = project_path / ".claude"
    claude_dir.mkdir(exist_ok=True)
    
    soul_files = ['SOUL.md', 'IDENTITY.md', 'PRINCIPLES.md', 'USER.md', 'HEARTBEAT.md', 'NOW.md']
    
    for soul_file in soul_files:
        source = soul_source / soul_file
        if source.exists():
            dest = claude_dir / soul_file
            shutil.copy2(source, dest)
            if verbose:
                print(f"  Deployed {soul_file}")
    
    print(f"✅ Soul deployed to {project_path}")


def soul_export(output_path: str = None, verbose: bool = False):
    """Export soul files as a standalone package."""
    if output_path:
        output = Path(output_path).expanduser()
    else:
        output = PACKAGES_DIR / f"Soul_Export_{datetime.now().strftime('%Y%m%d')}"
    
    output.mkdir(parents=True, exist_ok=True)
    
    # Copy soul files
    for f in SOUL_DIR.glob('*.md'):
        shutil.copy2(f, output / f.name)
    
    # Copy docs
    docs_dest = output / 'docs'
    docs_dest.mkdir(exist_ok=True)
    for f in (SOUL_DIR / 'docs').glob('*.md'):
        shutil.copy2(f, docs_dest / f.name)
    
    print(f"✅ Soul exported to {output}")
    return output


# ═══════════════════════════════════════════════════════════════════
# Export Mother
# ═══════════════════════════════════════════════════════════════════

def export_mother(output_path: str = None, verbose: bool = False):
    """Create a .zip of Mother for new machine setup."""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    zip_name = f"Mother_v{VERSION}_{timestamp}.zip"
    
    if output_path:
        zip_path = Path(output_path).expanduser() / zip_name
    else:
        PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = PACKAGES_DIR / zip_name
    
    print(f"\n📦 Exporting Mother v{VERSION}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all Mother files
        for filepath in MOTHER_ROOT.rglob('*'):
            if filepath.is_file():
                # Skip certain files/directories
                rel_path = filepath.relative_to(MOTHER_ROOT)
                skip_patterns = ['.git', '__pycache__', '.pyc', '.DS_Store', 'master_projects']
                if any(skip in str(rel_path) for skip in skip_patterns):
                    continue
                
                arcname = f"Mother/{rel_path}"
                zf.write(filepath, arcname)
                if verbose:
                    print(f"  + {rel_path}")
        
        # Add setup instructions
        setup_instructions = f"""# Mother Setup Instructions

## Quick Start (New Machine)

1. Extract this archive to ~/Desktop/
2. Run the setup:
   ```bash
   cd ~/Desktop/Mother
   python cli.py menu
   ```

## First Time Setup

1. **Configure Soul** (Option 1 in menu)
   - Provide 3 representative repositories
   - Fill in user profile
   - Soul files will be generated

2. **Deploy Soul to Project** (Option 2)
   - Point to your project directory
   - Soul files copied to .claude/

3. **Set up CLAUDE.md** in your project:
   ```markdown
   @.claude/SOUL.md
   @.claude/IDENTITY.md
   @.claude/PRINCIPLES.md
   @.claude/USER.md
   @.claude/HEARTBEAT.md
   ```

## Version
Mother v{VERSION}
Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Commands
```bash
python cli.py menu              # Interactive menu
python cli.py soul-init         # Initialize soul from repos
python cli.py soul-deploy       # Deploy soul to project
python cli.py export-mother     # Export Mother (this)
python cli.py prepare-package   # Create handoff package
```

## Directory Structure After Setup
```
~/Desktop/
├── Mother/                 # This folder
├── Skills/                 # Skills library
├── Knowledge/              # Domain knowledge
├── OC_Knowledge/           # Self-improvement knowledge
└── Packages/               # Export packages
```

## Support
Mother is a soul management framework for AI-assisted development.
"""
        zf.writestr("Mother/SETUP_INSTRUCTIONS.md", setup_instructions)
    
    size_kb = zip_path.stat().st_size / 1024
    
    print(f"""
✅ Mother exported successfully!

  File: {zip_path}
  Size: {size_kb:.1f} KB
  Version: {VERSION}

To set up on a new machine:
  1. Copy {zip_name} to the new machine
  2. Extract to ~/Desktop/
  3. Run: cd ~/Desktop/Mother && python cli.py menu
  4. Select "1) Configure Soul" to initialize
""")
    
    return zip_path


# ═══════════════════════════════════════════════════════════════════
# Project Management (existing functions, cleaned up)
# ═══════════════════════════════════════════════════════════════════

def init_project(project_name: str, target_dir: str = None, verbose: bool = False):
    """Create a new project sidecar from template."""
    
    if target_dir:
        sidecar_path = Path(target_dir) / f"{project_name}-mother"
    else:
        sidecar_path = MOTHER_ROOT.parent / f"{project_name}-mother"
    
    if sidecar_path.exists():
        print(f"Error: {sidecar_path} already exists")
        sys.exit(1)
    
    if not TEMPLATE_DIR.exists():
        print(f"Error: Template directory not found at {TEMPLATE_DIR}")
        sys.exit(1)
    
    shutil.copytree(TEMPLATE_DIR, sidecar_path)
    
    # Rename PROJECT_NAME directory
    old_project_dir = sidecar_path / "tars" / "PROJECT_NAME"
    new_project_dir = sidecar_path / "tars" / project_name
    if old_project_dir.exists():
        old_project_dir.rename(new_project_dir)
    
    # Replace placeholders
    today = datetime.now().strftime("%Y-%m-%d")
    placeholders = {
        "{{PROJECT_NAME}}": project_name,
        "{{DATE}}": today,
        "{{TASK_TITLE}}": "Initial Setup",
    }
    
    for filepath in sidecar_path.rglob("*"):
        if filepath.is_file() and filepath.suffix in [".md", ".yaml", ".yml"]:
            content = filepath.read_text()
            for placeholder, value in placeholders.items():
                content = content.replace(placeholder, value)
            filepath.write_text(content)
    
    print(f"✓ Initialized {project_name} sidecar at {sidecar_path}")
    print(f"\nNext steps:")
    print(f"  1. Update specs.md with feature list")
    print(f"  2. Add @includes to your project's CLAUDE.md")
    
    return sidecar_path


def archive_project(project_name: str, sidecar_path: str = None, verbose: bool = False):
    """Archive a completed project to master_projects/."""
    
    if sidecar_path:
        source = Path(sidecar_path) / "tars" / project_name
    else:
        possible = MOTHER_ROOT.parent / f"{project_name}-mother" / "tars" / project_name
        if possible.exists():
            source = possible
        else:
            print(f"Error: Could not find sidecar for {project_name}")
            sys.exit(1)
    
    if not source.exists():
        print(f"Error: {source} does not exist")
        sys.exit(1)
    
    today = datetime.now().strftime("%Y-%m-%d")
    archive_name = f"{project_name}_{today}"
    archive_path = MASTER_PROJECTS / archive_name
    
    if archive_path.exists():
        print(f"Error: Archive {archive_path} already exists")
        sys.exit(1)
    
    MASTER_PROJECTS.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, archive_path)
    
    print(f"✓ Archived {project_name} to {archive_path}")
    return archive_path


def validate_project(project_name: str, sidecar_path: str = None, verbose: bool = False):
    """Check project alignment with Prime Directive."""
    
    if sidecar_path:
        project_dir = Path(sidecar_path) / "tars" / project_name
    else:
        possible = MOTHER_ROOT.parent / f"{project_name}-mother" / "tars" / project_name
        if possible.exists():
            project_dir = possible
        else:
            print(f"Error: Could not find sidecar for {project_name}")
            sys.exit(1)
    
    issues = []
    warnings = []
    
    required_files = ["specs.md", "progress.yaml", "auto_knowledge.md"]
    for f in required_files:
        if not (project_dir / f).exists():
            issues.append(f"Missing required file: {f}")
    
    progress_file = project_dir / "progress.yaml"
    if progress_file.exists():
        content = progress_file.read_text()
        valid_phases = ["planning", "design", "implementation", "testing", "review", "done"]
        has_valid_phase = any(f"phase: {p}" in content for p in valid_phases)
        if not has_valid_phase:
            warnings.append("progress.yaml has no valid phase")
    
    if issues:
        print(f"✗ {project_name} has {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
    
    if warnings:
        print(f"⚠ {project_name} has {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not issues and not warnings:
        print(f"✓ {project_name} passes validation")
    
    return len(issues) == 0


def aggregate_lessons(verbose: bool = False):
    """Synthesize lessons from all archived projects."""
    
    if not MASTER_PROJECTS.exists():
        print("No master_projects/ directory found")
        return
    
    all_lessons = []
    
    for project_dir in MASTER_PROJECTS.iterdir():
        if not project_dir.is_dir():
            continue
        
        knowledge_file = project_dir / "auto_knowledge.md"
        if knowledge_file.exists():
            content = knowledge_file.read_text()
            lines = content.split("\n")
            current_entry = []
            for line in lines:
                if line.startswith("## ") and len(line) > 10:
                    if current_entry:
                        all_lessons.append({
                            "project": project_dir.name,
                            "content": "\n".join(current_entry)
                        })
                    current_entry = [line]
                elif current_entry:
                    current_entry.append(line)
            
            if current_entry and len(current_entry) > 1:
                all_lessons.append({
                    "project": project_dir.name,
                    "content": "\n".join(current_entry)
                })
    
    print(f"Found {len(all_lessons)} lessons across {len(list(MASTER_PROJECTS.iterdir()))} projects\n")
    
    if verbose and all_lessons:
        for lesson in all_lessons[:10]:
            print(f"[{lesson['project']}]")
            print(lesson['content'][:300])
            print("-" * 40)
    
    return all_lessons


def show_status(project_name: str = None, verbose: bool = False):
    """Show project status."""
    
    if project_name:
        possible = MOTHER_ROOT.parent / f"{project_name}-mother" / "tars" / project_name
        if not possible.exists():
            print(f"Error: Could not find sidecar for {project_name}")
            sys.exit(1)
        
        progress_file = possible / "progress.yaml"
        if progress_file.exists():
            content = progress_file.read_text()
            print(f"Project: {project_name}")
            for line in content.split("\n"):
                if line.startswith("phase:") or line.startswith("last_updated:"):
                    print(f"  {line.strip()}")
    else:
        print("Active Sidecars:")
        for item in MOTHER_ROOT.parent.iterdir():
            if item.name.endswith("-mother") and item.is_dir():
                project = item.name.replace("-mother", "")
                progress_file = item / "tars" / project / "progress.yaml"
                phase = "unknown"
                if progress_file.exists():
                    for line in progress_file.read_text().split("\n"):
                        if line.startswith("phase:"):
                            phase = line.split(":")[1].strip()
                            break
                print(f"  {project}: {phase}")
        
        archived_count = len(list(MASTER_PROJECTS.iterdir())) if MASTER_PROJECTS.exists() else 0
        print(f"\nArchived Projects: {archived_count} in master_projects/")


# ═══════════════════════════════════════════════════════════════════
# Prepare Package (existing, preserved)
# ═══════════════════════════════════════════════════════════════════

SECRET_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)[\s]*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
    r'(?i)(secret|password|passwd|pwd)[\s]*[=:]\s*["\']?[^\s"\'"`]{8,}',
    r'(?i)(token|bearer)[\s]*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
    r'(?i)aws[_-]?(access|secret)[_-]?key[\s]*[=:]',
    r'(?i)private[_-]?key',
    r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
]


def scan_for_secrets(directory: Path) -> list:
    """Scan directory for potential secrets."""
    findings = []
    patterns = [re.compile(p) for p in SECRET_PATTERNS]
    
    for filepath in directory.rglob('*'):
        if filepath.is_file() and filepath.suffix in ['.md', '.yaml', '.yml', '.json', '.py', '.txt', '.env']:
            try:
                content = filepath.read_text(errors='ignore')
                for i, pattern in enumerate(patterns):
                    matches = pattern.findall(content)
                    if matches:
                        findings.append({
                            'file': str(filepath.relative_to(directory)),
                            'pattern': SECRET_PATTERNS[i][:40] + '...',
                            'count': len(matches)
                        })
            except Exception:
                pass
    
    return findings


def get_git_state(repo_path: Path) -> dict:
    """Get git state including most recent rebase info."""
    state = {
        'branch': 'unknown',
        'last_commit': 'unknown',
        'last_commit_date': 'unknown',
        'last_rebase': None,
        'remote_url': 'unknown'
    }
    
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_path, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            state['branch'] = result.stdout.strip()
        
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%H|%ci|%s'],
            cwd=repo_path, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 3:
                state['last_commit'] = parts[0][:8]
                state['last_commit_date'] = parts[1]
        
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=repo_path, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            state['remote_url'] = result.stdout.strip()
    except Exception:
        pass
    
    return state


def prepare_package(package_name: str, target: str, verbose: bool = False) -> Path:
    """Create a handoff package for senior developer."""
    
    today = datetime.now().strftime('%m%d%Y')
    folder_name = f'{package_name}_{today}'
    
    PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    package_dir = PACKAGES_DIR / folder_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir(parents=True)
    
    print(f'\n📦 Creating package: {folder_name}')
    
    # Create structure
    (package_dir / 'artifacts' / 'skills').mkdir(parents=True)
    (package_dir / 'context').mkdir(parents=True)
    (package_dir / 'knowledge').mkdir(parents=True)
    
    # Copy skills
    if SKILLS_DIR.exists():
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                dest = package_dir / 'artifacts' / 'skills' / skill_dir.name
                shutil.copytree(skill_dir, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.git'))
    
    # Copy research
    research_dir = KNOWLEDGE_DIR / 'research'
    if research_dir.exists():
        for item in research_dir.iterdir():
            if item.is_dir() or item.suffix in ['.md', '.pdf']:
                dest = package_dir / 'knowledge' / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                else:
                    shutil.copy2(item, dest)
    
    # Git state
    git_state = get_git_state(MOTHER_ROOT)
    (package_dir / 'context' / 'git_state.json').write_text(json.dumps(git_state, indent=2))
    
    # Secret scan
    secret_findings = scan_for_secrets(package_dir)
    
    # Generate docs
    all_files = list(package_dir.rglob('*'))
    all_files = [f for f in all_files if f.is_file()]
    
    handoff_content = f'''# Handoff Package: {package_name}

## Overview
- **Package**: {folder_name}
- **Target System**: {target}
- **Created**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- **Mother Version**: {VERSION}

## Git State
- **Branch**: {git_state['branch']}
- **Commit**: {git_state['last_commit']}

## Files Included
{len(all_files)} files
'''
    
    (package_dir / 'HANDOFF.md').write_text(handoff_content)
    
    # Compress
    tar_path = PACKAGES_DIR / f'{folder_name}.tar.gz'
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add(package_dir, arcname=folder_name)
    
    shutil.rmtree(package_dir)
    
    print(f'\n✅ Package created: {tar_path}')
    return tar_path


# ═══════════════════════════════════════════════════════════════════
# Auto-Learn Commands (existing, preserved)
# ═══════════════════════════════════════════════════════════════════

def auto_learn_extract(verbose: bool = False):
    """Trigger Auto-Learn knowledge extraction."""
    extractor_script = AUTO_LEARN_SCRIPTS / "extractor.py"
    
    if not extractor_script.exists():
        print(f"Error: Auto-Learn not installed at {AUTO_LEARN_SCRIPTS}")
        return
    
    print("🧠 Auto-Learn: Extracting knowledge from session...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(extractor_script), "--mode=test"],
            capture_output=True,
            text=True,
            timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}")


def auto_learn_recall(query: str, limit: int = 10, verbose: bool = False):
    """Search Auto-Learn memories."""
    
    if not AUTO_LEARN_SCRIPTS.exists():
        print("Auto-Learn not installed")
        return
    
    sys.path.insert(0, str(AUTO_LEARN_SCRIPTS))
    
    try:
        from storage import KnowledgeStorage
        storage = KnowledgeStorage()
        results = storage.search(query, limit=limit)
        
        if not results:
            print(f"No memories found for: {query}")
            return
        
        print(f"🔍 Found {len(results)} memories for '{query}':\n")
        
        for i, entry in enumerate(results, 1):
            print(f"{i}. **{entry.title}** (score: {entry.score:.2f})")
            print(f"   Type: {entry.knowledge_type}")
            print()
    except ImportError:
        print("Auto-Learn modules not found")
    except Exception as e:
        print(f"Error: {e}")


def auto_learn_list(limit: int = 20, verbose: bool = False):
    """List recent Auto-Learn memories."""
    
    if not AUTO_LEARN_SCRIPTS.exists():
        print("Auto-Learn not installed")
        return
    
    sys.path.insert(0, str(AUTO_LEARN_SCRIPTS))
    
    try:
        from storage import KnowledgeStorage
        storage = KnowledgeStorage()
        
        all_entries = storage.load_all()
        all_entries.sort(key=lambda e: e.created_at, reverse=True)
        
        if not all_entries:
            print("No memories stored yet.")
            return
        
        print(f"📚 Auto-Learn Memories ({len(all_entries)} total):\n")
        
        for entry in all_entries[:limit]:
            print(f"  - {entry.title} ({entry.knowledge_type})")
        
    except ImportError:
        print("Auto-Learn modules not found")
    except Exception as e:
        print(f"Error: {e}")


def auto_learn_status(verbose: bool = False):
    """Show Auto-Learn system status."""
    
    print("🧠 Auto-Learn Status\n")
    print(f"Version: {VERSION}")
    print(f"Skills Path: {AUTO_LEARN_SCRIPTS}")
    print(f"Knowledge Path: {OC_KNOWLEDGE}")
    print()
    
    required_scripts = ['extractor.py', 'injector.py', 'monitor.py', 'storage.py']
    installed = sum(1 for s in required_scripts if (AUTO_LEARN_SCRIPTS / s).exists())
    
    print(f"Installed Scripts: {installed}/{len(required_scripts)}")
    
    print(f"\nKnowledge Directories:")
    for subdir in ['lessons', 'patterns', 'decisions', 'error_fixes']:
        path = OC_KNOWLEDGE / subdir
        if path.exists():
            count = len(list(path.glob('*.md')))
            print(f"  ✓ {subdir}/: {count} files")
        else:
            print(f"  ✗ {subdir}/: not found")


# ═══════════════════════════════════════════════════════════════════
# Spec Management (BuildfromSpec Integration)
# ═══════════════════════════════════════════════════════════════════

def spec_generate(project_name: str, project_path: str = None, verbose: bool = False):
    """Generate product specification from project."""
    
    if project_path:
        source = Path(project_path).expanduser()
    else:
        possible = MOTHER_ROOT.parent / f"{project_name}"
        if possible.exists():
            source = possible
        else:
            print(f"Error: Project {project_name} not found")
            sys.exit(1)
    
    # Create Mother sidecar if needed
    sidecar = MOTHER_ROOT.parent / f"{project_name}-mother"
    specs_dir = sidecar / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    spec_version = 1
    
    # Find next version
    existing = list(specs_dir.glob('PRODUCT_SPEC_v*'))
    if existing:
        versions = [int(p.name.split('_v')[1].split('_')[0]) for p in existing]
        spec_version = max(versions) + 1
    
    spec_dir = specs_dir / f"PRODUCT_SPEC_v{spec_version}_{today}"
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📄 Generating spec for {project_name}...")
    print(f"   Source: {source}")
    print(f"   Output: {spec_dir}")
    
    # Create manifest
    manifest = {
        'project': project_name,
        'version': f'v{spec_version}',
        'created': datetime.now().isoformat(),
        'source_path': str(source),
        'mother_version': VERSION,
    }
    
    (spec_dir / 'MANIFEST.yaml').write_text(
        f"# Product Specification Manifest\n"
        f"project: {project_name}\n"
        f"version: v{spec_version}\n"
        f"created: {datetime.now().isoformat()}\n"
        f"source: {source}\n"
        f"mother_version: {VERSION}\n"
    )
    
    # Create placeholder spec
    spec_md = f'''# Product Specification: {project_name}

**Version:** v{spec_version}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Source:** {source}

---

## Executive Summary

{{Generated by /build-spec generate}}

## Architecture

{{System architecture diagram}}

## Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR-001 | {{requirement}} | Pending |

## Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-001 | Performance | {{requirement}} |

## Architectural Decisions

{{ADRs}}

## Infrastructure Requirements

{{Services, ports, env vars}}

---

*Generated by Mother v{VERSION} | tool_BuildfromSpec*
'''
    (spec_dir / 'SPEC.md').write_text(spec_md)
    
    print(f"""
✅ Spec structure created!

  Location: {spec_dir}
  Version: v{spec_version}

Next steps:
  1. Run /build-spec generate in the AI assistant
  2. Or manually edit SPEC.md
  3. Convert to PDF: /build-spec --format pdf

The SPEC.pdf will become your project's Prime Directive.
""")
    
    return spec_dir


def spec_verify(project_name: str, verbose: bool = False):
    """Check spec alignment for a project."""
    
    sidecar = MOTHER_ROOT.parent / f"{project_name}-mother"
    specs_dir = sidecar / "specs"
    
    if not specs_dir.exists():
        print(f"No specs found for {project_name}")
        print(f"Run: python cli.py spec-generate {project_name}")
        return
    
    # Find latest spec
    specs = sorted(specs_dir.glob('PRODUCT_SPEC_v*'), reverse=True)
    if not specs:
        print("No spec versions found")
        return
    
    latest = specs[0]
    print(f"\n🔍 Spec Alignment Check: {project_name}")
    print(f"   Latest spec: {latest.name}")
    
    # Check for alignment report
    reports_dir = specs_dir / "alignment-reports"
    if reports_dir.exists():
        reports = sorted(reports_dir.glob('*.md'), reverse=True)
        if reports:
            print(f"   Latest report: {reports[0].name}")
    else:
        print("   No alignment reports yet")
        print(f"   Run /build-spec verify in the AI assistant")
    
    print(f"""
Verification Commands:
  /build-spec verify           Check current alignment
  /build-spec verify --strict  Fail on any deviation
  /build-spec verify --report  Generate detailed report
""")


def spec_status(project_name: str = None, verbose: bool = False):
    """Show spec status for project(s)."""
    
    if project_name:
        sidecar = MOTHER_ROOT.parent / f"{project_name}-mother"
        if not sidecar.exists():
            print(f"No sidecar found for {project_name}")
            return
        
        specs_dir = sidecar / "specs"
        if specs_dir.exists():
            specs = sorted(specs_dir.glob('PRODUCT_SPEC_v*'), reverse=True)
            print(f"\n📄 Spec Status: {project_name}")
            print(f"   Versions: {len(specs)}")
            if specs:
                print(f"   Latest: {specs[0].name}")
                manifest = specs[0] / 'MANIFEST.yaml'
                if manifest.exists():
                    content = manifest.read_text()
                    for line in content.split('\n'):
                        if line.startswith('created:'):
                            print(f"   Created: {line.split(': ')[1]}")
        else:
            print(f"No specs for {project_name}")
    else:
        print("\n📄 Spec Status (All Projects)\n")
        for item in MOTHER_ROOT.parent.iterdir():
            if item.name.endswith('-mother') and item.is_dir():
                project = item.name.replace('-mother', '')
                specs_dir = item / 'specs'
                if specs_dir.exists():
                    specs = list(specs_dir.glob('PRODUCT_SPEC_v*'))
                    print(f"  {project}: {len(specs)} spec version(s)")
                else:
                    print(f"  {project}: No specs")


# ═══════════════════════════════════════════════════════════════════
# TARS Integration (Spec-Driven Project Management)
# ═══════════════════════════════════════════════════════════════════

def tars_init(project_name: str, verbose: bool = False):
    """Initialize TARS for spec-driven project management."""
    
    sidecar = MOTHER_ROOT.parent / f"{project_name}-mother"
    tars_dir = sidecar / "tars"
    tars_dir.mkdir(parents=True, exist_ok=True)
    
    # Create TARS configuration
    tars_config = f'''# TARS Configuration: {project_name}
# Spec-Driven Project Management

project: {project_name}
created: {datetime.now().isoformat()}

# Prime Directive
spec_path: ../specs/PRODUCT_SPEC_v1/SPEC.pdf
require_spec_ref: true

# Progress tracking
tracking:
  method: spec_requirements
  report_frequency: daily
  
# Task assignment
assignment:
  derive_from: spec_requirements
  auto_create_tasks: true
  
# Deviation handling
deviations:
  action: flag  # flag | block | approve
  notify: true
'''
    (tars_dir / 'tars.yaml').write_text(tars_config)
    
    # Create timeline template
    timeline = f'''# Project Timeline: {project_name}

## Derived from SPEC.pdf

| Milestone | Spec Section | Target | Status |
|-----------|--------------|--------|--------|
| M1: Core | §3 | Week 1 | Pending |
| M2: API | §4 | Week 2 | Pending |
| M3: Tests | §5 | Week 3 | Pending |

## Progress

- [ ] Spec generated
- [ ] Requirements mapped
- [ ] Tasks created
- [ ] Implementation started
'''
    (tars_dir / 'timeline.md').write_text(timeline)
    
    # Create progress tracker
    progress = f'''# Progress: {project_name}

last_updated: {datetime.now().isoformat()}

alignment:
  current_score: 0
  target_score: 90
  last_check: null

requirements:
  total: 0
  completed: 0
  in_progress: 0
  pending: 0

deviations:
  count: 0
  resolved: 0
'''
    (tars_dir / 'progress.yaml').write_text(progress)
    
    print(f"""
✅ TARS initialized for {project_name}

  Location: {tars_dir}

Files created:
  - tars.yaml (configuration)
  - timeline.md (milestones from spec)
  - progress.yaml (tracking)

TARS will:
  1. Create timeline from spec milestones
  2. Assign tasks based on requirements
  3. Track progress against spec completion
  4. Flag work that deviates from spec
""")
    
    return tars_dir


# ═══════════════════════════════════════════════════════════════════
# JARVIS Integration (Spec-Verification Task Execution)
# ═══════════════════════════════════════════════════════════════════

def jarvis_init(project_name: str, verbose: bool = False):
    """Initialize JARVIS for spec-verified task execution."""
    
    sidecar = MOTHER_ROOT.parent / f"{project_name}-mother"
    jarvis_dir = sidecar / "jarvis"
    jarvis_dir.mkdir(parents=True, exist_ok=True)
    
    # Create JARVIS configuration
    jarvis_config = f'''# JARVIS Configuration: {project_name}
# Spec-Verification Task Execution

project: {project_name}
created: {datetime.now().isoformat()}

# Execution rules
execution:
  require_spec_ref: true
  verify_after_task: true
  stop_on_deviation: true
  min_alignment_score: 80

# Verification hooks
hooks:
  pre_task:
    - check_spec_reference
    - validate_task_format
  post_task:
    - run_tests
    - verify_alignment
    - update_progress

# Deviation handling
on_deviation:
  action: stop_and_report
  create_issue: true
  notify_tars: true
'''
    (jarvis_dir / 'jarvis.yaml').write_text(jarvis_config)
    
    # Create current task template
    current_task = '''# Current Task

task_id: null
spec_ref: null
requirement: null
status: idle

# Set by JARVIS when task starts
started_at: null
files_modified: []

# Verification
verification:
  pre_check: null
  post_check: null
  alignment_delta: null
'''
    (jarvis_dir / 'current_task.yaml').write_text(current_task)
    
    # Create deviations tracker
    deviations = f'''# Deviations Tracker: {project_name}

## Active Deviations

None

## Resolved Deviations

None

---

Log format:
- [DATE] DEVIATION_TYPE: description (SPEC ref) - STATUS
'''
    (jarvis_dir / 'deviations.md').write_text(deviations)
    
    print(f"""
✅ JARVIS initialized for {project_name}

  Location: {jarvis_dir}

Files created:
  - jarvis.yaml (configuration)
  - current_task.yaml (task tracking)
  - deviations.md (deviation log)

JARVIS will:
  1. Verify spec reference before each task
  2. Check alignment after each task
  3. Stop and report on deviation
  4. Update progress in TARS
""")
    
    return jarvis_dir


# ═══════════════════════════════════════════════════════════════════
# Skills Sync (remote skills repo)
# ═══════════════════════════════════════════════════════════════════

def skills_sync(verbose=False):
    """Sync remote skills repo to local Skills folder."""
    
    # <!-- CUSTOMIZE: Set your skills repo URL -->
    skills_dir = Path(os.path.expanduser('~/Desktop/Skills'))
    repo_dir = skills_dir / '.skills-repo'
    repo_url = 'https://github.com/[YOUR_ORG]/skills.git'  # <!-- CUSTOMIZE -->
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  SKILLS SYNC                                                      ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Clone or pull
    if repo_dir.exists():
        print('📥 Pulling latest changes...')
        result = subprocess.run(
            ['git', 'pull'],
            cwd=repo_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f'⚠️  Git pull failed: {result.stderr}')
            return
        print(result.stdout)
    else:
        print('📦 Cloning skills repo...')
        result = subprocess.run(
            ['git', 'clone', repo_url, str(repo_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f'❌ Clone failed: {result.stderr}')
            return
        print('✓ Cloned successfully')
    
    # Copy skills to main folder
    print('\n📋 Syncing skills...')
    
    # Copy modes
    modes_dir = repo_dir / 'modes'
    if modes_dir.exists():
        for item in modes_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dest = skills_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
                print(f'  ✓ {item.name}/ (mode)')
    
    # Copy shared
    shared_dir = repo_dir / 'shared'
    if shared_dir.exists():
        for item in shared_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dest = skills_dir / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
                print(f'  ✓ {item.name}/ (shared)')
    
    # Copy skills-directory.yaml
    index_file = repo_dir / 'skills-directory.yaml'
    if index_file.exists():
        shutil.copy(index_file, skills_dir / 'skills-directory.yaml')
        print('  ✓ skills-directory.yaml')
    
    # Load and display skills summary
    print('\n📊 Skills Summary:')
    print('─' * 50)
    
    try:
        import yaml
        with open(skills_dir / 'skills-directory.yaml', 'r') as f:
            directory = yaml.safe_load(f)
        
        if 'modes' in directory:
            print('\n🎭 MODES:')
            for name, info in directory['modes'].items():
                print(f"  • {name}: {info.get('description', 'No description')}")
        
        if 'shared' in directory:
            print('\n🔧 SHARED SKILLS:')
            for name, info in directory['shared'].items():
                print(f"  • {name}: {info.get('description', 'No description')}")
    except Exception as e:
        if verbose:
            print(f'Could not parse skills-directory.yaml: {e}')
    
    print('\n✅ Skills sync complete!')
    print(f'   Location: {skills_dir}')



# ═══════════════════════════════════════════════════════════════════
# Healthcheck
# ═══════════════════════════════════════════════════════════════════

def healthcheck(verbose: bool = False):
    """Run Mother system health check — verify all components are in place."""
    import time
    start = time.time()

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  MOTHER HEALTHCHECK v{VERSION}                                       ║
╚══════════════════════════════════════════════════════════════════╝
""")

    checks_passed = 0
    checks_failed = 0
    checks_warned = 0

    def check(name, condition, warn_only=False):
        nonlocal checks_passed, checks_failed, checks_warned
        if condition:
            print(f"  ✅ {name}")
            checks_passed += 1
        elif warn_only:
            print(f"  ⚠️  {name}")
            checks_warned += 1
        else:
            print(f"  ❌ {name}")
            checks_failed += 1

    # --- Core Files ---
    print("📁 CORE FILES")
    check("cli.py exists", (MOTHER_ROOT / "cli.py").exists())
    check("soul/ directory exists", SOUL_DIR.exists())
    check("manifest.yaml exists", (MOTHER_ROOT / "manifest.yaml").exists())
    check("soul/SOUL_COMPACT.yaml exists", (SOUL_DIR / "SOUL_COMPACT.yaml").exists())
    check("prime_directive/ exists", (MOTHER_ROOT / "prime_directive").is_dir())
    check("Personalities/ exists", (MOTHER_ROOT / "Personalities").is_dir())

    soul_files = ['SOUL.md', 'IDENTITY.md', 'PRINCIPLES.md', 'USER.md', 'HEARTBEAT.md', 'NOW.md']
    for sf in soul_files:
        check(f"soul/{sf}", (SOUL_DIR / sf).exists(), warn_only=True)

    # --- Commands ---
    print("\n\U0001f527 COMMANDS")
    commands_dir = MOTHER_ROOT / "commands"
    check("commands/ directory exists", commands_dir.is_dir())

    expected_commands = ['handoff.md', 'lessons.md', 'napkin.md', 'healthcheck.md']
    for cmd in expected_commands:
        check(f"commands/{cmd}", (commands_dir / cmd).exists() if commands_dir.is_dir() else False)

    # Check live commands in ~/.claude/commands/
    live_commands_dir = Path.home() / ".claude" / "commands"
    check("~/.claude/commands/ exists", live_commands_dir.is_dir())
    if live_commands_dir.is_dir():
        live_count = len(list(live_commands_dir.glob('*.md')))
        check(f"Live commands installed ({live_count} found)", live_count >= 4)

    # --- Skills ---
    print("\n🧠 SKILLS")
    skills_dir = Path.home() / ".claude" / "skills"
    check("~/.claude/skills/ exists", skills_dir.is_dir())
    if skills_dir.is_dir():
        skill_count = len(list(skills_dir.glob('*.md')))
        check(f"Skills installed ({skill_count} found)", skill_count >= 1)

    # --- Config ---
    print("\n⚙️  CONFIG")
    claude_settings = Path.home() / ".claude" / "settings.json"
    check("~/.claude/settings.json exists", claude_settings.exists())

    opencode_config = Path.home() / ".config" / "opencode" / "opencode.json"
    check("opencode.json exists", opencode_config.exists(), warn_only=True)

    omo_config = Path.home() / ".config" / "opencode" / "oh-my-opencode.json"
    check("oh-my-opencode.json exists", omo_config.exists(), warn_only=True)

    # --- Git ---
    print("\n📦 GIT")
    git_dir = MOTHER_ROOT / ".git"
    check("Mother is a git repo", git_dir.is_dir())
    if git_dir.is_dir():
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=MOTHER_ROOT, capture_output=True, text=True, timeout=5
            )
            dirty_count = len([l for l in result.stdout.strip().split('\n') if l.strip()])
            check(f"Working tree clean ({dirty_count} uncommitted)", dirty_count == 0, warn_only=True)
        except Exception:
            check("Git status check", False, warn_only=True)

    # --- Disk Usage ---
    print("\n💾 DISK")
    try:
        total_size = sum(f.stat().st_size for f in MOTHER_ROOT.rglob('*') if f.is_file() and '.git' not in str(f))
        size_mb = total_size / (1024 * 1024)
        check(f"Mother size: {size_mb:.1f} MB (< 50 MB target)", size_mb < 50)
    except Exception:
        check("Disk size check", False, warn_only=True)

    # --- Token Budget Estimate ---
    print("\n📊 TOKEN BUDGET")
    compact_path = SOUL_DIR / "SOUL_COMPACT.yaml"
    manifest_path = MOTHER_ROOT / "manifest.yaml"
    if compact_path.exists():
        compact_size = compact_path.stat().st_size
        est_tokens = int(compact_size / 4)
        check(f"SOUL_COMPACT.yaml: ~{est_tokens} tokens (compact mode)", est_tokens < 5000)
    if manifest_path.exists():
        manifest_size = manifest_path.stat().st_size
        est_tokens = int(manifest_size / 4)
        check(f"manifest.yaml: ~{est_tokens} tokens (index)", est_tokens < 1000)

    # --- Summary ---
    elapsed = time.time() - start
    total = checks_passed + checks_failed + checks_warned
    separator = '═' * 60
    print(f"\n{separator}")
    print(f"  RESULT: {checks_passed}/{total} passed, {checks_failed} failed, {checks_warned} warnings")
    print(f"  Time: {elapsed:.2f}s")
    print(f"{separator}\n")

    if checks_failed == 0:
        print("  🟢 Mother system is healthy!")
    else:
        print(f"  🔴 {checks_failed} check(s) failed — review above.")

    return checks_failed == 0

# ═══════════════════════════════════════════════════════════════════
# Main CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Mother CLI — Soul Manager & Development Sidecar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--mother", action="store_true", help="Enable personality blend")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="version", version=f"Mother v{VERSION}")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Menu
    subparsers.add_parser("menu", help="Show interactive menu")
    subparsers.add_parser("hello", help="Mother greeting")
    
    # Soul commands
    subparsers.add_parser("soul-init", help="Initialize new soul from repositories")
    
    soul_deploy_parser = subparsers.add_parser("soul-deploy", help="Deploy soul to project")
    soul_deploy_parser.add_argument("project_path", help="Path to project")
    soul_deploy_parser.add_argument("--source", "-s", help="Soul source directory")
    
    soul_export_parser = subparsers.add_parser("soul-export", help="Export soul files")
    soul_export_parser.add_argument("--output", "-o", help="Output directory")
    
    # Export Mother
    export_parser = subparsers.add_parser("export-mother", help="Export Mother as .zip")
    export_parser.add_argument("--output", "-o", help="Output directory")
    
    # Project commands
    init_parser = subparsers.add_parser("init", help="Create new project sidecar")
    init_parser.add_argument("project_name", help="Name of the project")
    init_parser.add_argument("--target", "-t", help="Target directory for sidecar")
    
    archive_parser = subparsers.add_parser("archive", help="Archive completed project")
    archive_parser.add_argument("project_name", help="Name of the project")
    archive_parser.add_argument("--path", "-p", help="Path to sidecar")
    
    validate_parser = subparsers.add_parser("validate", help="Validate project alignment")
    validate_parser.add_argument("project_name", help="Name of the project")
    validate_parser.add_argument("--path", "-p", help="Path to sidecar")
    
    subparsers.add_parser("aggregate-lessons", help="Synthesize lessons from all projects")
    
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("project_name", nargs="?", help="Specific project")
    
    package_parser = subparsers.add_parser("prepare-package", help="Create handoff package")
    package_parser.add_argument("package_name", help="Name of the package")
    package_parser.add_argument("--target", "-t", required=True, help="Target system")


    # Spec Management commands
    spec_gen_parser = subparsers.add_parser("spec-generate", help="Generate spec from project")
    spec_gen_parser.add_argument("project_name", help="Name of the project")
    spec_gen_parser.add_argument("--path", "-p", help="Project source path")
    
    spec_verify_parser = subparsers.add_parser("spec-verify", help="Verify spec alignment")
    spec_verify_parser.add_argument("project_name", help="Name of the project")
    
    spec_status_parser = subparsers.add_parser("spec-status", help="Show spec status")
    spec_status_parser.add_argument("project_name", nargs="?", help="Specific project")
    
    # TARS/JARVIS commands
    tars_parser = subparsers.add_parser("tars-init", help="Initialize TARS for project")
    tars_parser.add_argument("project_name", help="Name of the project")
    
    jarvis_parser = subparsers.add_parser("jarvis-init", help="Initialize JARVIS for project")
    jarvis_parser.add_argument("project_name", help="Name of the project")
    
    # Auto-Learn commands
    subparsers.add_parser("learn", help="Trigger Auto-Learn extraction")
    
    recall_parser = subparsers.add_parser("recall", help="Search Auto-Learn memories")
    recall_parser.add_argument("query", help="Search query")
    recall_parser.add_argument("--limit", "-n", type=int, default=10, help="Max results")
    
    memories_parser = subparsers.add_parser("memories", help="List Auto-Learn memories")
    memories_parser.add_argument("--limit", "-n", type=int, default=20, help="Max entries")
    
    subparsers.add_parser("auto-learn", help="Show Auto-Learn status")
    
    # Skills sync command
    subparsers.add_parser("skills-sync", help="Sync remote skills repo")

    # Healthcheck command
    subparsers.add_parser("healthcheck", help="Run Mother system health check")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.mother or args.command == "hello":
        mother_greeting()
        if args.command != "hello":
            return
    
    if args.command == "menu":
        show_menu(args.mother)
    elif args.command == "hello":
        pass  # Already handled above
    elif args.command == "soul-init":
        soul_init_interactive()
    elif args.command == "soul-deploy":
        soul_deploy(args.project_path, getattr(args, 'source', None), args.verbose)
    elif args.command == "soul-export":
        soul_export(getattr(args, 'output', None), args.verbose)
    elif args.command == "export-mother":
        export_mother(getattr(args, 'output', None), args.verbose)
    elif args.command == "init":
        init_project(args.project_name, args.target, args.verbose)
    elif args.command == "archive":
        archive_project(args.project_name, getattr(args, 'path', None), args.verbose)
    elif args.command == "validate":
        validate_project(args.project_name, getattr(args, 'path', None), args.verbose)
    elif args.command == "aggregate-lessons":
        aggregate_lessons(args.verbose)
    elif args.command == "status":
        show_status(getattr(args, 'project_name', None), args.verbose)
    elif args.command == "prepare-package":
        prepare_package(args.package_name, args.target, args.verbose)
    elif args.command == "learn":
        auto_learn_extract(args.verbose)
    elif args.command == "recall":
        auto_learn_recall(args.query, getattr(args, 'limit', 10), args.verbose)
    elif args.command == "memories":
        auto_learn_list(getattr(args, 'limit', 20), args.verbose)
    elif args.command == "auto-learn":
        auto_learn_status(args.verbose)
    elif args.command == "spec-generate":
        spec_generate(args.project_name, getattr(args, 'path', None), args.verbose)
    elif args.command == "spec-verify":
        spec_verify(args.project_name, args.verbose)
    elif args.command == "spec-status":
        spec_status(getattr(args, 'project_name', None), args.verbose)
    elif args.command == "tars-init":
        tars_init(args.project_name, args.verbose)
    elif args.command == "jarvis-init":
        jarvis_init(args.project_name, args.verbose)
    elif args.command == "skills-sync":
        skills_sync(args.verbose)
    elif args.command == "healthcheck":
        healthcheck(args.verbose)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
