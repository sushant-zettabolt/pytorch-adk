#!/usr/bin/env python3
"""
Stop hook — on session end:
Generates summary of files changed, questions answered, citations added.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

def get_changed_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f]
    except Exception:
        return []

def count_new_citations(changed_files: list[str]) -> int:
    count = 0
    for f in changed_files:
        if not os.path.exists(f):
            continue
        try:
            result = subprocess.run(
                ["git", "diff", "HEAD", "--", f],
                capture_output=True, text=True
            )
            # Count added lines with citation pattern
            for line in result.stdout.split("\n"):
                if line.startswith("+") and " — " in line and ":" in line:
                    count += 1
        except Exception:
            pass
    return count

def get_answered_questions() -> list[str]:
    questions_path = "questions.md"
    if not os.path.exists(questions_path):
        return []
    answered = []
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD", "--", questions_path],
            capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if line.startswith("+") and "answered-with-proof" in line:
                answered.append(line)
    except Exception:
        pass
    return answered

def main():
    changed = get_changed_files()
    new_citations = count_new_citations(changed)
    answered = get_answered_questions()

    print("\n" + "=" * 60)
    print(f"ADK Session Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if changed:
        print(f"\nFiles changed ({len(changed)}):")
        for f in changed[:10]:
            print(f"  {f}")
        if len(changed) > 10:
            print(f"  ... and {len(changed) - 10} more")
    else:
        print("\nNo files changed this session.")

    if new_citations > 0:
        print(f"\nNew citations added: {new_citations}")

    if answered:
        print(f"\nQuestions answered with proof: {len(answered)}")

    print("\nNext session: run session-start-init hook to verify index currency.")
    print("=" * 60)

if __name__ == "__main__":
    main()
