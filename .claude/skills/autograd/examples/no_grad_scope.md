# Example: Correct Use of torch.no_grad()

Verified against PyTorch source at `70d99e998b4`.

## What it does

`torch.no_grad()` sets a thread-local flag that prevents autograd from creating `grad_fn` on outputs. Used in inference, evaluation loops, and manual parameter updates.

`torch/autograd/grad_mode.py:22 — "class no_grad(_NoParamDecoratorContextManager)"`

## Correct: evaluation loop

```python
model.eval()
with torch.no_grad():
    for batch in val_loader:
        out = model(batch)         # no grad_fn built
        loss = criterion(out, ...)  # no backward graph
```

## Correct: manual parameter update (optimizer-free)

```python
with torch.no_grad():
    for p in model.parameters():
        p -= lr * p.grad           # in-place without autograd
        p.grad = None
```

## Pitfall: forgetting no_grad() in large inference

Without `no_grad()`, every op in the forward pass allocates a backward node and keeps all intermediate tensors alive. On a 1B-parameter model this can 2-3× memory usage for zero benefit in inference.

## Pitfall: using no_grad() inside a custom Function

```python
# WRONG — disables autograd for the backward too if ctx is not careful
class Bad(Function):
    @staticmethod
    def forward(ctx, x):
        with torch.no_grad():      # OK in forward
            return x * 2
    @staticmethod
    def backward(ctx, g):
        with torch.no_grad():      # Also OK — backward doesn't need grad tracking
            return g * 2
```

The backward `no_grad()` is fine here, but be aware that calling another differentiable op inside `backward` without `no_grad()` will create a second-order graph (higher-order gradients). That's intentional only if you need Hessians.
