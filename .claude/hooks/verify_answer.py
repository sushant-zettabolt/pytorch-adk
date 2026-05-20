#!/usr/bin/env python3
"""
Stop hook — grep-validate every path:LINE — "anchor" citation found in the
session transcript AND all skill files.

Reads Claude Code Stop hook JSON from stdin (may include transcript_path).
Exits non-zero if any citation anchor cannot be found within ±5 lines of
the stated line number in the actual file.
"""

import json
import os
import re
import sys

CITATION_PATTERN = re.compile(r'([\w][\w/.-]+\.\w+):(\d+) — "([^"]+)"')


def _project_root() -> str:
    try:
        import subprocess
        return subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return os.getcwd()


PYTORCH_ROOT = os.environ.get("PYTORCH_ROOT", _project_root())
ADK_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SEARCH_ROOTS = [PYTORCH_ROOT, ADK_ROOT, "."]


def find_file(rel_path: str) -> str | None:
    for root in SEARCH_ROOTS:
        candidate = os.path.join(root, rel_path)
        if os.path.isfile(candidate):
            return candidate
    return None


def validate_citation(rel_path: str, line_no: int, anchor: str) -> tuple[bool, str | None]:
    filepath = find_file(rel_path)
    if not filepath:
        return False, f"file not found: {rel_path}"
    try:
        with open(filepath, errors="replace") as f:
            lines = f.readlines()
        start = max(0, line_no - 6)   # line_no is 1-indexed
        end = min(len(lines), line_no + 5)
        window = "".join(lines[start:end])
        if anchor in window:
            return True, None
        return False, f'anchor "{anchor[:60]}" not found near line {line_no} (checked lines {start+1}–{end})'
    except Exception as e:
        return False, str(e)


def extract_text_from_transcript(transcript_path: str) -> list[str]:
    texts = []
    if not transcript_path or not os.path.exists(transcript_path):
        return texts
    try:
        with open(transcript_path, errors="replace") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    obj = json.loads(raw_line)
                    if obj.get("role") != "assistant":
                        continue
                    content = obj.get("content", "")
                    if isinstance(content, str):
                        texts.append(content)
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                texts.append(block.get("text", ""))
                except (json.JSONDecodeError, AttributeError):
                    pass
    except Exception:
        pass
    return texts


def collect_skill_texts() -> list[str]:
    texts = []
    skill_root = os.path.join(ADK_ROOT, ".claude", "skills")
    if not os.path.exists(skill_root):
        skill_root = ".claude/skills"
    if os.path.exists(skill_root):
        for root, _dirs, files in os.walk(skill_root):
            for fname in files:
                if fname.endswith(".md"):
                    try:
                        texts.append(open(os.path.join(root, fname), errors="replace").read())
                    except Exception:
                        pass
    return texts


def main() -> int:
    hook_input: dict = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            hook_input = json.loads(raw)
    except Exception:
        pass

    transcript_path = hook_input.get("transcript_path")

    texts: list[str] = []
    if transcript_path:
        texts.extend(extract_text_from_transcript(transcript_path))
    texts.extend(collect_skill_texts())

    # Collect unique citations
    citations: set[tuple[str, int, str]] = set()
    for text in texts:
        for match in CITATION_PATTERN.finditer(text):
            path, line_str, anchor = match.group(1), match.group(2), match.group(3)
            try:
                citations.add((path, int(line_str), anchor))
            except ValueError:
                pass

    if not citations:
        print("[verify_answer] No path:LINE citations found.")
        return 0

    failed: list[str] = []
    passed = 0
    for rel_path, line_no, anchor in sorted(citations):
        ok, reason = validate_citation(rel_path, line_no, anchor)
        if ok:
            passed += 1
        else:
            failed.append(f'  {rel_path}:{line_no} — "{anchor[:60]}"\n    reason: {reason}')

    total = passed + len(failed)
    print(f"[verify_answer] Citations checked: {passed}/{total} pass")

    if failed:
        print("[verify_answer] FAILED citations (anchor not found in file window):")
        for entry in failed[:20]:
            print(entry)
        if len(failed) > 20:
            print(f"  ... and {len(failed) - 20} more")
        print("\nFix by: (a) correcting the line number, (b) correcting the anchor phrase,")
        print("or (c) marking with TODO(citation-needed) if the source has moved.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
