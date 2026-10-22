# claude-code-wrapper orchestrator support record

## Summary

Asked: seven additive claude-code-wrapper changes for agent-orchestrator (idle_since, user_message event, backward history, GET /v1/peers, statusline relay, context surface, onStart hook), A1-A8 in approvals.json.
Shipped: all 11 tasks (8 planned feature tasks + 3 review-driven follow-ups + vocabulary-pins; 11 task files), merged as PR #1 (ca2ddf3). Full suite on epic tip 1594 passed, 12 deselected (810s); lint clean.
Verdict: pass (2026-10-23). All approvals delivered. Two tasks were accepted by ruling rather than by a clean verifier pass (idle-since-in-snapshot, vocabulary-pins).

## Planned vs built

Verifier head = `tasks[].verification.head` from the plan-execute returns (return1..4). Run = which return it landed in. Red = implementer's own `tests.red`; "none recorded" means the return has no `tests.red`.

| Task | Run | Status | Rounds | Files (from return) | Verifier head | Red / verification |
|---|---|---|---|---|---|---|
| idle-since-in-snapshot | 1 | done, accepted by ruling (land-failed) | 1 | session.py, manager.py, router.py, README.md, test_idle_since.py, test_router.py | 9961bc9 | red none recorded (tests written after code); 11 passed, ruff clean per ruling |
| on-start-instance-hook | 1 | done | 1 | config.py, hooks.py, service.py, README.md, config.example.yaml, test_on_start_hook.py, test_config.py, test_peer_hooks.py | 7f04ddc | red: `pytest tests/test_on_start_hook.py -q` FAILED before code |
| peer-mesh-view-route | 1 | done | 1 | peers.py (x2), app.py, README.md, test_api_peers_view.py | 8926100 | red: `pytest tests/test_api_peers_view.py -q` FAILED before code |
| user-message-event | 2 | done | 2 | return lists only test_user_message_event.py (code in sibling commit 795b27d; files disagree with a one-file summary) | d9c061f | red none recorded |
| history-before-seq-and-types | 2 | done | 1 | events.py (x2), README.md, test_history_backward.py, test_event_log.py | e6c6e4b | red: `pytest tests/test_history_backward.py -q` FAILED before code |
| statusline-relay | 2 | done | 1 | statusline.py, cli.py, internal_api.py, settings.py, router.py, README.md, test_statusline_relay.py, test_internal_api.py | 8fa8c5f | red none recorded |
| context-in-snapshot-and-sse | 2 | done | 2 | return lists only test_context_surface.py (code in f84ef67) | 25d4cc1 | red none recorded |
| history-scan-off-event-loop | 3 | done | 2 | events.py, test_event_log.py | d41dd76 | red none recorded |
| statusline-absolute-command | 3 | done | 2 | README.md only in this task's diff (code/test in sibling commit 976c968 per process gap) | 8cad3c4 | red none recorded |
| statusline-input-validation | 3 | done | 3 | internal_api.py, test_internal_api.py | 195bfac | red: `pytest tests/test_internal_api.py -q -k overflowing` FAILED before code |
| vocabulary-pins | 4 | done, accepted by ruling (gate-repeat) | 3 | test_command_vocabulary.py | 4d1989e (verifier FAILED: stale .pyc; hand-verified) | tests.red in the return is a tdd-revert command (`git show HEAD~1:... > tests/...`); not quoted as red. Red evidence: epic full-suite log `assert 21 == 20`. Hand run: 31 passed on 4d1989e |

Run 1 also stopped four tasks as dependency-failed (context-in-snapshot-and-sse, history-before-seq-and-types, statusline-relay, user-message-event) because idle-since-in-snapshot land-failed; they were rebuilt in run 2 after the ruling. Their `unverified` status in return1 is superseded by return2.

Approvals (A1-A8 from approvals.json; status from the latest return that carries the entry, A1 and A8 cross-checked against the review notes scope audit "every approval item A1-A8 landed"):

| Id | Text | Decisions | Tasks | Status |
|---|---|---|---|---|
| A1 | Snapshot idle_since and session_state since | D1 | idle-since-in-snapshot | delivered (ruling accepted land-failed; return1 showed escalated) |
| A2 | user_message event for every pasted prompt | D2 | user-message-event | delivered |
| A3 | History pages backwards (before_seq, types) | D3 | history-before-seq-and-types, history-scan-off-event-loop | delivered |
| A4 | GET /v1/peers peer mesh view | D4 | peer-mesh-view-route | delivered |
| A5 | Statusline relay | D5 | statusline-relay, statusline-absolute-command, statusline-input-validation | delivered |
| A6 | Context usage in snapshot and SSE | D6 | context-in-snapshot-and-sse | delivered |
| A7 | Fixed in wrapper; README per task; targeted verify; rebase note | D7 | 7 tasks incl. vocabulary-pins | delivered (return4 showed escalated gate-repeat; ruling accepted) |
| A8 | onStart instance hook once per process start | D8 | on-start-instance-hook | delivered (absent from returns 2-4 because landed in run 1; run 1 approvals list not read past A7, so status comes from the scope audit) |

## Deviations and rulings

