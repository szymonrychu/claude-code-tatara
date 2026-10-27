# leader auto handover record

## Asked

A hive leader (max_replicas > 1) passes leadership to another ready agent automatically before it compacts and before a scale-down removes its pod. Mechanism: a wrapper `compacting` event the orchestrator turns into an epoch-fenced handover at the leader's turn boundary, and a scale path that hands over first, both picking among ready agents that stay. Goals G1-G6: compaction handover, scale-down handover, eligibility among staying agents with retry, always on for hives and never for a cluster of one, reason in UI/API/stream with docs and e2e, release and deploy with a smoke step. Non-goals: no per-cluster switch, no holding of compaction, no threshold handover, no agent takeovers.

## Shipped

All 17 task files are done (15 planned, 2 added by the epic review). Epic review verdict: pass (2026-10-27); G1-G6 landed, no Act on items, findings dropped: none. Merged PRs, all on main:
- claude-code-wrapper PR #4 (merge ee10aa8; ef64fb0, 6d1d36e), tag v0.3.0 on ee10aa8: https://github.com/szymonrychu/claude-code-wrapper/pull/4
- agents-orchestrator PR #21 (merge 915207c; cc336cb..d56162d, 9 commits): https://github.com/szymonrychu/agents-orchestrator/pull/21
- agents-orchestrator PR #25 (merge 90f3ce3; 059372f, review follow-up, behaviour-preserving): https://github.com/szymonrychu/agents-orchestrator/pull/25
- agents-web PR #13 (merge d8769b1; d399857, b292688): https://github.com/szymonrychu/agents-web/pull/13
- agents-helmfile PR #28 (merge 5572e01; f73dc2c, e487037): https://github.com/szymonrychu/agents-helmfile/pull/28
- agents-helmfile PR #34 (merge b2b9033; b5ae9c3, c8141fa): https://github.com/szymonrychu/agents-helmfile/pull/34

