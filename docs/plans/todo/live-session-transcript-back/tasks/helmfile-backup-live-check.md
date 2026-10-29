---
title: helmfile backup live check
status: todo
repo: agents-helmfile
value: Live sessions are proven backed up to S3 after the deploy
files: [MEMORY.md]
verify: "mise run lint && grep -q 'live transcript backup live check' MEMORY.md"
depends_on: [helmfile-backup-pins]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1901552
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile backup live check

## Requirement

User request (mx-34 #234, 2026-10-28, relaying the user's priorities), verbatim: "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." Origin (mx-34 #232), verbatim: "there's no backup trigger for a live session (last_transcripts_backup=null)".

README Goal G5, verbatim: "released and deployed (orchestrator image, web image, helmfile pins), and proven live: a running session's transcripts object appears in S3 with a recent `last_transcripts_backup`."

Design D8 (the live check), verbatim: "Live check: after the apply, a running session gets a `sessions_backup` record `saved` and the object's LastModified in S3 is recent (HEAD with the reconciler's credentials is not available to agents; the check reads `status.cache` and the API field) (my call)."

Design D8 planner detail (2026-10-29, open question Q7 planned on its recommended answer), verbatim: "this epic's orchestrator and web pins are the first to deploy its changes too, including its copy migration of every pre-epic session at the first converge [...] The live check therefore also reads each live session's `status.cache.migration`. Apply order: orchestrator first, then web (the web reads the new required `BackupRun.kind`). The apply runs under the deploy Lease `agents/agents-helmfile-apply` (user decision)."

User decision, verbatim: "agents-helmfile (pins plus a live check after the apply under the deploy lease: Lease agents/agents-helmfile-apply created with kubectl create -f, holderIdentity, acquireTime, leaseDurationSeconds 3600; stale after 60 min, message the holder via the superleader before deleting; delete only your own; kubeconfig from the pod SA, context in-cluster-sa)".

Live applies are run by the orchestrator session only, never by a subagent. Steps, after the agents-helmfile PR merged, in `code/agents-helmfile` on `main`, least destructive first:
1. Claim the deploy Lease: `kubectl --context in-cluster-sa -n agents create -f <lease.yaml>` for Lease `agents-helmfile-apply` with `holderIdentity` (the session's own ccw address), `acquireTime` (now) and `leaseDurationSeconds: 3600`. If it already exists: an `acquireTime` under 60 minutes old means wait; a stale one (60 minutes or more) means message its holder via the superleader first and delete it only after that; never delete a Lease that is not your own otherwise.
2. Check that the pinned orchestrator and web image tags and chart versions exist in Harbor.
3. `mise run diff` read in full: only the agents-orchestrator and agents-web chart versions and image tags change; anything else stops the task (Lease released).
4. Write a handoff checkpoint naming the remaining steps before the apply (the apply may roll agent pods, the deployer's included).
5. `mise run apply -- --selector name=agents-orchestrator`, then `mise run apply -- --selector name=agents-web` (orchestrator first).
6. `mise run diff` shows no pending change; `mise run smoke` green.
7. Live check, read-only: each live session's `status.cache.migration` (decouple copy migration: `done`, or `failed` with its reason); a running session with a completed turn gets `status.cache.sessions_backup` `saved` with `last_saved`, and its API `backup.last_transcripts_backup` has `kind` `live` and a `finished_at` after the apply; that session's agent pods kept their uids through the backup (no pause, scale or restart); no `agent-<slug>-sessions-save` Job was created for a live session.
8. Delete your own Lease.
9. MEMORY.md entry containing the words `live transcript backup live check`, dated, with the applied orchestrator and web charts and images, the step 7 session slug, record and API values, and the migration outcomes.

## Acceptance conditions

- AC1: (orchestrator session) the deploy Lease agents/agents-helmfile-apply was created with this session as holderIdentity before the apply and deleted by it after the live check, and no other holder's Lease was deleted without messaging the holder via the superleader [evidence: judgement:orchestrator quotes the Lease holderIdentity, acquireTime and the delete in the task Notes]
- AC2: (orchestrator session) the pinned orchestrator and web image tags and chart versions exist in Harbor before the apply, and the pre-apply diff showed only those pins [evidence: judgement:orchestrator records the registry check and the diff summary in the task Notes]
- AC3: after the applies helmfile reports no pending change [evidence: command:mise run diff]
- AC4: the smoke passes against the applied release [evidence: command:mise run smoke]
- AC5: (orchestrator session) a running session has status.cache.sessions_backup saved with last_saved, its API backup.last_transcripts_backup has kind live and a finished_at after the apply, and its agent pods kept their uids [evidence: judgement:orchestrator quotes the session slug, the status.cache.sessions_backup record, the API field and the pod uids before and after in the task Notes]
- AC6: (orchestrator session) each live session's status.cache.migration outcome is recorded [evidence: judgement:orchestrator quotes each live session's migration record in the task Notes]
- AC7: MEMORY.md records the live check and the applied versions [evidence: command:grep -q "live transcript backup live check" MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

- None new; uses `kubectl --context in-cluster-sa` (kubeconfig from the pod service account), `mise run diff`, `mise run apply`, `mise run smoke`, and the public orchestrator API (port-forward as the smoke does) for `status.cache` and `backup`.
- Lease manifest: `apiVersion: coordination.k8s.io/v1`, `kind: Lease`, `metadata: {name: agents-helmfile-apply, namespace: agents}`, `spec: {holderIdentity: <own ccw address>, acquireTime: <now, RFC 3339 micro>, leaseDurationSeconds: 3600}`, written under the workbench `.scratchpad`.

## Expected outcome

The orchestrator and web releases of this epic run live; a running session's Claude transcripts have a fresh live backup in S3, visible as `kind: live` in the API; the decouple migration outcome of each live session is on record; the deploy Lease is released.

## Steps

- Orchestrator session only: steps 1-9 of the Requirement, in order; stop at step 3 if the diff shows more than the pins (release the Lease first).
- Write the handoff checkpoint (step 4) before the apply; after a roll, resume from it.
- Record each result in the task Notes as it happens (Lease holder and times, Harbor check, diff summary, smoke tail, the step 7 records and pod uids), then the MEMORY.md entry; commit it through the agents-helmfile PR flow; `mise run lint`; expect exit 0.

## Notes

- Never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run.
- The first live backup runs within a reconcile tick for a session with a completed turn and no backup record, so step 7 needs no 30-minute wait; if no running session has a completed turn, send one short read-only message to a session first and record it.
- Q7 is open; the plan follows its recommended answer (the decouple changes deploy here). A "no" adds a decouple-only deploy before this one.
- Recurring retro: live apply and proof tasks run several times their seed; budget for more than one attempt. A defect found live becomes a new task, never a hand fix.
- `gh` must be authenticated in the deploying pod for check-pins.
