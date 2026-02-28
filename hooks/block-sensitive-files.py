#!/usr/bin/env python3
"""PreToolUse hook: block writes to sensitive files (.env, credentials, secrets)."""
import sys, json, os

try:
    tool_input = json.load(sys.stdin)
except:
    sys.exit(0)  # can't parse, let it through

file_path = tool_input.get('tool_input', {}).get('file_path', '')
if not file_path:
    file_path = tool_input.get('file_path', '')

BLOCKED_NAMES = ['.env', '.env.local', '.env.production', '.env.development',
                 'credentials.json', 'secrets.json', 'secrets.yaml', 'secrets.yml',
                 '.netrc', 'id_rsa', 'id_ed25519']
BLOCKED_PATTERNS = ['.env.', 'secret', 'credential', 'password', 'api_key']

filename = os.path.basename(file_path).lower()

if filename in [b.lower() for b in BLOCKED_NAMES]:
    print(f"BLOCKED: Refusing to write to sensitive file: {file_path}", file=sys.stderr)
    sys.exit(2)

for pattern in BLOCKED_PATTERNS:
    if pattern in filename and '.env.' in filename:
        print(f"BLOCKED: Refusing to write to potential secrets file: {file_path}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
