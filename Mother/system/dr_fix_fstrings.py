"""
Fix malformed dict replacements inside f-strings.
The regex replacement put {"role": "user", "content": X} inside f-strings,
which breaks because { and } have special meaning in f-strings.

The real fix: the graphs use HumanMessage() OUTSIDE f-strings,
so the replacement was correct - the syntax errors are from the regex
replacing content inside multi-line f-string expressions.

Strategy: restore from # REMOVED_LC comments and fix manually.
"""

import pathlib, sys, re, ast

sys.stdout.reconfigure(encoding="utf-8")
DR = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")

# Read the broken files and show the problematic lines
for fname in [
    r"agents\synthesizer.py",
    r"agents\graphs\dd_graph.py",
    r"agents\graphs\quant_research_graph.py",
]:
    fp = DR / fname
    lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
    print("=== " + fname + " ===")
    for i, l in enumerate(lines, 1):
        # Show lines with the dict replacement pattern
        if '{"role":' in l or '"role":' in l:
            print(str(i).rjust(4) + ": " + l[:120])
    print()
