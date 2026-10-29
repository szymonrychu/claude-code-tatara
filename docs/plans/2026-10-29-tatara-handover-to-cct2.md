# Handover: claude-code-tatara to cct2 (2026-10-29 ~15:45Z)

The user is decommissioning claude-code-tatara (mx-34 #437, user 15:33Z: "Ask tatara to move all epics to cct and go idle"). Every tatara epic now belongs to cct2. Superrepo main carries this note and the submodule pins.

## Held resources

- Lease `agents-helmfile-apply`: not held (NotFound at 15:4xZ).
- Orchestrator file locks: none.
- Cluster: nothing half-applied. The last apply was hive-decoupling's final deploy (orchestrator df2b80e, plugins v0.4.0, helmfile 8114b16), smoke OK, lease released 15:1xZ. No apply has run since.
- Live versions: orchestrator df2b80e, connector c98c501, web 6ea3457, agent image 0.3.3 (per helmfile main; cct2's wrapper v0.4.1 is cct2's to deploy), plugins v0.4.0.
- In-pod helpers (kube context from the SA, Harbor helm login): `.scratchpad/session-loss/handoff-after-deploy.md` "Deploy gotchas" in the tatara workdir; rebuild them in your own pod.

## hive-decoupling (docs/plans/in-progress/hive-decoupling, stage build)

- Done (16/17): orch-activity-route, orch-hive-feed-removal, orch-drop-feed-cursor, helmfile-orch-slice1-pin, orch-handover-due-note, orch-handover-outcome-note, helmfile-orch-slice2-pin, plugin-activity-tool, plugins-release-0-4-0, orch-plugins-pin-0-4-0, orch-hive-tools-activity, orch-e2e-hive-activity, helmfile-smoke-activity, helmfile-deploy-pin, orch-flaky-push-after-decisi, helmfile-apply-live-proof.
- The live handover proof is DONE: evidence in tatara `.logs/hive-decoupling-deploy-2026-10-29/live-proof.md`; its MEMORY.md entry is agents-helmfile PR #53, reviewed pass and merged c786dc4.
- Open (1/17): helmfile-orch-flaky-fix-pin (todo, sonnet, 1 point). It pins agents-orchestrator to be554bb (PR #37 merge, flaky-test fix fe2c623, no migration), as mx-34 #430 relayed: "Tatara should deploy be554bb on its own". Nothing is written yet: no branch or PR. The task's Steps name branch `orch-flaky-fix-pin`, from origin/main. be554bb's main CI was still in progress at 15:30Z; wait for it to go green, including chart-publish. Then merge the pin and do an orchestrator-only deploy: lease, `mise run diff -- --selector name=agents-orchestrator` (image only), apply, `mise run smoke`, then release the lease.
- Next after that task: phases 5-7. Run start-review on the whole diff, then scope-auditor, then security-researcher. Then `ticket.py stage hive-decoupling review`, `review --verdict ...`, `move done`, `reap`, then record-writer and retro-writer. Run notes: tatara `.scratchpad/hive-decoupling/run-notes.md`.
- Open gates: none pending. The build ran on design.md open questions Q1-Q8 at their recommended answers, under the standing approval: recommended option on every gate (tatara `.scratchpad/session-loss/handoff-epic-run.md`). The user never answered them one by one.
- PRs in flight: none. All of hive-decoupling's PRs are merged: orchestrator #33, #34, #35, #37; plugins #3 (tag v0.4.0); helmfile #49, #50, #52, #53. Helmfile PR #48 (agents-helmfile-ci-test-job) is open and is not part of this epic.

## Queued epics (docs/plans/todo)

- session-orchestration-mcp: planned with 24 tasks. Blocked on hive-decoupling and slash-commands-from-chat; matrix-connector-agent-initi is done. Run it through workbench:epic-run when it unblocks.
- decision-board: README-only shell (created 2026-10-29, mx-34 #316). Blocked on session-orchestration-mcp. Not planned yet; open at planning are the component name and how an answer reaches the asking session.
- semver-image-tags-at-the-end: planned with 6 tasks and no blockers. It was agreed for the end of the chain. A proposal to run it earlier was never answered.

## Done since the split

- matrix-connector-agent-initi: done (35/35), with its record and retro, in docs/plans/done/.
- cct2-1 wedge: cleared 02:23Z. The follow-up, an orchestrator-side stale-busy detector, is not started. It is in docs/plans/2026-10-28-wrapper-queued-command-wedge-debug-record.md.

## Stale local refs (ignore)

The tatara clone holds local-only `slash-commands-from-chat` commits from 2026-10-27 in orchestrator, web, plugins and wrapper. Each one is superseded by a commit with the same subject on cct2's origin branch. They were not pushed.
