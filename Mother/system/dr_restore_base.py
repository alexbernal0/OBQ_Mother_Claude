"""
Restore LangChain in base_agent.py (it's the LLM factory - must keep).
Fix syntax error in synthesizer.py (extra } in f-string).
Fix synthesizer.py and graphs to use proper message format.
"""

import pathlib, sys, re

sys.stdout.reconfigure(encoding="utf-8")
DR = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")

# 1. Restore REMOVED_LC lines in base_agent.py - it needs LangChain for llm factory
ba = DR / "agents" / "base_agent.py"
txt = ba.read_text(encoding="utf-8", errors="ignore")
# Uncomment the REMOVED_LC lines
txt = txt.replace("# REMOVED_LC: ", "")
ba.write_text(txt, encoding="utf-8")
print("Restored base_agent.py LangChain imports (LLM factory must keep them)")

# 2. Fix synthesizer.py syntax error - extra } in f-string on line 448
synth = DR / "agents" / "synthesizer.py"
txt = synth.read_text(encoding="utf-8", errors="ignore")
# Fix the specific malformed f-string: ({thread_name}} -> ({thread_name})
txt = txt.replace(
    'f"You are an expert research analyst ({thread_name}}. Be precise, well-structured.")',
    'f"You are an expert research analyst ({thread_name}). Be precise, well-structured.")',
)
synth.write_text(txt, encoding="utf-8")
print("Fixed synthesizer.py f-string syntax error")

# 3. Restore REMOVED_LC in all graph files too (they use llm.invoke - need LangChain messages)
graph_files = list((DR / "agents" / "graphs").glob("*.py"))
graph_files += [
    DR / "agents" / "synthesizer.py",
    DR / "agents" / "gap_analyzer.py",
    DR / "memory" / "reflector.py",
]
for fp in graph_files:
    if not fp.exists():
        continue
    txt = fp.read_text(encoding="utf-8", errors="ignore")
    if "# REMOVED_LC:" in txt:
        restored = txt.replace("# REMOVED_LC: ", "")
        fp.write_text(restored, encoding="utf-8")
        print("Restored: " + fp.name)

# 4. For gatherer files - they use HumanMessage only in simple calls, not llm.invoke
# These can stay with dicts since they call base_agent's _call_llm() not direct llm.invoke
# Check which pattern they use
for fp in (DR / "agents" / "gatherers").glob("*.py"):
    if not fp.exists() or fp.name == "__init__.py":
        continue
    txt = fp.read_text(encoding="utf-8", errors="ignore")
    has_invoke = "llm.invoke" in txt or ".invoke(" in txt
    has_removed = "# REMOVED_LC:" in txt
    print(
        "Gatherer "
        + fp.name
        + ": has_invoke="
        + str(has_invoke)
        + " has_removed="
        + str(has_removed)
    )

print()
# Verify syntax
import ast

errors = []
ok = 0
for f in DR.rglob("*.py"):
    if "__pycache__" in str(f) or "_archive" in str(f):
        continue
    if "options_portfolio_backtester" in str(f):
        continue
    if str(f.relative_to(DR)).startswith("OBQ_AI"):
        continue
    try:
        ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        ok += 1
    except SyntaxError as e:
        errors.append(str(f.relative_to(DR)) + ": " + str(e))

print("Syntax OK:", ok, "files")
if errors:
    print("ERRORS:")
    for e in errors:
        print("  " + e)
else:
    print("ZERO syntax errors - all clean")
