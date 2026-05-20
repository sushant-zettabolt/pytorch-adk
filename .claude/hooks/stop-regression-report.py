#!/usr/bin/env python3
"""
Stop hook — on session end after build:
Compares test results against baseline and reports regressions.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

BASELINE_FILE = ".claude/index/test_baseline.json"


def _find_python() -> str:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        candidate = os.path.join(root, "venv", "bin", "python")
        if os.path.isfile(candidate):
            return candidate
    except Exception:
        pass
    import shutil
    return shutil.which("python3") or shutil.which("python") or "python3"


PYTHON_BIN = _find_python()


def run_quick_tests(test_files: list[str]) -> dict[str, str]:
    results = {}
    for test_file in test_files[:5]:  # Cap at 5 for quick check
        if not os.path.exists(test_file):
            continue
        try:
            result = subprocess.run(
                [PYTHON_BIN, "-m", "pytest", test_file, "-q", "--tb=no", "--no-header", "-x"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                results[test_file] = "PASS"
            else:
                results[test_file] = "FAIL"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results[test_file] = "TIMEOUT"
    return results

def load_baseline() -> dict[str, str]:
    if os.path.exists(BASELINE_FILE):
        try:
            with open(BASELINE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_baseline(results: dict[str, str]):
    os.makedirs(os.path.dirname(BASELINE_FILE), exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(results, f, indent=2)

def get_changed_test_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True
        )
        all_changed = result.stdout.strip().split("\n")
        return [f for f in all_changed if f.startswith("test/") and f.endswith(".py")]
    except Exception:
        return []

def main():
    changed_tests = get_changed_test_files()

    if not changed_tests:
        print("[stop-regression-report] No test files changed this session. Skipping.")
        return

    print(f"\n[stop-regression-report] Running regression check on {len(changed_tests)} changed test files...")

    baseline = load_baseline()
    current = run_quick_tests(changed_tests)

    regressions = []
    for test_file, status in current.items():
        if test_file in baseline and baseline[test_file] == "PASS" and status == "FAIL":
            regressions.append(test_file)

    if regressions:
        print(f"REGRESSIONS DETECTED ({len(regressions)}):")
        for r in regressions:
            print(f"  FAIL: {r}")
        print("\nDo not submit PR until regressions are resolved.")
    else:
        print("No regressions detected.")
        save_baseline(current)

    print(f"Results: {sum(1 for v in current.values() if v=='PASS')}/{len(current)} PASS")

if __name__ == "__main__":
    main()
