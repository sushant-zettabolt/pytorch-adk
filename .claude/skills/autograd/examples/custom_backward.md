# Example: Custom Autograd Function with Correct Backward

Verified against PyTorch source at `70d99e998b4`.

## Python custom Function

```python
import torch

class MySigmoid(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        result = 1 / (1 + torch.exp(-x))
        ctx.save_for_backward(result)   # saves output, not input
        return result

    @staticmethod
    def backward(ctx, grad_output):
        (result,) = ctx.saved_tensors
        return grad_output * result * (1 - result)

x = torch.randn(4, requires_grad=True)
y = MySigmoid.apply(x)
y.sum().backward()
print(x.grad)   # sigmoid'(x) = sigmoid(x) * (1 - sigmoid(x))
```

## How it hooks into autograd

`MySigmoid.apply(x)` creates a `Node` subclass internally. On `forward`, a C++ `Node` is attached as `y.grad_fn`. On `backward()`, the engine calls `Node::apply(grad_output)`, which invokes the Python `backward` function.

`torch/csrc/autograd/node.h:112 — "struct TORCH_API Node : c10::intrusive_ptr_target"`

## SavedVariable lifecycle

`ctx.save_for_backward(result)` stores `result` as a `SavedVariable`. The tensor is not freed until `backward()` completes or `del ctx` is called. This is why long chains can OOM — each intermediate tensor is held alive until its backward node runs.

`torch/csrc/autograd/saved_variable.h:22 — "class TORCH_API SavedVariable"`

## Gradcheck verification

```python
from torch.autograd import gradcheck
x = torch.randn(4, dtype=torch.double, requires_grad=True)
assert gradcheck(MySigmoid.apply, (x,), eps=1e-6, atol=1e-4)
```

Always run `gradcheck` with `dtype=torch.double` — float32 has insufficient precision for finite-difference Jacobian comparison.
