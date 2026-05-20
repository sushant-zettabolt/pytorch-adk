# Debugging Dispatcher Issues

## How to see which kernel is called

```python
import torch
import logging

# Enable dispatch logging
torch._C._log_api_usage_once("enable-dispatch-trace")

# Or use TORCH_SHOW_DISPATCH_TRACE=1 environment variable
# TORCH_SHOW_DISPATCH_TRACE=1 python my_script.py
```

## How to check what keys are in a DispatchKeySet

```python
import torch

a = torch.randn(3, requires_grad=True)
# DispatchKeySet is accessible via C++; in Python, use:
print(a.device)        # tells you which backend key applies
print(a.requires_grad) # tells you if AutogradCPU/AutogradCUDA is in the set
print(a.dtype)         # affects dispatch for some type-dispatched ops
```

## Common Dispatch Debugging Scenarios

### "NotImplementedError: could not run <op> with dispatch key <X>"
Cause: No kernel registered for (op, key) combination.
Fix: Register via `TORCH_LIBRARY_IMPL(aten, X, m) { m.impl("op", &fn); }`

### "Ambiguous dispatch: multiple kernels for key"
Cause: Same op registered twice for the same DispatchKey.
Fix: Check for duplicate `TORCH_LIBRARY_IMPL` blocks.

### Autograd not flowing through my op
Cause: Op registered to CPU but not AutogradCPU or CompositeImplicitAutograd.
Fix: Use `CompositeImplicitAutograd` if your op is decomposable via other differentiable ops.
