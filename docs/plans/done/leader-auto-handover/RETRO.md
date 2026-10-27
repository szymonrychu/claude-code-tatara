# leader auto handover retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| wrapper compacting event | 2 | 2 | 6 | 26 | 546295 | 881354 |
| compaction status projection | 3 | 3 | 7 | 323 | 996161 | 2641899 |
| leadership auto handover | 5 | 5 | 11 | 18 | 1836811 | 1400013 |
| scale down staying peer | 3 | 3 | 7 | 8 | 996161 | 1678149 |
| web scale hint | 1 | 1 | 4 | 2 | 662742 | 375407 |
| claim hold and handover wake | 3 | 3 | 7 | 6 | 996161 | 1449605 |
| reconciler leader pod hold | 2 | 2 | 6 | 5 | 546295 | 715063 |
| leader changed reason | 2 | 2 | 6 | 5 | 546295 | 591802 |
| web leader reason | 3 | 3 | 7 | 3 | 996161 | 679096 |
| wrapper release 0.3.0 | 1 | 1 | 4 | 16 | 662742 | 302582 |
| orch wrapper pin 0.3.0 | 1 | 1 | 4 | 7 | 662742 | 363796 |
| smoke scale below leader | 3 | 3 | 7 | 21 | 996161 | 694284 |
| kind e2e auto handover | 3 | 3 | 7 | 21 | 996161 | 795251 |
| helmfile deploy pin | 2 | 2 | 6 | 5 | 546295 | 386185 |
| helmfile apply smoke | 5 | 3 | 11 | 3 | 1836811 | 245900 |
| smoke step7 per-wait deadlines | 2 | 2 | 5 | 20 | 546295 | 715527 |
| orch eligibility single source | 3 | 3 | 6 | 15 | 963314 | 900392 |
| Total | 44 | 42 | 111 | 504 | 15333603 | 14816305 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| wrapper compacting event | 0 | 4.33 | 1.61 |
| compaction status projection | 0 | 46.14 | 2.65 |
| leadership auto handover | 0 | 1.64 | 0.76 |
| scale down staying peer | 0 | 1.14 | 1.68 |
| web scale hint | 0 | 0.50 | 0.57 |
| claim hold and handover wake | 0 | 0.86 | 1.46 |
| reconciler leader pod hold | 0 | 0.83 | 1.31 |
| leader changed reason | 0 | 0.83 | 1.08 |
| web leader reason | 0 | 0.43 | 0.68 |
| wrapper release 0.3.0 | 0 | 4.00 | 0.46 |
| orch wrapper pin 0.3.0 | 0 | 1.75 | 0.55 |
| smoke scale below leader | 0 | 3.00 | 0.70 |
| kind e2e auto handover | 0 | 3.00 | 0.80 |
| helmfile deploy pin | 0 | 0.83 | 0.71 |
| helmfile apply smoke | -2 | 0.27 | 0.13 |
| smoke step7 per-wait deadlines | 0 | 4.00 | 1.31 |
| orch eligibility single source | 0 | 2.50 | 0.93 |

- MdAPE points: 0.0%
- MdAPE minutes: 66.7%
- MdAPE tokens: 40.6%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 17 tasks delivered across 4 repos with points on estimate (MdAPE 0.0%, 44 est vs 42 post-delivery; helmfile apply smoke re-scored 5 to 3). | Minutes far over the seed: 504 actual vs 111 expected; minutes MdAPE 66.7%. compaction status projection took 323 vs 7 min (46.14x, 2.65x tokens); its task Notes name a full Docker VM disk as a blocker, cause not confirmed. |
| The three tasks closed by tatara-0 (helmfile-apply-smoke, smoke-step7-per-wait-deadlin, orch-eligibility-single-sour) each closed in 1 review round, with no escalation and no fix round. | Live/CI-bound tasks ran 3-4x over the minutes seed: smoke scale below leader 21 vs 7, kind e2e auto handover 21 vs 7, smoke step7 per-wait deadlines 20 vs 5, wrapper release 0.3.0 16 vs 4. |
| Phase 5 whole-diff review plus scope audit: G1-G5 landed, no Act-on item in merged code, nothing dropped; the two Consider items became tasks and were done. | Smoke step 7 reused the scale-up deadline for the agent1 lookup and the make-leader wait, so a slow pod-1 Ready could fail the smoke spuriously, and MEMORY.md claimed per-wait deadlines. Per-task review missed it; the epic review found it (task smoke-step7-per-wait-deadlin). |
| smoke-step7-per-wait-deadlin: implementer showed red then green; reviewer's tail "113 passed in 253.52s", lint green, both new tests fail on the pre-fix smoke.sh. | Duplicate SQL predicates (`_CANDIDATES`, `_target_ready`, `_HANDOVER_PENDING`, `REPLICAS` literal) were found only by the scope-auditor sweep, after PR #21 merged; fixed in follow-up PR #25. |
| orch-eligibility-single-sour: reviewer verified SQL equivalence line by line; PR #25 CI "1083 passed, 56 deselected, 1 warning in 205.29s", kind e2e pass, main CI on 90f3ce3 success. | No Docker in agent pods: orchestrator DB tests (525 testcontainers errors) could not run in this pod, so DB evidence came from GitHub CI, about 16 min later per PR. |
| helmfile-apply-smoke: live proof done (leader moved to pod-0 agent db57c360, leader_reason scale_down, message 69 answered "ok"); `mise run smoke` on main 0ed86cf exited 0. Finished in 3 min vs 11, 0.13x tokens. | Session gitconfig had no user identity and no gh credential helper, so `ticket.py new-task` failed to commit until both were set. |
| Releases and pins landed as planned: wrapper v0.3.0 tag on ee10aa8, orchestrator b3a2975, web 4701820, agent image claude-code-wrapper:0.3.0. | `ticket.py new-task` left template Interfaces/Expected outcome/Steps/Notes sections and `amend` refused them ("empty Steps section"); the supervisor filled them by hand. AC evidence kind `file:` was rejected (needs `symbol:`). |
| | An implementer ran a bare `git stash`; the guard-bash hook refuses to remove stash entries even by ref, leaving duplicate entry bc3b4ff in agents-orchestrator's stash (content already in 059372f). |
| | agents-helmfile has no CI workflows (only GitGuardian), so PR #34 rested on the reviewer's local verify; local helmfile tests were red on Harbor 401. |
| | Tokens: MdAPE 40.6%; compaction status projection 2.65x, scale down staying peer 1.68x, wrapper compacting event 1.61x. |
| | Two sessions ran the epic (the hive leader 14 tasks, tatara-0 the review and last 3), and the orchestrator notes for the first 14 carry no review rounds; those rounds are unknown here. |