- idle-since-in-snapshot land-failed accepted (rulings.json, 2026-10-22T22:37Z). Why: suite-lock contention (lock held 1200s by the template epic close, pid 79691), not a code failure; verified on 9961bc9, 11 passed, ruff clean. Cost if wrong: a real landing defect in session/manager/router would ride into the PR; mitigated by the later full-suite run (1594 passed). Process gap kept: tests written after code, no red run.
- vocabulary-pins gate-repeat accepted (rulings.json, 2026-10-22T23:17Z). Why: verifier hit a stale pytest assertion-rewrite .pyc (20->21 edit keeps file size). Hand-verified after deleting the .pyc: `uv run pytest tests/test_command_vocabulary.py tests/test_event_log.py -p no:cacheprovider` -> 31 passed; ruff clean. Cost if wrong: the 21st-hook-event pin could be unpinned; mitigated by the full-suite pass on the tip.
- Review-driven follow-up tasks added after the whole-diff review: statusline-absolute-command, statusline-input-validation, history-scan-off-event-loop (each acted on a medium finding or security finding). Cost if wrong: extra scope; all three landed with verifier heads.
- Dropped finding: onStart full-env (operator-configured, matches preJoin/postJoin). Cost if wrong: hook inherits full process env.
- forwardMerged: none in any return.

## Duplicates reconciled

none (duplicates empty in all four returns).

## Discovered and blocked

- Pre-existing `tests/test_event_log.py::test_event_types_exact` failure (expected list lacked `context`), found at history-scan-off-event-loop; fixed in d41dd76 ("event types test includes context").
- cannotVerify, not settled by a ruling, nobody can clear without a live environment (Szymon / agent-orchestrator deploy):
  - Live Claude Code statusline JSON shape (current_usage null before first call and after /compact) against a real claude; only parse_statusline-built fixtures tested.
  - Whether context stays null after compaction until the next statusline in a real session.
  - Live pod behaviour of the onStart hook (on-start-instance-hook).
  - Behaviour under a real multi-MB event file, concurrent appends and rotation (history-scan-off-event-loop).
  - Orchestrator-side routing on idle_since (outside this repo; agent-orchestrator).
- Declined findings (implementer/reviewer): non-numeric current_usage values 500 (later fixed by statusline-input-validation, 446a247/5b6e994/195bfac); README timestamp style +00:00 vs Z (style only); forward page() byte bound with rare types filter.
- Rebase onto origin/main before the PR (session claude-code-wrapper-58 develops concurrently): process gap flagged in return1; PR merged with CI passed. Rebase state not read from the files: unknown.
- Other process gaps: statusline-absolute-command diff command covered README only, code reviewed via merge-base diff.
- Contradiction: for user-message-event and context-in-snapshot-and-sse the return lists only the test file while the git log shows feature commits (795b27d, f84ef67); the log wins.

## Research that changed the plan

none recorded. The design source is section 4 of the orchestrator design doc; the onStart task (A8) was added after a gap found at the agent-orchestrator gate (onCreate runs after claude starts; setup_commands run per created session only).

## Cost

Agents by role, continuations and wall-clock: unknown (not in the returns read). Audit: off in all four runs; scope audit run once in the review phase. Review rounds per task in the table (total 21 across 11 tasks).

| Task | Estimate (min) | Actual |
|---|---|---|
| idle-since-in-snapshot | 6 | unknown |
| user-message-event | 6 | unknown |
| history-before-seq-and-types | 6 | unknown |
| peer-mesh-view-route | 6 | unknown |
| statusline-relay | 6 | unknown |
| context-in-snapshot-and-sse | 6 | unknown |
| on-start-instance-hook | 6 | unknown |
| vocabulary-pins | 6 | unknown |
| history-scan-off-event-loop | 5 | unknown |
| statusline-absolute-command | 5 | unknown |
| statusline-input-validation | 5 | unknown |

README Time: Estimate 63 agent-min, critical path 41 min, expected wall 1.4 h at P=1.5 (k=2.0), Actual 0 min (task `actual` fields empty), remaining estimate 6 min. Task estimates above sum to 63.

## MRs and deploy

https://github.com/szymonrychu/claude-code-wrapper/pull/1 - CI passed, merged as ca2ddf3. Full suite on tip: 1594 passed, 12 deselected; lint clean. Deploy: not confirmed (agent-orchestrator pod rollout out of scope here).

## Lessons routed to

- Tests written after code (idle-since-in-snapshot, 6 of 11 tasks have no tests.red): mechanical. Add a plan-execute gate that fails a behaviour task whose return has an empty `tests.red`.
- Stale pytest .pyc caused a false verifier gate-repeat (vocabulary-pins): mechanical. verify-task.py should run pytest with `-p no:cacheprovider` and clear `__pycache__` of touched test files before verifying.
- Suite lock held 1200s by another epic caused a false land-failed: mechanical. Land step should report lock holder and retry with a bounded wait instead of failing.
- Gap found only at the downstream gate (onStart hook): judgement call. Edit the start-development design checklist to name per-pod startup ordering for consumer integrations.
- Review findings (absolute command, numeric validation, blocking scan) surfaced only after build: judgement call; add input-validation and event-loop-blocking items to the implementer review rubric.
