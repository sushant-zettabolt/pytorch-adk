---
name: pr-review
description: "PyTorch PR review checklist: correctness, safety (generated/Tier 1 files), style, docs. Use when reviewing a PR or building a review checklist."
validated-at: 70d99e998b4
---

# PR Review Skill
## PR Review Checklist

### Correctness
- [ ] Does the op handle edge cases (empty tensor, 0-dim tensor, large shapes)?
- [ ] Is there a gradcheck test verifying the backward?
- [ ] Is there a Meta kernel for torch.compile compatibility?
- [ ] Are dtype/device combinations tested?

### Safety
- [ ] Does the PR edit any generated files? (Must be blocked)
- [ ] Does the PR touch Tier 1 files? (Requires Architecture Owner review)
- [ ] Does the PR change native_functions.yaml? (Requires thorough review)

### Style
- [ ] C++ code passes clang-format and clang-tidy?
- [ ] Python code passes flake8 and mypy?
- [ ] Commit message follows conventions?

### Documentation
- [ ] Is the operator documented in the Python API?
- [ ] Are deprecation notices added for removed functionality?

## Review Process
1. Check PR description for blast-radius assessment
2. Run `git diff main... -- aten/ torch/` to see all changed files
3. Classify each changed file by tier (see blast-radius.md)
4. Run eval golden tests: `python tools/adk/run_evals.py --agent pr-reviewer`

## Common Review Failures
- Missing Meta kernel → torch.compile breaks
- Missing gradcheck → backward correctness unverified
- Missing OpInfo entry → op not covered by unified test suite
- Edit to generated file → build system overwrites change silently
