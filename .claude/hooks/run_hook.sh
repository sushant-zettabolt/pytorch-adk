#!/bin/sh
# Portable Python launcher for ADK hooks.
# Finds venv/bin/python relative to the project root; falls back to python3.
# Usage: sh .claude/hooks/run_hook.sh .claude/hooks/<hook>.py
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON="$ROOT/venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    PYTHON="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)"
fi
if [ -z "$PYTHON" ]; then
    echo "[run_hook] ERROR: no Python interpreter found (looked for venv/bin/python, python3, python)" >&2
    exit 1
fi
exec "$PYTHON" "$@"
