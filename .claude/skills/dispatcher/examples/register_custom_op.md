# Example: Register a Custom Op via TORCH_LIBRARY_IMPL

Verified against PyTorch source at `70d99e998b4`.

## YAML entry (native_functions.yaml)

```yaml
- func: my_square(Tensor self) -> Tensor
  dispatch:
    CPU: my_square_cpu
    CUDA: my_square_cuda
```

`aten/src/ATen/native/native_functions.yaml:9 — "- func: _cast_Byte(Tensor self, bool non_blocking=False)"`

## Schema declaration (library.h)

```cpp
// myops.h — schema
TORCH_LIBRARY(my_ns, m) {
    m.def("my_square(Tensor self) -> Tensor");
}
```

`torch/library.h:1064 — "#define TORCH_LIBRARY_IMPL(ns, k, m)"`

## CPU implementation

```cpp
// myops_cpu.cpp
TORCH_LIBRARY_IMPL(my_ns, CPU, m) {
    m.impl("my_square", [](const at::Tensor& self) {
        return self * self;
    });
}
```

## Meta kernel (required for torch.compile / export)

```cpp
TORCH_LIBRARY_IMPL(my_ns, Meta, m) {
    m.impl("my_square", [](const at::Tensor& self) {
        // Returns a tensor with the same shape/dtype, no data
        return at::empty_like(self);
    });
}
```

`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`

## Verification

```python
import torch
x = torch.tensor([2.0, 3.0])
y = torch.ops.my_ns.my_square(x)
assert y.tolist() == [4.0, 9.0]
```
