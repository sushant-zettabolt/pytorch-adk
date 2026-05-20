# Dispatcher Pitfalls

## Footgun 1: Editing Generated Binding Files
`torch/csrc/autograd/generated/python_torch_functions_2.cpp` is regenerated on every build.
Any edit is silently overwritten. The pre-edit-block-generated hook blocks this.

## Footgun 2: Registering to Wrong DispatchKey
Registering a kernel under `CPU` when you mean `CompositeImplicitAutograd` prevents autograd from working.
`CompositeImplicitAutograd` = "I have autograd via torch ops; no custom backward needed."
`CompositeExplicitAutograd` = "I handle backward myself."

## Footgun 3: Missing Meta Kernel
If your op lacks a Meta kernel, `torch.compile` fails at shape inference time.
Always add `TORCH_LIBRARY_IMPL(aten, Meta, m)` alongside your CPU/CUDA impl.

## Footgun 4: DispatchKey Ordering
Keys are resolved by priority (highest bit in DispatchKeySet wins). AutogradCPU > CPU.
If you register to CPU but the input has autograd, your kernel bypasses autograd entirely.
