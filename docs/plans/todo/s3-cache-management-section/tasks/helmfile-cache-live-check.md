---
title: helmfile cache live check
status: todo
repo: agents-helmfile
value: "The Cache section is proven live: it lists the bucket and deletes one disposable object"
files: [MEMORY.md]
verify: "mise run lint && grep -q 's3 cache section live check' MEMORY.md"
depends_on: [helmfile-cache-pins]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1919629
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile cache live check

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G5, verbatim: "a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object."

Design D9 (Deploy and live check), verbatim: "Release orchestrator and web, pin in agents-helmfile with the quota values, apply under the deploy lease; the live check lists the bucket in the section and deletes one disposable object created for the check (a smoke object, never a session's cache) (my call)."

User decision, verbatim: "Repos: agents-orchestrator, agents-web, agents-helmfile (quota values, image pins, and a live check after the apply under the deploy lease Lease agents/agents-helmfile-apply: kubectl create -f, holderIdentity, acquireTime, leaseDurationSeconds 3600; stale after 60 min, message the holder via the superleader before deleting; delete only your own; kubeconfig from the pod SA, context in-cluster-sa). The live check deletes only one disposable object it created, never a session's cache."

Live applies are run by the orchestrator session only, never by a subagent. Steps, after the agents-helmfile PR of helmfile-cache-pins merged, in `code/agents-helmfile` on `main`, least destructive first:
1. Claim the deploy Lease: `kubectl --context in-cluster-sa -n agents create -f <lease.yaml>` for Lease `agents-helmfile-apply` with `holderIdentity` (the session's own ccw address), `acquireTime` (now) and `leaseDurationSeconds: 3600`. If it already exists: an `acquireTime` under 60 minutes old means wait; a stale one (60 minutes or more) means message its holder via the superleader first and delete it only after that; never delete a Lease that is not your own otherwise.
2. Check that the pinned orchestrator and web image tags and chart versions exist in Harbor.
3. Render every release with `helmfile template` and read `mise run diff` in full: only the agents-orchestrator and agents-web chart versions and image tags change, plus the two `ORCH_CACHE_QUOTA_*` settings in the orchestrator settings ConfigMap and the settings checksum annotation that follows them; anything else stops the task (Lease released).
4. Write a handoff checkpoint naming the remaining steps before the apply (the apply may roll agent pods, the deployer's included).
5. `mise run apply -- --selector name=agents-orchestrator`, then `mise run apply -- --selector name=agents-web` (orchestrator first).
6. `mise run diff` shows no pending change; `mise run smoke` green.
7. Live check, through the orchestrator API on the web port (port-forward as the smoke does):
   a. `GET /api/v1/cache`: `available` true and `quota` `{bytes: 100000000000, objects: 100000}`; `POST /api/v1/cache/refresh`, poll the request to `done`; `listed_at` is after the apply; record the listing's object and byte totals and the reconciler's logged pass duration.
   b. `GET /api/v1/cache/objects`: each live session's workspace object reads `in_use` with its slug.
   c. Advisory refusal, nothing deleted: `POST /api/v1/cache/deletions` for one `in_use` object answers 409 `in_use`; after a refresh the object is still listed.
   d. The disposable object: create a session `smoke-cache-del-<ts>` with a raw spec whose literal cache key is `smoke-cache-del-<ts>`, wait until its restore ran (`miss`), discard it and wait until its row is purged; refresh; the object `smoke-cache-del-<ts>.tar.zst` is listed with class `saved`; `POST /api/v1/cache/deletions` with its object and etag; poll the request to `done`; after a refresh the object is no longer listed. This is the only object deleted.
   e. The web serves the release with the Cache section (the served bundle holds the `/cache/objects` path).
8. Delete your own Lease.
9. MEMORY.md entry containing the words `s3 cache section live check`, dated, with the applied orchestrator and web charts and images, the step 7 values (quota, totals, pass duration, the 409 answer, the disposable object's request id and outcome).

## Acceptance conditions

- AC1: (orchestrator session) the deploy Lease agents/agents-helmfile-apply was created with this session as holderIdentity before the apply and deleted by it after the live check, and no other holder's Lease was deleted without messaging the holder via the superleader [evidence: judgement:orchestrator quotes the Lease holderIdentity, acquireTime and the delete in the task Notes]
- AC2: (orchestrator session) the pinned orchestrator and web image tags and chart versions exist in Harbor before the apply, and the pre-apply diff showed only the pins and the quota settings [evidence: judgement:orchestrator records the registry check and the diff summary in the task Notes]
- AC3: after the applies helmfile reports no pending change [evidence: command:mise run diff]
- AC4: the smoke passes against the applied release [evidence: command:mise run smoke]
- AC5: (orchestrator session) GET /api/v1/cache reports available true, the quota 100000000000 bytes and 100000 objects, and a listing done after the apply [evidence: judgement:orchestrator quotes the GET /api/v1/cache body and the refresh request in the task Notes]
- AC6: (orchestrator session) live sessions' objects read in_use with their slugs, and a deletion of one answers 409 in_use and leaves it listed [evidence: judgement:orchestrator quotes the objects page and the 409 body in the task Notes]
- AC7: (orchestrator session) the disposable object smoke-cache-del-<ts>.tar.zst created for the check was listed as saved, its delete request ended done and it is no longer listed; no other object was deleted [evidence: judgement:orchestrator quotes the request, its final status and the listings before and after in the task Notes]
- AC8: MEMORY.md records the live check and the applied versions [evidence: command:grep -q "s3 cache section live check" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

- None new; uses `kubectl --context in-cluster-sa` (kubeconfig from the pod service account), `helmfile template`, `mise run diff`, `mise run apply`, `mise run smoke`, and the orchestrator API on the web port (port-forward as `scripts/smoke.sh` does).
- Lease manifest: `apiVersion: coordination.k8s.io/v1`, `kind: Lease`, `metadata: {name: agents-helmfile-apply, namespace: agents}`, `spec: {holderIdentity: <own ccw address>, acquireTime: <now, RFC 3339 micro>, leaseDurationSeconds: 3600}`, written under the workbench `.scratchpad`.

## Expected outcome

The orchestrator and web releases of this epic run live with the quota set; the Cache section lists the bucket, refuses an in-use object and deleted exactly one disposable object created for the check; the deploy Lease is released.

## Steps

- Orchestrator session only: steps 1-9 of the Requirement, in order; stop at step 3 if the diff shows more than allowed (release the Lease first).
- Write the handoff checkpoint (step 4) before the apply; after a roll, resume from it.
- Record each result in the task Notes as it happens (Lease holder and times, Harbor check, diff summary, smoke tail, the step 7 bodies), then the MEMORY.md entry; commit it through the agents-helmfile PR flow; `mise run lint`; expect exit 0.

## Notes

- Never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run, and a builder subagent stops after helmfile-cache-pins.
- (my call) The disposable object comes through the product path (a session with a unique literal cache key, discarded so its save writes the object and its row is purged), because agents hold no S3 credential. Its discard also writes `sessions/smoke-cache-del-<ts>.tar.zst`; that transcripts object stays, like the existing `sessions/smoke-*` objects, because the user decision allows deleting only one object.
- Never delete a session's cache, and never send a deletion for any object other than the disposable one; the step 7c request must be refused, so pick an object `GET /api/v1/cache/objects` reports `in_use`.
- Assumption to confirm (design): the OBC key has DeleteObject. If the disposable delete ends `failed` with a 403, stop: that is a defect for a new task (bucket policy in agents-helmfile), never a hand fix.
- Retro (matrix-connector-agent-initi, recurring): a live apply surfaced defects tests missed; render every release with `helmfile template` and read the full diff before the apply. Live apply and proof tasks run several times their seed; a defect found live becomes a new task.
- `gh` must be authenticated in the deploying pod for check-pins.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- (my call) Builder check Q6: confirmed orchestrator-session only; a builder stops after helmfile-cache-pins and never takes this task.
