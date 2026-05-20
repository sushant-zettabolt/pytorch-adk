---
name: c10-core
description: "The c10 foundational layer: TensorImpl, Storage, DispatchKey, DeviceType, IValue. Use for questions about PyTorch's core data structures in c10/."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# c10-core Skill

## What Is c10?

c10 ("Caffe2 + PyTorch merged core") is the foundational library shared by all of PyTorch. Provides `TensorImpl`, `Storage`, `DispatchKey`, `DeviceType`, `IValue`, and core data structures. Everything in PyTorch depends on c10; nothing in c10 depends on the rest of PyTorch.

`c10/core/TensorImpl.h:528 — "struct C10_API TensorImpl : public c10::intrusive_ptr_target"`

## Key Q&A

**Q: What is TensorImpl?**
A: The internal C++ struct holding all tensor metadata: sizes, strides, storage pointer, dtype, device, autograd metadata, and dispatch key set. `at::Tensor` is a ref-counted handle to a `TensorImpl`.

`c10/core/TensorImpl.h:528 — "struct C10_API TensorImpl : public c10::intrusive_ptr_target"`
`c10/core/TensorImpl.h:3124 — "DispatchKeySet key_set_"`
`c10/core/TensorImpl.h:2967 — "std::unique_ptr<c10::AutogradMetaInterface> autograd_meta_ = nullptr"`

**Q: What is Storage / StorageImpl?**
A: `Storage` is a ref-counted Python-facing handle; `StorageImpl` is the C++ implementation holding the `DataPtr` (owns raw memory), allocator, and byte size. Multiple tensors sharing the same `StorageImpl` are views of each other.

`c10/core/Storage.h:25 — "struct C10_API Storage"`
`c10/core/StorageImpl.h:55 — "struct C10_API StorageImpl : public c10::intrusive_ptr_target"`

**Q: What is DeviceType?**
A: An `int8_t` enum of compute device types: CPU, CUDA, XLA, MPS, Meta, etc. A `Device` pairs a `DeviceType` with an index.

`torch/headeronly/core/DeviceType.h:35 — "enum class DeviceType : int8_t"`

**Q: What is DispatchKeySet?**
A: A bitmask over `DispatchKey` values, representing all the "active" dispatch layers for a tensor (e.g., `{CPU, AutogradCPU, ADInplaceOrView}`). The Dispatcher picks the highest-priority active key.

`c10/core/DispatchKeySet.h:167 — "class DispatchKeySet final"`
`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`

**Q: What is IValue?**
A: PyTorch's universal value type used by the TorchScript runtime, JIT, and boxed dispatch. Can hold a `Tensor`, `int`, `float`, `bool`, `str`, `List`, `Dict`, `None`, etc.

`aten/src/ATen/core/ivalue.h:225 — "struct TORCH_API IValue final"`
`aten/src/ATen/core/ivalue.h:1212 — "enum class Tag : uint32_t"`

**Q: What is `numel()` on TensorImpl?**
A: Returns the total number of elements: product of all dimension sizes. Inlined for performance; delegates to `numel_default()` for symbolic sizes.

`c10/core/TensorImpl.h:712 — "int64_t numel() const"`

## Blast Radius

- `c10/core/TensorImpl.h` — Tier 1. Every tensor in PyTorch.
- `c10/core/DispatchKey.h` — Tier 1. Adding/changing enum values invalidates all dispatch tables.
- `c10/core/StorageImpl.h` — Tier 2. Memory management for all tensors.
- `c10/core/Storage.h` — Tier 2. Python-facing storage API.
- `aten/src/ATen/core/ivalue.h` — Tier 2. TorchScript/JIT value type.
- `torch/headeronly/core/DeviceType.h` — Tier 2. Adding a new device type requires registration in ~10 places.
