---
name: backend-reg
description: "How backends (CPU, CUDA, XLA, MPS) register kernel implementations for ATen operators. Covers TORCH_LIBRARY_IMPL, CompositeImplicitAutograd vs CompositeExplicitAutograd. Use for questions about kernel registration."
validated-at: 70d99e998b4
---

# Backend Registration Skill
## What Is Backend Registration?
The mechanism by which a backend (CPU, CUDA, XLA, MPS) registers kernel implementations for ATen operators.

## Key Questions

**Q: How do you register a CPU kernel?**
A:
```cpp
TORCH_LIBRARY_IMPL(aten, CPU, m) {
  m.impl("add.Tensor", &add_cpu_impl);
}
```
`aten/src/ATen/native/Add.cpp:LINE — "TORCH_LIBRARY_IMPL.*CPU"`

**Q: What is CompositeImplicitAutograd?**
A: A DispatchKey meaning the kernel is implemented purely in terms of other differentiable ops. Autograd flows through automatically.
`c10/core/DispatchKey.h:LINE — "CompositeImplicitAutograd"`

**Q: What is CompositeExplicitAutograd?**
A: The kernel handles its own autograd (has a custom backward). Autograd does NOT flow through the forward kernel.
`c10/core/DispatchKey.h:LINE — "CompositeExplicitAutograd"`

**Q: How does backend fallback work?**
A: If no kernel for a key, Dispatcher checks alias keys (CompositeImplicitAutograd → CPU → catch-all).

## Blast Radius
- `aten/src/ATen/core/op_registration/` — Tier 1 (registration infrastructure)
