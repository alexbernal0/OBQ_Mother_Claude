#!/usr/bin/env python3
"""PostToolUse hook: Track tool output sizes and flag bloat.

Deterministic context-health monitor — no LLM calls.
Logs every tool call's output size to .mother/telemetry/usage.jsonl.
Warns (non-blocking) when a single tool output exceeds threshold.
"""
import sys, json, os, hashlib, time
from datetime import datetime

MOTHER_DIR = os.path.join(os.path.expanduser("~"), ".mother")
TELEMETRY_DIR = os.path.join(MOTHER_DIR, "telemetry")
COMPRESSED_DIR = os.path.join(MOTHER_DIR, "compressed")
USAGE_LOG = os.path.join(TELEMETRY_DIR, "usage.jsonl")
WARN_THRESHOLD = 5000  # chars — warn if single tool output exceeds this

# Ensure directories exist
for d in [TELEMETRY_DIR, COMPRESSED_DIR]:
    os.makedirs(d, exist_ok=True)

try:
    hook_data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

# Extract tool info
tool_name = hook_data.get("tool_name", "unknown")
tool_input = hook_data.get("tool_input", {})
tool_output = hook_data.get("tool_output", "")

# Calculate output size
if isinstance(tool_output, str):
    output_size = len(tool_output)
elif isinstance(tool_output, dict):
    output_size = len(json.dumps(tool_output))
else:
    output_size = len(str(tool_output))

# Estimate tokens (~4 chars per token)
est_tokens = output_size // 4

# Log to telemetry
entry = {
    "ts": datetime.now().isoformat(),
    "tool": tool_name,
    "input_file": tool_input.get("file_path", tool_input.get("command", ""))[:120],
    "output_chars": output_size,
    "est_tokens": est_tokens,
}

try:
    with open(USAGE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
except Exception:
    pass  # telemetry is best-effort

# Warn on large outputs (non-blocking)
if output_size > WARN_THRESHOLD:
    print(f"[Mother Compressor] Large output: {tool_name} → {output_size:,} chars (~{est_tokens:,} tokens). Consider /compress-now.", file=sys.stderr)

# For very large outputs, store a compressed hash reference
if output_size > 20000:
    content_hash = hashlib.md5(str(tool_output).encode()).hexdigest()[:12]
    ref_file = os.path.join(COMPRESSED_DIR, f"{content_hash}.ref")
    try:
        with open(ref_file, "w", encoding="utf-8") as f:
            json.dump({
                "ts": entry["ts"],
                "tool": tool_name,
                "source": entry["input_file"],
                "chars": output_size,
                "preview": str(tool_output)[:500],
            }, f, indent=2)
    except Exception:
        pass

sys.exit(0)
