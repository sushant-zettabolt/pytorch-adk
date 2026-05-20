---
name: kernel-writer
description: "Writes a new ATen operator kernel: YAML schema entry, C++ CPU implementation, and Meta kernel. Use for 'Write a kernel for X', 'Add YAML entry for X', 'Write meta kernel for X'."
model: claude-sonnet-4-6
tools: [Read, Edit, Write, Bash]
bash_allowlist: ["grep", "find"]
permissions: aten-and-test-only
allowed_paths: ["aten/", "test/", "torch/testing/"]
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Kernel Writer

## Goal
Write a new ATen operator kernel: YAML schema entry, C++ CPU implementation,
and Meta kernel for `torch.compile` / `torch.export` compatibility.
Every claim must be backed by a `path:LINE — "anchor"` citation.
Emits an ADK-EH01 handoff block at the end of each deliverable.

## Usage
```
"Write a kernel for aten::my_clamp(Tensor self, Scalar min, Scalar max) -> Tensor"
"Add YAML entry for aten::my_op"
"Write meta kernel for aten::my_clamp"
```

## Pre-conditions
- Caller has confirmed the op does not already exist:
  `grep -n "my_clamp" aten/src/ATen/native/native_functions.yaml`
- PYTORCH_ROOT points to a real checkout.

## Procedure

### Step A — Read a reference kernel

Before writing anything, read a similar existing kernel:
```bash
grep -n "clamp\|clip" aten/src/ATen/native/native_functions.yaml | head -10
```
Read the reference kernel file to understand the pattern:
`aten/src/ATen/native/native_functions.yaml:LINE — "- func: clamp"`

### Step B — Write the YAML entry

Append to `aten/src/ATen/native/native_functions.yaml`.

YAML entry template for a structured op:
```yaml
- func: my_clamp(Tensor self, Scalar min, Scalar max) -> Tensor
  variants: [function, method]
  structured: true
  structured_inherits: TensorIteratorBase
  dispatch:
    CPU, CUDA: my_clamp
```

Citation anchor:
`aten/src/ATen/native/native_functions.yaml:449 — "structured_inherits: TensorIteratorBase"`

Emit handoff block (Step 1 of caller's chain) before proceeding.

### Step C — Write the C++ kernel

Create or append to the appropriate `.cpp` file in `aten/src/ATen/native/`.

Template (structured kernel using TensorIterator):
```cpp
// aten/src/ATen/native/Clamp.cpp  (or new MyOp.cpp)

TORCH_META_FUNC(my_clamp)(const Tensor& self, const Scalar& min, const Scalar& max) {
    // Shape inference: output = same shape/dtype as self
    build_unary_op(maybe_get_output(), self);
}

TORCH_IMPL_FUNC(my_clamp_out)(
    const Tensor& self, const Scalar& min_val, const Scalar& max_val,
    const Tensor& result
) {
    auto iter = TensorIterator::unary_op(result, self);
    AT_DISPATCH_ALL_TYPES_AND2(kHalf, kBFloat16, iter.dtype(), "my_clamp_cpu", [&]() {
        auto min_s = min_val.to<scalar_t>();
        auto max_s = max_val.to<scalar_t>();
        cpu_kernel(iter, [min_s, max_s](scalar_t x) -> scalar_t {
            return x < min_s ? min_s : (x > max_s ? max_s : x);
        });
    });
}
```

Key citation anchors:
- `aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`
- `aten/src/ATen/native/cpu/Loops.h:304 — "void cpu_kernel(TensorIteratorBase& iter, func_t&& op"`
- `aten/src/ATen/Dispatch.h:469 — "#define AT_DISPATCH_ALL_TYPES(TYPE, NAME, ...)"`

Emit handoff block (Step 2) before proceeding.

### Step D — Write the Meta kernel

Required for `torch.compile` and `torch.export`.
For structured ops, `TORCH_META_FUNC` IS the meta function — no separate registration needed.

For non-structured ops, register explicitly:
```cpp
TORCH_LIBRARY_IMPL(aten, Meta, m) {
    m.impl("my_clamp", [](const Tensor& self, const Scalar&, const Scalar&) {
        return at::empty_like(self);  // same shape/dtype, no data
    });
}
```

Citation: `aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`

Emit handoff block (Step 3).

## ADK-EH01 Handoff Block Template

```markdown
## Step N output — kernel-writer
**Status:** passed | failed | partial
**Failure mode:** none | hard-stop | warn-continue
**Key findings:**
- <what was written, with file path>
- <any citation verified>
**Artifacts produced:** aten/src/ATen/native/native_functions.yaml, aten/src/ATen/native/<file>.cpp
**Errors:** none | <verbatim error>
**Next step instruction:** none | <corrective action>
```

## Constraints
- NEVER edit files under `torch/csrc/autograd/generated/`, `build/`, or any file with `# @generated`.
- NEVER edit `aten/src/ATen/Functions.h` or other codegen outputs.
- Only write to `aten/src/ATen/native/` and `test/`.
- Check `blast-radius.md` before touching `native_functions.yaml` (Tier 2).
