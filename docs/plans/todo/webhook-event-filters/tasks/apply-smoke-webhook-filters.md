---
title: apply smoke webhook filters
status: todo
repo: agents-helmfile
value: endpoint filters are live and proven by the smoke
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-webhook-filters, smoke-webhook-filters]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# apply smoke webhook filters

## Requirement

Apply to the live `agents` namespace and prove it (design D9; brief: "The orchestrator (main session) runs `mise run apply`; never put apply in AC evidence."). Paths are in code/agents-helmfile.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: agents-webhook chart version and image tag, the removed `WEBHOOK_ALLOWED_AUTHORS` env entry, agents-web chart version and image tag. Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator (main session, never a subagent): `mise run apply` in code/agents-helmfile; a failing apply is not retried blindly: read the helm error and report it with its tail.
- After the apply, implementer: `mise run diff` again (no drift) and `mise run smoke` (exit 0, including the filter checks); `MEMORY.md`: a dated line: applied agents-webhook `0.1.0-main.<sha7>` (endpoint filters, migration 0004) and agents-web `0.1.0-main.<sha7>` (filters UI); `WEBHOOK_ALLOWED_AUTHORS` removed; smoke green (quote its last log line).
- No other file changes.

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the webhook filter checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q 'filters' MEMORY.md && grep -q 'smoke' MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]

## Files

- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
