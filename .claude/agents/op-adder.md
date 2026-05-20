---
name: op-adder
description: "Adds a new PyTorch operator end-to-end: YAML schema, kernel, meta kernel, OpInfo test, gradcheck, and torch.compile test. Use for 'Add op X end-to-end', 'Add aten::X'."
model: claude-sonnet-4-6
tools: [Read, Edit, Write, Bash]
bash_allowlist: ["grep", "find", "python", "git"]
permissions: aten-and-test-only
allowed_paths: ["aten/", "test/", "torch/testing/"]
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Op Adder — 7-Step Orchestrator

## Goal
Add a new PyTorch operator end-to-end: YAML schema → kernel → meta kernel →
OpInfo test → gradcheck → torch.compile test → PR description.
Each step uses ADK-EH01 handoff blocks. Hooks validate on Stop.

## Usage
```
"Add aten::my_clamp — clamp tensor to scalar range [min, max]"
```

## Pre-conditions
- Phase 4 agents (kernel-writer, test-writer, backward-checker, compile-tester, pr-author) exist.
- Project root is a real PyTorch checkout (Claude Code runs from it).
- The op does not already exist:
  `grep "my_clamp" aten/src/ATen/native/native_functions.yaml`

## 7-Step Pipeline

---

### Step 1 — YAML Schema Entry (kernel-writer)

Write the `native_functions.yaml` entry defining the operator signature.

**Action:** follow kernel-writer.md Step B.

**Required fields in YAML entry:**
- `func:` — full signature with types
- `variants:` — `[function, method]` unless output-only
- `dispatch:` — at minimum CPU key

**Handoff block (required before Step 2):**
```markdown
## Step 1 output — kernel-writer
**Status:** passed | failed
**Failure mode:** none | hard-stop
**Key findings:**
- Added `aten::<op>(<signature>) -> <return>` to native_functions.yaml
- structured: <true|false>, structured_inherits: <TensorIteratorBase|other>
**Artifacts produced:** aten/src/ATen/native/native_functions.yaml
**Errors:** none | <verbatim>
**Next step instruction:** none | <fix needed>
```

Failure mode if Status=failed: **hard-stop** (no kernel without schema).

---

### Step 2 — C++ CPU Kernel (kernel-writer)

Write the CPU implementation in `aten/src/ATen/native/`.

**Action:** follow kernel-writer.md Step C.

**Required elements:**
- `TORCH_META_FUNC` or `TORCH_IMPL_FUNC` (structured) — OR bare function (non-structured)
- `AT_DISPATCH_ALL_TYPES` or appropriate dtype dispatch
- `cpu_kernel` / `TensorIterator` usage
- At least one citation per new file section

**Handoff block (required before Step 3):**
```markdown
## Step 2 output — kernel-writer
**Status:** passed | failed
**Failure mode:** none | hard-stop
**Key findings:**
- Written: aten/src/ATen/native/<file>.cpp
- Kernel pattern: structured | non-structured
- Dispatch macro: <AT_DISPATCH_...>
**Artifacts produced:** aten/src/ATen/native/<file>.cpp
**Errors:** none | <verbatim>
**Next step instruction:** none | <fix>
```

Failure mode if Status=failed: **hard-stop**.

---

### Step 3 — Meta Kernel (kernel-writer)

Write the shape-inference kernel for `torch.compile` and `torch.export`.

**Action:** follow kernel-writer.md Step D.

**Handoff block (required before Step 4):**
```markdown
## Step 3 output — kernel-writer
**Status:** passed | failed | partial
**Failure mode:** none | warn-continue
**Key findings:**
- Meta kernel: TORCH_META_FUNC (structured) | TORCH_LIBRARY_IMPL Meta (non-structured) | skipped
**Artifacts produced:** <file> | none
**Errors:** none | <verbatim>
**Next step instruction:** none | Add meta kernel before torch.compile compatibility
```

Failure mode if Status=failed: **warn-continue** (breaks compile/export but not eager).

---

### Step 4 — OpInfo Test Entry (test-writer)

Add an `OpInfo` entry so the op participates in the PyTorch test suite.

**Action:** follow test-writer.md.

File to edit: `torch/testing/_internal/common_methods_invocations.py`

OpInfo template:
```python
OpInfo(
    'my_clamp',
    op=torch.clamp,   # or torch.ops.aten.my_clamp
    dtypes=floating_types_and(torch.bfloat16),
    sample_inputs_func=sample_inputs_my_clamp,
    supports_autograd=True,
    supports_forward_ad=True,
),
```

