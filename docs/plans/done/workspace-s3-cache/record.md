# workspace s3 cache record

## Asked

Optional per-preset workspace caching in S3, like GitLab runner caches: at session start the workspace archive is downloaded and unpacked, at session end the workdir is archived and uploaded under the same name. Key is a user slug or a pseudorandom preset-derived string. S3 configuration generic, deployed on rook-ceph. User request 2026-10-25: 'S3 based workspace caching similar to caching in gitlab runners ... Deploy using rook-ceph s3, but configuration must be generic ... Optionally user can provide cache slug, by default it's pseudorandom (preset derived) string.' This record covers the core epic only (agents-orchestrator, G1-G6); the deploy half is the epic workspace-s3-cache-deploy.

## Shipped

All 13 tasks done. Epic review verdict: pass (2026-10-26); G1-G6 delivered, G7 and G8 belong to workspace-s3-cache-deploy. Merged: agents-orchestrator PR #18 (747ca91), CI green on 2290dbb (lint, test, images, chart, e2e). Local full suite from the review: 935 passed.

Not yet live: the deploy half (rook-ceph bucket, helmfile wiring, agents-web form, live smoke) is workspace-s3-cache-deploy, in progress. Nothing of the cache runs in the agents namespace yet.

## Tasks

Status, repo, verified head and points (planned/actual) are from the task files (all `done`, all with a verified head). The plan-execute return value was not provided, so the independent verifier head, red evidence, declined, cannotVerify and forwardMerged entries could not be read; review rounds and verification tails are "unknown". The shown head is the task file's verified_head. All tasks are in agents-orchestrator.

| Task | Status | Verified head | Points | Rounds | Verification tail |
|---|---|---|---|---|---|
| cache-config | done | de8fe0a | 3/3 | unknown | unknown |
| cache-key-on-create | done | 2bf9fa9 | 3/3 | unknown | unknown |
| cache-key-reserved-prefix | done | 8d8b2c3 | 2/2 | unknown | unknown |
| cache-archive | done | 8dfe3f0 | 3/3 | unknown | unknown |
| cache-presign | done | 781151a | 3/3 | unknown | unknown |
| cache-transfer-cli | done | 53a14e9 | 3/3 | unknown | unknown |
| cache-job-render | done | 75baef2 | 3/3 | unknown | unknown |
| cache-restore-runner | done | bf58295 | 5/5 | unknown | unknown |
| cache-save-on-discard | done | 52b5a1a | 5/5 | unknown | unknown |
| cache-save-allowlist | done | 45c221c | 2/2 | unknown | unknown |
| cache-chart-values | done | d4d5d57 | 3/3 | unknown | unknown |
| cache-docs | done | 3015bc9 | 1/1 | unknown | unknown |
| orch-services-secret-checksu | done | 2290dbb | 1/1 | unknown | unknown |

Approvals ledger: the epic dir has no approvals.json, so no ledger rows. The gate approval is in root MEMORY.md (2026-10-25, user: 'Go'; workspace-s3-cache Q1 last-writer-wins, Q2 5 GiB cap keeps previous archive; irreversible ops approved: rook-ceph bucket creation and live applies). Per-entry status: unknown.

## Rulings

