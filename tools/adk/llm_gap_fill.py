#!/usr/bin/env python3
"""
Stage 3 — LLM gap fill for unresolved Python→C++ boundary edges.

Reads:
  - .claude/index/unresolved_edges.json  (from parse_boundaries.py)
  - .claude/index/boundary_table.json    (existing entries)

For each unresolved edge:
  - Sends (python call site + 20 lines of context) to the LLM
  - Accepts edges with confidence >= 0.7 → resolution: "llm"
  - Below threshold → resolution: "unknown"

Writes updated boundary_table.json and unresolved_edges.json.

Usage:
    python tools/adk/llm_gap_fill.py [--dry-run] [--max-calls N]

Set ANTHROPIC_API_KEY to enable LLM resolution.
Without the key, runs in dry-run mode (all edges tagged resolution: unknown).
"""

import json
import os
import sys
from pathlib import Path


INDEX_DIR = Path(os.environ.get("INDEX_DIR", ".claude/index"))
CONFIDENCE_THRESHOLD = 0.7
MAX_CONTEXT_LINES = 20

SYSTEM_PROMPT = """\
You are a PyTorch codebase expert. Given a Python call site in PyTorch and \
surrounding context, identify the C++ function it calls through the pybind11 binding layer.

Respond in JSON only:
{
  "cpp_target": "<namespace::function_name or null>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>"
}

Rules:
- If you cannot determine the C++ target with confidence >= 0.7, set cpp_target to null.
- cpp_target format: "at::relu", "torch::autograd::backward", etc.
- Do NOT use generated file paths as citations.
"""


def call_llm(python_call_site: str, context_lines: list[str], source_file: str) -> dict:
    """Call the Anthropic API to resolve a boundary edge."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "cpp_target": None,
            "confidence": 0.0,
            "reasoning": "No ANTHROPIC_API_KEY — dry run",
        }

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        context = "\n".join(context_lines)
        user_msg = (
            f"Python call site: `{python_call_site}`\n"
            f"Source file: {source_file}\n\n"
            f"Context:\n```python\n{context}\n```\n\n"
            "What C++ function does this call through pybind11?"
        )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = message.content[0].text.strip()

        # Parse JSON response
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = "\n".join(text.splitlines()[1:])
            if text.endswith("```"):
                text = text[: text.rfind("```")]

        return json.loads(text)

    except Exception as e:
        return {
            "cpp_target": None,
            "confidence": 0.0,
            "reasoning": f"Error: {e}",
        }


def main():
    dry_run = "--dry-run" in sys.argv
    max_calls = int(sys.argv[sys.argv.index("--max-calls") + 1]) if "--max-calls" in sys.argv else 100

    print("Stage 3 — llm_gap_fill.py")
    if dry_run:
        print("  Mode: dry-run (no LLM calls)")
    elif not os.environ.get("ANTHROPIC_API_KEY"):
        print("  Mode: dry-run (ANTHROPIC_API_KEY not set)")
        dry_run = True
    else:
        print(f"  Mode: live LLM (max {max_calls} calls, threshold={CONFIDENCE_THRESHOLD})")

    # Load existing data
    unresolved_path = INDEX_DIR / "unresolved_edges.json"
    boundary_path = INDEX_DIR / "boundary_table.json"

    if not unresolved_path.exists():
        print(f"  No unresolved_edges.json found at {unresolved_path}")
        print("  Run parse_boundaries.py first.")
        return 0

    with open(unresolved_path) as f:
        unresolved_data = json.load(f)

    unresolved = unresolved_data.get("unresolved", [])
    print(f"  Found {len(unresolved)} unresolved edges")

    if boundary_path.exists():
        with open(boundary_path) as f:
            boundary_table = json.load(f)
    else:
        boundary_table = {}

    # Process unresolved edges
    resolved_count = 0
    unknown_count = 0
    still_unresolved = []

    for i, item in enumerate(unresolved[:max_calls]):
        py_call_site = item["python_call_site"]
        source_file = item.get("source_file", "unknown")
        context = item.get("context", [])

        if dry_run:
            result = {"cpp_target": None, "confidence": 0.0, "reasoning": "dry-run"}
        else:
            if i % 10 == 0:
                print(f"  Processing {i+1}/{min(len(unresolved), max_calls)}: {py_call_site}")
            result = call_llm(py_call_site, context, source_file)

        cpp_target = result.get("cpp_target")
        confidence = result.get("confidence", 0.0)

        if cpp_target and confidence >= CONFIDENCE_THRESHOLD:
            boundary_table[py_call_site] = {
                "cpp_target": cpp_target,
                "resolution": "llm",
                "confidence": confidence,
                "reasoning": result.get("reasoning", ""),
                "binding_file": source_file,
            }
            resolved_count += 1
        else:
            boundary_table[py_call_site] = {
                "cpp_target": None,
                "resolution": "unknown",
                "confidence": confidence,
                "reasoning": result.get("reasoning", ""),
            }
            still_unresolved.append(item)
            unknown_count += 1

    # Any items beyond max_calls stay unresolved
    if len(unresolved) > max_calls:
        still_unresolved.extend(unresolved[max_calls:])

    # Write updated boundary_table.json
    with open(boundary_path, "w") as f:
        json.dump(boundary_table, f, indent=2)

    # Update unresolved_edges.json
    total = len(boundary_table)
    remaining_unresolved = [v for v in boundary_table.values() if isinstance(v, dict) and v.get("resolution") == "unknown"]
    unresolved_pct = len(remaining_unresolved) / total * 100 if total > 0 else 0.0

    with open(unresolved_path, "w") as f:
        json.dump(
            {
                "_meta": {
                    "unresolved_count": len(remaining_unresolved),
                    "total_call_sites": total,
                    "unresolved_pct": round(unresolved_pct, 1),
                    "llm_resolved": resolved_count,
                },
                "unresolved": still_unresolved,
            },
            f,
            indent=2,
        )

    print(f"  LLM resolved: {resolved_count}  Unknown: {unknown_count}")
    print(f"  Total boundary entries: {total}")
    print(f"  Unresolved: {unresolved_pct:.1f}%")

    gate_pass = unresolved_pct < 25.0
    print(f"  Gate: unresolved < 25% → {'PASS' if gate_pass else 'FAIL'}")
    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
