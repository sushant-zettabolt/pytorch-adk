# Pitfall: Using AT_DISPATCH_ALL_TYPES on a Float-Only Op

## What Goes Wrong

```cpp
TORCH_IMPL_FUNC(my_sigmoid_out)(const Tensor& self, const Tensor& result) {
    AT_DISPATCH_ALL_TYPES(self.scalar_type(), "my_sigmoid", [&]() {
        cpu_kernel(*this, [](scalar_t a) -> scalar_t {
            return 1.0 / (1.0 + std::exp(-a));  // std::exp not defined for int
        });
    });
}
```

`AT_DISPATCH_ALL_TYPES` expands to a switch over all numeric types including `int8`, `int16`, `int32`, `int64`. Calling `std::exp(-a)` on an integer type either silently truncates or doesn't compile.

`aten/src/ATen/Dispatch.h:469 — "#define AT_DISPATCH_ALL_TYPES(TYPE, NAME, ...)"`

## Fix

Use the appropriate dispatch macro for your operation's type requirements:

| Macro | Covers |
|---|---|
| `AT_DISPATCH_FLOATING_TYPES` | `float`, `double` |
| `AT_DISPATCH_FLOATING_TYPES_AND_HALF` | `float`, `double`, `half` |
| `AT_DISPATCH_FLOATING_AND_COMPLEX_TYPES` | `float`, `double`, `complex64`, `complex128` |
| `AT_DISPATCH_ALL_TYPES` | All numeric (including int) |
| `AT_DISPATCH_ALL_TYPES_AND_COMPLEX` | All numeric + complex |

```cpp
// Correct for sigmoid:
AT_DISPATCH_FLOATING_TYPES_AND_HALF(self.scalar_type(), "my_sigmoid", [&]() {
    cpu_kernel(*this, [](scalar_t a) -> scalar_t {
        return 1.0f / (1.0f + std::exp(-a));
    });
});
```

## Detection

Write a unit test that calls your op with an integer input. A correct implementation either raises a `RuntimeError` ("not implemented for Int") or handles it explicitly.
