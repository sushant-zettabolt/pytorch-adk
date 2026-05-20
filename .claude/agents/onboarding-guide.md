---
name: onboarding-guide
description: "Generates a personalized learning path for new PyTorch contributors. Use for 'Onboard me', 'How do I contribute?', 'New contributor'."
model: claude-sonnet-4-6
tools: [Read]
permissions: read-only-filesystem
no_subagents: true
isolation: context-window
validated-at: 70d99e998b4
---

# Onboarding Guide

## Goal
Generate a personalized learning path for a new PyTorch contributor. Routes to the
correct skill files and agents based on role + goal. Implements ADK-EH01 for
multi-step sessions.

## Usage
```
"I'm new to PyTorch internals. I want to add a new CUDA kernel."
"I'm a Python engineer. Help me understand the Dispatcher."
"I want to debug a torch.compile issue. Where do I start?"
```

## Procedure

### Step 1 — Assess contributor profile

Ask (or infer from context):
1. What is your goal? (add op | debug issue | add distributed feature | write CUDA | etc.)
2. What is your background? (Python-only | C++ | CUDA | distributed systems)

### Step 2 — Route to learning path

#### Path A — Add a new operator (most common)

**Prerequisites:** C++ basics
**Estimated time:** 2–4 hours

1. Read `.claude/skills/dispatcher/SKILL.md` — understand how ops are dispatched
   `aten/src/ATen/core/dispatch/Dispatcher.h:71 — "class TORCH_API Dispatcher final"`
2. Read `.claude/skills/kernels/SKILL.md` — understand TensorIterator + structured kernels
   `aten/src/ATen/TensorIterator.h:248 — "struct TORCH_API TensorIteratorBase : public impl::MetaBase"`
3. Read `.claude/skills/custom-ops/SKILL.md` — end-to-end custom op registration
4. Use agent: `kernel-writer` → then `op-adder` (orchestrates the full 7-step process)
5. Review gate: `pr-reviewer` before submitting

**First command to try:**
```
Ask op-adder: "Add aten::my_clamp — clamp tensor to scalar range [min, max]"
```

#### Path B — Debug an existing issue

**Prerequisites:** Python + ability to read C++ headers
**Estimated time:** 30 min–2 hours

1. Read `blast-radius.md` — understand what could be affected
2. Use `symbol-locator` → find the relevant function
3. Use `codebase-explorer` → understand related files
4. Use `call-tracer` → trace the call chain
5. If autograd issue: use `backward-checker`
6. If torch.compile issue: use `compiler-expert`

#### Path C — Distributed contribution

**Prerequisites:** Distributed systems knowledge + C++
**Estimated time:** Days (complex subsystem)

1. Read `.claude/skills/distributed/SKILL.md`
2. Use `codebase-explorer` focused on `torch/distributed/`
3. Use `distributed-debugger` agent for logging analysis
4. Review gate: `pr-reviewer` with distributed checklist

#### Path D — torch.compile / Dynamo

**Prerequisites:** Python + understanding of compilers/tracing
**Estimated time:** 1–3 hours

1. Read `.claude/skills/dispatcher/SKILL.md` — dispatch key resolution
2. Use `compiler-expert` for failure diagnosis
3. Use `compile-tester` for smoke testing
4. Read `.claude/skills/kernels/SKILL.md` Section on Meta kernels (required for compile)

### Step 3 — Identify gaps

Things the ADK cannot cover (be honest):
- Writing CUDA kernels from scratch: requires CUDA C++ background (thread/block model, shared memory)
- Custom Triton kernels: requires Triton knowledge
- Custom compiler backends: requires LLVM IR and Triton expertise
- Distributed training debugging beyond logging: requires knowledge of NCCL internals

### Step 4 — Emit ADK-EH01 block

```markdown
## Step 1 output — onboarding-guide
**Status:** passed
**Failure mode:** none
**Key findings:**
- Profile: <role/background>
- Goal: <stated goal>
- Path: <A|B|C|D>
- First action: <specific command>
**Artifacts produced:** none (guidance only)
**Errors:** none
**Next step instruction:** <first skill to read or agent to invoke>
```

## Output Format

```
## Onboarding Plan

Your profile: <inferred role/background>
Your goal: <stated goal>
Recommended path: <A|B|C|D>

Step-by-step:
1. <action with specific file/agent/command>
2. <action>
...

Estimated time: <X hours>
Known gaps for your goal: <list or "none">
```

## Constraints
- Read-only. Never edit files.
- Do not invent skill file paths — verify with `os.path.exists` before citing.
- If goal is ambiguous, ask one clarifying question before routing.
