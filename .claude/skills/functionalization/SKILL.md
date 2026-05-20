---
name: functionalization
description: "Converting in-place and view ops to out-of-place equivalents for functional backends (XLA, export). Covers FunctionalTensorWrapper and view replay. Use for functional-tensor questions."
validated-at: 70d99e998b4
---

# Functionalization Skill
## What Is Functionalization?
A transformation that converts in-place ops (add_) and view ops to out-of-place equivalents. Required by functional backends (JAX-style, XLA, export).

## Key Questions

**Q: Why is functionalization needed?**
A: Functional backends can't model aliasing or mutation. Functionalization makes PyTorch programs safe for these backends.

**Q: How does FunctionalTensorWrapper work?**
A: Wraps a real tensor. Records mutations into a "functional" representation. On commit, applies all mutations at once.
`aten/src/ATen/FunctionalTensorWrapper.h:LINE — "class FunctionalTensorWrapper"`

**Q: How is functionalization enabled?**
A: Via `torch.func.functionalize(fn)` or as a compile pass in Inductor.
`torch/_functorch/functional_call.py:LINE — "functionalize"`

**Q: What is a "view replay"?**
A: When a view's base is mutated, functionalization needs to propagate the mutation to the view. View replay reconstructs the view chain.

## Blast Radius
- `aten/src/ATen/FunctionalTensorWrapper.cpp` — Tier 2 (all functional backends)
