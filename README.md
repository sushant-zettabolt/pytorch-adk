# PyTorch ADK

A Claude Code plugin for PyTorch development — 22 custom agents, 25 skill files, and
automated hooks that wire into every Claude Code session.

## What's included

| Component | Count | What it does |
|---|---|---|
| Agents | 22 | Specialized subagents (symbol-locator, kernel-writer, op-adder, …) |
| Skills | 25 | Deep-knowledge files (dispatcher, autograd, kernels, inductor, …) |
| Hooks | 11 | Session-start init, pre-edit blast-radius checks, stop citation verifier |
| MCP configs | 4 | GitHub, CI, profiler, benchmark-db integrations |
| Tools | 4 | Index builder, boundary parser, graph stitcher, LLM gap-fill |

## Install

**Requirements:** a PyTorch git checkout with a Python venv at `<checkout>/venv/`.

```bash
# 1. Clone this repo
git clone <internal-git-url>/pytorch-adk.git

# 2. Run the installer, pointing at your PyTorch checkout
bash pytorch-adk/install.sh ~/pytorch

# 3. Build the index (required — not shipped with the plugin)
cd ~/pytorch
python tools/adk/build_index.py

# 4. Open a Claude Code session — the session hook confirms everything is healthy
claude .
```

That's it. The session-start hook fires on every `claude` invocation and prints index
currency status. Agents and skills are picked up automatically.

## Updating

```bash
cd pytorch-adk
git pull
bash install.sh ~/pytorch   # re-run installer; hooks/skills/agents are overwritten
```

## If you already have a settings.json

The installer will not overwrite an existing `.claude/settings.json`. Manually merge
the hooks block from `.claude/settings.json.template` into your file. The required
hooks are:

```
SessionStart  → .claude/hooks/session-start-init.py
PreToolUse    → .claude/hooks/pre-edit-block-generated.sh
PreToolUse    → .claude/hooks/pre-edit-dispatcher-check.sh
PostToolUse   → .claude/hooks/post-edit-targeted-tests.py
PostToolUse   → .claude/hooks/post-edit-impact-analysis.py
Stop          → .claude/hooks/stop-summary.py
Stop          → .claude/hooks/stop-regression-report.py
Stop          → .claude/hooks/verify_answer.py
Stop          → .claude/hooks/handoff-block-enforcer.py
```

## Feature list

### Agents

Agents are specialized subagents that Claude routes to automatically based on your query.

| Query pattern | Agent |
|---|---|
| "Where is X defined?" / "Find X" / "Locate X" / "What file is X in?" | `symbol-locator` |
| "Trace X from Python to kernel" / "How does X reach C++?" / "Dispatch path for X" | `call-tracer` |
| "What files do I touch to do X?" / "How is X structured?" / "Explore X" | `codebase-explorer` |
| "Write a kernel for X" / "Add YAML entry for X" / "Write meta kernel for X" | `kernel-writer` |
| "Add op X end-to-end" / "Add aten::X" | `op-adder` |
| "Write tests for X" / "Write OpInfo for X" / "Write gradcheck for X" | `test-writer` |
| "Check backward for X" / "Verify gradcheck for X" / "Jacobian mismatch in X" | `backward-checker` |
| "Check torch.compile for X" / "Graph break in X" / "Is X compile-compatible?" | `compile-tester` |
| "Review this PR" / "Review these changes" | `pr-reviewer` |
| "Review this file" / "Review this diff" / "Check this code for footguns" | `code-reviewer` |
| "Write a PR description for X" | `pr-author` |
| "Track PR status" / "Monitor PR CI" / "Is PR X ready to merge?" | `pr-lifecycle` |
| "Lint X" / "Check citations in X" | `lint-checker` |
| "Build error" / "Compiler error" / "Why does the build fail?" | `compiler-expert` |
| "Run the build" / "What build command do I run?" | `build-runner` |
| "File a GitHub issue" / "Comment on PR" / "Create PR" | `github-ops` |
| "Triage this issue" | `issue-triager` |
| "CUDA memory" / "Memory leak" / "Peak memory for X" | `cuda-perf` |
| "Distributed error" / "NCCL error" / "DDP issue" | `distributed-debugger` |
| "Onboard me" / "How do I contribute?" / "New contributor" | `onboarding-guide` |
| "Answer question X from questions.md" / "Find proof for X" | `question-solver` |
| "Update stale citations" / "Migrate citations after commit switch" | `adk-migrator` |

