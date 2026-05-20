---
name: torchgen
description: "Code generation from native_functions.yaml: generated Python bindings and C++ dispatch stubs. Use for questions about torchgen or generated files."
validated-at: 70d99e998b4
---

# Torchgen Skill
## What Is Torchgen?
The code generation system that reads `native_functions.yaml` and generates C++ bindings, Python wrappers, and dispatch stubs.

## Key Questions

**Q: What does torchgen generate?**
A: From `native_functions.yaml`:
- `torch/csrc/autograd/generated/` — Python bindings (DO NOT EDIT)
- `build/aten/src/ATen/` — C++ dispatch stubs (DO NOT EDIT)

**Q: How is torchgen invoked?**
A: `python tools/codegen/gen.py` (or via cmake build system).
`tools/codegen/gen.py:LINE — "def main"`

**Q: What is a `dispatch:` key in native_functions.yaml?**
A: Maps DispatchKey to implementation function name.
```yaml
- func: add.Tensor(Tensor self, Tensor other) -> Tensor
  dispatch:
    CPU: add_cpu
    CUDA: add_cuda
```

## Blast Radius
- `tools/codegen/` — Tier 2 (code generation system)
- Generated files — read-only (never edit directly)
