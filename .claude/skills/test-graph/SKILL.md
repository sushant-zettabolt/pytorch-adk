---
name: test-graph
description: "test_weighted_graph.graphml — unified call graph annotated with per-edge test coverage. Use for questions about test coverage of call edges or blast-radius checks."
validated-at: 70d99e998b4
---

# Test Graph Skill ⭐
## What Is the Test Graph?
`test_weighted_graph.graphml` — the unified call graph augmented with per-edge test coverage counts. Produced by `tools/adk/build_test_graph.py`.

## Edge Attributes

| Attribute | Type | Meaning |
|---|---|---|
| `test_count` | int | Number of test functions that exercise this call edge |
| `coverage` | str | `"dynamic"` (traced) or `"static-only"` (not traced by any test) |
| `test_names` | list[str] | Names of tests that exercise this edge |

## Key Questions

**Q: How is the test graph built?**
A:
- Phase A: `sys.settrace` wraps each test, recording `(test_name, caller, callee)` tuples.
  C++ boundary crossings correlated via `torch.profiler` timestamps.
- Phase B: Load `unified_graph.graphml`. Increment `edge['test_count']` per trace. Write `test_weighted_graph.graphml`.

**Q: How do backward-checker and compile-tester use the graph?**
A: Before modifying a function, they query the graph for its edges. Low-coverage edges (test_count < 3) trigger a Tier 1 blast-radius warning.

**Q: What does test_count=0 mean?**
A: The edge has NEVER been exercised by a Python test. Critical caveat: may be exercised by C++ tests or by torch.compile paths not captured by sys.settrace.
Treat as Tier 1 blast radius regardless.

**Q: How often is the test graph rebuilt?**
A: Nightly job. Checked via `test_weighted_graph.graphml` modification time vs current commit.
