# deploy-safe agent sessions retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| helmfile pin check | 5 | 5 | 8 | 22 | 1828146 | 2535829 |
| helmfile smoke continuity | 5 | 5 | 8 | 31 | 1828146 | 3058400 |
| orch dead agent ineligible | 3 | 3 | 6 | 37 | 940114 | 1862484 |
| orch e2e main failure | 3 | 3 | 6 | 22 | 936557 | 1504839 |
| orch ingester reattach | 5 | 5 | 8 | 67 | 1828146 | 7999692 |
| orch onstart nonfatal | 2 | 2 | 5 | 20 | 544297 | 820107 |
| orch sessions backup save | 5 | 5 | 8 | 40 | 1828146 | 6393804 |
| web ci publish gate | 1 | 1 | 4 | 5 | 641999 | 250789 |
| wrapper shutdown turn resume | 5 | 5 | 8 | 211 | 1828146 | 12569789 |
| orch ci publish gate | 2 | 2 | 5 | 19 | 544297 | 556633 |
| orch default continue prompt | 2 | 2 | 5 | 19 | 544297 | 1172307 |
| orch sessions backup restore | 5 | 5 | 8 | 42 | 1828146 | 7308288 |
| orch api session safety | 3 | 3 | 6 | 31 | 936557 | 3378333 |
| wrapper patch release | 1 | 1 | 4 | 17 | 641999 | 247269 |
| orch rollout replacer | 8 | 8 | 14 | 83 | 3155191 | 10288310 |
| orch wrapper pin patch | 2 | 3 | 5 | 69 | 544297 | 2223518 |
| orch e2e rollout mid turn | 5 | 5 | 8 | 104 | 1828146 | 15410029 |
| web sync session safety api | 1 | 1 | 4 | 8 | 641999 | 306882 |
| web agent unavailable banner | 5 | 3 | 8 | 9 | 1828146 | 868989 |
| web discard backup notice | 3 | 3 | 6 | 13 | 940114 | 965826 |
| web-review-fixes | 3 | 2 | 6 | 6 | 950968 | 644127 |
| orch-rollout-dispatch-reservation | 3 | 2 | 6 | 18 | 950968 | 1029725 |
| orch-sessions-save-unconverged | 3 | 3 | 6 | 10 | 950968 | 1555464 |
| orch-security-hardening | 3 | 2 | 6 | 57 | 950968 | 1883710 |
| helmfile-pin-check-attempts | 2 | 2 | 5 | 5 | 556633 | 435637 |
| helmfile deploy pins | 2 | 2 | 5 | 11 | 544297 | 564830 |
| helmfile apply live check | 5 | 5 | 8 | not recorded | 1828146 | not recorded |
| Total | 92 | 88 | 176 | 976 (26 of 27 tasks) | 32369834 | 85835610 (26 of 27 tasks) |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| helmfile pin check | 0 | 2.75 | 1.39 |
| helmfile smoke continuity | 0 | 3.88 | 1.67 |
| orch dead agent ineligible | 0 | 6.17 | 1.98 |
| orch e2e main failure | 0 | 3.67 | 1.61 |
| orch ingester reattach | 0 | 8.38 | 4.38 |
| orch onstart nonfatal | 0 | 4.00 | 1.51 |
| orch sessions backup save | 0 | 5.00 | 3.50 |
| web ci publish gate | 0 | 1.25 | 0.39 |
| wrapper shutdown turn resume | 0 | 26.38 | 6.88 |
| orch ci publish gate | 0 | 3.80 | 1.02 |
| orch default continue prompt | 0 | 3.80 | 2.15 |
| orch sessions backup restore | 0 | 5.25 | 4.00 |
| orch api session safety | 0 | 5.17 | 3.61 |
| wrapper patch release | 0 | 4.25 | 0.39 |
| orch rollout replacer | 0 | 5.93 | 3.26 |
| orch wrapper pin patch | +1 | 13.80 | 4.09 |
| orch e2e rollout mid turn | 0 | 13.00 | 8.43 |
| web sync session safety api | 0 | 2.00 | 0.48 |
| web agent unavailable banner | -2 | 1.12 | 0.48 |
| web discard backup notice | 0 | 2.17 | 1.03 |
| web-review-fixes | -1 | 1.00 | 0.68 |
| orch-rollout-dispatch-reservation | -1 | 3.00 | 1.08 |
| orch-sessions-save-unconverged | 0 | 1.67 | 1.64 |
| orch-security-hardening | -1 | 9.50 | 1.98 |
| helmfile-pin-check-attempts | 0 | 1.00 | 0.78 |
| helmfile deploy pins | 0 | 2.20 | 1.04 |
| helmfile apply live check | 0 | not recorded | not recorded |

