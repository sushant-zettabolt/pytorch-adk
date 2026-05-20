#!/usr/bin/env python3
"""
PostToolUse hook — after any Edit: determine which test files cover the changed file.
Uses test_weighted_graph.graphml if available; falls back to grep heuristics.
"""

import json
import os
import subprocess
import sys

def get_tool_result():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}

def find_tests_for_file(changed_file: str) -> list[str]:
    tests = []

    # Try index first
    graph_path = ".claude/index/test_weighted_graph.graphml"
    if os.path.exists(graph_path):
        try:
            import networkx as nx
            G = nx.read_graphml(graph_path)
            # Find nodes matching the changed file
            for node, data in G.nodes(data=True):
                if changed_file in data.get("file", ""):
                    # Find all tests that reach this node
                    for test_node in G.nodes():
                        if test_node.startswith("test_"):
                            if nx.has_path(G, test_node, node):
                                tests.append(test_node)
        except ImportError:
            pass  # networkx not available, fall back to grep

    if not tests:
        # Grep fallback: find test files that import or reference the module
        base_name = os.path.basename(changed_file).replace(".cpp", "").replace(".h", "").replace(".py", "")
        try:
            result = subprocess.run(
                ["grep", "-rl", base_name, "test/"],
                capture_output=True, text=True, timeout=10
            )
            tests = result.stdout.strip().split("\n") if result.stdout.strip() else []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            tests = []

    return [t for t in tests if t]

def main():
    data = get_tool_result()
    changed_file = data.get("file_path", "")

    if not changed_file:
        return

    print(f"\n[post-edit-targeted-tests] Changed: {changed_file}")

    tests = find_tests_for_file(changed_file)

    if tests:
        print(f"Tests that cover this file:")
        for test in tests[:10]:  # Cap at 10
            print(f"  {test}")
        if len(tests) > 10:
            print(f"  ... and {len(tests) - 10} more")
        print(f"\nRun targeted tests:")
        print(f"  python -m pytest {tests[0]} -v")
    else:
        print("No test coverage found via index or grep.")
        print("Consider adding an OpInfo entry or checking test/ directory manually.")

if __name__ == "__main__":
    main()
