---
name: opinfo
description: "OpInfo entries in common_methods_invocations.py: dtype support, sample inputs, gradcheck/gradgrad flags. Use for questions about writing OpInfo tests."
validated-at: 70d99e998b4
---

# OpInfo Skill
## What Is OpInfo?
A data structure that describes an operator for the unified test suite. Each `OpInfo` entry specifies: supported dtypes, sample inputs, gradcheck settings, known failures.

## Key Questions

**Q: Where is op_db defined?**
A: `torch/testing/_internal/common_methods_invocations.py` — the list of all OpInfo entries.
`torch/testing/_internal/common_methods_invocations.py:LINE — "op_db"`

**Q: How do I add an OpInfo entry?**
A:
```python
OpInfo(
    "aten::my_op",
    dtypes=all_types_and_complex_and(torch.bool),
    sample_inputs_func=sample_inputs_my_op,
    supports_autograd=True,
    supports_gradgrad=True,
)
```

**Q: What does `gradcheck` verify?**
A: Numerically computes the Jacobian via finite differences and compares it to the analytical gradient. Confirms backward is correct.
`torch/testing/_comparison.py:LINE — "def gradcheck"`

**Q: What is `supports_forward_ad`?**
A: Whether the op supports forward-mode automatic differentiation (jvp). Required for `torch.func.jvp`.

## Blast Radius
- `torch/testing/_internal/common_methods_invocations.py` — Tier 2 (all op tests)
