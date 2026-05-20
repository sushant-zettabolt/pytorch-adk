# Pitfall: Missing Meta Kernel Breaks torch.compile and Export

## What Goes Wrong

You register a CPU and CUDA kernel but skip the `Meta` dispatch key registration. Everything works in eager mode. Then:

```python
import torch
from torch._dynamo import export

@torch.compile
def f(x):
    return torch.ops.my_ns.my_op(x)

f(torch.randn(4))
# RuntimeError: Could not run 'my_ns::my_op' with arguments from the 'Meta' backend.
```

## Why

`torch.compile` and `torch.export` run the op under `FakeTensor` (Meta backend) to infer output shapes without executing real computation. Without a Meta kernel, the Dispatcher has no entry for key `Meta` and throws.

`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`
`aten/src/ATen/core/dispatch/Dispatcher.h:413 — "backendFallbackKernels_"`

## Fix

```cpp
TORCH_LIBRARY_IMPL(my_ns, Meta, m) {
    m.impl("my_op", [](const at::Tensor& self) {
        return at::empty_like(self);  // same shape/dtype, no data
    });
}
```

## Detection

Run: `python -c "import torch; torch.ops.my_ns.my_op(torch.empty(4, device='meta'))"`. If it throws, the Meta kernel is missing.