Full routing rules are in `.claude/CLAUDE.md`.

### Skills

Skills are deep-knowledge files that Claude loads automatically when a question touches the relevant domain.

| Query domain | Skill |
|---|---|
| Dispatcher routing, DispatchKey, kernel tables | `dispatcher` |
| Backward passes, grad_fn, autograd engine internals | `autograd` |
| ATen kernels, native_functions.yaml, structured kernels | `kernels` |
| torch._inductor, Triton codegen, lowering failures | `inductor` |
| CUDA allocator, streams, synchronization, kernel launch | `cuda_runtime` |
| torch.fx, Graph, Node, GraphModule, symbolic tracing | `fx` |
| torch.export, ExportedProgram, dynamic shapes | `export` |
| Distributed training, DDP, NCCL, FSDP, all_reduce | `distributed` |
| TorchDynamo, bytecode tracing, FakeTensor, graph breaks | `dynamo` |
| c10 layer, TensorImpl, Storage, IValue, DeviceType | `c10-core` |
| Tensor object hierarchy, StorageImpl, DataPtr, memory layout | `tensor-internals` |
| Backend kernel registration, TORCH_LIBRARY_IMPL, CompositeImplicitAutograd | `backend-reg` |
| OpInfo entries, sample inputs, gradcheck flags | `opinfo` |
| In-place/view op functionalization, FunctionalTensorWrapper | `functionalization` |
| pybind11 layer, THPVariable, Python↔C++ bindings | `pybind` |
| torchgen code generation from native_functions.yaml | `torchgen` |
| PyTorch build system, setup.py, CMake, build failures | `build` |
| pre-commit, flake8, mypy, clang-format, clang-tidy | `lint` |
| PR lifecycle, gh commands, CI systems | `github` |
| Custom operator registration via torch.library / TORCH_LIBRARY | `custom-ops` |
| PR review checklist, correctness, safety, style | `pr-review` |
| ADK index artifacts, symbols.json, O(1) symbol lookup | `index` |
| Test coverage of call edges, blast-radius checks | `test-graph` |
| Multi-step orchestrator failure modes, handoff block schema | `error-handling` |
| Citation completeness verification, path:LINE anchors | `verify-answer` |

### Hooks

Hooks fire automatically on tool events — no query needed.

| Trigger event | Hook | What it does |
|---|---|---|
| Session start (`SessionStart`) | `session-start-init.py` | Loads ADK.md, checks index currency, reviews questions.md |
| Before any file edit (`PreToolUse`) | `pre-edit-block-generated.sh` | Blocks writes to generated files (`@generated`, `build/`, etc.) |
| Before editing Tier 1 files (`PreToolUse`) | `pre-edit-dispatcher-check.sh` | Blast-radius check; requires explicit user confirmation |
| After any file edit (`PostToolUse`) | `post-edit-targeted-tests.py` | Runs tests that cover the changed file |
| After any file edit (`PostToolUse`) | `post-edit-impact-analysis.py` | Reports downstream symbols affected by the change |
| Session end (`Stop`) | `stop-summary.py` | Prints a concise session summary |
| Session end (`Stop`) | `stop-regression-report.py` | Reports any test regressions introduced this session |
| Session end (`Stop`) | `verify_answer.py` | Verifies all factual citations resolve to real path:LINE anchors |
| Session end (`Stop`) | `handoff-block-enforcer.py` | Ensures orchestrator handoff blocks match canonical schema |

## Index

The index (`symbols.json`, call graphs) is built locally and not committed. Rebuild it
whenever you switch commits:

```bash
python tools/adk/build_index.py
```

If your PyTorch checkout is not at `$PWD`, set `PYTORCH_ROOT`:

```bash
PYTORCH_ROOT=/path/to/pytorch python tools/adk/build_index.py
```

## Troubleshooting

**Stop hook error at session end** — run `verify_answer.py` manually to see which
citations failed:
```bash
echo '{}' | python .claude/hooks/verify_answer.py
```

**Agent not found** — confirm the agent `.md` file in `.claude/agents/` has a
`description:` field in its frontmatter. Without it, Claude Code won't register it.

**Index stale warning** — run `python tools/adk/build_index.py` to rebuild.
