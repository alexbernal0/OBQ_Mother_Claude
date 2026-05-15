import pathlib, sys, datetime
sys.stdout.reconfigure(encoding='utf-8')
home = pathlib.Path.home()
now = datetime.datetime.now()

targets = [
    'C--Users-admin-Desktop-QGSI-Claude-Data-File',
    'd--Master-Data-Backup-2025-PapersWBacktest',
    'C--Users-admin',
]

for proj_name in targets:
    p = home / '.claude' / 'projects' / proj_name
    if not p.is_dir():
        continue
    files = [f for f in p.rglob('*') if f.is_file()]
    files.sort(key=lambda f: f.stat().st_size, reverse=True)
    total = sum(f.stat().st_size for f in files) / 1024 / 1024
    if not files:
        continue
    oldest = min(datetime.datetime.fromtimestamp(f.stat().st_mtime) for f in files)
    newest = max(datetime.datetime.fromtimestamp(f.stat().st_mtime) for f in files)
    print(proj_name[:55])
    print("  files=%d  %.1fMB  oldest=%s  newest=%s" % (
        len(files), total,
        oldest.strftime('%Y-%m-%d'),
        newest.strftime('%Y-%m-%d')
    ))
    for f in files[:6]:
        mb = f.stat().st_size / 1024 / 1024
        age = (now - datetime.datetime.fromtimestamp(f.stat().st_mtime)).days
        print("    %6.1fMB  %3dd  %s" % (mb, age, f.name[:60]))
    print()
