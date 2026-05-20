#!/usr/bin/env bash
# PreToolUse hook — warns before editing Dispatcher.h / TensorImpl.h (Tier 1 files).

set -euo pipefail

TOOL_INPUT="${1:-}"
if [ -z "$TOOL_INPUT" ]; then
  TOOL_INPUT=$(cat)
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON="$ROOT/venv/bin/python"; [ -f "$PYTHON" ] || PYTHON="$(command -v python3 || command -v python)"
FILE_PATH=$(echo "$TOOL_INPUT" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Tier 1 files — highest blast radius
TIER1_FILES=(
  "aten/src/ATen/Dispatcher.h"
  "aten/src/ATen/Dispatcher.cpp"
  "c10/core/TensorImpl.h"
  "c10/core/TensorImpl.cpp"
  "c10/core/DispatchKey.h"
  "torch/csrc/autograd/python_variable.cpp"
  "aten/src/ATen/core/op_registration/"
)

for tier1 in "${TIER1_FILES[@]}"; do
  if echo "$FILE_PATH" | grep -q "$tier1"; then
    echo "WARNING: You are about to edit a TIER 1 file: $FILE_PATH" >&2
    echo "" >&2
    echo "Tier 1 files have the highest blast radius in PyTorch." >&2
    echo "A bug here cannot be contained to one subsystem." >&2
    echo "" >&2
    echo "Requirements before editing:" >&2
    echo "  1. Load blast-radius.md and confirm tier classification" >&2
    echo "  2. Notify Architecture Owner" >&2
    echo "  3. Run post-edit-impact-analysis after the edit" >&2
    echo "" >&2
    echo "To proceed, the user must explicitly confirm this edit." >&2
    # Exit 2 = warning (allow with confirmation), not hard block
    exit 2
  fi
done

exit 0
