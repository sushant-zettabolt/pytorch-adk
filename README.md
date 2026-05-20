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

## Agent routing

Claude routes automatically based on your request. Key agents:

| Ask Claude... | Agent invoked |
|---|---|
| "Where is X defined?" | `symbol-locator` |
| "Trace X from Python to kernel" | `call-tracer` |
| "Write a kernel for X" | `kernel-writer` |
| "Add op X end-to-end" | `op-adder` |
| "Check backward for X" | `backward-checker` |
| "Review this PR" | `pr-reviewer` |
| "Check torch.compile for X" | `compile-tester` |
| "Triage this issue" | `issue-triager` |

Full routing table is in `.claude/CLAUDE.md`.

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
