# Dispatcher References

## Design Documents
- PyTorch Dispatcher RFC: https://github.com/pytorch/pytorch/wiki/PyTorch-dispatcher-walkthrough
- Operator Registration Guide: https://pytorch.org/docs/stable/notes/extending.html

## Key Source Files
- `aten/src/ATen/Dispatcher.h` — Primary Dispatcher interface
- `aten/src/ATen/Dispatcher.cpp` — Dispatcher implementation
- `c10/core/DispatchKey.h` — DispatchKey enum and DispatchKeySet
- `aten/src/ATen/core/dispatch/` — Internal dispatch machinery

## Talks
- "PyTorch Internals: The Dispatcher" — PyTorch Dev Day 2020
- "Under the Hood of torch.compile" — PyTorch Conference 2023

## Blog Posts
- "How PyTorch Dispatches to Kernels" — PyTorch Blog
