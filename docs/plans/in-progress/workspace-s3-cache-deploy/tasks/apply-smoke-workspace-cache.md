---
title: apply smoke workspace cache
status: in-progress
repo: agents-helmfile
value: the workspace cache is live on rook-ceph and proven by the smoke
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-workspace-cache, helmfile-cache-bucket, smoke-workspace-cache]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 670370
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


Orchestrator ruling 2026-10-26 (the core reviews could not prove these against moto): after the apply, run a one-off read-only probe from inside the reconciler pod, which already holds the S3 credentials, without printing any credential or URL. (1) Presign a PUT URL for a throwaway key `probe-<random>` with the app's own presign and send a GET with it: expect 403 (method is part of the signature). (2) Presign a GET for that key, which does not exist: expect 404, not 403, so a first restore is a cache miss. Run it with `kubectl exec deploy/agents-orchestrator-reconciler -- python -c ...`. No object is created. Quote both status codes in the task notes; any other result stops the task blocked.

## Acceptance conditions

- AC1: the bucket claim is bound [evidence: command:kubectl -n agents get obc agents-workspace-cache -o jsonpath='{.status.phase}' | grep -qx Bound]
- AC2: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC3: the smoke passes against the live orchestrator, including the workspace cache check [evidence: command:mise run smoke]
- AC4: MEMORY.md records the applied versions, the bucket and the smoke result [evidence: command:grep -q "agents-workspace-cache" MEMORY.md && grep -q "0.1.0-main" MEMORY.md]
- AC5: the pre-apply diff showed only the expected changes [evidence: judgement:the diff output quoted in the task notes]
- AC-probe: a presigned PUT URL is refused for GET (403) and a GET on a missing key returns 404 [evidence: judgement:the task notes quote both status codes from the one-off reconciler-pod probe]

## Files

- `MEMORY.md`

## Interfaces

See the Requirement; no new cross-repo contract.

## Expected outcome

Every acceptance condition holds on the committed HEAD.

## Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

## Notes

- See the Requirement and the epic design.md.

- 2026-10-26 amended: live presign proofs as a one-off probe instead of permanent smoke steps
