# Example: Minimal CPU Elementwise Kernel (Structured)

Verified against PyTorch source at `70d99e998b4`.

## 1. native_functions.yaml entry

```yaml
- func: my_square(Tensor self) -> Tensor
  structured: True
  structured_inherits: TensorIteratorBase
  dispatch:
    CPU, CUDA: my_square_out
    Meta: my_square_out
  tags: pointwise
```

`aten/src/ATen/native/native_functions.yaml:449 — "structured_inherits: TensorIteratorBase"`

## 2. Meta kernel (shape inference, no data)

```cpp
// aten/src/ATen/native/MyOps.cpp
#include <ATen/TensorIterator.h>
#include <ATen/TensorMeta.h>

TORCH_META_FUNC(my_square)(const Tensor& self) {
    build_borrowing_unary_op(maybe_get_output(), self);
}
```

`aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`

## 3. CPU implementation

```cpp
// aten/src/ATen/native/cpu/MyOps.cpp
#include <ATen/Dispatch.h>
#include <ATen/native/cpu/Loops.h>

TORCH_IMPL_FUNC(my_square_out)(const Tensor& self, const Tensor& result) {
    AT_DISPATCH_ALL_TYPES(self.scalar_type(), "my_square", [&]() {
        cpu_kernel(*this, [](scalar_t a) -> scalar_t {
            return a * a;
        });
    });
}
```

`aten/src/ATen/native/cpu/Loops.h:304 — "void cpu_kernel(TensorIteratorBase& iter, func_t&& op"`
`aten/src/ATen/Dispatch.h:469 — "#define AT_DISPATCH_ALL_TYPES(TYPE, NAME, ...)"`

## 4. Register the kernel

The `structured: True` flag means registration is generated automatically. No `TORCH_LIBRARY_IMPL` needed for built-in namespaces.

## 5. Verify

```python
import torch
x = torch.tensor([-2.0, 3.0])
y = torch.my_square(x)
assert y.tolist() == [4.0, 9.0]
```
