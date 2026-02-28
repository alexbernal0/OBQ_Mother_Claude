#!/bin/bash
# PostToolUse hook: Python syntax validation after any .py file write

TOOL_INPUT=$(cat)
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') or d.get('file_path',''))" 2>/dev/null)

if [[ "$FILE_PATH" == *.py ]]; then
    if python3 -m py_compile "$FILE_PATH" 2>/dev/null; then
        echo "Syntax OK: $FILE_PATH"
        exit 0
    else
        ERRORS=$(python3 -m py_compile "$FILE_PATH" 2>&1)
        echo "SYNTAX ERROR in $FILE_PATH:" >&2
        echo "$ERRORS" >&2
        exit 0  # exit 0 = warn but don't block (syntax errors need to be fixed but shouldn't block Claude)
    fi
fi
exit 0