Deploy: applied live. Orchestrator b3a2975 (contains 915207c), agents-web 4701820 (contains d8769b1), agent image claude-code-wrapper:0.3.0. 90f3ce3 (PR #25) is not applied (leader instruction: no apply in this epic). Live proof: session cc2f85d7-cd74-4ea1-be90-43cb597e3eec, leader moved to pod-0 agent db57c360 with leader_reason scale_down, message 69 answered "ok" (.logs/lah-live-proof.log); `mise run smoke` on agents-helmfile main 0ed86cf exited 0 (.logs/lah-smoke-ac1.log).

Epic-wide check in the closing pod (2026-10-27): lint green in all 4 repos. Tests red only for environment reasons: orchestrator 525 testcontainers errors (no Docker) plus 1 lightkube test reading the in-cluster env (predates the epic); helmfile 9 failed on Harbor 401 chart pull; wrapper 4 PTY/process-group/docker tests in files the epic does not touch (not proven pre-existing on a clean host). DB evidence comes from GitHub CI.

## Tasks

Every verified head below appears in the git log of its repo's main. Review rounds and verification tails exist in the orchestrator notes only for the three tasks closed in the closing session; for the other 14 the notes give none, so they are "unknown". The notes say "14/15 done" at hand-over; the files show 17 done, consistent with 15 planned plus 2 added.

| Task | Repo | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|---|
| wrapper-compacting-event | claude-code-wrapper | done | ef64fb0fbe913ca9f0a6a5ea2680ae242f04b485 | unknown | unknown |
| wrapper-release-0-3-0 | claude-code-wrapper | done | 6d1d36ef05da8f88467915b0ae340a6c15b26347 | unknown | unknown |
| compaction-status-projection | agents-orchestrator | done | cc336cb6b426e15c3689659727502205d4e2c3b8 | unknown | unknown |
| leadership-auto-handover | agents-orchestrator | done | d2ca76c8efe33e088a71b41117adfb526d579786 | unknown | unknown |
| scale-down-staying-peer | agents-orchestrator | done | 8d03b3830508c724abff19565ade9a7c82c4dae7 | unknown | unknown |
| claim-hold-and-handover-wake | agents-orchestrator | done | 712cc8c629b80940ed080dc8b25cb9682d4adec8 | unknown | unknown |
| reconciler-leader-pod-hold | agents-orchestrator | done | c61e41718c6f6dbe12bdade6cb2a8bfa604c887e | unknown | unknown |
| leader-changed-reason | agents-orchestrator | done | 8bb46459db60b14e86d848fa245c6b9ff7ea3f98 | unknown | unknown |
| orch-wrapper-pin-0-3-0 | agents-orchestrator | done | 2529aaf34592abcf2e28e2b2db7e04f8a510d7b5 | unknown | unknown |
| kind-e2e-auto-handover | agents-orchestrator | done | d56162d0a7d5a1fb2419d74301598fe054a17a09 | unknown | unknown (collect-only verify; e2e not run in the epic review, needs kind) |
| web-scale-hint | agents-web | done | d3998572f4fab98cc417c48e0513bd67a83aba1e | unknown | unknown |
| web-leader-reason | agents-web | done | b292688129e359cc918d54ecca42b18ea3cfb47c | unknown | unknown |
| smoke-scale-below-leader | agents-helmfile | done | f73dc2c2148b1ea2ee36d03398e2530eb7428198 | unknown | unknown |
| helmfile-deploy-pin | agents-helmfile | done | e487037cfeae15573f98693d5daed71904a92a99 | unknown | unknown |
| helmfile-apply-smoke | agents-helmfile | done | b5ae9c39ccd972dcbc8d354ab7130df0deec4ca7 | 1 (clean), no fix rounds | AC1 `mise run smoke` on main 0ed86cf exit 0, incl. "leader is 3af24cc9... with reason scale_down"; steps 1-4 run by the hive leader |
| smoke-step7-per-wait-deadlin (added by review) | agents-helmfile | done | c8141fa00c2a2603470bf0dce369e36086353ed7 | 1 (clean), no fix rounds | "113 passed in 253.52s", lint green; both new tests fail on pre-fix smoke.sh; implementer showed red then green |
| orch-eligibility-single-sour (added by review) | agents-orchestrator | done | 059372fcd3ce0453be243bd7b62ad1a15fd67d56 | 1 (clean) after a line-by-line SQL equivalence check, no fix rounds | PR #25 CI: "1083 passed, 56 deselected, 1 warning in 205.29s"; kind e2e pass; main CI on 90f3ce3 success; DB tests not runnable in the pod (no Docker) |

Done 17 of 17 task files (15 planned plus 2 added). Escalations: none. Fix rounds in the closing session: none.

## Rulings

- Two review "Consider" items promoted to tasks instead of dropped: (1) agents-helmfile smoke step 7 reused the scale-up deadline for the agent lookup and make-leader waits, and MEMORY claimed each wait had its own deadline; (2) duplicated eligibility and handover-pending SQL predicates in agents-orchestrator. Why: both are drift or flake risks inside the epic's own feature. Cost if wrong: (1) spurious smoke failures on a slow pod-1 and a false MEMORY line; (2) the pass, the claim hold and set_replicas drifting apart on who may lead. Both were small and done; the (2) refactor touched the hottest SQL, guarded by existing tests plus CI.
- `_target_ready` kept without the `wrapper_session_id IS NOT NULL` requirement (manual make-leader target), exactly as before, in orch-eligibility-single-sour. Why: the refactor must not change behaviour; whether the omission is intended was left as written in the task. Cost if wrong: a manual make-leader target can be an agent the automatic pick would not choose.
- PR #25 (90f3ce3) left unapplied. Why: leader instruction, no apply in this epic. Cost if wrong: live orchestrator b3a2975 lacks the refactor; none functionally (behaviour-preserving).
- helmfile-apply-smoke steps 1-4 (diff, apply, live proof) were run by the hive leader, not the implementer. Why: cluster actions are the orchestrator's. Cost if wrong: none observed; evidence logged in .logs.
- Findings dropped: none. Escalations judged: none.

## Discovered and blocked

- Blocked: none.
- Environment, orchestrator DB tests: no Docker in agent pods, so testcontainers tests are CI-only evidence (about 16 min delay per PR). Clearable by: whoever owns the agent pod image/runtime (Docker or a Postgres service).
- Environment, other red tests in the pod: lightkube test `test_lightkube_default_client_uses_env_config` fails under an in-cluster service account (test predates the epic); helmfile tests need Harbor credentials (401); wrapper `test_example_config_validates_in_image`, `test_shutdown_stops_all`, `test_exit_without_eof_still_fires`, `test_close_terminates_group_then_kill` fail in this pod, not proven pre-existing on a clean host. Clearable by: the component owners, by running on a host with Docker and registry credentials.
- agents-helmfile has no CI workflows (only GitGuardian), so PR #34 rested on the reviewer's local verification. Clearable by: the agents-helmfile owner adding a workflow.
- Stale stash entry in code/agents-orchestrator (stash@{0}, duplicate bc3b4ff of content already committed in 059372f). The guard-bash hook refuses to drop stash entries. Clearable by: a human running `git stash drop`.
- Unproven live: real Claude Code firing PreCompact before an auto compaction (only the fake claude proves it); no live `compacting` event observed since the apply. Clearable by: a live observation on the next real compaction.
- Design assumptions noted by the review: the busy-leader race is pinned at queue level only (`test_compacted_leader_never_takes_next_message` cannot force it); correctness near an election assumes wrapper pod and DB clocks agree (`compaction_at > l.since`).
- Not run: kind e2e `test_leader_compaction_hands_over` and `test_scale_down_below_leader_hands_over` in the epic review (need kind); PR #25 CI ran the kind e2e and passed. Harbor artifacts and release.yaml success for v0.3.0: tag verified on origin only.
- Side note: turn_completed events are stored with top-level turn_id null (data.record carries it), so filtering events by turn_id misses them. Clearable by: the orchestrator ingester owner.
- File inconsistency: README frontmatter still says `stage: review` while the epic sits in docs/plans/done. Clearable by: the supervisor via ticket.py.

## Not pushed

- Components: nothing committed locally and unpushed. `git log origin/main..main` is empty in claude-code-wrapper, agents-orchestrator, agents-web and agents-helmfile. Local main trails origin in agents-orchestrator (b3a2975 vs origin 90f3ce3) and agents-helmfile (0ed86cf vs origin b2b9033); the superrepo pointers were advanced to 90f3ce3 and b2b9033 in f2ad0402.
- Superrepo: local main is 89 commits ahead of origin/main (9 of them leader-auto-handover: c3164b73 retro, e051863a move done, f2ad0402 pointers, b0f124fa review pass, 95c15f0d stage review, 37bda172, bd1e74c5, ca655269, 2aeb205e; the rest belong to other epics). The record.md is uncommitted. Who pushes: the human or the hive leader (tatara-1).

## Lessons routed to

- Session gitconfig had no user identity and no gh credential helper, so `ticket.py new-task` failed to commit. Check: a preflight in ticket.py (and a test) that fails early with a clear message when `git config user.name`, `user.email` or the gh credential helper is missing.
- `ticket.py new-task` emits template Interfaces/Expected outcome/Steps/Notes sections that `amend` refuses ("empty Steps section"), so the supervisor filled them by hand. Check: a ticket.py test that a fresh new-task file passes the same validation `amend` applies, or new-task rejects it up front.
- AC evidence kind `file:` is not accepted, only `symbol:`. Check: make the validator error list the accepted kinds, with a test on the message.
- A bare `git stash` by an implementer left a stash the guard-bash hook then refused to drop. Check: a guard-bash hook rule (and test) refusing bare `git stash` while keeping drop refused, so the mistake cannot be made.
- agents-helmfile has no CI. Check: add a CI workflow running `mise run lint` and the offline tests in agents-helmfile.
- No Docker in agent pods makes DB tests CI-only. Judgement call: edit the epic-run skill to say DB-backed task evidence is the PR CI result, and to wait for it before closing the task.
- "Each wait gets its own deadline" was asserted in MEMORY.md while the code reused one. Check: the added tests in smoke-step7-per-wait-deadlin pin it; no further action.
