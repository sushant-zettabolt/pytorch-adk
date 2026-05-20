#!/usr/bin/env python3
"""
Stop hook — ADK-EH01 handoff block enforcer.

Parses ADK-EH01 handoff blocks emitted in the session transcript.
Exits non-zero if:
  - Any block has Status: failed AND Failure mode: hard-stop
  - Any block is malformed (missing required fields)

Exits zero (warning printed) if:
  - Status: failed AND Failure mode: warn-continue

Silently passes if:
  - No handoff blocks found (not every session uses an orchestrator)
"""

import json
import os
import re
import sys

BLOCK_HEADER = re.compile(
    r'^#{1,3}\s+Step (\d+)\s+output\s*[-—]\s*(.+?)\s*$', re.MULTILINE
)
REQUIRED_FIELDS = [
    'Status:',
    'Failure mode:',
    'Key findings:',
    'Artifacts produced:',
    'Errors:',
    'Next step instruction:',
]
FIELD_RE = re.compile(r'\*?\*?(\w[\w /:-]+:)\*?\*?\s*(.+?)(?=\n\*?\*?\w[\w /:-]+:\*?\*?|\Z)', re.DOTALL)


def extract_transcript_text(transcript_path: str) -> list[str]:
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


def parse_handoff_blocks(text: str) -> list[dict]:
    blocks = []
    matches = list(BLOCK_HEADER.finditer(text))
    for i, match in enumerate(matches):
        step_num = match.group(1)
        agent_name = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        blocks.append({
            'step': step_num,
            'agent': agent_name,
            'content': content,
        })
    return blocks


def extract_field(content: str, field_name: str) -> str | None:
    pattern = re.compile(
        rf'\*?\*?{re.escape(field_name)}\*?\*?\s*(.+?)(?=\n\*?\*?\w|\Z)', re.DOTALL | re.IGNORECASE
    )
    m = pattern.search(content)
    if m:
        return m.group(1).strip().splitlines()[0].strip()
    return None


def main() -> int:
    hook_input: dict = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            hook_input = json.loads(raw)
    except Exception:
        pass

    transcript_path = hook_input.get("transcript_path")
    texts = extract_transcript_text(transcript_path)
    full_text = "\n".join(texts)

    blocks: list[dict] = []
    for text in texts:
        blocks.extend(parse_handoff_blocks(text))

    if not blocks:
        print("[handoff-block-enforcer] No handoff blocks found — OK.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    for block in blocks:
        step = block['step']
        agent = block['agent']
        content = block['content']

        missing = [f for f in REQUIRED_FIELDS if f.lower() not in content.lower()]
        if missing:
            errors.append(
                f"Step {step} ({agent}): malformed block — missing fields: {missing}\n"
                f"  Content preview: {content[:120].strip()}"
            )
            continue

        status = extract_field(content, 'Status:') or ''
        failure_mode = extract_field(content, 'Failure mode:') or ''

        if 'failed' in status.lower():
            if 'hard-stop' in failure_mode.lower():
                next_inst = extract_field(content, 'Next step instruction:') or '(none)'
                errors.append(
                    f"Step {step} ({agent}): HARD STOP\n"
                    f"  Status: {status}\n"
                    f"  Failure mode: {failure_mode}\n"
                    f"  Next step: {next_inst[:200]}"
                )
            elif 'warn-continue' in failure_mode.lower():
                warnings.append(f"Step {step} ({agent}): warn-continue (partial result, execution continues)")
            elif 'retry' in failure_mode.lower():
                warnings.append(f"Step {step} ({agent}): retry requested")
            elif 'unknown' in failure_mode.lower():
                errors.append(
                    f"Step {step} ({agent}): unknown failure mode — manual intervention required\n"
                    f"  Content: {content[:200].strip()}"
                )
            else:
                errors.append(
                    f"Step {step} ({agent}): Status=failed but Failure mode unrecognized: '{failure_mode}'"
                )

    print(f"[handoff-block-enforcer] Checked {len(blocks)} handoff block(s).")
    for w in warnings:
        print(f"  WARNING: {w}")

    if errors:
        print("[handoff-block-enforcer] FATAL errors detected:")
        for e in errors:
            print(f"  ERROR: {e}")
        return 1

    if warnings:
        print("[handoff-block-enforcer] Completed with warnings (warn-continue steps noted above).")
    else:
        print("[handoff-block-enforcer] All blocks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
