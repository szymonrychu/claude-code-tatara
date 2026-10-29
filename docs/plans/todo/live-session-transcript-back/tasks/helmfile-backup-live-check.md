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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
