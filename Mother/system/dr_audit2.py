import pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
dr = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")

# What graphs does research_api.py actually use?
ra = dr / "gui" / "api" / "research_api.py"
txt = ra.read_text(encoding="utf-8", errors="ignore")
print("=== research_api.py lazy/conditional graph imports ===")
for l in txt.splitlines():
    if "graph" in l.lower() or "Graph" in l or "agents." in l:
        print("  " + l.strip())

print()
# Which graphs are ONLY called from _ scripts (dead for production)?
print("=== Graphs only used from _scripts (safe to archive) ===")
graphs_dir = dr / "agents" / "graphs"
for gf in sorted(graphs_dir.glob("*.py")):
    if gf.name == "__init__.py":
        continue
    name = gf.stem
    # find who imports this
    importers = []
    for f in dr.rglob("*.py"):
        if "graphs" in str(f):
            continue
        if "__pycache__" in str(f):
            continue
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
            if name in t:
                importers.append(str(f.relative_to(dr)))
        except:
            pass
    script_only = all(i.startswith("_") for i in importers)
    print("  " + name.ljust(30) + " importers: " + str(importers))

print()
# Count files in _archive candidates
print("=== _ scripts count and total size ===")
scripts = [f for f in dr.glob("_*.py")]
total = sum(f.stat().st_size for f in scripts)
print("Count: " + str(len(scripts)) + "  Total: " + str(round(total / 1024)) + " KB")
