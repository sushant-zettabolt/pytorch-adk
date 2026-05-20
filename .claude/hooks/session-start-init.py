#!/usr/bin/env python3
"""
SessionStart hook — on session open:
1. Load ADK.md and check pinned commit
2. Check index currency (index_meta.json vs HEAD)
3. Remind of open questions.md items
"""

import json
import os
import subprocess
import sys

def get_head_commit() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"

def check_index_currency() -> tuple[bool, str]:
    meta_path = ".claude/index/index_meta.json"
    if not os.path.exists(meta_path):
        return False, "index_meta.json not found — run python tools/adk/build_index.py"

    try:
        with open(meta_path) as f:
            meta = json.load(f)
        built_at = meta.get("built_at_commit", "unknown")
        head = get_head_commit()
        # In no-git context treat index as current (can't determine staleness)
        if not head or head == "unknown":
            return True, f"Index built at {built_at[:8]} (no git context — cannot verify)"
        if built_at == head:
            return True, f"Index current at {built_at[:8]}"
        else:
            return False, f"Index stale: built at {built_at[:8]}, HEAD is {head[:8]}"
    except Exception as e:
        return False, f"Error reading index_meta.json: {e}"

def get_open_questions() -> list[str]:
    questions_path = "questions.md"
    if not os.path.exists(questions_path):
        return []

    open_items = []
    try:
        with open(questions_path) as f:
            for line in f:
                if "| open |" in line:
                    # Format: | question | open | citation |
                    parts = line.split("|")
                    if len(parts) >= 3:
                        question = parts[1].strip()
                        open_items.append(question)
    except Exception:
        pass
    return open_items[:5]  # Show at most 5

def get_pinned_commit() -> str:
    adk_path = "ADK.md"
    if not os.path.exists(adk_path):
        return "unknown"
    try:
        with open(adk_path) as f:
            for line in f:
                if "Pinned Commit" in line and "`" in line:
                    # Extract commit from backticks
                    parts = line.split("`")
                    if len(parts) >= 2:
                        return parts[1]
    except Exception:
        pass
    return "unknown"

def main():
    print("=" * 60)
    print("PyTorch ADK — Session Initialized")
    print("=" * 60)

    # Check pinned commit
    pinned = get_pinned_commit()
    head = get_head_commit()
    if pinned != "unknown" and head != "unknown":
        if head.startswith(pinned) or pinned.startswith(head[:7]):
            print(f"Commit: {head[:8]} ✓ (matches pinned {pinned[:8]})")
        else:
            print(f"WARNING: HEAD={head[:8]} differs from pinned commit={pinned[:8]}")
            print("  Run: python tools/adk/staleness-scanner.py to check staleness")

    # Check index currency
    index_ok, index_msg = check_index_currency()
    if index_ok:
        print(f"Index: {index_msg} ✓")
    else:
        print(f"WARNING: {index_msg}")
        print("  Navigation agents will use grep fallback")
        print("  Fix: venv/bin/python tools/adk/build_index.py")

    # Show open questions
    open_qs = get_open_questions()
    if open_qs:
        print(f"\nOpen questions ({len(open_qs)} shown of all in questions.md):")
        for q in open_qs:
            print(f"  - {q}")
    else:
        print("\nNo open questions — questions.md up to date.")

    print("=" * 60)

if __name__ == "__main__":
    main()
