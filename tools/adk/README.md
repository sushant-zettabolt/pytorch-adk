# tools/adk — ADK Index and Eval Scripts

## Scripts

| Script | Purpose | Run |
|---|---|---|
| `build_index.py` | Build flat symbol index for any codebase | `python tools/adk/build_index.py` |
| `staleness-scanner.py` | Check citation staleness after a commit switch | `python tools/adk/staleness-scanner.py <old> <new>` |
| `run_evals.py` | Run golden-set agent eval harness | `python tools/adk/run_evals.py --agent <name>` |

## Quick Start

```bash
# Index the current repo
python tools/adk/build_index.py

# Index a different project
python tools/adk/build_index.py --root /path/to/other/project

# Skip C++ scanning (faster, Python only)
python tools/adk/build_index.py --skip-cpp

# Override root via env var
REPO_ROOT=/path/to/project python tools/adk/build_index.py
```

## Outputs (all in `.claude/index/`)

| File | Contains |
|---|---|
| `symbols.json` | Symbol name → {file, line, anchor, language} |
| `index_meta.json` | Build metadata + `built_at_commit` for staleness check |

## Index Staleness Check

Every navigation agent checks `index_meta.json` at startup:
```python
import json, subprocess
meta = json.load(open(".claude/index/index_meta.json"))
head = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
if meta["built_at_commit"] != head:
    print("WARNING: Index stale — run python tools/adk/build_index.py")
```

## How It Works

`build_index.py` does a single-pass AST/regex scan:

1. **Python** — walks all `.py` files (skipping `build/`, `generated`, `.git`, `venv`), extracts every `def` and `class` definition.
2. **C++** — walks all `.h`/`.hpp`/`.cpp` files, uses `ctags` if available, otherwise falls back to regex pattern matching for `class`, `struct`, and function declarations.

Results are merged into `symbols.json` (Python wins on name collision). Navigation agents (`symbol-locator`, `codebase-explorer`, `call-tracer`) load this file for O(1) symbol lookups.

## evals/ Directory

Golden test fixtures for the eval harness. Each subdirectory contains `.md` files.

Format per golden file:
```markdown
## Input
...

## Expected output
matcher: contains | exact | regex | llm-judge
...

## Rationale
...
```

Run: `python tools/adk/run_evals.py --agent symbol-locator`
