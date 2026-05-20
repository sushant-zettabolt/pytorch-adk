---
name: dynamo
description: "TorchDynamo internals: Python bytecode tracing, FX graph capture, FakeTensor, and graph break causes. Use for questions about @torch.compile tracing or graph breaks."
validated-at: 70d99e998b4
---

# Dynamo Skill
## What Is Dynamo?
TorchDynamo is a Python bytecode transformer that intercepts Python execution, traces PyTorch ops into an FX graph, and hands that graph to a backend compiler (default: Inductor).

## Key Questions

**Q: How does `@torch.compile` work?**
A: Installs a custom Python frame evaluator via CPython's `sys.settrace` equivalent. On first call, Dynamo traces the function, produces an FX graph, and compiles it.
`torch/_dynamo/eval_frame.py:LINE — "_compile"`

**Q: What causes a graph break?**
Top causes:
1. Python control flow that depends on tensor values (if tensor > 0)
2. Data-dependent shapes
3. `print()` statements inside compiled region
4. Unsupported Python builtins
5. Calling non-torch code that Dynamo can't trace
`torch/_dynamo/exc.py:LINE — "Unsupported"`

**Q: What is FakeTensor?**
A: A Tensor subclass used during tracing. Operations are recorded without executing. Shape/dtype metadata is preserved.
`torch/_subclasses/fake_tensor.py:LINE — "class FakeTensor"`

**Q: How to debug graph breaks?**
A: `torch._dynamo.explain(fn)(*args)` — prints graph break locations and reasons.

## Blast Radius
- `torch/_dynamo/eval_frame.py` — Tier 2 (all torch.compile entry paths)
- `torch/_dynamo/bytecode_transformation.py` — Tier 2 (bytecode transformation)
