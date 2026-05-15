"""
DeepResearch cleanup script — run once, archives scripts, deletes duplicate,
cleans LangChain imports, adds quality modules.
"""

import pathlib, shutil, sys, re

sys.stdout.reconfigure(encoding="utf-8")

DR = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")
PKG = pathlib.Path(
    r"C:\Users\admin\Downloads\DR_Package_extracted\system\deep_research"
)

# ── Phase 1: Create archive dirs ──────────────────────────────────────────────
(DR / "_archive" / "research_scripts").mkdir(parents=True, exist_ok=True)
(DR / "_archive" / "knowledge_utils").mkdir(parents=True, exist_ok=True)
(DR / "_archive" / "unused_graphs").mkdir(parents=True, exist_ok=True)
print("Archive dirs created")

# ── Phase 1a: Move all _*.py scripts ─────────────────────────────────────────
moved = 0
for f in sorted(DR.glob("_*.py")):
    dest = DR / "_archive" / "research_scripts" / f.name
    shutil.move(str(f), str(dest))
    moved += 1
print(f"Archived {moved} _*.py scripts to _archive/research_scripts/")

# ── Phase 1b: Move knowledge/ utility scripts ────────────────────────────────
utils_to_archive = [
    "add_links.py",
    "bm_extract.py",
    "build_excel.py",
    "build_excel_v2.py",
    "extract_bm.py",
    "get_categories.py",
    "get_cookies.py",
]
moved_k = 0
for name in utils_to_archive:
    src = DR / "knowledge" / name
    if src.exists():
        shutil.move(str(src), str(DR / "_archive" / "knowledge_utils" / name))
        moved_k += 1
print(f"Archived {moved_k} knowledge/ utils to _archive/knowledge_utils/")

# ── Phase 1c: Move unused graphs ─────────────────────────────────────────────
for name in ["recursive_graph.py", "storm_graph.py"]:
    src = DR / "agents" / "graphs" / name
    if src.exists():
        shutil.move(str(src), str(DR / "_archive" / "unused_graphs" / name))
        print(f"Archived agents/graphs/{name}")

# ── Phase 1d: Delete nested duplicate ────────────────────────────────────────
dup = DR / "OBQ_AI" / "OBQ_AI_DeepResearch"
if dup.exists():
    shutil.rmtree(str(dup))
    print("Deleted nested duplicate OBQ_AI/OBQ_AI_DeepResearch/")

# ── Phase 1e: Write archive README ───────────────────────────────────────────
(DR / "_archive" / "README.md").write_text(
    "# _archive\n\nArchived research scripts and utilities.\n"
    "Not part of active app. Preserved for historical reference.\n\n"
    "## Contents\n"
    "- `research_scripts/` — one-time research runs (lithium, options encyclopedia, radar, etc.)\n"
    "- `knowledge_utils/` — knowledge base utility scripts moved from knowledge/\n"
    "- `unused_graphs/` — graph implementations not used by production research_api.py\n",
    encoding="utf-8",
)
print("Archive README written")

# ── Phase 2: Remove LangChain imports — replace with native dicts ─────────────
# Pattern: replace HumanMessage/SystemMessage with native dict format
# Pattern: replace langchain_* client classes with native clients in base_agent.py

LC_IMPORT_PATTERNS = [
    r"^from langchain_core\.messages import.*\n",
    r"^from langchain_core import.*\n",
    r"^from langchain_ollama import.*\n",
    r"^from langchain_anthropic import.*\n",
    r"^from langchain_openai import.*\n",
    r"^from langchain_google_genai import.*\n",
    r"^import langchain.*\n",
]


def strip_lc_imports(text):
    for pattern in LC_IMPORT_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    return text


def replace_lc_messages(text):
    # HumanMessage(content=X) → {"role": "user", "content": X}
    text = re.sub(
        r"HumanMessage\(content=([^)]+)\)", r'{"role": "user", "content": \1}', text
    )
    # SystemMessage(content=X) → {"role": "system", "content": X}
    text = re.sub(
        r"SystemMessage\(content=([^)]+)\)", r'{"role": "system", "content": \1}', text
    )
    # HumanMessage(X) where X is a simple string variable → {"role": "user", "content": X}
    text = re.sub(
        r"\bHumanMessage\(([^)]+)\)", r'{"role": "user", "content": \1}', text
    )
    # SystemMessage(X) → {"role": "system", "content": X}
    text = re.sub(
        r"\bSystemMessage\(([^)]+)\)", r'{"role": "system", "content": \1}', text
    )
    return text


