# Pitfall: Meta Kernel Returns Wrong Output Shape

## What Goes Wrong

```cpp
TORCH_META_FUNC(my_reduce)(const Tensor& self, int64_t dim) {
    // BUG: forgot to remove the reduced dimension
    set_output_raw_strided(0, self.sizes(), {}, self.options());
}
```

In eager mode everything looks fine — the real kernel allocates its own output with the right shape. But `torch.compile` uses the meta kernel to plan memory, so:

```python
@torch.compile
def f(x):
    return torch.ops.aten.my_reduce(x, 0)

f(torch.randn(4, 3))
# Shape mismatch or silent wrong result at runtime
```

## Why

The meta kernel's job is to compute output shape/dtype *without data*. `torch.compile` traces through the meta kernel to determine what memory to allocate for subsequent ops. A wrong shape propagates silently through the entire compiled graph.

`aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`

## Fix

```cpp
TORCH_META_FUNC(my_reduce)(const Tensor& self, int64_t dim) {
    auto out_sizes = self.sizes().vec();
    out_sizes.erase(out_sizes.begin() + dim);   // remove reduced dim
    set_output_raw_strided(0, out_sizes, {}, self.options());
}
```

## Detection

Test the meta kernel explicitly:

```python
x = torch.randn(4, 3, device='meta')
out = torch.ops.aten.my_reduce(x, 0)
assert out.shape == torch.Size([3]), f"got {out.shape}"
```

Never skip this test if you're writing a reduction op.
