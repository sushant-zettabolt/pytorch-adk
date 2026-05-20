#!/usr/bin/env bash
# PreToolUse hook — blocks any edit to generated files before it happens.

set -euo pipefail

# Get the file path from the tool input (passed as first argument or from stdin JSON)
TOOL_INPUT="${1:-}"
if [ -z "$TOOL_INPUT" ]; then
  TOOL_INPUT=$(cat)
fi

# Extract file_path from the JSON input
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON="$ROOT/venv/bin/python"; [ -f "$PYTHON" ] || PYTHON="$(command -v python3 || command -v python)"
FILE_PATH=$(echo "$TOOL_INPUT" | "$PYTHON" -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0  # Not an edit tool call with a file_path
fi

# Patterns for generated files
GENERATED_PATTERNS=(
  "torch/csrc/autograd/generated/"
  "build/"
  "_generated"
  "@generated"
  "python_torch_functions_2.cpp"
  "python_torch_functions_1.cpp"
)

for pattern in "${GENERATED_PATTERNS[@]}"; do
  if echo "$FILE_PATH" | grep -q "$pattern"; then
    echo "ERROR: Blocked edit to generated file: $FILE_PATH" >&2
    echo "Generated files must not be edited directly. They are overwritten on every build." >&2
    echo "If you need to change this file's output, modify the template or generator script instead." >&2
    exit 1
  fi
done

# Also check file header for @generated marker
if [ -f "$FILE_PATH" ] && head -5 "$FILE_PATH" | grep -q "@generated"; then
  echo "ERROR: Blocked edit to generated file: $FILE_PATH" >&2
  echo "This file has a @generated header. Do not edit it directly." >&2
  exit 1
fi

exit 0
