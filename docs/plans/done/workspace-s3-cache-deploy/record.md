# workspace s3 cache deploy record

## Asked

Deploy half of the optional per-preset workspace S3 cache (user request 2026-10-25, GitLab-runner-style caches, deployed on rook-ceph, generic configuration): rook-ceph bucket and wiring in agents-helmfile, cache fields in the agents-web preset form, pinned builds, apply and a live smoke proving restore across sessions. Core is epic workspace-s3-cache. The README Description and Goals are empty; the scope is taken from the project brief and the task files.

## Shipped

All 6 tasks done. Epic review verdict: pass (2026-10-26). Merged: agents-web #11 (d81b219), agents-orchestrator #19 (ea1fac7), agents-helmfile #25 (2d65d0a). Superrepo pins 829849f. Live in the agents namespace: agents-orchestrator 0.1.0-main.ea1fac7 (rev 4), agents-web 0.1.0-main.d81b219, OBC agents-workspace-cache Bound, post-apply diff "No affected releases", smoke OK with a cache round trip (session B restored session A's marker; .logs/cache-smoke3.log). helmfile `mise run test`: 165 passed (review note).

## Tasks

Status, repo, verified head and points (planned/actual) are from the task files. The plan-execute return value was not provided, so the independent verifier head, red evidence, declined, cannotVerify and forwardMerged entries could not be read; rounds are "unknown". The shown head is the task file's verified_head. The `review` field is empty in every task file.

| Task | Repo | Status | Verified head | Points | Rounds | Verification tail |
|---|---|---|---|---|---|---|
| helmfile-cache-bucket | agents-helmfile | done | 8ebfff6 | 2/2 | unknown | unknown |
| web-preset-cache-fields | agents-web | done | 5c7f9d1 | 3/3 | unknown | unknown |
| smoke-workspace-cache | agents-helmfile | done | 9308871 | 2/2 | unknown | unknown |
| deploy-pin-workspace-cache | agents-helmfile | done | 9893b65 | 2/1 | unknown | unknown |
| cache-put-signs-content-type | agents-orchestrator | done | 9c8bb44 | 1/1 | unknown | unknown |
| apply-smoke-workspace-cache | agents-helmfile | done | 23054c0 | 1/3 | unknown | smoke log last line: "smoke: deleted schedule bf43b3cb-ac06-4a9c-8931-90d06a9138ba"; post-diff "No affected releases" |

cache-put-signs-content-type was added mid-epic (the fix for the RGW finding below). apply-smoke-workspace-cache took 3 points against 1 planned (54 min actual vs 4 expected) because of two failed smokes (.logs/cache-smoke.log and cache-smoke2.log end in "task failed"; smoke3 passed).

Approvals ledger: the epic dir has no approvals.json, so no ledger rows. The gate approval is in root MEMORY.md (2026-10-25, workspace-s3-cache entry, irreversible ops approved: rook-ceph bucket creation and live applies). No 2026-10-26 cache line was found in root MEMORY.md; the 2026-10-26 line is in code/agents-helmfile/MEMORY.md. Per-entry status: unknown.

## Rulings

- Quota in the raw OBC file: the bucket quota (maxSize 100G, 100000 objects) lives in the raw OBC manifest, in rook's documented G unit. Why: raw resources are not templated, and G is rook's documented form. Cost if wrong: an unenforced or misparsed quota; the epic security review confirmed the user quota is enforced at 100G / 100000 objects.
- Live presign proofs as a one-off probe: the 403 (PUT-presigned URL used for GET) and 404 (GET on a missing key) proofs were run once from the reconciler pod, not added as permanent smoke steps. Why: the pod already holds the S3 credentials; the probe prints no credential or URL and creates no object. Cost if wrong: a future regression of method scoping or missing-key status is not caught by the smoke.
- RGW Content-Type 403 fixed by signing Content-Type: RGW 20.2.4 rejected a presigned PUT carrying an unsigned Content-Type (AccessDenied, anonymous); the orchestrator now signs it (cache-put-signs-content-type, ea1fac7, PR #19). Why: the first smokes failed on it, and moto could not show it. Cost if wrong: cache saves fail with 403 on RGW and the save is skipped.
- Diagnosis-probe object verified and deleted: the 7-byte object left by the diagnosis probe was checked and deleted. Why: the bucket should hold only real cache archives. Cost if wrong: a stray object under a probe key, bounded by the quota.
- Orchestrator api restart gotcha: fixed by the services Secret checksum on the api pod template, delivered in the core epic (orch-services-secret-checksu, 2290dbb). Not repeated here.
- Pin takes the latest main containing both epics: webhook-event-filters also pins agents-web, so deploy-pin-workspace-cache pinned the latest main merge containing both.

## Discovered and blocked

- Open decision, unanswered: whether an unreadable archive should self-repair (start empty and overwrite). Today the save allow-list skips the save after any restore failure, so a corrupt or unreadable archive stays until deleted by hand. It was asked of the user and has no answer. Cleared by: the user. Until then the current behaviour (no self-repair) stands.
- RGW rejects an unsigned Content-Type on a presigned PUT (found by the first smoke): fixed by ea1fac7, not blocking.
- The core epic's two unproven items (presign scoping, 403 versus 404 on a missing key) are cleared by the probe: 403 and 404.
- Declined and cannotVerify entries: unknown (return value not provided).
- Security review: no medium-or-higher findings. The OBC Secret is used only by the reconciler; rgw is ClusterIP only; the namespace has no NetworkPolicy, so no new gap.

## Not pushed

All three PRs are merged (agents-web #11, agents-orchestrator #19, agents-helmfile #25) and the superrepo pin 829849f is committed on main. Whether the superrepo main is pushed: unknown; pushing stays with the user.

## Lessons routed to

- RGW rejects an unsigned Content-Type on a presigned PUT and moto does not: a unit test that the presigned PUT signs Content-Type (added in cache-put-signs-content-type); the live smoke round trip is the check against real RGW.
- Method scoping and missing-key status cannot be proven under moto: a judgement call for the deploy skill (prove them with a one-off pod probe at apply time), not a mechanical check.
- Quota in a templated versus raw file: a judgement call for the bucket task notes; a helmfile test asserting the OBC carries maxSize and maxObjects is possible.
