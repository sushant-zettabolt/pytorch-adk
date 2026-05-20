---
name: index
description: "The pre-computed ADK call-graph index (.claude/index/): symbols.json, graph files, boundary table. Use for questions about index artifacts or O(1) symbol lookup."
validated-at: 70d99e998b4
---

# Index Skill ⭐
## What Is the Index?
Pre-computed call graphs stored in `.claude/index/`. Enables O(1) navigation lookups instead of O(file reads) re-scanning.

## Index Artifacts

| File | Contents |
|---|---|
| `symbols.json` | Symbol → file:line mapping for all known symbols |
| `python_graph.graphml` | Python-layer call graph |
| `cpp_graph.graphml` | C++ layer call graph |
| `boundary_table.json` | Python→C++ boundary crossings (pybind11 edges) |
| `unified_graph.graphml` | Cross-language merged graph |
| `test_weighted_graph.graphml` | unified graph + test coverage weights |
| `unresolved_edges.json` | Edges that couldn't be resolved |
| `index_meta.json` | `built_at_commit`, `built_at_timestamp`, `unresolved_count` |

## Usage by Navigation Agents
```python
import json, networkx as nx

symbols = json.load(open(".claude/index/symbols.json"))
location = symbols.get("TensorIterator")  # O(1) lookup

G = nx.read_graphml(".claude/index/unified_graph.graphml")
path = nx.shortest_path(G, source="torch.relu", target="at::relu_cpu")
```

## Key Questions

**Q: How is the index built?**
A: `python tools/adk/build_index.py` runs the 3-stage pipeline:
Stage 1: static parsing (Graphify + tree-sitter)
Stage 2: LLM gap-fill for unresolved edges
Stage 3: merge and write all artifacts

**Q: What does index staleness mean?**
A: `index_meta.json.built_at_commit ≠ git rev-parse HEAD`.
Action: re-run `python tools/adk/build_index.py` before any navigation agent runs.

**Q: What does `resolution: static` vs `llm` mean?**
A: `static` = edge confirmed by grep/parse. `llm` = inferred by LLM (confidence ≥ 0.7). Both are usable.
`unknown` = below confidence threshold. Treat unknown edges as Tier 1 blast radius.

**Q: What does test_count=0 mean?**
A: Zero Python tests exercise this edge. Does NOT mean "safe to change." Treat as Tier 1 blast radius.
