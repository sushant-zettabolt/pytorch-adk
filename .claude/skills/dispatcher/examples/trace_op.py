"""
Example: Tracing an operator through the Dispatcher.

Run this to see the dispatch key resolution for torch.add on CPU.
"""
import torch

# Enable dispatch key logging
torch._C._log_api_usage_once("dispatcher-example")

# This call goes through:
# 1. Python torch.add
# 2. pybind11 binding
# 3. Dispatcher::call with DispatchKeySet{CPU, AutogradCPU}
# 4. AutogradCPU handler (if requires_grad=True)
# 5. CPU kernel: at::add_cpu

a = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
b = torch.tensor([4.0, 5.0, 6.0])
c = torch.add(a, b)

print(f"Result: {c}")
print(f"grad_fn: {c.grad_fn}")
print(f"Device: {c.device}")
