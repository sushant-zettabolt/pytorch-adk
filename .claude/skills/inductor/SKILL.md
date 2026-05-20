---
name: inductor
description: "torch._inductor compiler backend: FX → loop IR → Triton/C++ codegen. Use for questions about Inductor compilation, Triton kernels, or compile-time (vs graph-break) failures."
validated-at: 70d99e998b4
---

# Inductor Skill
## What Is Inductor?
torch._inductor is PyTorch's default compiler backend for torch.compile. It takes an FX graph and generates optimized CPU (C++/OpenMP) or GPU (Triton) kernels.

## Key Questions

**Q: What is the compilation pipeline?**
A: FX graph → Inductor lowering → Loop-level IR (Loops) → Triton codegen → compiled kernel
`torch/_inductor/compile_fx.py:LINE — "def compile_fx"`

**Q: What is a Triton kernel?**
A: A GPU kernel written in the Triton DSL, JIT-compiled to PTX. Inductor generates Triton automatically for eligible ops.
`torch/_inductor/codegen/triton.py:LINE — "class TritonKernel"`

**Q: How to debug "graph break" vs "compilation failure"?**
A: Graph break = Dynamo couldn't trace. Compilation failure = Dynamo succeeded but Inductor failed to lower/codegen.
Use `TORCH_COMPILE_DEBUG=1` env var for full trace.

**Q: What is `torch._inductor.config`?**
A: Configuration object controlling optimization passes (fusions, tiling, padding).
`torch/_inductor/config.py:LINE — "class Config"`

## Blast Radius
- `torch/_inductor/compile_fx.py` — Tier 2 (all compiled kernel tests)
- `torch/_inductor/lowering.py` — Tier 2 (op lowering to loop IR)
