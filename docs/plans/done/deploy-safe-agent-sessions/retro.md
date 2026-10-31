# deploy-safe agent sessions retro

## Review

Migrated from the epic format.

## What went well

- Deployed 2026-10-28 16:34Z from agents-helmfile main 030c93d (PR #37): orchestrator b451f08, web 4d066a4, wrapper 0.3.2. check-pins ok (9 pins), smoke OK including continuity (message reached sent after the restart, same wrapper session id), no agent dead afterwards (.logs/deploy-safe-2026-10-28/live-check.md).
- The rollout fix did what it was built for: every agent StatefulSet moved to OnDelete, idle pods were replaced one per session, the busy agent-mx-34-2 kept its pod until idle, and the deployer pod kept its uid through apply and smoke (after-sts.txt, reconciler-rollout.log).
- Points held: MdAPE 0.0% on 27 tasks (92 estimated, 88 post-delivery); only five re-scores (orch wrapper pin patch 2 to 3, web agent unavailable banner 5 to 3, web-review-fixes 3 to 2, orch-rollout-dispatch-reservation 3 to 2, orch-security-hardening 3 to 2).
- The e2e task caught a product gap in round 1: wrapper resume_on_start plus the adopt path recorded no resume marker, so a hand-deleted busy pod stayed dead (fixed 4ee2fbe, CI 40683839123 green, 46 e2e passed).
- The pre-merge review (whole-diff, scope audit, security) found real defects before merge and each was ruled in review/judgement.md: 5 fix tasks (orch-rollout-dispatch-reservation, orch-sessions-save-unconverged, orch-security-hardening, web-review-fixes, helmfile-pin-check-attempts), the rest dropped or noted with a stated reason.
- The user hotfix (agents-orchestrator #29 c042f79, cherry-picks of tasks 3-5, deployed via helmfile #36) was reconciled: epic branches rebased onto it, pins moved, the stale AC9 of helmfile pin check ruled a point-in-time check (not a code gap).
- Design decisions were recorded as they happened (D3 close-after-resume e809cafd, D1 OnDelete transition and idle rollout handover 879e2aa8, AC amendments for orch-sessions-backup-save, orch-wrapper-pin-patch, orch-e2e-rollout-mid-turn), so the reviewers had a fixed target.
- Standing approvals were written in handoff-epic-run.md (recommended answers, limits on destructive ops), so the loop ran unattended through two leadership handovers without gate questions.

## What went wrong or could improve

- Minutes ran 976 actual vs 176 expected over 26 timed tasks (5.5x; MdAPE minutes 73.9%) and tokens 85835610 vs 32369834 (2.65x; MdAPE 51.5%). Worst: wrapper shutdown turn resume 211 min vs 8 (26.38x, 6.88x tokens), orch wrapper pin patch 69 vs 5 (13.80x), orch e2e rollout mid turn 104 vs 8 (13.00x, 8.43x tokens). Part of this is waiting on CI, releases and restarts, not work; the split is unknown.
- helmfile apply live check has no recorded minutes or tokens: the leader (tatara-0) ran steps 1-5 itself in the foreground, so the totals cover 26 of 27 tasks.
- Points say nothing about wall clock here: the same 5-point estimate produced 22 min (helmfile pin check) and 211 min (wrapper shutdown turn resume).
- orch e2e rollout mid turn needed a fix round and used 15410029 tokens, the largest of the epic after the wrapper task (12569789). Its flaky test_reconnect_backoff_after_disconnect (untouched file) was seen once under load and was not turned into a task.
- The most serious defect, rollout.py:50 replacer ignoring the dispatch reservation (a sent-not-busy pod was deletable), passed the per-task review of orch rollout replacer (83 min, ba2ef3b) and surfaced only in the epic review; the epic's core promise was unproven until then.
- The user had to hotfix externally mid-epic (agents-orchestrator #29): the epic could not ship the fix itself in time, three tasks (orch dead agent ineligible, orch e2e main failure, orch ingester reattach) landed on main by cherry-pick outside the epic flow, and the branches and superrepo main needed rebasing on the user pointers (about 145 local ticket commits remain unpushed).
- wrapper patch release was marked done after the PR merge and tag push (5fd93ff, v0.3.2), then reverted: release run 40653754978 attempt 1 was cancelled when a Harbor layer pull stalled to the 15 min timeout; attempt 2 succeeded. The done status was set before the artifact existed.
- check-pins refused re-run builds (run attempt greater than 1), fixed in helmfile-pin-check-attempts (5 min), but the first helmfile pin check task shipped a check that rejected a legitimate state.
- Session restarts cut off agents (the problem this epic fixes, hit while building it); implementers were dispatched fresh per fix round because SendMessage is unavailable.
- Two leadership handovers near context limits (handoff-epic-run at task 3, then the phase 5 handoff at 20 of 22 tasks; a third, handoff-after-deploy, followed the deploy). The task Notes of most tasks hold only "done"; review rounds and verification tails survive only in the scratchpad notes, so per-task rounds are unknown here.
- Several task files had empty Steps sections; ticket.py refused them at close and the orchestrator had to fill them (59b6d06d, 95a3c674).
- No Docker in the pod: orchestrator DB tests ran via a local pgserver plugin kept in a session temp dir, with CI authoritative. Harbor 401 broke 4 helmfile release tests until a manual helm registry login.

## Recommendations

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

## Delivery record (migrated)

### Asked

Agent sessions survive deploys and pod restarts (incident 2026-10-27: the 20:03Z agents-helmfile #35 apply rolled every agent pod, the orchestrator never re-attached, the user discarded both hung sessions and lost both conversations). Scope G1-G10: ingester re-attach after resume, dead agent never leader, OnDelete plus idle-only replacer (leader last), wrapper continues a shutdown-interrupted turn, non-fatal onStart install, /sessions transcripts backed up to S3 and restored, web discard notice and agent-unavailable banner, no red main build published or deployed, kind e2e rolling the image mid-turn, release/deploy with a live check. Planned 22 tasks; 5 added during the run (4 epic-review fixes, 1 pin-check rule fix) = 27.

### Shipped

All 27 task files are `done`; epic review verdict: pass (2026-10-28). Merged: agents-orchestrator PR #28 (merge commit b451f08), agents-web PR #20 (4d066a4), agents-helmfile PR #37 (030c93d, pins) and #38 (c9ba047, MEMORY live-check entry), claude-code-wrapper PR #7 (5fd93ff, tag v0.3.2, release run 40653754978 attempt 2 success). Before the epic merged, the user cherry-picked three tasks' fixes to main as agents-orchestrator PR #29 (c042f79) and deployed them via agents-helmfile PR #36 (3b5004e). Deployed 2026-10-28 16:34Z by tatara-0 from agents-helmfile main 030c93d: orchestrator chart 0.1.0-main.b451f08 + image b451f08, agents-web chart 0.1.0-main.4d066a4 + image 4d066a4, agent image claude-code-wrapper:0.3.2; check-pins ok (9 pins); smoke OK including the continuity step. Live check: all agent StatefulSets OnDelete, idle pods replaced one per session, leaders last after handover, deployer pod kept its uid, no agent dead. Evidence: /workdir/workdir/.logs/deploy-safe-2026-10-28/live-check.md.

### Tasks

Status is `done` for all rows. Review rounds: the orchestrator notes record rounds only for orch-e2e-rollout-mid-turn; every task file has an empty `review:` field, so other rounds are unknown. Tails not in the notes are unknown. "Not in log" = the file's verified head is not reachable from the repo's main (rebased or cherry-picked); the files win, the content landed under the sha named by subject match.

| Task | Status | Verified head | Rounds | Verification tail |
|---|---|---|---|---|
| helmfile-pin-check | done | fdedfc7 (not in log; rebased to 80b8204) | unknown | unknown |
| helmfile-smoke-continuity | done | bdc3fca (not in log; rebased to eb810ea) | unknown | unknown; live smoke OK incl. continuity (smoke.log) |
| helmfile-pin-check-attempts | done | 5a726d0 (in log) | unknown | unknown; check-pins ok on all 9 pins at apply |
| helmfile-deploy-pins | done | 3b1bc0b (in log) | unknown | check-pins ok (9 pins), release tests 30 passed with Harbor login; orch main CI 40716752343 and web main CI 40722375652 green |
| helmfile-apply-live-check | done | 2bc3ddd (in log) | unknown | mise run smoke OK incl. continuity; live-check.md |
| orch-ingester-reattach | done | 4ca88ea (not in log; landed via hotfix #29 c042f79) | unknown | unknown |
| orch-dead-agent-ineligible | done | c822ff5 (not in log; landed as c97b003 in #29) | unknown | unknown |
| orch-e2e-main-failure | done | 5736cbf (not in log; landed in #29, e2e fixes 5c0d385/4a7ad59) | unknown | unknown |
| orch-onstart-nonfatal | done | 289be85 (not in log; landed as 3ddc07d) | unknown | unknown |
| orch-default-continue-prompt | done | 6982b3b (in log) | unknown | unknown |
| orch-sessions-backup-save | done | 65f92de (not in log; landed as 95e58b4/7a09db5/7ef5da5) | unknown | unknown |
| orch-sessions-backup-restore | done | 10ba36a (in log) | unknown | unknown |
| orch-api-session-safety | done | 07fce27 (in log) | unknown | unknown |
| orch-ci-publish-gate | done | ca39f8e (in log) | unknown | unknown |
| orch-rollout-replacer | done | ba2ef3b (in log) | unknown | unknown |
| orch-wrapper-pin-patch | done | 288d9af (in log) | unknown | unknown; CI e2e job now also runs test:integration |
| orch-e2e-rollout-mid-turn | done | e0b6e12 (in log) | 2 or more: round 1 found the resume-marker gap, a fix round followed; exact count unknown | CI run 40683839123 green, 46 e2e passed |
| orch-rollout-dispatch-reserv | done | 053d323 (in log) | unknown | unknown |
| orch-sessions-save-unconverg | done | bd10241 (in log) | unknown | unknown |
| orch-security-hardening | done | 28459cc (in log) | unknown | unknown |
| web-ci-publish-gate | done | eec81dd (in log) | unknown | unknown |
| web-sync-session-safety-api | done | ace35f8 (in log) | unknown | unknown |
| web-agent-unavailable-banner | done | d3be27f (in log) | unknown | unknown |
| web-discard-backup-notice | done | 29e97be (in log) | unknown | unknown |
| web-review-fixes | done | 454e1aa (in log) | unknown | unknown; web main CI 40722375652 green |
| wrapper-shutdown-turn-resume | done | 91d785d (in log) | unknown | unknown |
| wrapper-patch-release | done | 5fd93ff (in log) | unknown | PR CI 40650156587 green on cb51746; main CI 40651891291 green; release run 40653754978 attempt 2 success |

Notes versus files:
- run-state.md snapshots "16/22 done"; the files show 27 of 27 done (22 planned + 5 added).
- judgement.md names fix tasks `orch-review-fixes` and `orch-rollout-reservation`; the files hold three tasks instead: orch-rollout-dispatch-reserv, orch-sessions-save-unconverg, orch-security-hardening.
- Seven verified heads are not in the repo logs (rows above); the task files keep the pre-rebase or pre-cherry-pick sha.
- helmfile-apply-live-check `## Notes` repeats the "done" and "actuals: no agent records" lines; actual_minutes, actual_tokens and actual_roles are empty in that file.

### Rulings

- D1 deploy together (my call): orch-default-continue-prompt changes every session's config hash, so it deploys only in the same apply as the OnDelete switch. Why: a hash change under RollingUpdate would roll every pod at once, the incident. Cost if wrong: a repeat of the 2026-10-27 mass roll. Result: one apply; all StatefulSets OnDelete after it.
- D1 amendment, transition and idle-only rollout handover (879e2aa8): a live StatefulSet not on OnDelete gets a strategy-only merge patch before the apply; the rollout handover is queued only when the leader is idle. Why: the API server may reject the defaulted rollingUpdate.partition next to OnDelete; leadership must not move mid-turn. Cost if wrong: apply errors on every existing StatefulSet, or a leader handed over mid-turn. Proven by e2e AC9 and the live check.
- D3 amendment, close-after-resume (fable architect; .scratchpad/session-loss/decisions/d3-close-after-resume.md): a session_closed is honoured only when the wrapper's live snapshot maps to dead, not by database order. Why: when the orchestrator restarts in the same deploy the close is stored after the resume. Cost if wrong: an agent left dead after a restart (the hang), or a truly dead agent re-attached.
- e2e product gap (orch-e2e-rollout-mid-turn round 1): wrapper resume_on_start plus the adopt path recorded no resume marker; fixed in the task (4ee2fbe) instead of deferred. Cost if wrong: a hand-deleted busy pod stays dead after the wrapper resumes it.
- Merge orchestrator PR #28 with a merge commit, not squash. Why: agents-web openapi/orchestrator.source pins e0b6e12, a PR-branch commit. Cost if wrong: the pin points at an unreachable sha and check:api drifts.
- Deploy order: agents-web after agents-orchestrator. Why: web 29e97be reads the required SessionView.backup; an old orchestrator makes the discard dialog throw. Cost if wrong: broken discard dialog until the orchestrator rolls. Both were in one apply at 16:34Z.
- orch-sessions-backup-save amendment: tests/test_cache_save.py session setup helper changed (sessions restore record that skips the transcripts save), no assertion changed. Why: the discard now ends after the sessions save. Cost if wrong: a weakened workdir-save test; mitigated, assertions untouched.
- Q1-Q3 settled as my call: wrapper tag v0.3.2; banner narrowed to "no ready alive agent, or oldest queued older than 10 minutes"; slash-commands-from-chat parked so the 11 prepared tasks could be created. Cost if wrong: a wrong patch number, a noisy or silent banner, a delayed sibling epic.
- Epic review, findings acted on (six fix groups): replacer ignored the dispatch reservation (rollout.py:50); sessions save on a never-converged session held discard up to 30 minutes (save_rule.py:31); README onStart wording; orchestrator ci.yaml regctl-installer@main with push secrets (pinned by SHA, contents: read); Claude credentials (config/.credentials.json) in the /sessions archive (excluded, my call); web chart-publish-tag needing only chart, discard dialog wording for transcripts, missing ChatView banner mount test, permissions block. Cost if wrong: a pod deleted mid-handoff, 30 minute discard stalls, credentials in S3, a red tag build published.
- Epic review, findings dropped or noted: restore planting via bucket write (same trust boundary as the workdir cache restore); check_pins name-only repo mapping (pins live in our reviewed helmfile); check_pins all-skipped green (no skip in our pins); on_error allow (by design D6). Cost if wrong: bucket writers can plant a transcript restore; a mis-mapped or all-skipped pin passes the check.
- Scope-audit gap dropped: helmfile-pin-check AC9 (grep for 96e46f3 refused) was a point-in-time check; the hotfix moved pins to c042f79 and the refusal is proven by tests/fixtures/check_runs_agents_orchestrator.json. Cost if wrong: the check could pass a red pin unnoticed; the fixture test would still catch it.
- helmfile-pin-check-attempts added (my call, option b): a gated job counts as green if it succeeded in any attempt of the pinned run. Why: check-pins refused correctly published agents-webhook 838ba1f and agents-schedule 0.1.0 after a re-run failed on the chart-publish guard. Cost if wrong: a pin whose later attempt is red but earlier attempt published passes; a job red in every attempt still refuses.

### Discovered and blocked

- Deployer pod agent-claude-code-tatara-0 was still busy on 0.3.1 at live-check time; the replacer rolls it when its turn ends (self-clearing; tatara-0 confirms the pod uid change).
- Live-check step 5 asked for status.rollout draining to empty; live-check.md does not record that observation (the deployer's roll was still pending). Cleared by: tatara-0, one read of the session status after the deployer's turn.
- Pre-existing: claude-code-wrapper tests/test_manager.py::test_shutdown_stops_all fails locally on base fb005fd. Noted, not doing now; cleared by the wrapper owner in a later wrapper epic.
- Local environment failures (CI authoritative): orchestrator test_lightkube_default_client_uses_env_config, helmfile template tests (Harbor 401 without login), test_reconnect_backoff_after_disconnect flaky once under load. No Docker in agent pods.
- Wrapper release run 40653754978 attempt 1 was cancelled (Harbor pull stalled to the 15 minute timeout); attempt 2 succeeded. Harbor owner.
- Deferred by non-goals and sticking: SIGTERM exit keystrokes, periodic (non-discard) transcript backups, in-cluster helmfile Job runner. Also noted: `_target_ready` omits `wrapper_session_id IS NOT NULL`; agents-helmfile has no CI workflows.

### Not pushed

- Superrepo /workdir/workdir main is 185 commits ahead of origin/main (this epic's ticket commits, the submodule pin 878ab4fa, and other epics' ticket commits). Pushed by tatara-0 or the user (the superrepo needs the https URL with the gh credential helper). This record and RETRO.md are written after the last commit and are uncommitted until committed.
- agents-orchestrator, agents-web, agents-helmfile and claude-code-wrapper: `git log origin/<base>..<base>` is empty for each; nothing unpushed. The origin branches deploy-safe-agent-sessions remain after merge.

### Lessons routed to

- Verified heads that rebase or cherry-pick leaves unreachable (7 here): add a check to `ticket.py close` that every task's verified_head is reachable from the repo's epic ref or base, or is re-recorded; mechanical, so a ticket.py test, not a skill edit.
- Per-task review rounds and the verification tail were not in any file (review: empty on all 27): add a check to `ticket.py task done` that its note carries rounds and the tail line; mechanical.
- Publish-gate defects reached the epic review (tag chart publish needing only chart, moving @main action with push secrets, no permissions block): add a lint test in each repo's CI test (tests/test_chart_ci.py, scripts/ci.test.mjs) that no workflow uses a moving ref and every publish job needs the full gate list; mechanical.
- Replacer ignored the dispatch reservation and the save rule ignored never-converged sessions: a judgement call (shared predicates must match the dispatcher's own idle condition); edit the start-review reviewer checklist, with the e2e test as the executable check.
- Live-check evidence was gathered by hand and missed the status.rollout drain: add a `mise run` live-check task in agents-helmfile that prints the AC step 5 observations; mechanical.
- A user hotfix cherry-picking epic tasks to main left their verified heads unreachable: judgement call; edit the start-development skill to record the main sha in the task Notes when work lands outside the epic branch.
- Estimates: live, e2e and wrapper tasks ran far above the seed minutes again (wrapper-shutdown-turn-resume 211 vs 8, orch-e2e-rollout-mid-turn 104 vs 8, helmfile-smoke-continuity 31 vs 8): the design already records this recurring pattern; edit the planner's estimate guidance in start-development, not a mechanical check.
