# Pitfall: In-place Op on a Leaf Tensor That Requires Grad

## What Goes Wrong

```python
x = torch.randn(4, requires_grad=True)
x += 1    # in-place on leaf tensor
x.sum().backward()
# RuntimeError: a leaf Variable that requires grad has been used in an in-place operation
```

## Why

Leaf tensors (created directly, not as output of another op) that require grad cannot be modified in-place because autograd cannot record the mutation correctly. The version counter prevents backward from silently computing wrong gradients.

`c10/core/TensorImpl.h:352 — "c10::intrusive_ptr<VersionCounter> version_counter_"`

## Another form: saved tensor version mismatch

```python
x = torch.randn(4, requires_grad=True)
y = x * 2        # saves x in backward node
x.add_(1)        # increments version_counter
y.sum().backward()
# RuntimeError: one of the variables needed for gradient computation has been modified by an inplace operation
```

Autograd records `version_counter` at `save_for_backward` time. If the counter changed by backward time (because of in-place ops), it raises this error.

`torch/csrc/autograd/saved_variable.h:22 — "class TORCH_API SavedVariable"`

## Fix

Use out-of-place ops:

```python
x_new = x + 1    # new tensor, doesn't modify x
y = x * 2
y.sum().backward()  # x unchanged — OK
```

Or detach before in-place:

```python
with torch.no_grad():
    x.add_(1)    # OK: detached from autograd graph
```
