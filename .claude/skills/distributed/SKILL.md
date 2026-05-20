---
name: distributed
description: "torch.distributed concepts: ProcessGroup, DDP gradient sync, NCCL/Gloo backends, barriers, all_reduce, FSDP. Use for questions about distributed training."
validated-at: 70d99e998b4
---

# Distributed Skill
## What Is torch.distributed?
PyTorch's framework for distributed training across multiple GPUs and machines.

## Key Questions

**Q: What is a ProcessGroup?**
A: The abstraction for a group of processes that can communicate. Backends: NCCL (GPU), Gloo (CPU/GPU), MPI.
`torch/csrc/distributed/c10d/ProcessGroup.hpp:LINE — "class ProcessGroup"`

**Q: How does DDP gradient sync work?**
A: DDP registers autograd hooks on parameters. After backward, gradients are bucketed and all-reduced via NCCL before optimizer step.
`torch/nn/parallel/distributed.py:LINE — "class DistributedDataParallel"`

**Q: What is `dist.barrier()`?**
A: A synchronization point. All ranks in the group block until all reach the barrier.
`torch/distributed/__init__.py:LINE — "def barrier"`

**Q: How does all_reduce work?**
A: Sums (or reduces) tensors across all ranks. Result is identical on all ranks.
`torch/distributed/__init__.py:LINE — "def all_reduce"`

**Q: What is FSDP?**
A: Fully Sharded Data Parallel. Shards model parameters, gradients, and optimizer state across ranks to reduce per-device memory.
`torch/distributed/fsdp/__init__.py:LINE — "class FullyShardedDataParallel"`

## Blast Radius
- `torch/csrc/distributed/c10d/ProcessGroupNCCL.cpp` — Tier 2
- `torch/distributed/__init__.py` — Tier 2
