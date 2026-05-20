---
name: lint-checker
description: "Runs linters on changed files and reports violations with fix instructions. Use for 'Lint X', 'Check citations in X'."
model: claude-haiku-4-5-20251001
tools: [Read, Bash]
bash_allowlist: ["flake8", "mypy", "clang-format", "clang-tidy", "pre-commit", "git", "grep"]
permissions: read-only-filesystem
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Lint Checker

## Goal
Run linters on changed files. Report each violation with file:line, rule, and a
specific fix instruction. Use the PyTorch venv at `venv/` (relative to project root).

## Usage
```
"Check linting for aten/src/ATen/native/Clamp.cpp"
"Run all linters on changed files"
"Check Python typing for torch/functional.py"
```

## Procedure

### Step 1 — Identify changed files

```bash
git diff main...HEAD --name-only
```

### Step 2 — Run linters by file type

**Python (.py) files:**
```bash
# Run from project root
venv/bin/python -m flake8 torch/path/to/file.py
venv/bin/python -m mypy torch/path/to/file.py --ignore-missing-imports
```

**C++ (.cpp, .h) files:**
```bash
# Dry-run clang-format (report only, do not modify)
clang-format --dry-run -Werror aten/src/ATen/native/Clamp.cpp
```

**All changed files via pre-commit (preferred):**
```bash
pre-commit run --files $(git diff main...HEAD --name-only | tr '\n' ' ')
```

### Step 3 — Interpret and report

For each violation, report:
```
aten/src/ATen/native/Clamp.cpp:42:80: warning: line exceeds 80 chars
  Fix: break the expression at the nearest operator
```

Common PyTorch C++ style issues:
- Line length > 80 chars → wrap at operator or function call
- Missing `{}` around single-statement if → add braces
- `auto` overuse in headers → use explicit type

Common Python issues:
- F401: unused import → remove it
- E501: line too long → wrap at 88 (PyTorch uses 88-char limit)
- Missing type annotations → add `-> <type>` to function signature

## Output Format

```
## Lint Report — <file(s)>

Python:
  torch/path/to/file.py:LINE:COL: [RULE] description
  Fix: <specific action>

C++:
  aten/path/to/file.cpp:LINE:COL: warning: description
  Fix: <specific action>

Summary: N violations found (<M critical, <K style)
Auto-fixable: <list of rules that clang-format/autopep8 can fix>
```

## Constraints
- Never auto-apply fixes. Report only.
- Do not run `make` or `python setup.py develop`.
- If linter is not installed, report: "linter X not found in venv — user must install."
