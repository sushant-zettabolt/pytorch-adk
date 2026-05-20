---
name: custom-ops
description: "Registering custom operators via torch.library (Python) or TORCH_LIBRARY (C++) so they integrate with autograd, torch.compile, and torch.export. Use for questions about adding custom ops."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# Custom Ops Skill

## What Are Custom Ops?

Custom operators registered into PyTorch's operator registry via `torch.library` (Python) or `TORCH_LIBRARY` (C++). They integrate with autograd, `torch.compile`, `torch.export`, and all backends.

`torch/library.py:204 — "class Library"`
`torch/library.h:1064 — "#define TORCH_LIBRARY_IMPL(ns, k, m)"`

---

## Section 1 — Schema Declaration

Every op must have a schema registered before any implementation. Schema defines the function signature (types, mutability, aliasing).

### Python API

```python
import torch
from torch.library import Library

mylib = Library("mylib", "DEF")
mylib.define("my_square(Tensor x) -> Tensor")
```

`torch/library.py:204 — "class Library"`

### C++ API

```cpp
TORCH_LIBRARY(mylib, m) {
    m.def("my_square(Tensor x) -> Tensor");
}
```

`torch/library.h:1064 — "#define TORCH_LIBRARY_IMPL(ns, k, m)"`

---

## Section 2 — Kernel Implementation

Implement once per dispatch key. CPU and CUDA are independent implementations.

### Python (CPU)

```python
from torch.library import impl

@impl(mylib, "my_square", "CPU")
def my_square_cpu(x: torch.Tensor) -> torch.Tensor:
    return x * x
```

### C++ (CPU)

```cpp
TORCH_LIBRARY_IMPL(mylib, CPU, m) {
    m.impl("my_square", [](const at::Tensor& x) {
        return x * x;
    });
}
```

`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`

---

## Section 3 — Meta Kernel (Required for torch.compile + export)

The Meta kernel computes output shape/dtype WITHOUT data. Required by `FakeTensor` (used by `torch.compile`, `torch.export`, and shape inference).

### Python

```python
@impl(mylib, "my_square", "Meta")
def my_square_meta(x: torch.Tensor) -> torch.Tensor:
    return torch.empty_like(x)   # same shape/dtype, no data
```

### C++

```cpp
TORCH_LIBRARY_IMPL(mylib, Meta, m) {
    m.impl("my_square", [](const at::Tensor& x) {
        return at::empty_like(x);
    });
}
```

**Test the meta kernel explicitly:**

```python
x = torch.randn(4, device='meta')
out = torch.ops.mylib.my_square(x)
assert out.shape == x.shape
```

`aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`

---

## Section 4 — Autograd Registration

Two options:

### Option A: CompositeImplicitAutograd (automatic, if op decomposes into differentiable ops)

The implementation calls other differentiable ops → autograd is free. Use `CompositeImplicitAutograd` dispatch key (no explicit autograd registration needed).

### Option B: Explicit autograd via torch.autograd.Function

```python
class MySquareFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return torch.ops.mylib.my_square(x)

    @staticmethod
    def backward(ctx, grad_output):
        (x,) = ctx.saved_tensors
        return grad_output * 2 * x   # d/dx x^2 = 2x
```

`torch/csrc/autograd/saved_variable.h:22 — "class TORCH_API SavedVariable"`

### Verify with gradcheck

```python
from torch.autograd import gradcheck
x = torch.randn(4, dtype=torch.double, requires_grad=True)
assert gradcheck(MySquareFunction.apply, (x,), eps=1e-6, atol=1e-4)
```

---

## Section 5 — Testing (OpInfo)

Add an entry to `common_methods_invocations.py` for automated testing across dtypes, devices, and edge cases.

```python
# torch/testing/_internal/common_methods_invocations.py
OpInfo(
    'my_square',
    op=torch.ops.mylib.my_square,
    dtypes=floating_types(),
    sample_inputs_func=lambda op, device, dtype, requires_grad, **kwargs: [
        SampleInput(torch.randn(4, device=device, dtype=dtype, requires_grad=requires_grad))
    ],
    supports_autograd=True,
)
```

`torch/testing/_internal/common_methods_invocations.py:LINE — "see op_db near top of file"` (citation needed)

---

## Blast Radius

- Custom op in a new namespace (`mylib::my_op`): Tier 3 — isolated to the registration.
- Custom op overriding an `aten` namespace op: Tier 2 — can affect all backends.
- Adding to `native_functions.yaml`: Tier 2 — rebuilds dispatch tables.

`aten/src/ATen/native/native_functions.yaml:9 — "- func: _cast_Byte(Tensor self, bool non_blocking=False)"`