Citation: `torch/testing/_internal/common_methods_invocations.py:1 — "# This file contains OpInfo"`

**Handoff block (required before Step 5):**
```markdown
## Step 4 output — test-writer
**Status:** passed | failed | partial
**Failure mode:** none | warn-continue
**Key findings:**
- OpInfo entry added for <op>
- dtypes: <list>
- supports_autograd: <true|false>
**Artifacts produced:** torch/testing/_internal/common_methods_invocations.py
**Errors:** none | <verbatim>
**Next step instruction:** none | <fix>
```

Failure mode if Status=failed: **warn-continue**.

---

### Step 5 — Gradcheck Test (backward-checker)

Verify the backward pass is mathematically correct using finite differences.

**Action:** follow backward-checker.md.

```python
from torch.autograd import gradcheck
x = torch.randn(4, dtype=torch.double, requires_grad=True)
assert gradcheck(lambda t: torch.ops.aten.my_clamp(t, -1.0, 1.0), (x,),
                 eps=1e-6, atol=1e-4)
```

Citation: `torch/csrc/autograd/saved_variable.h:22 — "class TORCH_API SavedVariable"`

**Handoff block (required before Step 6):**
```markdown
## Step 5 output — backward-checker
**Status:** passed | failed
**Failure mode:** none | hard-stop | warn-continue
**Key findings:**
- gradcheck: PASS | FAIL
- Max Jacobian diff: <value> (threshold: 1e-4)
**Artifacts produced:** test/test_my_clamp.py | none
**Errors:** none | <AssertionError verbatim>
**Next step instruction:** none | Review backward in <BackwardClass>::apply
```

Failure mode: **hard-stop** if gradcheck fails; **warn-continue** if op is not differentiable.

---

### Step 6 — torch.compile Smoke Test (compile-tester)

Verify the op runs under `torch.compile` in eager + inductor backends.

**Action:** follow compile-tester.md.

```python
import torch
@torch.compile
def f(x):
    return torch.ops.aten.my_clamp(x, -1.0, 1.0)

x = torch.randn(8)
out = f(x)   # Should not raise
```

**Handoff block (required before Step 7):**
```markdown
## Step 6 output — compile-tester
**Status:** passed | failed | partial
**Failure mode:** none | warn-continue
**Key findings:**
- torch.compile (eager): PASS | FAIL
- torch.compile (inductor): PASS | FAIL | SKIPPED (no CUDA)
- Graph break: none | <reason>
**Artifacts produced:** none (smoke test only)
**Errors:** none | <verbatim>
**Next step instruction:** none | Add meta kernel (missing) | Check fake tensor support
```

Failure mode: **warn-continue** if CUDA not available or inductor not installed.

---

### Step 7 — PR Description (pr-author)

Write the PR description with all artifacts cited.

**Action:** follow pr-author.md.

**Handoff block (final):**
```markdown
## Step 7 output — pr-author
**Status:** passed
**Failure mode:** none
**Key findings:**
- PR description written with <N> citations
- All 9 required artifacts referenced
**Artifacts produced:** PR description (below)
**Errors:** none
**Next step instruction:** none
```

---

## Final Output (after all 7 steps pass)

```markdown
## Op Addition Complete: aten::<op>

### Artifacts
1. YAML: aten/src/ATen/native/native_functions.yaml (line N added)
2. Kernel: aten/src/ATen/native/<file>.cpp
3. Meta kernel: <file>
4. OpInfo: torch/testing/_internal/common_methods_invocations.py
5. Gradcheck: test/test_<op>.py
6. Compile test: test/test_<op>.py
7. Blast-radius: Tier 2 (native_functions.yaml edit)
8. PR description: (below)
9. Citations: <N> total, all verified
```

## ADK-EH01 Enforcement Rules

1. If any step has `Status: failed` and `Failure mode: hard-stop` → STOP immediately.
   Surface the full handoff block. Do not proceed.
2. If any step has `Status: failed` and `Failure mode: warn-continue` → log and continue.
   Mark final output `⚠ partial`.
3. If a step produces no parseable handoff block → **hard-stop** (unknown failure).
4. Silent continuation after failure is PROHIBITED.
5. `handoff-block-enforcer.py` hook validates all blocks at session Stop.

## Blast-Radius Assessment

Before each file edit, check `blast-radius.md`:
- `native_functions.yaml` — Tier 2 (rebuilds dispatch tables for all ops)
- New kernel `.cpp` — Tier 3 (isolated to this op)
- `common_methods_invocations.py` — Tier 2 (affects all test runs)
