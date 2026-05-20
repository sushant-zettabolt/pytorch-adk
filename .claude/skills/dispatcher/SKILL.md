---
name: dispatcher
description: "PyTorch's operator dispatch system: how torch.add etc. route to the right kernel via DispatchKeySet and per-operator kernel tables. Use for questions about dispatch routing, DispatchKey, or the Dispatcher class."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# Dispatcher Skill

## What Is the Dispatcher?

The central operator dispatch system in PyTorch. Every call to `torch.add`, `torch.relu`, etc. routes through it. It resolves which kernel to invoke based on the operator name and the `DispatchKeySet` of the input tensors.

`aten/src/ATen/core/dispatch/Dispatcher.h:71 — "class TORCH_API Dispatcher final"`

## Key Q&A

**Q: How does dispatch routing work?**
A: The Dispatcher maintains an `operatorLookupTable_` keyed by `OperatorName`. For each operator, a per-dispatch-key kernel table is consulted. Given the input tensors' `DispatchKeySet`, the highest-priority matching key wins and that kernel is called.

`aten/src/ATen/core/dispatch/Dispatcher.h:403 — "operatorLookupTable_"`
`c10/core/DispatchKeySet.h:167 — "class DispatchKeySet final"`

**Q: What is a DispatchKey?**
A: An enum value (`uint16_t`) identifying a backend or transformation layer: CPU, CUDA, AutogradCPU, CompositeImplicitAutograd, etc. A tensor's `DispatchKeySet` holds a bitmask of active keys; the Dispatcher picks the highest-priority one.

`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`

**Q: What is the call entry point for unboxed dispatch?**
A: `TypedOperatorHandle::call(Args...)`, which delegates to `Dispatcher::singleton().call<Return, Args...>`. The hot path avoids boxing/unboxing overhead.

`aten/src/ATen/core/dispatch/Dispatcher.h:613 — "C10_ALWAYS_INLINE Return call(Args... args) const"`
`aten/src/ATen/core/dispatch/Dispatcher.h:112 — "C10_ALWAYS_INLINE static Dispatcher& singleton()"`

**Q: What is the call entry point for boxed dispatch (JIT / TorchScript)?**
A: `Dispatcher::callBoxed(const OperatorHandle& op, Stack* stack)`. Passes inputs/outputs via a `Stack` (vector of `IValue`). Necessary when the type signature is only known at runtime.

`aten/src/ATen/core/dispatch/Dispatcher.h:204 — "void callBoxed(const OperatorHandle& op, Stack* stack) const"`

**Q: How do you register a kernel?**
A: Use `TORCH_LIBRARY_IMPL(namespace, DispatchKey, m) { m.impl("op_name", &fn); }`. The macro expands to a static registration object that calls into the Dispatcher at load time.

`torch/library.h:1064 — "#define TORCH_LIBRARY_IMPL(ns, k, m)"`

**Q: What happens when no kernel is registered for a key?**
A: The Dispatcher checks alias keys (e.g., `CompositeImplicitAutograd` covers all backends). If still no match, it looks for a boxed fallback registered via `m.fallback()`. If none, it throws `NotImplementedError`.

`aten/src/ATen/core/dispatch/Dispatcher.h:413 — "backendFallbackKernels_"`

**Q: What is redispatch and when is it used?**
A: Autograd and other transformation layers (Functionalize, BatchedTensor) call `redispatch` after doing their work, passing a lowered `DispatchKeySet` that excludes their own key so the next layer handles it.

`aten/src/ATen/core/dispatch/Dispatcher.h:179 — "Return call(const TypedOperatorHandle<Return(Args...)>& op, Args... args)"`

## Call Sequence: torch.relu(x)

```
Python:  torch.relu(x)
         ↓ pybind11 (python_torch_functions_*.cpp — parse, don't cite)
C++:     at::relu(self)
         ↓ generated wrapper → Dispatcher::call
         lookup "aten::relu" in operatorLookupTable_
         → compute DispatchKeySet from tensor device+dtype
         → resolve highest-priority key (e.g. CPU)
         → call registered at::native::relu
```

## Alias Keys (Important)

| Key | Meaning |
|---|---|
| `CompositeImplicitAutograd` | Kernel works for all backends; autograd derived automatically |
| `CompositeExplicitAutograd` | Kernel works for all backends; autograd registered separately |
| `AutogradCPU`, `AutogradCUDA` | Backend-specific autograd override |
| `Functionalize` | Used by functorch and export to make in-place ops functional |

`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`

## Blast Radius
- `aten/src/ATen/core/dispatch/Dispatcher.h` — Tier 1. Architecture Owner sign-off required.
- `c10/core/DispatchKey.h` — Tier 1. Changing enum values breaks ALL dispatch tables.
- `torch/library.h` — Tier 2. Macro changes affect all op registrations.
