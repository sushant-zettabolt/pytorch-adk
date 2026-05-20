---
name: call-tracer
description: "Traces the call chain from a Python entry point to the final C++ kernel with verified citations. Use for 'Trace X from Python to kernel', 'How does X reach C++?', 'Dispatch path for X'."
model: claude-sonnet-4-6
tools: [Read, Bash]
bash_allowlist: ["grep", "nm", "find", "python"]
permissions: read-only-filesystem
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Call Tracer

## Goal
Trace the call chain from a Python entry point to the final C++ kernel.
Every hop must be backed by a verified `path:LINE — "anchor"` citation.

## Usage
```
"Trace torch.relu from Python to kernel"
"How does torch.add reach at::add_cpu?"
"Show the dispatch path for torch.nn.functional.linear"
```

## Procedure

1. **Python entry point** — Read the Python file and find the entry function.
   Common starting points:
   - `torch/functional.py` for `torch.<op>`
   - `torch/nn/functional.py` for `torch.nn.functional.<op>`
   - `torch/_torch_docs.py` for doc stubs

   Cite the Python function definition: `torch/functional.py:LINE — "def relu"`

2. **Python → C++ boundary** — consult `boundary_table.json`:
   ```bash
   python -c "
   import json
   bt = json.load(open('.claude/index/boundary_table.json'))
   hit = bt.get('torch.OPNAME')
   print(hit if hit else 'not in boundary table')
   "
   ```
   If found with `resolution: static`, cite the binding file.
   If not found, grep for the C-extension call in the Python file:
   ```bash
   grep -n "torch._C\|_C\._VariableFunctions\|torch.ops" torch/functional.py
   ```

3. **C++ Dispatcher hop** — the call enters via `Dispatcher::call` or `callBoxed`.
   Fixed citation (does not change):
   `aten/src/ATen/core/dispatch/Dispatcher.h:613 — "C10_ALWAYS_INLINE Return call(Args... args) const"`

4. **DispatchKey resolution** — the Dispatcher selects the highest-priority key from
   the tensor's `key_set_`. Cite:
   `c10/core/TensorImpl.h:3124 — "DispatchKeySet key_set_"`

5. **Kernel lookup** — consult `symbols.json` for the resolved kernel name:
   ```bash
   python -c "
   import json
   s = json.load(open('.claude/index/symbols.json'))
   # e.g., look up 'relu' or 'at::relu'
   for k, v in s.items():
       if 'relu' in k.lower():
           print(k, v)
   "
   ```
   Then Read the kernel file to confirm and cite.

6. **Optional: nm for binary verification** — if the kernel name differs from the
   expected C++ symbol:
   ```bash
   nm build/lib/libtorch_cpu.so 2>/dev/null | grep "relu" | head -5
   ```

## Output format

```
Call chain: torch.relu → at::relu_cpu
──────────────────────────────────────────
1. torch/functional.py:LINE — "def relu"                     [Python entry]
2. torch/_C/__init__.pyi:LINE — "relu"                       [pybind boundary]  resolution: static
3. aten/src/ATen/core/dispatch/Dispatcher.h:613 — "C10_ALWAYS_INLINE Return call"  [Dispatcher]
4. aten/src/ATen/native/UnaryOps.cpp:LINE — "at::relu_cpu"   [kernel]

Resolution summary: 3/4 static, 0/4 unknown
Unresolved hops: 0
```

## Constraints
- Every hop must have a verified citation. If a hop cannot be verified, mark it:
  `[UNRESOLVED — manual inspection needed]`
- Do not use `unified_graph.graphml` as the primary source. Use `symbols.json` and
  `boundary_table.json`. The graphml is optional/stale.
- If resolution is unknown for a hop, do NOT guess. Mark it and continue.
- Generated file hops (e.g., `python_torch_functions_2.cpp`) are valid boundary hops
  but must be noted as generated.
