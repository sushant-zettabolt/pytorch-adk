#!/usr/bin/env bash
# Install the PyTorch ADK into a target PyTorch checkout.
# Usage: bash install.sh /path/to/pytorch-checkout

set -euo pipefail

ADK_SRC="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
  echo "Usage: bash install.sh /path/to/pytorch-checkout"
  exit 1
fi

if [[ ! -d "$TARGET/.git" ]]; then
  echo "ERROR: $TARGET is not a git repository."
  exit 1
fi

echo "Installing PyTorch ADK into: $TARGET"
echo "Source: $ADK_SRC"
echo ""

# Agents
echo "[1/5] Copying agents..."
mkdir -p "$TARGET/.claude/agents"
cp "$ADK_SRC/.claude/agents/"*.md "$TARGET/.claude/agents/"

# Skills
echo "[2/5] Copying skills..."
mkdir -p "$TARGET/.claude/skills"
cp -r "$ADK_SRC/.claude/skills/"* "$TARGET/.claude/skills/"

# Hooks
echo "[3/5] Copying hooks..."
mkdir -p "$TARGET/.claude/hooks"
cp "$ADK_SRC/.claude/hooks/"*.py "$TARGET/.claude/hooks/"
cp "$ADK_SRC/.claude/hooks/"*.sh "$TARGET/.claude/hooks/"
chmod +x "$TARGET/.claude/hooks/"*.sh

# MCP configs
echo "[4/5] Copying MCP configs..."
mkdir -p "$TARGET/.claude/mcp"
cp "$ADK_SRC/.claude/mcp/"*.json "$TARGET/.claude/mcp/"

# ADK tools
echo "[5/5] Copying tools..."
mkdir -p "$TARGET/tools/adk"
cp "$ADK_SRC/tools/adk/"*.py "$TARGET/tools/adk/"

# CLAUDE.md
cp "$ADK_SRC/.claude/CLAUDE.md" "$TARGET/.claude/CLAUDE.md"

# settings.json — merge-safe: never overwrite an existing file
if [[ -f "$TARGET/.claude/settings.json" ]]; then
  echo ""
  echo "NOTE: $TARGET/.claude/settings.json already exists — not overwritten."
  echo "  Merge the hooks block from: $ADK_SRC/.claude/settings.json.template"
  echo "  The hooks you need wired up are listed in that file."
else
  cp "$ADK_SRC/.claude/settings.json.template" "$TARGET/.claude/settings.json"
  echo "  Wrote settings.json from template."
fi

echo ""
echo "Done. Next steps:"
echo ""
echo "  1. cd $TARGET"
echo "  2. python tools/adk/build_index.py"
echo "     Builds symbols.json, boundary_table.json, and unified_graph.graphml."
echo "     Set PYTORCH_ROOT if needed: PYTORCH_ROOT=$TARGET python tools/adk/build_index.py"
echo ""
echo "  3. Open a Claude Code session in $TARGET."
echo "     The session-start hook fires automatically and confirms index currency."
echo ""
