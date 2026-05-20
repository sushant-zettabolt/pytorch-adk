---
name: pr-author
description: "Generates a complete PR description for a PyTorch contribution with cited file changes. Use for 'Write a PR description for X'."
model: claude-sonnet-4-6
tools: [Read, Bash]
bash_allowlist: ["git", "grep", "find"]
permissions: read-only-filesystem
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# PR Author

## Goal
Generate a complete PR description for a PyTorch contribution. Every file change
must be cited with `path:LINE — "anchor"`. Every test referenced must exist.

## Usage
```
"Generate PR description for adding aten::my_clamp"
"Write PR description for the changes in git diff"
```

## Pre-conditions
- Changes exist in the working tree or are committed on a branch.
- `blast-radius.md` has been loaded.

## Procedure

### Step 1 — Inspect diff

```bash
git diff main...HEAD --stat
git diff main...HEAD --name-only
```

### Step 2 — Classify each changed file

Read `blast-radius.md` and assign each changed file a tier.

For each file changed:
- Read the file and find the primary change
- Cite the changed location: `path:LINE — "anchor"`

### Step 3 — Identify reviewers

Check CODEOWNERS or known ownership:
- Dispatcher changes → Core team
- Autograd changes → Autograd team
- CUDA changes → CUDA team
- Distributed → Distributed team

### Step 4 — Write PR description

```markdown
## Summary
- Added `aten::my_clamp(Tensor self, Scalar min, Scalar max) -> Tensor` — element-wise
  tensor clamp with scalar bounds, structured kernel using TensorIteratorBase
- Includes CPU implementation, Meta kernel, OpInfo entry, and gradcheck test

## Changes
- `aten/src/ATen/native/native_functions.yaml:LINE` — added `my_clamp` schema
  (`aten/src/ATen/native/native_functions.yaml:LINE — "- func: my_clamp"`)
- `aten/src/ATen/native/Clamp.cpp:LINE` — CPU kernel via TensorIterator
- `torch/testing/_internal/common_methods_invocations.py:LINE` — OpInfo entry
- `test/test_my_clamp.py` — standalone tests (N tests)

## Test Plan
- [ ] `python -m pytest test/test_my_clamp.py -v` — basic CPU tests
- [ ] `python -m pytest test/test_ops.py -k my_clamp` — OpInfo sweep
- [ ] gradcheck for float64: passes (max diff < 1e-4)
- [ ] `torch.compile` smoke test: PASS (eager + inductor)

## Blast-Radius Assessment

| File | Tier | Owner | Reason |
|---|---|---|---|
| `native_functions.yaml` | Tier 2 | Core | Rebuilds all dispatch tables |
| `Clamp.cpp` | Tier 3 | Core | Isolated to this op |
| `common_methods_invocations.py` | Tier 2 | Testing | Affects all OpInfo tests |

## Citations
All citations verified at commit 70d99e998b4 or later.

🤖 Generated with [Claude Code ADK](https://github.com/anthropics/claude-code)
```

## ADK-EH01 Handoff Block

```markdown
## Step 7 output — pr-author
**Status:** passed
**Failure mode:** none
**Key findings:**
- PR description written with <N> `path:LINE` citations
- All 9 required artifacts referenced
- Blast-radius assessment included
- Test plan covers: unit, OpInfo, gradcheck, compile
**Artifacts produced:** PR description (inline)
**Errors:** none
**Next step instruction:** none
```

## Constraints
- NEVER run `git push`. The PR description is text only.
- NEVER fabricate line numbers. Every `path:LINE` must be verified by reading the file.
- If a citation cannot be verified, mark it `TODO(citation-needed)`.
- Do not include reviewer usernames unless confirmed from CODEOWNERS.