- MdAPE points: 0.0%
- MdAPE minutes: 73.9%
- MdAPE tokens: 51.5%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| Deployed 2026-10-28 16:34Z from agents-helmfile main 030c93d (PR #37): orchestrator b451f08, web 4d066a4, wrapper 0.3.2. check-pins ok (9 pins), smoke OK including continuity (message reached sent after the restart, same wrapper session id), no agent dead afterwards (.logs/deploy-safe-2026-10-28/live-check.md). | Minutes ran 976 actual vs 176 expected over 26 timed tasks (5.5x; MdAPE minutes 73.9%) and tokens 85835610 vs 32369834 (2.65x; MdAPE 51.5%). Worst: wrapper shutdown turn resume 211 min vs 8 (26.38x, 6.88x tokens), orch wrapper pin patch 69 vs 5 (13.80x), orch e2e rollout mid turn 104 vs 8 (13.00x, 8.43x tokens). Part of this is waiting on CI, releases and restarts, not work; the split is unknown. |
| The rollout fix did what it was built for: every agent StatefulSet moved to OnDelete, idle pods were replaced one per session, the busy agent-mx-34-2 kept its pod until idle, and the deployer pod kept its uid through apply and smoke (after-sts.txt, reconciler-rollout.log). | helmfile apply live check has no recorded minutes or tokens: the leader (tatara-0) ran steps 1-5 itself in the foreground, so the totals cover 26 of 27 tasks. |
| Points held: MdAPE 0.0% on 27 tasks (92 estimated, 88 post-delivery); only five re-scores (orch wrapper pin patch 2 to 3, web agent unavailable banner 5 to 3, web-review-fixes 3 to 2, orch-rollout-dispatch-reservation 3 to 2, orch-security-hardening 3 to 2). | Points say nothing about wall clock here: the same 5-point estimate produced 22 min (helmfile pin check) and 211 min (wrapper shutdown turn resume). |
| The e2e task caught a product gap in round 1: wrapper resume_on_start plus the adopt path recorded no resume marker, so a hand-deleted busy pod stayed dead (fixed 4ee2fbe, CI 40683839123 green, 46 e2e passed). | orch e2e rollout mid turn needed a fix round and used 15410029 tokens, the largest of the epic after the wrapper task (12569789). Its flaky test_reconnect_backoff_after_disconnect (untouched file) was seen once under load and was not turned into a task. |
| The pre-merge review (whole-diff, scope audit, security) found real defects before merge and each was ruled in review/judgement.md: 5 fix tasks (orch-rollout-dispatch-reservation, orch-sessions-save-unconverged, orch-security-hardening, web-review-fixes, helmfile-pin-check-attempts), the rest dropped or noted with a stated reason. | The most serious defect, rollout.py:50 replacer ignoring the dispatch reservation (a sent-not-busy pod was deletable), passed the per-task review of orch rollout replacer (83 min, ba2ef3b) and surfaced only in the epic review; the epic's core promise was unproven until then. |
| The user hotfix (agents-orchestrator #29 c042f79, cherry-picks of tasks 3-5, deployed via helmfile #36) was reconciled: epic branches rebased onto it, pins moved, the stale AC9 of helmfile pin check ruled a point-in-time check (not a code gap). | The user had to hotfix externally mid-epic (agents-orchestrator #29): the epic could not ship the fix itself in time, three tasks (orch dead agent ineligible, orch e2e main failure, orch ingester reattach) landed on main by cherry-pick outside the epic flow, and the branches and superrepo main needed rebasing on the user pointers (about 145 local ticket commits remain unpushed). |
| Design decisions were recorded as they happened (D3 close-after-resume e809cafd, D1 OnDelete transition and idle rollout handover 879e2aa8, AC amendments for orch-sessions-backup-save, orch-wrapper-pin-patch, orch-e2e-rollout-mid-turn), so the reviewers had a fixed target. | wrapper patch release was marked done after the PR merge and tag push (5fd93ff, v0.3.2), then reverted: release run 40653754978 attempt 1 was cancelled when a Harbor layer pull stalled to the 15 min timeout; attempt 2 succeeded. The done status was set before the artifact existed. |
| Standing approvals were written in handoff-epic-run.md (recommended answers, limits on destructive ops), so the loop ran unattended through two leadership handovers without gate questions. | check-pins refused re-run builds (run attempt greater than 1), fixed in helmfile-pin-check-attempts (5 min), but the first helmfile pin check task shipped a check that rejected a legitimate state. |
| | Session restarts cut off agents (the problem this epic fixes, hit while building it); implementers were dispatched fresh per fix round because SendMessage is unavailable. |
| | Two leadership handovers near context limits (handoff-epic-run at task 3, then the phase 5 handoff at 20 of 22 tasks; a third, handoff-after-deploy, followed the deploy). The task Notes of most tasks hold only "done"; review rounds and verification tails survive only in the scratchpad notes, so per-task rounds are unknown here. |
| | Several task files had empty Steps sections; ticket.py refused them at close and the orchestrator had to fill them (59b6d06d, 95a3c674). |
| | No Docker in the pod: orchestrator DB tests ran via a local pgserver plugin kept in a session temp dir, with CI authoritative. Harbor 401 broke 4 helmfile release tests until a manual helm registry login. |

## Improvements

- Code:
  - agents-helmfile `check_pins`: maps a pinned image to its repo by name only (security M3, noted) and reports green when every pin was skipped (low, noted); resolve owner/repo from the pin and fail when zero pins were checked.
  - agents-orchestrator `/sessions` archive (security-hardening): credentials are excluded by a deny list (config/.credentials.json); an allow list of workdir content would not leak a new credential file by default.
  - agents-orchestrator `ci.yaml`: regctl-installer was pinned by SHA and a permissions block added; keep a test or lint that rejects floating `@main` action refs in the workflows of the three components touched.
  - agents-orchestrator `test_reconnect_backoff_after_disconnect`: flaked once under load; give it a deterministic clock or a wider bound.
  - agents-orchestrator `test_lightkube_default_client_uses_env_config`: still fails in-cluster (set KUBERNETES_SERVICE_HOST); already listed in file-download-in-file-browse and not fixed.
  - claude-code-wrapper `tests/test_manager.py::test_shutdown_stops_all`: fails locally on base fb005fd (pre-existing, noted, not doing now); fix or guard it.
- Delivered differently:
  - 27 tasks ran against 22 planned: five fix tasks were added by the pre-merge review (orch-rollout-dispatch-reservation, orch-sessions-save-unconverged, orch-security-hardening, web-review-fixes, helmfile-pin-check-attempts), because the review found real defects and a check-pins defect.
  - Tasks 3-5 (orch dead agent ineligible, orch e2e main failure, orch ingester reattach) reached main as the user's cherry-pick agents-orchestrator #29 c042f79, deployed via helmfile #36, before the epic merged; the production incident could not wait.
  - Design changed during the run: D3 close-after-resume (e809cafd) and D1 OnDelete transition plus idle rollout handover (879e2aa8), with AC amendments to orch-sessions-backup-save (AC9), orch-wrapper-pin-patch (sha, 2 to 3 points after the v0.3.2 release) and orch-e2e-rollout-mid-turn (AC9, switch proven on a real API server); each was needed to make rollout safe on StatefulSets that already existed.
  - Orchestrator PR #28 merged with a merge commit instead of a squash, because web `openapi/orchestrator.source` pins a PR-branch commit (e0b6e12).
  - The /sessions archive excludes Claude credentials, which no task AC required (the leader's call on security M2 part), because the archive goes to S3.
  - helmfile apply live check was run by the leader pod in the foreground, not by an implementer, so the apply stayed on a busy pod that is not rolled; its remaining step was only the MEMORY.md entry.
  - The scope audit gap on helmfile-pin-check AC9 (grep for 96e46f3 refused) was dropped: it was a point-in-time check and the hotfix moved the pins to c042f79; tests/fixtures/check_runs_agents_orchestrator.json proves the refusal.
- Tech debt:
  - Restore can plant files through bucket write access (security M2): accepted because bucket write is already trusted for the workdir cache restore; signed archives or per-agent prefixes would remove it.
  - on_error allow in the save rule is by design (D6): a failed backup never blocks a discard path; a visible alert on the failure would reduce the risk.
  - Deploy-order coupling: agents-web must deploy after agents-orchestrator (web 29e97be reads the required SessionView.backup) and the default continue prompt (6982b3b) changes every config hash, so it must deploy with the OnDelete switch; nothing enforces either order. Making web tolerate a missing backup field and having check-pins verify the ordering would remove both.
  - The local pgserver pytest plugin used for orchestrator DB tests lives in the session scratchpad, not in the repo; committing it under the orchestrator test tooling would remove the dependence on CI for DB tests.
  - About 145 ticket commits sit unpushed on the superrepo main (pushing is the user's); pushing them removes the divergence from origin.
  - Wrapper release workflow can stall on a Harbor layer pull until its 15 min timeout; a pull retry or a shorter step timeout with automatic rerun would remove the manual rerun.
- Workflow:
  - recurring (parked-epic-stage): task files created with empty Steps; ticket.py refuses them at close, so the orchestrator filled them twice here (59b6d06d, 95a3c674) and 21 times in parked-epic-stage. Change: `ticket.py new-task` rejects empty Steps, or the planner must write them before the approval gate.
  - recurring (parked-epic-stage, file-editor-with-tabs-and-hi, markdown-rendering-in-chat, file-download-in-file-browse): minutes and tokens seeds are off; earlier epics ran mostly under the seed, here 976 vs 176 minutes (5.5x) and 2.65x tokens. Change: calibrate the seeds by task kind from recorded actuals, with a high multiplier for tasks that touch wrapper or e2e rollout behaviour, releases or live infrastructure, and record waiting time (CI, releases, restarts) separately from work time.
  - recurring (file-editor-with-tabs-and-hi): defects that passed per-task review and surfaced only in the epic review (here rollout.py:50 ignoring the dispatch reservation, the credential leak into the archive, floating CI action refs). Change: add to the reviewer brief a check of the epic's headline promise end to end (a reservation or busy flag respected by every deleter) and run the security checklist for CI, RBAC and archive changes per task, not only at the epic review.
  - recurring (file-download-in-file-browse, file-editor-with-tabs-and-hi): no Docker in the pod makes orchestrator DB tests CI-only, and test_lightkube_default_client_uses_env_config is listed again unfixed. Change: ship the pgserver plugin with the harness, and turn a named environment failure recorded twice in Improvements into a task.
  - recurring (file-editor-with-tabs-and-hi): leadership handover loses per-task review rounds and rulings; here the task Notes of most tasks read only "done". Change: epic-run writes the review rounds, verification tail and head sha into the task Notes at each close, and the handoff skill lists the last mx-34 message ids.
  - recurring (file-editor-with-tabs-and-hi, generic-any-mcp-with-git-and): deploy depends on Harbor; here a Harbor layer pull stalled the wrapper release (run 40653754978 attempt 1) and release tests got 401 until a manual helm registry login. Change: epic-run preflight runs the Harbor login and a pull check, and the release job gets a retry.
  - recurring (file-download-in-file-browse): git push needed the inline gh credential helper and an https URL for ssh remotes (wrapper and superrepo) again. Change: the harness setup or SessionStart hook configures `gh auth setup-git` and https push URLs.
  - A task was marked done before its artifact existed (wrapper patch release, reverted after the release run was cancelled): one-off, Retro table only.
  - check-pins refused re-run builds until helmfile-pin-check-attempts: one-off, Retro table only.
