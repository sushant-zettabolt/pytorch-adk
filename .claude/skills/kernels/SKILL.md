---
name: kernels
description: "ATen native kernels: native_functions.yaml, structured kernels (TORCH_META_FUNC + TORCH_IMPL_FUNC), end-to-end op addition. Use for questions about writing or adding kernels."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# Kernels Skill

## ATen Native Kernels

Located in `aten/src/ATen/native/`. Each file covers a subsystem (`Math.cpp`, `Loss.cpp`, `UnaryOps.cpp`, etc.). Kernels are registered via `native_functions.yaml` and the `TORCH_LIBRARY_IMPL` macro.

`aten/src/ATen/TensorIterator.h:248 — "struct TORCH_API TensorIteratorBase : public impl::MetaBase"`

## Key Q&A

**Q: How is a new kernel added end-to-end?**
A: Four required steps in order:
1. Add entry in `aten/src/ATen/native/native_functions.yaml` (signature + dispatch table)
2. Write C++ implementation in `aten/src/ATen/native/<file>.cpp`
3. Write `TORCH_META_FUNC` (shape/dtype inference) and `TORCH_IMPL_FUNC` (actual compute) for structured kernels
4. Add `OpInfo` in `torch/testing/_internal/common_methods_invocations.py` + gradcheck test

`aten/src/ATen/native/native_functions.yaml:9 — "- func: _cast_Byte(Tensor self, bool non_blocking=False)"`

**Q: What is a structured kernel?**
A: A kernel declared with `structured: True` and `structured_inherits: TensorIteratorBase` in YAML. Codegen auto-generates the wrapper; you only write `meta()` (shape/dtype) and `impl()` (compute). This pattern is required for all new pointwise ops.

`aten/src/ATen/native/native_functions.yaml:449 — "structured_inherits: TensorIteratorBase"`
`aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`

**Q: What is a TensorIterator?**
A: PyTorch's vectorized elementwise kernel infrastructure. Handles broadcasting, type promotion, contiguity checks, and SIMD dispatch automatically. Almost all pointwise kernels go through it.

`aten/src/ATen/TensorIterator.h:248 — "struct TORCH_API TensorIteratorBase : public impl::MetaBase"`
`aten/src/ATen/TensorIterator.h:736 — "struct TORCH_API TensorIterator final : public TensorIteratorBase"`

**Q: How do you write a CPU kernel using TensorIterator?**
A: Use `cpu_kernel(iter, lambda)`. The lambda receives scalar elements; vectorized dispatch is automatic via `at::vec::Vectorized`.

```cpp
void my_op_cpu_kernel(TensorIteratorBase& iter) {
    AT_DISPATCH_ALL_TYPES(iter.dtype(), "my_op", [&]() {
        cpu_kernel(iter, [](scalar_t a) { return a * a; });
    });
}
```

`aten/src/ATen/native/cpu/Loops.h:304 — "void cpu_kernel(TensorIteratorBase& iter, func_t&& op"`
`aten/src/ATen/Dispatch.h:469 — "#define AT_DISPATCH_ALL_TYPES(TYPE, NAME, ...)"`

**Q: How do you build a TensorIterator for binary ops?**
A: Use `TensorIteratorConfig` then `build_binary_op`. The config handles output shape inference, type promotion, and broadcasting.

`aten/src/ATen/TensorIterator.h:571 — "void build_binary_op"`

**Q: What is a meta kernel and why is it required?**
A: The meta kernel (registered under `DispatchKey::Meta`) runs the op's shape/dtype inference without touching actual data. Required by `torch.compile`, `torch.export`, and `FakeTensor` mode. A meta kernel that returns the wrong shape or dtype will silently corrupt the export graph.

`aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`
`aten/src/ATen/native/UnaryOps.cpp:252 — "TORCH_META_FUNC(neg)"`

**Q: Where does structured kernel codegen output go?**
A: `build/aten/src/ATen/RegisterCPU.cpp` and friends. These are generated — do not edit them directly. Change the YAML or the `meta()`/`impl()` functions instead.

`aten/src/ATen/native/native_functions.yaml:9 — "- func: _cast_Byte(Tensor self, bool non_blocking=False)"`

## Minimal Structured Kernel Template

```yaml
# native_functions.yaml entry
- func: my_op(Tensor self) -> Tensor
  structured: True
  structured_inherits: TensorIteratorBase
  dispatch:
    CPU, CUDA: my_op_out
    Meta: my_op_out
```

```cpp
// aten/src/ATen/native/MyOps.cpp
TORCH_META_FUNC(my_op)(const Tensor& self) {
    // Set output shape and dtype — no data access
    set_output_raw_strided(0, self.sizes(), {}, self.options());
}

TORCH_IMPL_FUNC(my_op_out)(const Tensor& self, const Tensor& result) {
    AT_DISPATCH_FLOATING_TYPES(self.scalar_type(), "my_op", [&]() {
        cpu_kernel(*this, [](scalar_t a) { return a; });
    });
}
```

## Blast Radius

- `aten/src/ATen/native/native_functions.yaml` — Tier 2. Changes rebuild all dispatch tables.
- `aten/src/ATen/TensorIterator.h` — Tier 2. All elementwise kernels.
- `aten/src/ATen/TensorMeta.h` — Tier 3. Meta kernel macro.
