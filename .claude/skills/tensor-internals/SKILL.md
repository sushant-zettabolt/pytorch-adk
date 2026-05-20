---
name: tensor-internals
description: "Tensor object hierarchy: torch.Tensor → THPVariable → at::Tensor → TensorImpl → StorageImpl → DataPtr. Use for questions about tensor internals and memory layout."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# Tensor Internals Skill

## Tensor Object Hierarchy

```
Python tensor (torch.Tensor)
    → THPVariable (C++ Python wrapper)
        → at::Tensor (ref-counted handle)
            → TensorImpl (all metadata)
                → StorageImpl (raw memory, allocator)
                    → DataPtr (void* + deleter)
```

`torch/csrc/autograd/python_variable.h:17 — "struct THPVariable"`
`c10/core/TensorImpl.h:528 — "struct C10_API TensorImpl : public c10::intrusive_ptr_target"`
`c10/core/StorageImpl.h:55 — "struct C10_API StorageImpl : public c10::intrusive_ptr_target"`

## Key Q&A

**Q: What fields in TensorImpl define the tensor's shape and memory layout?**
A: `sizes_and_strides_` holds both sizes and strides in a single inline array (optimized for ≤5 dims). `storage_offset_` is the number of elements from the start of storage to the first element.

`c10/core/TensorImpl.h:2976 — "c10::impl::SizesAndStrides sizes_and_strides_"`
`c10/core/TensorImpl.h:2978 — "int64_t storage_offset_ = 0"`

**Q: What is the difference between a view and a copy?**
A: A view shares the same `StorageImpl` with its source, but may have different `sizes_and_strides_` and `storage_offset_`. `tensor.view(shape)` returns a view; `tensor.clone()` allocates new `StorageImpl` and copies data. Views are detected by checking whether two tensors have the same `storage().data_ptr()`.

`c10/core/TensorImpl.h:2976 — "c10::impl::SizesAndStrides sizes_and_strides_"`

**Q: What are strides and when does contiguity matter?**
A: Strides are step sizes in each dimension (in elements, not bytes). For a contiguous tensor of shape `[d0, d1, d2]`, strides are `[d1*d2, d2, 1]`. Non-contiguous strides cause cache inefficiency; most kernels call `contiguous()` before operating. `.is_contiguous()` checks if strides match this formula.

`c10/core/TensorImpl.h:637 — "return sizes_and_strides_.sizes_arrayref()"`

**Q: How does `data_ptr()` work?**
A: Returns the raw pointer computed as `storage().data() + storage_offset() * element_size()`. Valid only while the tensor is alive; detach from storage to persist.

`c10/core/TensorImpl.h:772 — "return storage_offset_"`

**Q: What is the `key_set_` field?**
A: A `DispatchKeySet` bitmask holding all dispatch layers active for this tensor (CPU/CUDA/Meta + Autograd + Functionalize, etc.). The Dispatcher reads this to pick which kernel to call.

`c10/core/TensorImpl.h:3124 — "DispatchKeySet key_set_"`
`c10/core/DispatchKeySet.h:167 — "class DispatchKeySet final"`

**Q: What is `autograd_meta_` and when is it null?**
A: A heap-allocated `AutogradMetaInterface` holding `grad_fn`, `grad`, `requires_grad`, and `version_counter`. It is `nullptr` for tensors with `requires_grad=False` (the common case) to avoid allocation overhead.

`c10/core/TensorImpl.h:2967 — "std::unique_ptr<c10::AutogradMetaInterface> autograd_meta_ = nullptr"`

**Q: What is `version_counter_` and how does it protect backward?**
A: A monotonically increasing counter on `StorageImpl` (not `TensorImpl`). Every in-place op increments it. `SavedVariable` records the version at `save_for_backward` time; if it changed by backward time, an error is raised.

`c10/core/TensorImpl.h:352 — "c10::intrusive_ptr<VersionCounter> version_counter_"`

**Q: What is `numel()`?**
A: Product of all dimension sizes. Inlined for performance.

`c10/core/TensorImpl.h:712 — "int64_t numel() const"`

## Blast Radius

- `c10/core/TensorImpl.h` — Tier 1. Every single tensor in PyTorch.
- `c10/core/StorageImpl.h` — Tier 2. Memory management for all tensors.
- `torch/csrc/autograd/python_variable.h` — Tier 1. Python↔C++ tensor bridge.
- `c10/core/DispatchKeySet.h` — Tier 2. Tensor dispatch routing.
