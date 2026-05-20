---
name: fx
description: "torch.fx symbolic tracing: Graph, Node, GraphModule, Transformer, Interpreter. Use for questions about FX graphs or symbolic tracing."
validated-at: 70d99e998b4
---

# FX Skill
## What Is FX?
`torch.fx` is a symbolic tracing toolkit for PyTorch. It produces a `Graph` of `Node` objects representing PyTorch operations on `GraphModule` — a `nn.Module` that wraps the graph.

## Key Questions

**Q: What is a Node?**
A: A single operation in the FX graph. Has an `op` field (call_function, call_method, call_module, placeholder, output), `target`, `args`, and `kwargs`.
`torch/fx/node.py:LINE — "class Node"`

**Q: How is a Graph created?**
A: `torch.fx.symbolic_trace(module)` returns a `GraphModule`. Internally uses `Proxy` objects that record operations.
`torch/fx/symbolic_trace.py:LINE — "def symbolic_trace"`

**Q: How to transform an FX graph?**
A: Subclass `torch.fx.Transformer` and override `call_function` / `call_method` methods. Or iterate `graph.nodes` and use `node.replace_all_uses_with()`.
`torch/fx/transformer.py:LINE — "class Transformer"`

**Q: How does Interpreter work?**
A: `torch.fx.Interpreter(gm).run(*args)` executes the graph node-by-node using Python dispatch.
`torch/fx/interpreter.py:LINE — "class Interpreter"`

## Blast Radius
- `torch/fx/graph.py` — Tier 2 (all FX and Inductor tests)
- `torch/fx/node.py` — Tier 2 (graph structure)
