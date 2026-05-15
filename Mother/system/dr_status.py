import pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
dr = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")

archive = dr / "_archive"
print("_archive exists:", archive.exists())
if archive.exists():
    for sub in archive.iterdir():
        if sub.is_dir():
            count = len(list(sub.rglob("*.py")))
            print("  " + sub.name + "/: " + str(count) + " files")

print()
dup = dr / "OBQ_AI" / "OBQ_AI_DeepResearch"
print("Duplicate deleted:", not dup.exists())

print()
scripts = list(dr.glob("_*.py"))
print("Remaining _*.py at root:", len(scripts))

print()
print("Remaining langchain imports in agents/:")
found = 0
for f in (dr / "agents").rglob("*.py"):
    if "__pycache__" in str(f):
        continue
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if "from langchain" in txt or "import langchain" in txt:
            print("  " + str(f.relative_to(dr)))
            found += 1
    except:
        pass
if not found:
    print("  NONE - clean")

print()
for name in ["claim_verifier.py", "report_scorer.py", "iterative_deepener.py"]:
    p = dr / "agents" / name
    status = "EXISTS " + str(p.stat().st_size) + "b" if p.exists() else "MISSING"
    print(name + ": " + status)

print()
req = dr / "requirements.txt"
if req.exists():
    txt = req.read_text(encoding="utf-8", errors="ignore")
    lc_lines = [l for l in txt.splitlines() if "langchain" in l or "langgraph" in l]
    print("langchain in requirements.txt: " + str(len(lc_lines)) + " lines remaining")
    for l in lc_lines:
        print("  " + l)