- Split into core and deploy: the epic holds only agents-orchestrator work (G1-G6); the rook-ceph bucket, helmfile wiring, agents-web form and live smoke (G7, G8) moved to workspace-s3-cache-deploy. Why: the deploy tasks need the merged and published orchestrator chart. Cost if wrong: a feature that is merged but not live; the grouping is the only change, scope is unchanged.
- botocore over boto3: presigning uses botocore (design D2), not the full boto3 client. Why: presigning is local and needs no transfer client; the task note sketches a boto3 client call, the design says botocore, the design wins. Cost if wrong: swapping the library later touches only the presign module. Whether boto3 was ever added as a dependency: unknown.
- Pack skips escaping symlinks: symlinks pointing outside the workdir are skipped on save and counted in `skipped_links` in the outcome line (MEMORY D11). Why: a link out of the workdir must not put foreign files in the archive, and failing the whole save would lose the cache. Cost if wrong: a workspace that relies on an escaping link restores without it, visible in `skipped_links`.
- Member-count cap dropped: a review medium finding (no cap on archive members) was dropped (cache-archive note, 2026-10-25). Why: archives come only from this session's own save and unpack onto the same session PVC, so a member flood is no more than the agent could create directly. Cost if wrong: a key shared across sessions lets one session's flood reach the next; accepted as same-session blast radius (security review low finding).
- No TTL on the cache Jobs: the restore and save Jobs have no ttlSecondsAfterFinished; the runner reads the outcome from the pod log and deletes the Job itself, as the init Job does (design D1). Why: a TTL could remove the Job before the reconciler read its outcome. Cost if wrong: a Job left behind when the reconciler is down stays until it returns.
- Reserved `preset-` prefix, and a preset copy drops the derived key: a user key cannot start with `preset-`, and copying a preset does not carry the source's derived key (cache-key-reserved-prefix, 4c83e12 and 8d8b2c3). Why: security review medium, cache-key spoofing - a user could name a key equal to another preset's derived key and read or overwrite its archive. Cost if wrong: keys already stored with that prefix are refused; none exist, the feature was not live.
- Save allow-list: the save runs only after the restore ended `restored` or `miss`; every other state or reason skips it (cache-save-allowlist, 45c221c, MEMORY D11). Why: epic review medium - the deny-list missed `exit <code>`, `bad_output` and `no_cache_key`, so an OOM-killed restore could leave a partial workdir that a save uploaded over a good archive. Cost if wrong: a corrupt archive is never replaced by a save; it is fixed by deleting the object by hand.
- CACHE_VERIFY_TLS passed to the Job: the Job env carries `CACHE_VERIFY_TLS` from `ORCH_CACHE_S3_VERIFY_TLS` (default true). Why: the presigned URL is fetched by the Job pod, so a private-CA or self-signed endpoint needs the flag there too. Cost if wrong: a Job against a private CA fails TLS, or verification is off where it should be on.
- Services Secret checksum: orch-services-secret-checksu (2290dbb) adds a checksum of the services Secret to the api pod template. Why: found during the epic review - the orchestrator api did not reload the services Secret on change. Cost if wrong: Secret changes need a manual restart of the api.
- Superrepo pointer for the moved submodule was stale until 2c2219c: the submodule moved to code/agents-orchestrator was not initialized in the main checkout, so earlier superrepo pins skipped it; 2c2219c pinned it at 747ca91. Cost if wrong: the superrepo pointed at a pre-cache commit; fixed.
- Bucket total bound moved to deploy: security review medium (no bound on bucket total) moved to workspace-s3-cache-deploy helmfile-cache-bucket as a quota. Cost if wrong: unbounded bucket growth until that task lands.

## Discovered and blocked

- Live S3 behaviour unproven: Moto does not enforce SigV4, so single-method and single-object scoping of the presigned URLs is unproven against real RGW (cache-presign note). Cleared by the live smoke in workspace-s3-cache-deploy.
- 403 versus 404 on a missing key without ListBucket: a 403 would be `download_failed` and skip the save forever (epic review cannotVerify). Cleared by the live smoke in workspace-s3-cache-deploy.
- DB-backed tests (test_api_cache and others) timed out at fixture setup in the review sandbox (no Postgres), so the reviewer did not run them; PR #18 CI (e2e green) and the 935-pass local run cover them. The 935 run's environment: unknown.
- Bucket quota: owned by workspace-s3-cache-deploy.
- Low findings accepted: URL expiry is timeout+600 s by design; no member-count cap.
- Not verifiable by me: nothing else open.

## Not pushed

Everything is pushed: agents-orchestrator PR #18 is merged (747ca91) and the superrepo pin 2c2219c is committed on main. Whether the superrepo main is pushed: unknown; pushing it stays with the user.

## Lessons routed to

- The save skip rule was a deny-list that missed restore failure reasons: a unit test that enumerates every restore state and reason and asserts the save runs only for `restored` and `miss` (added in cache-save-allowlist).
- Cache-key spoofing through a user key equal to a derived key: a test that rejects a user key with the `preset-` prefix and that a preset copy drops the derived key (added in cache-key-reserved-prefix).
- The api did not reload the services Secret: a chart test (helm template) asserting every Secret mounted or read by a Deployment has a checksum annotation on its pod template (a chart lint to add).
- Presign scoping cannot be proven under Moto: a judgement call for the deploy skill and test notes (prove single-method scoping in the live smoke), not a mechanical check.
- The submodule pin skipped an uninitialized moved submodule: a judgement call for the close or rename skill (init submodules before pinning); a check that `git submodule status` shows no leading `-` before a pin commit is possible but not added.
