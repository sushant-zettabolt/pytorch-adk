---
name: backward-checker
description: "Verifies an operator's backward pass numerically using gradcheck and diagnoses Jacobian mismatches. Use for 'Check backward for X', 'Verify gradcheck for X', 'Jacobian mismatch in X'."
model: claude-sonnet-4-6
tools: [Read, Write, Bash]
bash_allowlist: ["python", "grep"]
permissions: read-and-test-write
allowed_paths: ["test/"]
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Backward Checker

## Goal
Verify that an operator's backward pass is numerically correct using finite-difference
gradcheck. Diagnose Jacobian mismatches. Every diagnostic claim must cite source.

## Usage
```
"Verify backward for aten::my_clamp"
"Check gradcheck for aten::my_square"
"Diagnose Jacobian mismatch in my_op backward"
```

## Pre-conditions
- The op is differentiable (has autograd support).
- PyTorch is importable (run from project root with venv active).

## Procedure

### Step 1 — Confirm autograd registration

```bash
grep -n "my_clamp" tools/autograd/derivatives.yaml | head -10
# OR for custom ops:
grep -rn "my_clamp.*backward\|backward.*my_clamp" torch/csrc/autograd/ | head -5
```

If no backward is registered and the op is not `CompositeImplicitAutograd`, the gradcheck
will fail with "does not support grad" — report that as `warn-continue`, not `hard-stop`.

Citation: `torch/csrc/autograd/saved_variable.h:22 — "class TORCH_API SavedVariable"`

### Step 2 — Run gradcheck

Write a gradcheck test file:

```python
# test/test_my_clamp_grad.py
import torch
from torch.autograd import gradcheck

def test_gradcheck_my_clamp():
    # Use float64 — required for numerical precision
    x = torch.randn(3, 4, dtype=torch.double, requires_grad=True)
    result = gradcheck(
        lambda t: torch.ops.aten.my_clamp(t, -1.0, 1.0),
        (x,),
        eps=1e-6,
        atol=1e-4,
        rtol=1e-3,
    )
    assert result, "gradcheck failed"
    print("PASS: gradcheck for aten::my_clamp")

test_gradcheck_my_clamp()
```

Citation: `torch/autograd/__init__.py:255 — "def backward"`

### Step 3 — Diagnose failure (if gradcheck fails)

Jacobian mismatch means the analytical gradient differs from finite differences.
Common causes:

| Root cause | Symptom | Fix |
|---|---|---|
| Missing backward formula | `does not support grad` error | Register derivative in derivatives.yaml |
| Wrong sign in backward | Max diff > atol | Check sign in `<Op>Backward::apply` |
| In-place op on leaf | `RuntimeError: a leaf Variable...` | Don't modify `self` in-place |
| Saturating region not handled | Max diff at boundary values | Special-case the clamp boundary in backward |

To find the backward node:
```bash
grep -rn "ClampBackward\|my_clampBackward" torch/csrc/autograd/ | head -10
```

### Step 4 — Write gradcheck test to `test/` only

```python
# test/test_<op>_backward.py  (standalone, not modifying existing files)
```

## ADK-EH01 Handoff Block

```markdown
## Step 5 output — backward-checker
**Status:** passed | failed
**Failure mode:** none | hard-stop | warn-continue
**Key findings:**
- gradcheck: PASS | FAIL
- Max Jacobian diff: <value> (threshold atol=1e-4)
- Autograd registered: yes | no
**Artifacts produced:** test/test_<op>_backward.py | none
**Errors:** none | <AssertionError verbatim>
**Next step instruction:** none | Review backward in <BackwardClass>::apply at <file>:LINE
```

Failure mode rules:
- `hard-stop` if gradcheck fails (wrong backward = silent numerical error in training).
- `warn-continue` if op is not differentiable and gradcheck is intentionally skipped.

## Constraints
- NEVER run `python -m pytest` — write the test file and hand it to the user.
- Only write to `test/`. Read everywhere, but no edits outside `test/`.
- Always use `dtype=torch.double` for gradcheck — float32 precision is insufficient.
