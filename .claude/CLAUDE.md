# PyTorch ADK — Project Session Protocol

## Pinned Commit
`70d99e998b4` — always verify with `git rev-parse HEAD` at session start.

## Build Command
```bash
python setup.py develop 2>&1 | tail -20
```

## ADK Session Entry Protocol
1. Load ADK.md — confirm pinned commit matches HEAD.
2. Check `.claude/index/index_meta.json` — if `built_at_commit ≠ HEAD`, emit ⚠ stale-index warning.
3. Review `questions.md` — note any open items for this session.
4. Check `blast-radius.md` before any file edit.

## Generated File Patterns (This Repo)
- `torch/csrc/autograd/generated/**`
- `build/**`
- `python_torch_functions*.cpp`
- Any file with `# @generated` header

## Tier 1 Files (Highest Blast Radius)
- `aten/src/ATen/Dispatcher.h`
- `c10/core/TensorImpl.h`
- `torch/csrc/autograd/python_variable.cpp`
- `aten/src/ATen/core/op_registration/`

## Subsystem Ownership
- Dispatcher: Core team
- Autograd: Autograd team
- CUDA: CUDA team
- Distributed: Distributed team

## Citation Format
`path:LINE — "anchor phrase"` — anchor phrase must be grep-able verbatim.

---

## Agent Routing — MANDATORY

You MUST delegate to the listed agent instead of answering directly. These are not suggestions.

| If the user asks... | Delegate to |
|---|---|
| Where is X defined? / Find X / Locate X / What file is X in? | `symbol-locator` |
| Trace X from Python to kernel / How does X reach C++? / Dispatch path for X | `call-tracer` |
| What files do I touch to do X? / How is X structured? / Explore X | `codebase-explorer` |
| Write a kernel for X / Add YAML entry for X / Write meta kernel for X | `kernel-writer` |
| Add op X end-to-end / Add aten::X | `op-adder` |
| Write tests for X / Write OpInfo for X / Write gradcheck for X | `test-writer` |
| Check backward for X / Verify gradcheck for X / Jacobian mismatch in X | `backward-checker` |
| Check torch.compile for X / Graph break in X / Is X compile-compatible? | `compile-tester` |
| Review this PR / Review these changes | `pr-reviewer` |
| Review this file / Review this diff / Check this code for footguns | `code-reviewer` |
| Write a PR description for X | `pr-author` |
| Track PR status / Monitor PR CI / Is PR X ready to merge? | `pr-lifecycle` |
| Lint X / Check citations in X | `lint-checker` |
| Build error / Compiler error / Why does the build fail? | `compiler-expert` |
| Run the build / What build command do I run? | `build-runner` |
| File a GitHub issue / Comment on PR / Create PR | `github-ops` |
| Triage this issue | `issue-triager` |
| CUDA memory / Memory leak / Peak memory for X | `cuda-perf` |
| Distributed error / NCCL error / DDP issue | `distributed-debugger` |
| Onboard me / How do I contribute? / New contributor | `onboarding-guide` |
| Answer question X from questions.md / Find proof for X | `question-solver` |
| Update stale citations / Migrate citations after commit switch | `adk-migrator` |

### How to delegate

Use the Agent tool with the agent's name. Example:

```
User: "Where is Dispatcher defined?"
→ Agent(subagent_type="symbol-locator", prompt="Locate the Dispatcher class. Return one path:LINE — "anchor" citation.")
```

Pass the user's question verbatim in the prompt, plus any relevant context (op name, file path, error text).

### When NOT to delegate

- Simple factual questions answerable from this CLAUDE.md or ADK.md without file reads.
- The user explicitly says "don't use an agent" or "just answer directly".
- The agent for that task does not exist in `.claude/agents/`.
