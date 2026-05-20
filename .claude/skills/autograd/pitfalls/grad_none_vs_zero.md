# Pitfall: Confusing grad=None with grad=zeros

## What Goes Wrong

```python
x = torch.randn(4, requires_grad=True)
loss = (x * 0).sum()    # zero contribution to loss
loss.backward()
print(x.grad)           # tensor([0., 0., 0., 0.]) — NOT None
```

Then later:

```python
x2 = torch.randn(4, requires_grad=True)
print(x2.grad)          # None — backward never called
```

Code that branches on `x.grad is None` behaves differently for "grad is zero" vs "backward never called."

## Why

PyTorch accumulates gradients — it does `grad += new_grad`. If `grad` is `None` initially, it is set to `new_grad` directly. If it already exists, the new value is added. After backward, even a zero gradient is a real tensor (not `None`).

`c10/core/TensorImpl.h:2967 — "std::unique_ptr<c10::AutogradMetaInterface> autograd_meta_ = nullptr"`

## Fix: zero the gradient before each backward

```python
optimizer.zero_grad()    # or manually: x.grad = None  (faster than zero)
loss.backward()
```

Setting `x.grad = None` is faster than `x.grad.zero_()` because it avoids the fill op. Preferred in tight training loops.

## Accumulating gradients intentionally (gradient checkpointing / microbatches)

```python
for micro_batch in micro_batches:
    loss = model(micro_batch) / len(micro_batches)
    loss.backward()    # grads accumulate across micro_batches
optimizer.step()
optimizer.zero_grad()
```

This is intentional accumulation. Don't call `zero_grad()` inside the inner loop.
