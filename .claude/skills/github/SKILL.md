---
name: github
description: "PyTorch GitHub workflow: PR lifecycle, gh commands, CI systems. Use for questions about contributing PRs to pytorch/pytorch."
validated-at: 70d99e998b4
---

# GitHub Skill
## PyTorch GitHub Workflow

**Repository:** `pytorch/pytorch` on GitHub

## PR Lifecycle
1. Fork or branch from `main`
2. Push branch: `git push origin feature/my-op`
3. Open PR: `gh pr create --title "..." --body "..."`
4. CI runs automatically (Linux, Windows, CUDA builds)
5. Reviewers assigned via `CODEOWNERS`
6. Merge requires 1+ approvals + all CI green

## Key Commands
```bash
gh pr create --title "Add aten::my_op" --body "$(cat PR_DESCRIPTION.md)"
gh pr view 12345
gh pr checks 12345
gh issue create --title "Bug: ..." --label "bug"
gh issue list --label "triaged"
```

## CI Systems
- **Linux CI**: `pytorch-linux-xenial-py3-gcc5.4` (build + test)
- **CUDA CI**: `pytorch-linux-xenial-cuda10.2-cudnn7` (GPU tests)
- **Windows CI**: `pytorch-win-vs2019-cuda10.1`
- **macOS CI**: `pytorch-macos-10.15-py3` (CPU only)

## CODEOWNERS Routing
- `aten/src/ATen/native/` → Core team
- `torch/_dynamo/` → Compiler team
- `torch/distributed/` → Distributed team
- `torch/csrc/cuda/` → CUDA team

## PR Description Template
```markdown
## Summary
[What does this PR do?]

## Test Plan
[How was this tested?]

## Blast Radius
[Which Tier 1/2/3 files were changed?]
```