## Improvements

- Code:
  - agents-orchestrator `db/leadership.py` `_target_ready`: omits `wrapper_session_id IS NOT NULL` (a manual make-leader target can be one `ELIGIBLE` would not pick); the review asked to confirm whether intended and no ruling is recorded. Add a test pinning the chosen behaviour.
  - agents-orchestrator tests: `test_compacted_leader_never_takes_next_message` cannot force the busy-leader race; the hold is pinned at queue level only. A race-forcing fixture would pin it end to end.
  - agents-orchestrator ingester: turn_completed events are stored with top-level turn_id null (data.record carries it), so filtering events by turn_id misses them; store the id at top level or document the lookup.
- Delivered differently:
  - Two tasks were added beyond the plan, from the phase 5 review: smoke-step7-per-wait-deadlin (a shared deadline in agents-helmfile `scripts/smoke.sh`) and orch-eligibility-single-sour (duplicated SQL predicates in agents-orchestrator).
  - helmfile-apply-smoke was re-scored 5 to 3, and follow-up PR #25 (90f3ce3, behaviour-preserving) was left unapplied on the leader's instruction (no apply in this epic), so live runs b3a2975, not the final main.
  - Kind e2e tests (`test_leader_compaction_hands_over`, `test_scale_down_below_leader_hands_over`) exist and passed in CI, but the epic review could not run them (no kind), and the epic's DB tests were seen green only in CI.
- Tech debt:
  - agents-orchestrator stash entry bc3b4ff: duplicate of committed 059372f; a human removes it, because the hook refuses agents.
  - agents-helmfile has no CI workflows: add a workflow running `mise run test` (lint, shellcheck, unit tests) so helmfile PRs have remote evidence.
  - Correctness near an election depends on wrapper pod vs DB clock skew for `compaction_at > l.since` (design assumption); a DB-side timestamp would remove it.
  - Real Claude Code firing PreCompact before an auto compaction is proven only with the fake claude; a live `compacting` event since the apply is unconfirmed.
  - Wrapper tests `test_pty_proc.py`, `test_manager.py`, `test_container.py` failed in this pod (4 failures in files the epic does not touch); not proven pre-existing on a clean host.
- Workflow:
  - recurring (generic-any-mcp-with-git-and, cross-session-messaging-and, matrix-read-receipts): live smoke, apply, e2e and release tasks run 3-4x over the minutes seed here (21 vs 7, 21 vs 7, 20 vs 5, 16 vs 4). Change: seed live apply/smoke/e2e/release tasks at 15-25 min in planning, calibrated from earlier actuals.
  - recurring (generic-any-mcp-with-git-and, cross-session-messaging-and): a defect that per-task verify and review missed, found only in the epic review or live (smoke step 7 shared deadline here; text-vs-JSON assumption and the make-leader race there). Change: for smoke-script tasks the reviewer checks every timeout or deadline against the AC and the MEMORY claim, and the duplicate-predicate sweep runs before the last code task merges, not after.
  - recurring (paste-env-contents-into-the): `ticket.py` task tooling friction; there `amend` linted the whole epic, here `new-task` leaves template sections that `amend` refuses ("empty Steps section") and `file:` is rejected as an evidence kind. Change: `new-task` takes a body (or `amend` accepts the template sections as a draft), and the evidence-kind list appears in the task template and in the error message.
  - Session gitconfig without identity or credential helper broke `ticket.py new-task`: harness setup should provide both (one-off, Retro table only).
  - Bare `git stash` by an implementer left an entry the hook will not let an agent remove: add a line to the implementer brief to commit or use a worktree instead (one-off, Retro table only).
  - No Docker in agent pods makes orchestrator DB tests CI-only (about 16 min per PR): single occurrence in history; a Docker-capable or shared Postgres runner would remove it (one-off, Retro table only).
