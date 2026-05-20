---
name: cuda_runtime
description: "PyTorch's CUDA runtime integration: caching allocator, streams, synchronization, and custom kernel launch. Use for questions about CUDA memory, streams, or sync."
validated-at: 70d99e998b4
---

# CUDA Runtime Skill
## What Is the CUDA Runtime Layer?
PyTorch's CUDA integration: memory allocation, stream management, kernel launch, synchronization.

## Key Questions

**Q: How does PyTorch's CUDA caching allocator work?**
A: Maintains free blocks per stream. Allocations first check cache; on miss, calls cudaMalloc. Freed blocks return to cache (not to CUDA).
`c10/cuda/CUDACachingAllocator.cpp:LINE — "CUDACachingAllocator"`

**Q: What is a CUDA stream in PyTorch?**
A: Sequence of operations that execute in order on the GPU. Multiple streams run concurrently.
`c10/cuda/CUDAStream.h:LINE — "class CUDAStream"`

**Q: What is `torch.cuda.synchronize()`?**
A: Blocks CPU until all GPU kernels on the current device complete. Use for profiling; avoid in production (serializes CPU and GPU).

**Q: What are CUDA synchronization bugs?**
A: Bugs where CPU reads GPU memory before the GPU kernel completes. Usually caused by missing stream synchronization.
Detected by: `PYTORCH_NO_CUDA_MEMORY_CACHING=1` + `cuda-memcheck`.

**Q: How do you launch a custom CUDA kernel?**
A: Define `__global__` function, use `<<<grid, block, shared, stream>>>` launch syntax inside an `.cu` file.

## Blast Radius
- `c10/cuda/CUDACachingAllocator.cpp` — Tier 2 (all GPU memory ops)
- `c10/cuda/CUDAStream.h` — Tier 2 (stream management)
