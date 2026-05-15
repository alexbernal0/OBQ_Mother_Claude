"""
Strip all active LangChain imports from DeepResearch agents.
Uses line-by-line approach - safe and precise.
"""

import pathlib, sys, re

sys.stdout.reconfigure(encoding="utf-8")

DR = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")

LC_IMPORT_PREFIXES = (
    "from langchain_core.messages import",
    "from langchain_core import",
    "from langchain_ollama import",
    "from langchain_anthropic import",
    "from langchain_openai import",
    "from langchain_google_genai import",
    "import langchain",
    "from langchain",
)


def process_file(fp):
    original = fp.read_text(encoding="utf-8", errors="ignore")
    lines = original.splitlines(keepends=True)
    new_lines = []
    changed = False
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in LC_IMPORT_PREFIXES):
            new_lines.append("# REMOVED_LC: " + line.rstrip() + "\n")
            changed = True
        else:
            new_lines.append(line)
    if changed:
        fp.write_text("".join(new_lines), encoding="utf-8")
    return changed


# Files with message-type imports
files = [
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

for fp in files:
    if fp.exists():
        changed = process_file(fp)
        print(("CLEANED" if changed else "no change") + "  " + fp.name)

# base_agent.py needs the client replacements too
ba = DR / "agents" / "base_agent.py"
if ba.exists():
    changed = process_file(ba)
    print(("CLEANED" if changed else "no change") + "  base_agent.py")

# Verify
print()
print("=== Remaining active LangChain imports ===")
found = 0
for f in DR.rglob("*.py"):
    if "__pycache__" in str(f) or "_archive" in str(f):
        continue
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        active = [
            l.strip()
            for l in txt.splitlines()
            if ("from langchain" in l or "import langchain" in l)
            and not l.strip().startswith("#")
        ]
        if active:
            print("  " + str(f.relative_to(DR)))
            for l in active[:2]:
                print("    " + l)
            found += 1
    except:
        pass
print("Total files with active LangChain:", found)
