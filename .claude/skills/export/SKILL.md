---
name: export
description: "torch.export and ExportedProgram: capturing PyTorch programs as portable graphs, dynamic shapes via Dim, export constraints. Use for questions about torch.export."
validated-at: 70d99e998b4
---

# Export Skill
## What Is torch.export?
A mechanism to capture a PyTorch program as a portable, serializable representation (ExportedProgram) suitable for deployment without a Python runtime.

## Key Questions

**Q: How does `torch.export.export` work?**
A: Traces the function with sample inputs, running Dynamo tracing + functionalization. Produces an `ExportedProgram` containing a flat FX graph with no Python control flow.
`torch/export/__init__.py:LINE — "def export"`

**Q: What is an ExportedProgram?**
A: A data structure holding the traced graph, parameter/buffer state dict, and module hierarchy.
`torch/export/exported_program.py:LINE — "class ExportedProgram"`

**Q: What is `torch.export.Dim`?**
A: Specifies symbolic dynamic dimensions in the exported program.
```python
batch = torch.export.Dim("batch", min=1, max=128)
torch.export.export(fn, args, dynamic_shapes={"x": {0: batch}})
```
`torch/export/dynamic_shapes.py:LINE — "class Dim"`

**Q: What constraints must the program satisfy for export?**
A: No data-dependent control flow, no unsupported Python operations, all custom ops fully registered with Meta kernels.

## Blast Radius
- `torch/export/` — Tier 2 (all export tests)
