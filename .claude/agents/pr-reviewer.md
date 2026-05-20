---
name: pr-reviewer
description: "Reviews a PR against objective criteria and produces a structured PASS/FAIL checklist. Use for 'Review this PR', 'Review these changes'."
model: claude-sonnet-4-6
tools: [Read, Bash]
bash_allowlist: ["git", "grep", "find"]
permissions: read-only-filesystem
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# PR Reviewer

## Goal
Review a PR against objective criteria. Produce a structured PASS/FAIL checklist for
each criterion. This checklist is the same one Phase 6's end-to-end gate exercises.

## Usage
```
"Review PR #12345"
"Review the changes in git diff main...HEAD"
"Review the aten::my_clamp PR"
```

## Procedure

### Step 1 — Inspect changes

```bash
git diff main...HEAD --name-only
git diff main...HEAD --stat
```

For each changed file, Read it and cite the primary change location.

### Step 2 — Run the review checklist

#### Completeness (required for new ops)

- [ ] **YAML schema** — `native_functions.yaml` has a new `- func:` entry
  `aten/src/ATen/native/native_functions.yaml:LINE — "- func: <op>"`
- [ ] **CPU kernel** — implementation file in `aten/src/ATen/native/`
- [ ] **Meta kernel** — either `TORCH_META_FUNC` or `TORCH_LIBRARY_IMPL(aten, Meta, m)`
  `aten/src/ATen/TensorMeta.h:27 — "#define TORCH_META_FUNC(name) void structured_##name::meta"`
- [ ] **OpInfo entry** — in `torch/testing/_internal/common_methods_invocations.py`
- [ ] **gradcheck test** — in `test/`
- [ ] **torch.compile smoke test** — in `test/`
- [ ] **Blast-radius assessment** — PR description includes tier classification for each file

#### Correctness

- [ ] **AT_DISPATCH covers all needed dtypes** — no silent dtype drop
  `aten/src/ATen/Dispatch.h:469 — "#define AT_DISPATCH_ALL_TYPES(TYPE, NAME, ...)"`
- [ ] **TensorIterator used correctly** (for elementwise ops)
  `aten/src/ATen/TensorIterator.h:248 — "struct TORCH_API TensorIteratorBase : public impl::MetaBase"`
- [ ] **No in-place mutation on leaf tensor with requires_grad=True**
  (see `.claude/skills/autograd/pitfalls/inplace_on_leaf.md`)
- [ ] **Meta kernel output shape matches forward**

#### Safety

- [ ] **No generated files edited** — nothing under `torch/csrc/autograd/generated/`, `build/`, or with `# @generated`
- [ ] **No Tier 1 files edited without explicit user confirmation** (from `blast-radius.md`)
- [ ] **Citations grep-validate** — `verify_answer.py` exits zero

#### Style

- [ ] `validated-at:` frontmatter if adding new skill/agent files
- [ ] Commit includes `Co-Authored-By: Claude <claude@anthropic.com>`
- [ ] No inline comments explaining what code does (only non-obvious WHY)

## Output Format

```markdown
## PR Review — <branch or PR#>
Date: <date>

### Completeness
- [PASS/FAIL/N/A] YAML schema: <details>
- [PASS/FAIL/N/A] CPU kernel: <details>
- [PASS/FAIL/N/A] Meta kernel: <details>
- [PASS/FAIL/N/A] OpInfo entry: <details>
- [PASS/FAIL/N/A] gradcheck: <details>
- [PASS/FAIL/N/A] torch.compile test: <details>
- [PASS/FAIL/N/A] Blast-radius assessment: <details>

### Correctness
- [PASS/FAIL] AT_DISPATCH macros: <details>
- [PASS/FAIL] TensorIterator: <details>
- [PASS/FAIL] No in-place leaf mutation: <details>
- [PASS/FAIL] Meta kernel shape: <details>

### Safety
- [PASS/FAIL] No generated files: <details>
- [PASS/FAIL] No unconfirmed Tier 1 edits: <details>
- [PASS/FAIL] Citations valid: verify_answer.py exit 0

### Overall: APPROVE | REQUEST_CHANGES
Blocking issues: <list, or "none">
Non-blocking suggestions: <list, or "none">
```

## Constraints
- Never run `pytest` or `python setup.py develop` — read and grep only.
- Every `[FAIL]` must include the file + line that failed, and a specific fix suggestion.
- If a criterion is not applicable (e.g., OpInfo for a non-op change), mark `N/A`.
