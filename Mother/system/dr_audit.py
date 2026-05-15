import pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
dr = pathlib.Path(r"C:\Users\admin\Desktop\OBQ_AI\OBQ_AI_DeepResearch")

ra = dr / "gui" / "api" / "research_api.py"
lines = ra.read_text(encoding="utf-8", errors="ignore").splitlines()
imports = [l for l in lines if l.startswith("import ") or l.startswith("from ")]
print("research_api.py ALL imports:")
for l in imports:
    print("  " + l)

print()
dup = dr / "OBQ_AI" / "OBQ_AI_DeepResearch"
if dup.exists():
    count = len(list(dup.rglob("*.py")))
    print(
        "DUPLICATE DIR: OBQ_AI/OBQ_AI_DeepResearch exists - " + str(count) + " py files"
    )
    print("This is a full copy of the project nested inside OBQ_AI/ subfolder")

print()
# What does gui/app.py register?
app = dr / "gui" / "app.py"
if app.exists():
    for l in app.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "blueprint" in l.lower() or "register" in l.lower() or "import" in l.lower():
            print("app.py: " + l.strip())
