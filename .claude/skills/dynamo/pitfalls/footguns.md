# Dynamo / torch.compile Pitfalls

## Footgun 1: print() inside compiled region
print() causes a graph break. Dynamo cannot trace through Python I/O.
Fix: Guard with `if not torch.compiler.is_compiling(): print(...)`

## Footgun 2: len() on a dynamic tensor list
`len(list_of_tensors)` where the list changes size causes a graph break or recompilation.
Fix: Use `torch.stack(list_of_tensors).shape[0]`

## Footgun 3: Global state mutation inside compiled function
Mutating global Python state inside a compiled function is not captured in the graph.
Fix: Pass all state as function arguments.

## Footgun 4: Non-tensor control flow depending on tensor values
`if tensor.item() > 0:` forces a graph break because it reads a tensor value at trace time.
Fix: Use `torch.where(condition, x, y)` for tensor-conditional operations.

## Footgun 5: torch.compile on non-deterministic code
If the function produces different outputs for the same inputs (e.g., random seeds),
torch.compile may cache and reuse incorrect outputs.
Fix: Use `torch.manual_seed()` or `torch.Generator` for reproducible randomness.
