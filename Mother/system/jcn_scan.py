import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
jcn = pathlib.Path(r'C:\Users\admin\Desktop\JCNDashboardApp')

pages = jcn / 'src' / 'app' / '(dashboard)'
print('Dashboard pages:')
for d in sorted(pages.iterdir()):
    if d.is_dir():
        files = [f.name for f in d.iterdir() if f.is_file()]
        print('  /' + d.name.ljust(30) + ' ' + str(files))

print()
api = jcn / 'api'
print('API modules:')
for f in sorted(api.iterdir()):
    if f.suffix == '.py' and not f.name.startswith('_'):
        lines = f.read_text(encoding='utf-8', errors='ignore').splitlines()
        desc = ''
        for l in lines[1:10]:
            s = l.strip().strip('"').strip("'")
            if s and not s.startswith('#') and len(s) > 10:
                desc = s[:75]
                break
        print('  ' + f.name.ljust(42) + ' ' + desc)

print()
print('Key config files:')
for fname in ['vercel.json', 'next.config.mjs', 'requirements.txt', 'package.json']:
    p = jcn / fname
    if p.exists():
        print('  ' + fname + ' (' + str(p.stat().st_size) + ' bytes)')

print()
print('Existing checkpoints:')
for f in sorted(jcn.glob('CHECKPOINT*.md')):
    print('  ' + f.name)
