# Example: Binary Op Using TensorIteratorConfig

Verified against PyTorch source at `70d99e998b4`.

## When to use TensorIteratorConfig directly

Use when you need explicit control over type promotion, output allocation, or broadcasting that the structured kernel shorthand doesn't expose.

## Setup

```cpp
#include <ATen/TensorIterator.h>

void my_add_kernel(TensorIteratorBase& iter, const Scalar& alpha) {
    AT_DISPATCH_ALL_TYPES(iter.common_dtype(), "my_add", [&]() {
        scalar_t alpha_val = alpha.to<scalar_t>();
        cpu_kernel(iter, [alpha_val](scalar_t a, scalar_t b) -> scalar_t {
            return a + alpha_val * b;
        });
    });
}

Tensor my_add_cpu(const Tensor& self, const Tensor& other, const Scalar& alpha) {
    Tensor out = at::empty_like(self);
    auto iter = TensorIteratorConfig()
        .set_check_mem_overlap(true)
        .allow_cpu_scalars(true)
        .promote_inputs_to_common_dtype(true)
        .cast_common_dtype_to_outputs(true)
        .resize_outputs(false)
        .add_output(out)
        .add_input(self)
        .add_input(other)
        .build();
    my_add_kernel(iter, alpha);
    return out;
}
```

`aten/src/ATen/TensorIterator.h:736 — "struct TORCH_API TensorIterator final : public TensorIteratorBase"`
`aten/src/ATen/TensorIterator.h:571 — "void build_binary_op"`
`aten/src/ATen/native/cpu/Loops.h:304 — "void cpu_kernel(TensorIteratorBase& iter, func_t&& op"`

## Key config options

| Option | Meaning |
|---|---|
| `promote_inputs_to_common_dtype` | Cast all inputs to the common type before applying the lambda |
| `allow_cpu_scalars` | Allow 0-d tensors to be treated as scalars (fast path) |
| `set_check_mem_overlap` | Raise error if output aliased with input (for in-place safety) |
| `resize_outputs(false)` | Don't resize out — use when out is pre-allocated |
