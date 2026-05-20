# Autograd Pitfalls

## Footgun 1: Modifying a saved tensor in-place
If you modify a tensor that was saved for backward with `ctx.save_for_backward()`, the
version_counter will be bumped and PyTorch will raise a RuntimeError during backward.
Fix: Clone the tensor before in-place modification, or use the out-of-place variant.

## Footgun 2: Returning views from custom backward
Returning a view of an input from a custom forward without correctly handling the gradient
of the view in backward leads to incorrect gradients.
Fix: Always test with `gradcheck`. Return cloned output from forward if unsure.

## Footgun 3: Detaching tensors mid-graph
`tensor.detach()` removes the tensor from the computation graph. If done incorrectly,
gradients won't flow through the detached edge.
Fix: Only detach tensors that intentionally stop gradient flow.

## Footgun 4: Non-leaf tensor .grad
`.grad` is only populated for leaf tensors (those with `requires_grad=True` and no `grad_fn`).
Accessing `.grad` on a non-leaf tensor always returns None.
Fix: Use `tensor.retain_grad()` before backward to retain non-leaf gradients.

## Footgun 5: Gradient accumulation without zero_grad()
PyTorch accumulates gradients by default. Without `optimizer.zero_grad()` before each
backward pass, gradients from multiple batches pile up.
Fix: Call `optimizer.zero_grad()` at the start of each training step.
