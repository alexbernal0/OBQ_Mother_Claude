import pathlib, sys, datetime, shutil
sys.stdout.reconfigure(encoding='utf-8')
home = pathlib.Path.home()
now = datetime.datetime.now()
claude = home / '.claude'

total_freed = 0.0
total_deleted = 0

def nuke_old(directory, days, label):
    global total_freed, total_deleted
    if not directory.is_dir():
        return
    cutoff = now - datetime.timedelta(days=days)
    freed, deleted = 0.0, 0
    for f in directory.rglob('*'):
        if f.is_file() and datetime.datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            mb = f.stat().st_size / 1024 / 1024
            try:
                f.unlink()
                freed += mb
                deleted += 1
            except Exception as e:
                print("  SKIP %s: %s" % (f.name, e))
    total_freed += freed
    total_deleted += deleted
    # Check remaining
    remain = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file()) / 1024 / 1024
    print("%-30s  freed=%.1fMB (%d files)  remain=%.1fMB" % (label, freed, deleted, remain))

print("=== DEBLOAT RUN ===\n")

# Transcripts: 7d
nuke_old(claude / 'transcripts',    7,  'transcripts (7d)')

# file-history: 7d
nuke_old(claude / 'file-history',   7,  'file-history (7d)')

# projects/: 7d (claude code caches)
nuke_old(claude / 'projects',       7,  'projects cache (7d)')

# cache: all
nuke_old(claude / 'cache',          0,  'cache (all)')

# shell-snapshots: 3d
nuke_old(claude / 'shell-snapshots', 3, 'shell-snapshots (3d)')

# usage-data: 30d
nuke_old(claude / 'usage-data',     30, 'usage-data (30d)')

# paste-cache: all
nuke_old(claude / 'paste-cache',    0,  'paste-cache (all)')

# debug: all
nuke_old(claude / 'debug',          0,  'debug (all)')

# stats-cache.json
sc = claude / 'stats-cache.json'
if sc.exists():
    mb = sc.stat().st_size / 1024 / 1024
    sc.unlink()
    total_freed += mb
    print("%-30s  freed=%.2fMB" % ('stats-cache.json', mb))

print()
print("=== SUMMARY ===")
print("Total freed: %.1fMB  |  Files deleted: %d" % (total_freed, total_deleted))
print()

# Final state
print("Final .claude state:")
for sub in ['transcripts', 'file-history', 'projects', 'skills', 'commands', 'cache', 'sessions']:
    p = claude / sub
    if p.is_dir():
        mb = sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) / 1024 / 1024
        print("  %-20s %.1fMB" % (sub, mb))
