---
name: autograd
description: "PyTorch's automatic differentiation engine — backward graph construction, Node types, grad_fn, and how autograd metadata is exposed to Python. Use for questions about backward passes, gradients, and autograd internals."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# Autograd Skill

## What Is Autograd?

PyTorch's automatic differentiation engine. Builds a dynamic computation graph during the forward pass, then traverses it backward to compute gradients.

`torch/csrc/autograd/node.h:112 — "struct TORCH_API Node : c10::intrusive_ptr_target"`

## Key Q&A

**Q: How does the backward graph get built?**
A: Each differentiable op creates a `Node` subclass (e.g., `ReluBackward0`) and attaches it as the `grad_fn` on output tensors. The node stores `next_edges_` pointing to the `grad_fn` of each input, forming a DAG.

`torch/csrc/autograd/node.h:112 — "struct TORCH_API Node : c10::intrusive_ptr_target"`
`torch/csrc/autograd/node.h:116 — "sequence_nr_(sequence_nr), next_edges_(std::move(next_edges))"`

**Q: Where is the grad_fn exposed to Python?**
A: `THPVariable_get_grad_fn` in `python_variable.cpp` reads `var.grad_fn()` from the tensor and wraps the C++ `Node` pointer in a Python object.

`torch/csrc/autograd/python_variable.cpp:2706 — "static PyObject* THPVariable_get_grad_fn"`

**Q: How is `backward()` triggered?**
A: Python `tensor.backward()` → `torch/autograd/__init__.py:backward()` → `_engine_run_backward()` (C++ binding) → `Engine::execute()`.

`torch/autograd/__init__.py:255 — "def backward"`
`torch/csrc/autograd/engine.cpp:1294 — "auto Engine::execute"`

**Q: How does the Engine traverse the graph?**
A: `Engine::execute` uses a priority queue of `NodeTask`s ordered by `sequence_nr_`. It runs nodes in reverse topological order, accumulating gradients at each leaf. `Engine` is a singleton.

`torch/csrc/autograd/engine.h:130 — "struct TORCH_API Engine"`
`torch/csrc/autograd/engine.h:152 — "virtual variable_list execute"`

**Q: What is `saved_tensors` / `SavedVariable`?**
A: Tensors captured via `ctx.save_for_backward()` are stored as `SavedVariable` instances. They hold a weak reference during the forward pass; the reference is materialized when `saved_tensors` is accessed in backward. Calling `del ctx` or completing backward releases them.

`torch/csrc/autograd/saved_variable.h:22 — "class TORCH_API SavedVariable"`

**Q: How does `torch.no_grad()` suppress gradient tracking?**
A: Sets a thread-local flag via `GradMode::set_enabled(false)`. Ops under this context do not create `grad_fn` on outputs.

`torch/autograd/grad_mode.py:22 — "class no_grad(_NoParamDecoratorContextManager)"`

**Q: How does autograd interact with custom C++ ops?**
A: Ops registered with `CompositeImplicitAutograd` get autograd for free (the decomposition provides the formula). Ops that need custom backward register a `setup_context` + `backward` pair via `TORCH_LIBRARY_IMPL(aten, Autograd, m)`.

`torch/library.h:1064 — "#define TORCH_LIBRARY_IMPL(ns, k, m)"`
`c10/core/DispatchKey.h:136 — "enum class DispatchKey : uint16_t"`

**Q: What is `autograd_meta_` on TensorImpl?**
A: A heap-allocated `AutogradMetaInterface` (null for non-differentiable tensors) that stores `grad_fn`, `grad`, `version_counter`, and `requires_grad`. Only allocated when autograd is active.

`c10/core/TensorImpl.h:2967 — "std::unique_ptr<c10::AutogradMetaInterface> autograd_meta_ = nullptr"`

## Blast Radius

- `torch/csrc/autograd/python_variable.cpp` — Tier 1. All Python tensor attribute access.
- `torch/csrc/autograd/engine.cpp` — Tier 2. All backward passes.
- `torch/csrc/autograd/node.h` — Tier 2. All custom autograd functions.
- `torch/csrc/autograd/saved_variable.h` — Tier 3. Memory management for backward tensors.
