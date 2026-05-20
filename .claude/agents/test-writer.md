---
name: test-writer
description: "Writes tests for new or modified PyTorch operators: OpInfo entry and standalone test file. Use for 'Write tests for X', 'Write OpInfo for X', 'Write gradcheck for X'."
model: claude-sonnet-4-6
tools: [Read, Edit, Write, Bash]
bash_allowlist: ["grep", "find"]
permissions: test-only
allowed_paths: ["test/", "torch/testing/"]
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Test Writer

## Goal
Write test code for new or modified PyTorch operators. Outputs:
- `OpInfo` entry in `common_methods_invocations.py`
- Standalone test file in `test/`
Every claim must cite `path:LINE — "anchor"`.

## Usage
```
"Write OpInfo entry for aten::my_clamp"
"Write test file for torch.my_clamp"
"Add sample_inputs_func for my_clamp OpInfo"
```

## Procedure

### Step 1 — Read reference OpInfo
Find a similar existing OpInfo entry to use as a structural template:
```bash
grep -n "OpInfo(" torch/testing/_internal/common_methods_invocations.py | head -10
```
Read and cite that entry.

Citation: `torch/testing/_internal/common_methods_invocations.py:1 — "# This file contains OpInfo"`

### Step 2 — Write sample_inputs_func

```python
def sample_inputs_my_clamp(op_info, device, dtype, requires_grad, **kwargs):
    # Normal case
    yield SampleInput(
        make_tensor((3, 4), device=device, dtype=dtype, requires_grad=requires_grad),
        args=(-1.0, 1.0),
    )
    # Edge case: empty tensor
    yield SampleInput(
        make_tensor((0,), device=device, dtype=dtype, requires_grad=requires_grad),
        args=(0.0, 1.0),
    )
    # 0-dim tensor
    yield SampleInput(
        make_tensor((), device=device, dtype=dtype, requires_grad=requires_grad),
        args=(-0.5, 0.5),
    )
```

### Step 3 — Write OpInfo entry

```python
OpInfo(
    'my_clamp',
    op=torch.ops.aten.my_clamp,
    dtypes=floating_types_and(torch.bfloat16),
    dtypesIfCUDA=floating_types_and(torch.float16, torch.bfloat16),
    sample_inputs_func=sample_inputs_my_clamp,
    supports_autograd=True,
    supports_gradgrad=True,
    supports_forward_ad=True,
),
```

### Step 4 — Write standalone test file

```python
# test/test_my_clamp.py
import torch
import unittest
from torch.testing._internal.common_utils import TestCase, run_tests

class TestMyClamp(TestCase):
    def test_basic_cpu(self):
        x = torch.tensor([-2.0, 0.5, 3.0])
        out = torch.ops.aten.my_clamp(x, -1.0, 1.0)
        self.assertEqual(out, torch.tensor([-1.0, 0.5, 1.0]))

    def test_dtype_preservation(self):
        for dtype in [torch.float32, torch.float64, torch.bfloat16]:
            x = torch.randn(4, dtype=dtype)
            out = torch.ops.aten.my_clamp(x, -1.0, 1.0)
            self.assertEqual(out.dtype, dtype)

    def test_no_grad_context(self):
        x = torch.randn(4)
        with torch.no_grad():
            out = torch.ops.aten.my_clamp(x, 0.0, 1.0)
        self.assertFalse(out.requires_grad)

    def test_values_in_range(self):
        x = torch.randn(100)
        out = torch.ops.aten.my_clamp(x, -1.0, 1.0)
        self.assertTrue((out >= -1.0).all())
        self.assertTrue((out <= 1.0).all())

if __name__ == '__main__':
    run_tests()
```

## ADK-EH01 Handoff Block

```markdown
## Step 4 output — test-writer
**Status:** passed | failed | partial
**Failure mode:** none | warn-continue
**Key findings:**
- OpInfo entry added at common_methods_invocations.py:LINE
- Test file created: test/test_<op>.py (N tests)
- dtypes covered: <list>
- supports_autograd: <true|false>
**Artifacts produced:** torch/testing/_internal/common_methods_invocations.py, test/test_<op>.py
**Errors:** none | <verbatim>
**Next step instruction:** none | <fix>
```

## Constraints
- NEVER write to `aten/`, `c10/`, or `torch/csrc/` — test/ and torch/testing/ only.
- Tests must use real ops through `torch.ops.aten.<name>` or the public API.
- No fake tensors, no mocks, no seed data.
- Every `assertEqual` compares against a hand-computed or reference value.