# Files to process (message type replacement only — not base_agent.py)
msg_files = [
    DR / "agents" / "synthesizer.py",
    DR / "agents" / "gap_analyzer.py",
    DR / "memory" / "reflector.py",
    DR / "agents" / "gatherers" / "academic_agent.py",
    DR / "agents" / "gatherers" / "github_agent.py",
    DR / "agents" / "gatherers" / "hyde_code_expander.py",
    DR / "agents" / "graphs" / "code_search_graph.py",
    DR / "agents" / "graphs" / "dd_graph.py",
    DR / "agents" / "graphs" / "deeper_graph.py",
    DR / "agents" / "graphs" / "innovation_graph.py",
    DR / "agents" / "graphs" / "parallel_graph.py",
    DR / "agents" / "graphs" / "quant_research_graph.py",
    DR / "agents" / "graphs" / "repogradar_graph.py",
]

cleaned = 0
for fp in msg_files:
    if not fp.exists():
        print(f"  SKIP (not found): {fp.name}")
        continue
    original = fp.read_text(encoding="utf-8", errors="ignore")
    text = strip_lc_imports(original)
    text = replace_lc_messages(text)
    if text != original:
        fp.write_text(text, encoding="utf-8")
        cleaned += 1
        print(f"  Cleaned: {fp.relative_to(DR)}")
    else:
        print(f"  No change: {fp.relative_to(DR)}")

print(f"Phase 2: {cleaned} files cleaned of LangChain message types")

# ── Phase 2b: Clean requirements.txt ─────────────────────────────────────────
req = DR / "requirements.txt"
if req.exists():
    lines = req.read_text(encoding="utf-8", errors="ignore").splitlines()
    to_remove = {
        "langchain",
        "langchain-anthropic",
        "langchain-ollama",
        "langchain-openai",
        "langchain-community",
        "langchain-google-genai",
        "langgraph",
    }
    new_lines = [
        l for l in lines if not any(l.strip().startswith(pkg) for pkg in to_remove)
    ]
    req.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    removed = len(lines) - len(new_lines)
    print(f"requirements.txt: removed {removed} langchain packages")

# ── Phase 3: Copy quality modules from package ───────────────────────────────
quality_modules = ["claim_verifier.py", "report_scorer.py", "iterative_deepener.py"]
for name in quality_modules:
    src = PKG / name
    dst = DR / "agents" / name
    if src.exists():
        text = src.read_text(encoding="utf-8", errors="ignore")
        # Fix import paths: these reference .planner, .synthesizer etc. from their original module
        # Replace relative imports with standalone comments
        text = text.replace("from .planner import", "# from .planner import")
        text = text.replace("from .synthesizer import", "# from .synthesizer import")
        text = text.replace("from .gatherers import", "# from .gatherers import")
        text = text.replace("from .gap_analyzer import", "# from .gap_analyzer import")
        text = text.replace(
            "from .report_scorer import", "# from .report_scorer import"
        )
        text = text.replace(
            "from .obsidian_writer import", "# from .obsidian_writer import"
        )
        text = text.replace(
            "from .iterative_deepener import", "# from .iterative_deepener import"
        )
        text = text.replace(
            "from .claim_verifier import", "# from .claim_verifier import"
        )
        text = text.replace(
            "from loguru import logger",
            "import logging\nlogger = logging.getLogger(__name__)",
        )
        dst.write_text(text, encoding="utf-8")
        print(f"Copied quality module: {name} ({dst.stat().st_size}b)")
    else:
        print(f"MISSING from package: {name}")

print()
print("=== FINAL STATUS ===")
# Verify
lc_remaining = []
for f in (DR / "agents").rglob("*.py"):
    if "__pycache__" in str(f) or "_archive" in str(f):
        continue
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if "from langchain" in txt or "import langchain" in txt:
            lc_remaining.append(str(f.relative_to(DR)))
    except:
        pass

print("LangChain remaining in agents/:", lc_remaining if lc_remaining else "NONE")
print("_*.py at root:", len(list(DR.glob("_*.py"))))
print(
    "_archive/research_scripts:",
    len(list((DR / "_archive" / "research_scripts").glob("*.py")))
    if (DR / "_archive" / "research_scripts").exists()
    else 0,
)
print("Duplicate deleted:", not (DR / "OBQ_AI" / "OBQ_AI_DeepResearch").exists())
for name in quality_modules:
    p = DR / "agents" / name
    print(name + ":", "OK " + str(p.stat().st_size) + "b" if p.exists() else "MISSING")
