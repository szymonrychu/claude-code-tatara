---
title: apply smoke workspace cache
status: todo
repo: agents-helmfile
value: the workspace cache is live on rook-ceph and proven by the smoke
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-workspace-cache, helmfile-cache-bucket, smoke-workspace-cache]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# apply smoke workspace cache

## Requirement

Apply the pinned releases and the bucket claim to the live `agents` namespace and prove the cache with the smoke (design D9; user decision: deployed on rook-ceph). Paths are in code/agents-helmfile. Runs only after tasks deploy-pin-workspace-cache, helmfile-cache-bucket and smoke-workspace-cache are done. The orchestrator runs `mise run apply` itself (live applies are refused in subagents); the apply is never acceptance evidence.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: the agents-orchestrator chart version, image tag and cache settings; the agents-web chart version and image tag; the new ObjectBucketClaim `agents-workspace-cache` (raw/ drift). Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator: `mise run apply` (lint, test and the kube-context guard run first; never bypass the guard or set EXPECTED_KUBE_CONTEXT). A failing apply is not retried blindly: read the helm error and report its tail.
- After the apply, implementer: `kubectl -n agents get obc agents-workspace-cache` shows `Bound`; `mise run diff` exits 0 (no drift); `mise run smoke` exits 0 including the workspace cache check.
- `MEMORY.md`: a dated line: applied agents-orchestrator `0.1.0-main.<sha7>` and agents-web `0.1.0-main.<sha7>` with the workspace cache, bucket `agents-workspace-cache` on rook-ceph, smoke green (quote its last log line).
- No other file changes.

## Acceptance conditions

- AC1: the bucket claim is bound [evidence: command:kubectl -n agents get obc agents-workspace-cache -o jsonpath='{.status.phase}' | grep -qx Bound]
- AC2: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC3: the smoke passes against the live orchestrator, including the workspace cache check [evidence: command:mise run smoke]
- AC4: MEMORY.md records the applied versions, the bucket and the smoke result [evidence: command:grep -q "agents-workspace-cache" MEMORY.md && grep -q "0.1.0-main" MEMORY.md]
- AC5: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]

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
