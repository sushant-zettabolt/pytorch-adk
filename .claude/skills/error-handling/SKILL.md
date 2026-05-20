---
name: error-handling
description: "ADK-EH01 protocol for multi-step orchestrators: four failure modes, canonical handoff block schema, hook enforcement. Use when building orchestrator agents or handling failed steps."
validated-at: 70d99e998b4
validated-by: phase-2-knowledge-layer
---

# Error-Handling Protocol Skill ⭐ (ADK-EH01)

## Purpose

All multi-step orchestrators (op-adder, adk-migrator, onboarding-guide) MUST implement this protocol. Without it, a failed step causes silent continuation with bad output or an unrecoverable crash with no recovery path.

The protocol consists of: four defined failure modes, a canonical handoff block schema, and a hook (`handoff-block-enforcer.py`, added in Phase 3) that parses blocks and stops the chain on `hard-stop`.

## Four Failure Modes

| Mode | Trigger | Behavior |
|---|---|---|
| **hard-stop** | `Status: failed` AND no fallback exists | Stop immediately. Surface full handoff block to user. Do not proceed. |
| **retry** | `Status: failed` AND retry instruction in step spec | Retry once with corrective instruction. If retry also fails → hard-stop. |
| **warn-continue** | `Status: failed` AND step is explicitly optional | Log failure in handoff block. Continue. Mark final output ⚠ partial. |
| **unknown** | Step produces no output block or malformed output | Hard-stop. Report: "Step N produced no parseable output. Manual intervention required." |

## Canonical Handoff Block Schema

Every orchestrator step transition MUST produce a block in exactly this format:

```markdown
## Step N output — <agent-name>
**Status:** passed | failed | partial
**Failure mode:** hard-stop | retry | warn-continue | unknown | none
**Key findings:**
- <bullet per finding>
**Artifacts produced:** <comma-separated paths, or "none">
**Errors:** <error text verbatim, or "none">
**Next step instruction:** <corrective note or "none">
```

## Rules (enforced by handoff-block-enforcer.py hook)

1. Every orchestrator agent file MUST declare the handoff block format for each step transition.
2. Scratch state is NEVER held only in Claude's context window — always written explicitly into the next prompt.
3. If `Status: failed` and `Failure mode: hard-stop` — the block enforcer hook exits non-zero, preventing the next step.
4. If `Status: failed` and `Failure mode: warn-continue` — execution continues but the final output is marked `⚠ partial`.
5. Silent continuation after failure is PROHIBITED.

## Usage in op-adder (7-step orchestrator)

| Step | Agent | Artifact | Failure mode if missing |
|---|---|---|---|
| 1 | kernel-writer | YAML entry | hard-stop (no kernel without schema) |
| 2 | kernel-writer | C++ impl | hard-stop |
| 3 | kernel-writer | Meta kernel | warn-continue (breaks compile/export, not eager) |
| 4 | test-writer | OpInfo entry | warn-continue |
| 5 | backward-checker | gradcheck PASS | hard-stop if gradcheck fails; warn-continue if skipped for non-differentiable op |
| 6 | compile-tester | torch.compile smoke test | warn-continue if CUDA not available |
| 7 | pr-author | PR description | warn-continue |

## Handoff Block Example (passing step)

```markdown
## Step 1 output — kernel-writer
**Status:** passed
**Failure mode:** none
**Key findings:**
- Added `aten::my_clamp(Tensor self, Scalar min, Scalar max) -> Tensor` to native_functions.yaml
- structured: True, structured_inherits: TensorIteratorBase
**Artifacts produced:** aten/src/ATen/native/native_functions.yaml
**Errors:** none
**Next step instruction:** none
```

## Handoff Block Example (hard-stop)

```markdown
## Step 5 output — backward-checker
**Status:** failed
**Failure mode:** hard-stop
**Key findings:**
- gradcheck failed: Jacobian mismatch at input index 0, max diff 0.04 > atol 1e-4
**Artifacts produced:** none
**Errors:** AssertionError: Jacobian mismatch...
**Next step instruction:** Review backward formula in ReluBackward0::apply. Check sign of gradient.
```
