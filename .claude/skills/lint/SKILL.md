---
name: lint
description: "PyTorch linters: pre-commit, flake8, mypy, clang-format, clang-tidy. Use for questions about running linters or fixing lint failures."
validated-at: 70d99e998b4
---

# Lint Skill
## Linting Tools
PyTorch uses multiple linters enforced via `pre-commit` hooks:
- `flake8` — Python style
- `mypy` — Python type checking
- `clang-format` — C++ formatting
- `clang-tidy` — C++ static analysis
- `pylint` (subset) — additional Python checks

## Key Questions

**Q: How do you run all linters locally?**
A:
```bash
pre-commit run --all-files    # run all hooks on all files
pre-commit run flake8         # run only flake8
```

**Q: How do you run mypy on a module?**
A:
```bash
python -m mypy torch/distributed/ --ignore-missing-imports
```

**Q: How do you format C++ files?**
A:
```bash
clang-format -i aten/src/ATen/native/MyOp.cpp
```

**Q: What does `# noqa: E501` mean?**
A: Inline suppression for flake8 rule E501 (line too long). Use sparingly.

**Q: How are lint rules configured?**
A:
- Python: `.flake8`, `setup.cfg` `[mypy]` section
- C++: `.clang-format`, `.clang-tidy`

## Blast Radius
- `setup.cfg` — Tier 3 (lint config only)
- `.pre-commit-config.yaml` — Tier 2 (all CI lint checks)
