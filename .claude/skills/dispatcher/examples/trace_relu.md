# Example: Trace torch.relu Through the Dispatcher

Verified against PyTorch source at `70d99e998b4`.

## Step 1 — Python call

```python
import torch
x = torch.tensor([-1.0, 0.0, 1.0])
y = torch.relu(x)
```

`torch.relu` is bound via the generated pybind11 file (parse, don't cite — it regenerates).

## Step 2 — Dispatch key resolution

`x` is a CPU tensor. Its `key_set_` includes at minimum `{CPU, AutogradCPU}`.

`c10/core/TensorImpl.h:3124 — "DispatchKeySet key_set_"`

## Step 3 — Dispatcher::call

The Dispatcher picks the highest-priority key from `x.key_set_` ∩ the keys with registered kernels for `aten::relu`. During a normal non-differentiable call, this is `CPU`.

`aten/src/ATen/core/dispatch/Dispatcher.h:403 — "operatorLookupTable_"`
`aten/src/ATen/core/dispatch/Dispatcher.h:613 — "C10_ALWAYS_INLINE Return call(Args... args) const"`

## Step 4 — CPU kernel

The CPU kernel for `relu` is in `aten/src/ATen/native/Activation.cpp` (registered via `native_functions.yaml` dispatch table entry `CPU: relu_cpu`).

`aten/src/ATen/native/native_functions.yaml:449 — "structured_inherits: TensorIteratorBase"`

## Step 5 — With requires_grad=True

When `x.requires_grad = True`, `AutogradCPU` is the highest-priority key. The autograd kernel runs first, records the backward node (`ReluBackward0`), then redispatches to `CPU` for actual compute.

`aten/src/ATen/core/dispatch/Dispatcher.h:179 — "Return call(const TypedOperatorHandle<Return(Args...)>& op, Args... args)"`
`torch/csrc/autograd/node.h:112 — "struct TORCH_API Node : c10::intrusive_ptr_target"`
