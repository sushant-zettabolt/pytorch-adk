#!/usr/bin/env python3
"""
SubagentStop hook — when any subagent finishes:
Verifies output contains required path:LINE citations.
"""

import json
import re
import sys

CITATION_PATTERN = re.compile(r'[\w/.-]+\.\w+:\d+ — "[\w\s]+"')

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    agent_name = data.get("agent_name", "unknown")
    output = data.get("output", "")

    if not output:
        print(f"[subagent-citation-check] Agent '{agent_name}' produced no output.")
        return

    # Agents that MUST produce citations
    citation_required_agents = [
        "symbol-locator",
        "call-tracer",
        "question-solver",
        "code-reviewer",
        "pr-reviewer",
        "kernel-writer",
        "codebase-explorer",
    ]

    if agent_name not in citation_required_agents:
        return  # Other agents don't need citations

    citations = CITATION_PATTERN.findall(output)

    if not citations:
        print(f"[subagent-citation-check] WARNING: Agent '{agent_name}' produced output with NO citations.")
        print("  All factual claims require path:LINE — 'anchor phrase' citations.")
        print("  Re-run the agent with explicit citation requirements.")
    else:
        print(f"[subagent-citation-check] Agent '{agent_name}' produced {len(citations)} citation(s). ✓")
        for citation in citations[:3]:
            print(f"  {citation}")
        if len(citations) > 3:
            print(f"  ... and {len(citations) - 3} more")

if __name__ == "__main__":
    main()
