import json, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
home = pathlib.Path.home()

oc = home / '.config' / 'opencode' / 'opencode.json'
d = json.loads(oc.read_text(encoding='utf-8'))
models = list(d['provider']['ollama']['models'].keys())
print('opencode.json ollama models:')
for m in models: print('  ' + m)

omo = home / '.config' / 'opencode' / 'oh-my-opencode.json'
d2 = json.loads(omo.read_text(encoding='utf-8'))
print()
print('Agent routing:')
for agent, cfg in d2['agents'].items():
    print('  ' + agent.ljust(22) + cfg['model'])
print()
print('Category routing:')
for cat, cfg in d2['categories'].items():
    print('  ' + cat.ljust(22) + cfg['model'])

c_models = pathlib.Path('C:/Users/admin/.ollama/models')
print()
if c_models.exists():
    files = list(c_models.iterdir())
    print('C drive models: ' + str(files) + ' WARNING')
else:
    print('C drive models: NONE - clean OK')

print()
print('D drive model manifests:')
d_mfst = pathlib.Path(r'D:\LLM Models\manifests\registry.ollama.ai\library')
if d_mfst.exists():
    for m in d_mfst.iterdir():
        print('  ' + m.name)
