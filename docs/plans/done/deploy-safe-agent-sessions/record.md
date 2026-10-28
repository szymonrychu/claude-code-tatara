# deploy-safe agent sessions record

## Asked

Agent sessions survive deploys and pod restarts (incident 2026-10-27: the 20:03Z agents-helmfile #35 apply rolled every agent pod, the orchestrator never re-attached, the user discarded both hung sessions and lost both conversations). Scope G1-G10: ingester re-attach after resume, dead agent never leader, OnDelete plus idle-only replacer (leader last), wrapper continues a shutdown-interrupted turn, non-fatal onStart install, /sessions transcripts backed up to S3 and restored, web discard notice and agent-unavailable banner, no red main build published or deployed, kind e2e rolling the image mid-turn, release/deploy with a live check. Planned 22 tasks; 5 added during the run (4 epic-review fixes, 1 pin-check rule fix) = 27.

## Shipped

All 27 task files are `done`; epic review verdict: pass (2026-10-28). Merged: agents-orchestrator PR #28 (merge commit b451f08), agents-web PR #20 (4d066a4), agents-helmfile PR #37 (030c93d, pins) and #38 (c9ba047, MEMORY live-check entry), claude-code-wrapper PR #7 (5fd93ff, tag v0.3.2, release run 40653754978 attempt 2 success). Before the epic merged, the user cherry-picked three tasks' fixes to main as agents-orchestrator PR #29 (c042f79) and deployed them via agents-helmfile PR #36 (3b5004e). Deployed 2026-10-28 16:34Z by tatara-0 from agents-helmfile main 030c93d: orchestrator chart 0.1.0-main.b451f08 + image b451f08, agents-web chart 0.1.0-main.4d066a4 + image 4d066a4, agent image claude-code-wrapper:0.3.2; check-pins ok (9 pins); smoke OK including the continuity step. Live check: all agent StatefulSets OnDelete, idle pods replaced one per session, leaders last after handover, deployer pod kept its uid, no agent dead. Evidence: /workdir/workdir/.logs/deploy-safe-2026-10-28/live-check.md.

## Tasks

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

## Rulings

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

## Discovered and blocked

- Deployer pod agent-claude-code-tatara-0 was still busy on 0.3.1 at live-check time; the replacer rolls it when its turn ends (self-clearing; tatara-0 confirms the pod uid change).
- Live-check step 5 asked for status.rollout draining to empty; live-check.md does not record that observation (the deployer's roll was still pending). Cleared by: tatara-0, one read of the session status after the deployer's turn.
- Pre-existing: claude-code-wrapper tests/test_manager.py::test_shutdown_stops_all fails locally on base fb005fd. Noted, not doing now; cleared by the wrapper owner in a later wrapper epic.
- Local environment failures (CI authoritative): orchestrator test_lightkube_default_client_uses_env_config, helmfile template tests (Harbor 401 without login), test_reconnect_backoff_after_disconnect flaky once under load. No Docker in agent pods.
- Wrapper release run 40653754978 attempt 1 was cancelled (Harbor pull stalled to the 15 minute timeout); attempt 2 succeeded. Harbor owner.
- Deferred by non-goals and sticking: SIGTERM exit keystrokes, periodic (non-discard) transcript backups, in-cluster helmfile Job runner. Also noted: `_target_ready` omits `wrapper_session_id IS NOT NULL`; agents-helmfile has no CI workflows.

## Not pushed

- Superrepo /workdir/workdir main is 185 commits ahead of origin/main (this epic's ticket commits, the submodule pin 878ab4fa, and other epics' ticket commits). Pushed by tatara-0 or the user (the superrepo needs the https URL with the gh credential helper). This record and RETRO.md are written after the last commit and are uncommitted until committed.
- agents-orchestrator, agents-web, agents-helmfile and claude-code-wrapper: `git log origin/<base>..<base>` is empty for each; nothing unpushed. The origin branches deploy-safe-agent-sessions remain after merge.

## Lessons routed to

- Verified heads that rebase or cherry-pick leaves unreachable (7 here): add a check to `ticket.py close` that every task's verified_head is reachable from the repo's epic ref or base, or is re-recorded; mechanical, so a ticket.py test, not a skill edit.
- Per-task review rounds and the verification tail were not in any file (review: empty on all 27): add a check to `ticket.py task done` that its note carries rounds and the tail line; mechanical.
- Publish-gate defects reached the epic review (tag chart publish needing only chart, moving @main action with push secrets, no permissions block): add a lint test in each repo's CI test (tests/test_chart_ci.py, scripts/ci.test.mjs) that no workflow uses a moving ref and every publish job needs the full gate list; mechanical.
- Replacer ignored the dispatch reservation and the save rule ignored never-converged sessions: a judgement call (shared predicates must match the dispatcher's own idle condition); edit the start-review reviewer checklist, with the e2e test as the executable check.
- Live-check evidence was gathered by hand and missed the status.rollout drain: add a `mise run` live-check task in agents-helmfile that prints the AC step 5 observations; mechanical.
- A user hotfix cherry-picking epic tasks to main left their verified heads unreachable: judgement call; edit the start-development skill to record the main sha in the task Notes when work lands outside the epic branch.
- Estimates: live, e2e and wrapper tasks ran far above the seed minutes again (wrapper-shutdown-turn-resume 211 vs 8, orch-e2e-rollout-mid-turn 104 vs 8, helmfile-smoke-continuity 31 vs 8): the design already records this recurring pattern; edit the planner's estimate guidance in start-development, not a mechanical check.
