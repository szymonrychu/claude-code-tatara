# deploy-safe agent sessions implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: helmfile pin check

- Status: done
- Files: `scripts/check_pins.py`, `tests/test_check_pins.py`, `tests/fixtures/check_runs_agents_orchestrator.json`, `mise.toml`, `tests/test_mise_tasks.py`, `README.md`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_check_pins.py tests/test_mise_tasks.py && mise run lint`
- Verified head: fdedfc74fbedcc32063e8b3198523ebbbd1a1f71

#### Requirement

Design D9, user decision verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator, web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no override flag. Its tests use fakes like tests/test_smoke_script.py."

Design D9 (my call), verbatim: "The pin check calls `gh api repos/szymonrychu/<repo>/commits/<ref>/check-runs` from a script in agents-helmfile: the submodule is an independent repo and cannot import the workbench's `_lib/scm.py`. A pin passes only when at least one check run exists and every one is `completed` with conclusion `success`, `neutral` or `skipped`. `0.1.0-main.<sha7>` resolves to that commit; a release version `X.Y.Z` (agents-schedule chart `0.1.0`, wrapper image `0.3.2`) resolves through tag `vX.Y.Z`. `mise run apply` depends on it."

Goal G8, verbatim: "No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green."

Scope (agents-helmfile):
- `scripts/check_pins.py` (run with `uv run`): reads the pins from `helmfile.yaml.gotmpl` (chart `version:` of agents-orchestrator, agents-web, agents-webhook, agents-schedule, agents-matrix-connector) and `values/agents-orchestrator/common.yaml` (`image.tag`, `agentImage`, `env.ORCH_AGENT_IMAGES`) and `values/agents-web/common.yaml` (`image.tag`); maps each to its GitHub repo (`szymonrychu/<repo>`, the wrapper image to `claude-code-wrapper`); resolves `0.1.0-main.<sha7>` or an image sha7 to the commit, `X.Y.Z` through tag `vX.Y.Z`; lists the commit's check runs through `gh api` (paginated); prints one line per pin and exits non-zero naming each refused pin (repo, version, commit, and the checks that are not green). A missing or unparsable pin is a refusal, never a pass. No flag or env var skips it.
- `mise.toml`: task `check-pins` (description names what it checks); `apply` depends on `check-pins`; `gh` pinned in `[tools]` if the repo does not already provide it (probe the version, never guess).
- `tests/test_check_pins.py`: a fake `gh` on PATH (the fakebin pattern of `tests/test_smoke_script.py`) serving responses built from a real `gh api repos/szymonrychu/agents-orchestrator/commits/<sha>/check-runs` response captured once and committed as `tests/fixtures/check_runs_agents_orchestrator.json` (retro: fakes must follow a captured real output).
- `tests/test_mise_tasks.py`: `apply` depends on `check-pins`.
- `README.md` (Operating) names the task; MEMORY.md dated entry.

Interfaces: `mise run check-pins` exit 0 only when every pin is green; output lines `pin <release> <version> <commit>: ok|refused (<reasons>)`.

Steps: capture the real response first (`gh api repos/szymonrychu/agents-orchestrator/commits/96e46f3/check-runs > tests/fixtures/check_runs_agents_orchestrator.json`, secrets-free); write the tests and see them fail; then the script and the task; run the verify.

Notes: against today's pins the check must refuse agents-orchestrator 96e46f3 (main CI run 40565058706, e2e failed), which is the incident this guards. `mise run apply` is never run by this task. gitleaks runs in lint: keep the fixture free of tokens.

#### Acceptance conditions

- AC1: every pin source is resolved: orchestrator, web, webhook, schedule and matrix-connector charts, the orchestrator and web image tags, agentImage and ORCH_AGENT_IMAGES [evidence: test:tests/test_check_pins.py::test_every_pin_resolved]
- AC2: pins whose check runs are all completed success, neutral or skipped pass with exit 0 [evidence: test:tests/test_check_pins.py::test_green_pins_pass]
- AC3: a failed, cancelled, timed-out, in-progress or absent check run refuses with the repo, version, commit and check names and a non-zero exit [evidence: test:tests/test_check_pins.py::test_red_pin_refused]
- AC4: a release version X.Y.Z resolves through tag vX.Y.Z [evidence: test:tests/test_check_pins.py::test_release_version_resolves_through_tag]
- AC5: no flag or environment variable skips the check [evidence: test:tests/test_check_pins.py::test_no_override]
- AC6: the fake gh serves responses built from a captured real check-runs response [evidence: test:tests/test_check_pins.py::test_fixture_is_real_check_runs_shape]
- AC7: apply depends on check-pins [evidence: test:tests/test_mise_tasks.py::test_apply_depends_on_check_pins]
- AC8: README names every task, check-pins included [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- AC9: against today's pins the live check refuses agents-orchestrator 96e46f3 [evidence: command:mise run check-pins 2>&1 | grep -q "agents-orchestrator.*96e46f3.*refused"]
- AC10: MEMORY.md records the decision [evidence: command:grep -q "check-pins" MEMORY.md]
- AC11: lint passes [evidence: command:mise run lint]

#### Files

- `scripts/check_pins.py`
- `tests/test_check_pins.py`
- `tests/fixtures/check_runs_agents_orchestrator.json`
- `mise.toml`
- `tests/test_mise_tasks.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_check_pins.py tests/test_mise_tasks.py && mise run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_check_pins.py tests/test_mise_tasks.py && mise run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done

### S2: helmfile smoke continuity

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `mise.toml`, `README.md`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_smoke_script.py && mise run lint`
- Verified head: bdc3fca6aa195282273226c8a46b774a41697c33

#### Requirement

Design D12, user decision verbatim: "smoke.sh in agents-helmfile gets a session-continuity check if a safe trigger exists without rolling real agents; otherwise record why not (my call)."

Design D12 (my call), verbatim: "A safe trigger exists: deleting the pod of a session the smoke itself created (smoke already scales its own session's pods). After one real turn, the pod is deleted; the smoke asserts the pod returns Ready, the agent's wrapper session id is unchanged, the agent is not `dead`, and a message sent after the restart reaches `sent`. No user session and no template change is involved."

Goal G1, verbatim: "After an agent pod restart and a successful wrapper resume, the ingester re-attaches from the last stored event, the agent leaves `dead`, and queued messages are delivered (the 20:07-20:29 hang cannot recur)."

Scope (agents-helmfile):
- `scripts/smoke.sh`: a session-continuity step on a session the smoke created (reuse one it already makes or create `smoke-cont-<ts>`, deleted by the trap): post a message and wait for `sent` (so a transcript exists); read the agent's `wrapper_session_id` from the events API (`GET /api/v1/sessions/{id}/events?agent_id=...`); record the pod uid; `kubectl delete pod` that pod only; wait for a new uid and Ready; wait until the agent view's state is not `dead`; post a second message and wait for `sent`; assert the events after the restart carry the same `wrapper_session_id`. Each wait has its own deadline (leader-auto-handover retro). Outputs are matched, never printed.
- `tests/test_smoke_script.py`: the fake API and fake kubectl model the restart (new uid, resumed agent) and the failure cases.
- `mise.toml` smoke description, README `Operating` smoke paragraph and the header comment of `smoke.sh` mention the step; MEMORY.md dated entry with why this trigger is safe.

Steps: tests first, seen failing; then the step; run the verify. The live run is task helmfile-apply-live-check.

Notes: subagent `kubectl exec` is denied by the classifier; this step needs no exec. Never touch a session the smoke did not create. The deployed orchestrator must carry the re-attach fix (task orch-ingester-reattach) for the live run to pass; the unit tests use fakes only.

#### Acceptance conditions

- AC1: after one turn the smoke deletes its own session's pod, sees a new Ready pod, the same wrapper session id, an agent that is not dead and a second message reaching sent [evidence: test:tests/test_smoke_script.py::test_session_continuity_after_pod_restart]
- AC2: a changed wrapper session id after the restart fails the smoke naming the step [evidence: test:tests/test_smoke_script.py::test_continuity_new_wrapper_session_fails]
- AC3: an agent that stays dead fails the smoke within its own deadline [evidence: test:tests/test_smoke_script.py::test_continuity_dead_agent_fails]
- AC4: a message after the restart that never reaches sent fails within its own deadline [evidence: test:tests/test_smoke_script.py::test_continuity_message_not_delivered_fails]
- AC5: the step deletes only the pod of a smoke-created session [evidence: test:tests/test_smoke_script.py::test_continuity_deletes_only_smoke_pod]
- AC6: the whole smoke test file passes [evidence: command:uv run pytest -q tests/test_smoke_script.py]
- AC7: README and MEMORY.md describe the step and why the trigger is safe [evidence: command:grep -q "continuity" README.md && grep -q "continuity" MEMORY.md]
- AC8: lint passes [evidence: command:mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `mise.toml`
- `README.md`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_smoke_script.py && mise run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_smoke_script.py && mise run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 done

### S3: orch dead agent ineligible

- Status: done
- Files: `src/agents_orchestrator/db/eligibility.py`, `src/agents_orchestrator/db/leadership.py`, `tests/test_dead_agent_eligibility.py`, `tests/test_eligibility_fragments.py`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_dead_agent_eligibility.py tests/test_eligibility_fragments.py tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: c822ff50fd66d41c7ce30089ca9f5151fd7a8559

#### Requirement

Design D4, user decision verbatim: "Leader eligibility excludes agents whose agent_status is dead (db/eligibility.py), all call sites covered by tests."

Goal G2, verbatim: "A dead agent is never eligible as leader; leadership moves to a live agent."

Design D4 (my call), verbatim: "Both `ELIGIBLE` and `READY_STAYS` (the manual make-leader target) exclude a dead agent; a leader whose agent is dead is handled as a lost leader (moved after `LEADER_GRACE_SECONDS`, reason `leader_lost`), so G2's "leadership moves to a live agent" holds. This is the exclusion itself, not a new handover rule (README non-goal)."

Scope (agents-orchestrator):
- `src/agents_orchestrator/db/eligibility.py`: one fragment excludes an agent whose `agent_status.state` is `dead` (an agent with no status row stays eligible as today); `READY_STAYS` and `ELIGIBLE` embed it. Every predicate stays spelled once here (module rule); the module docstring cites D4.
- `src/agents_orchestrator/db/leadership.py`: `_CANDIDATES` also selects a hive whose leader's agent is dead; the lost-leader step (step 4) treats a dead leader like a not-ready one (`unready_since` set on first sight, moved after `LEADER_GRACE_SECONDS` to `_free_longest`, reason `leader_lost`, cleared when it is live again).
- Call sites covered by tests (new file `tests/test_dead_agent_eligibility.py`, real Postgres like `tests/test_leadership_pass.py`): the initial pick, `_free_longest` (queued handover, compaction, scale-down, lost leader), `_target_ready` (manual make-leader), `db/queue.py:_HANDOVER_PENDING` (claim hold) and `db/sessions.py:set_replicas`.

Interfaces: `db/eligibility.py` constants `READY_STAYS`, `ELIGIBLE` keep their names and the agent alias `a`; `leadership_pass` signature unchanged.

Steps: write the tests first and see them fail on main (a dead agent is picked); then the fragment and the lost-leader change; run the verify.

Notes: no Docker in agent pods, so the DB tests error locally (testcontainers); the PR CI run is the evidence (retro, recurring). Reuse the fixtures of `tests/test_leadership_pass.py` and `tests/test_queue_leader_routing.py`. `queue.py` and `sessions.py` need no edit: they embed `ELIGIBLE`. MEMORY.md gets a dated entry with the why.

#### Acceptance conditions

- AC1: a dead agent is never the initial leader [evidence: test:tests/test_dead_agent_eligibility.py::test_dead_agent_never_initial_leader]
- AC2: a handover (queued request, compaction or scale-down) never picks a dead agent [evidence: test:tests/test_dead_agent_eligibility.py::test_dead_agent_never_handover_target]
- AC3: a manual make-leader request to a dead agent is rejected target_not_ready [evidence: test:tests/test_dead_agent_eligibility.py::test_make_leader_to_dead_agent_rejected]
- AC4: a dead leader is replaced by a live agent after the grace, reason leader_lost [evidence: test:tests/test_dead_agent_eligibility.py::test_dead_leader_replaced_after_grace]
- AC5: the claim hold does not wait for a handover when only dead agents could take over [evidence: test:tests/test_dead_agent_eligibility.py::test_claim_hold_ignores_dead_peer]
- AC6: set_replicas counts a dead staying agent as unable to lead [evidence: test:tests/test_dead_agent_eligibility.py::test_set_replicas_counts_dead_agent_ineligible]
- AC7: the shared fragments exclude dead agents and stay spelled once [evidence: test:tests/test_eligibility_fragments.py::test_eligible_excludes_dead_agents]
- AC8: the existing leadership and routing suites pass [evidence: command:uv run pytest -q tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py tests/test_eligibility_fragments.py]
- AC9: MEMORY.md records the decision [evidence: command:grep -q "dead agent" MEMORY.md]
- AC10: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/eligibility.py`
- `src/agents_orchestrator/db/leadership.py`
- `tests/test_dead_agent_eligibility.py`
- `tests/test_eligibility_fragments.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_dead_agent_eligibility.py tests/test_eligibility_fragments.py tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_dead_agent_eligibility.py tests/test_eligibility_fragments.py tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S4: orch e2e main failure

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `tests/e2e/conftest.py`, `scripts/e2e.sh`, `MEMORY.md`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5736cbf25d5b742cf0e4491f4206dc09af93258b

#### Requirement

Design D10, user decision verbatim: "The orchestrator main CI e2e failed on run 40565058706 (commit 96e46f3) while the PR run 40562435463 passed: one task diagnoses it from the run log (gh run view --log-failed) and fixes the cause, so gating on e2e keeps main green."

Planner probe (read-only, 2026-10-27), verbatim from design D10: "the failed test is `tests/e2e/test_e2e_kind.py::test_in_session_pod_refused_by_allowlist`, `httpx.RemoteProtocolError: Server disconnected without sending a response.` on the port-forwarded `api` client, `1 failed, 39 passed`. The cause is the task's to confirm."

Scope (agents-orchestrator):
- Read `gh run view 40565058706 --repo szymonrychu/agents-orchestrator --log-failed` and compare with PR run 40562435463; name the cause (the line and the evidence) in MEMORY.md.
- Fix the cause in `tests/e2e/test_e2e_kind.py`, `tests/e2e/conftest.py` or `scripts/e2e.sh`. A retry that hides a product defect is not a fix: a cause in `src/` is returned as a discovered item (what, where, why) instead.
- The fixed test keeps its assertions (403 forbidden from an in-session pod, health exempt, loopback allowed).

Steps: read the log; reproduce or explain; fix; `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`; the PR CI e2e job (kind) passes.

Notes: no Docker or kind in agent pods: the PR CI e2e job is the evidence (about 16 min). This task runs before orch-ci-publish-gate so gating on e2e does not block a green main.

#### Acceptance conditions

- AC1: MEMORY.md names the cause of the run 40565058706 e2e failure with its evidence [evidence: command:grep -q "40565058706" MEMORY.md]
- AC2: the e2e tests are collected [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC3: the kind e2e passes, test_in_session_pod_refused_by_allowlist included, with its assertions unchanged [evidence: command:mise run test:e2e]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `tests/e2e/conftest.py`
- `scripts/e2e.sh`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S5: orch ingester reattach

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0009_wrapper_resume.sql`, `src/agents_orchestrator/db/agents.py`, `src/agents_orchestrator/reconciler/wrapper_sessions.py`, `src/agents_orchestrator/ingester/loop.py`, `tests/test_ingester.py`, `tests/test_wrapper_session_bootstrap.py`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_migrations.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 4ca88eacea5f0c226b8b917c505e1991269c8f62

#### Requirement

Design D3, user decision verbatim: "Ingester root cause: the bootstrapper's successful resume becomes a re-attach trigger (e.g. a resume generation/timestamp on the agent row included in AgentRef or equivalent); a stored session_closed is honoured only if no resume happened after it; re-attach replays from the last stored seq (wrapper keeps seq across resume; carto-orchestrator.md item 1). Amend tests/test_ingester.py:723 with the reason. Also mark the agent idle/ready again on re-attach so the dispatcher delivers."

Design D3 (my call), verbatim: ""After it" is decided by database order (the events row id or the database clock), never by comparing the wrapper's event `ts` with the database clock (clock-skew debt recorded by leader-auto-handover)." and "The marker is a new column on `agents` written only by the reconciler (the agents row's writer), in a new migration numbered after the highest one on main when the task runs (0008 today; 0009 if slash-commands-from-chat's `0008_slash_messages.sql` lands first)."

Goal G1, verbatim: "After an agent pod restart and a successful wrapper resume, the ingester re-attaches from the last stored event, the agent leaves `dead`, and queued messages are delivered (the 20:07-20:29 hang cannot recur)."

Scope (agents-orchestrator):
- Migration `src/agents_orchestrator/db/migrations/0009_wrapper_resume.sql` (renumber to the next free number on main): the resume marker column on `agents`.
- `db/agents.py`: write the marker on a successful resume (database clock or a counter); `Agent` carries it.
- `reconciler/wrapper_sessions.py`: both resume paths (the stored session and `_pick`) record the marker; adopt and create do not.
- `ingester/loop.py`: `AgentRef` includes the marker, so `refresh` restarts the stream after a resume; `_stored_closed` honours a stored `session_closed` only when no resume was recorded after it; the re-attach streams from `events.last_seq` (the wrapper continues seq across resume, SSE replay stops at a replayed close, so `after_seq >= close seq` streams live); the attach projects the snapshot state (a resumed `ready` becomes `idle`, `notify_agent_free` fires) so the dispatcher delivers. Module docstring updated (it says `session_closed` ends the task "until the reconciler records a new session").
- Test no longer accurate, to amend: `tests/test_ingester.py::test_session_closed_marks_dead_and_stops` (line 723) still asserts dead and no reconnect when no resume followed the close; its docstring states why the old "until a new session" rule changed (D3).

Interfaces: `AgentRef(agent_id, session_id, wrapper_session_id, url, <marker>)`; `agents_repo.set_wrapper_session(..., resumed=...)` or a separate `mark_resumed`; the migration is additive.

Steps: tests first in `tests/test_ingester.py` and `tests/test_wrapper_session_bootstrap.py`, seen failing (the agent stays dead after a resume); then the migration and code; run the verify.

Notes: DB tests need Docker; PR CI is the evidence. Replayed events below `last_seq` are never re-projected (existing `_store` rule). MEMORY.md: dated entry on the root cause and the marker.

#### Acceptance conditions

- AC1: after a resume of the same wrapper session the ingester re-attaches from the last stored seq and stores the later events [evidence: test:tests/test_ingester.py::test_resume_reattaches_from_last_stored_seq]
- AC2: a stored session_closed followed by a recorded resume is not honoured: the agent leaves dead and its stream runs [evidence: test:tests/test_ingester.py::test_closed_before_resume_not_honoured]
- AC3: the re-attach marks a ready agent idle and notifies agent_free so the dispatcher delivers [evidence: test:tests/test_ingester.py::test_reattach_marks_idle_and_notifies]
- AC4: a session_closed with no later resume still marks the agent dead and stops the stream, the test states the reason for the amendment [evidence: test:tests/test_ingester.py::test_session_closed_marks_dead_and_stops]
- AC5: events replayed on a re-attach are not projected again [evidence: test:tests/test_ingester.py::test_reattach_does_not_reproject_replayed_events]
- AC6: both resume paths record the resume marker; adopt and create do not [evidence: test:tests/test_wrapper_session_bootstrap.py::test_successful_resume_records_resume_marker]
- AC7: the migration applies on a fresh and an existing database [evidence: test:tests/test_migrations.py::test_rerun_is_noop]
- AC8: MEMORY.md records the root cause and the fix [evidence: command:grep -q "re-attach" MEMORY.md]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/migrations/0009_wrapper_resume.sql`
- `src/agents_orchestrator/db/agents.py`
- `src/agents_orchestrator/reconciler/wrapper_sessions.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
- `tests/test_wrapper_session_bootstrap.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_migrations.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_migrations.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S6: orch onstart nonfatal

- Status: done
- Files: `src/agents_orchestrator/k8s/render.py`, `src/agents_orchestrator/k8s/on_start.py`, `tests/test_render.py`, `tests/test_on_start.py`, `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_render.py tests/test_on_start.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 289be85a6859eb7a923fd98ce8feb045ceafefcc

#### Requirement

Design D6, user decision verbatim: "onStart plugin install: stays blocking (tools ready before sessions resume) but with on_error allow, and the on_start.py script logs and swallows an install failure (never exits non-zero for it, never exit 2); a failed install leaves the pod Ready."

Design D6 (my call), verbatim: "Both installs are covered: the any-mcp package install (then `.ref` is not written, so the next start retries) and `any-mcp plugins install`; the trailing `any-mcp --help` check is skipped after a failed install. Each failure prints one line to stderr naming the step."

Goal G5, verbatim: "A failed any-mcp plugin install in onStart is logged and leaves the agent pod Ready."

Scope (agents-orchestrator):
- `k8s/render.py`: the onStart hook stays `blocking: True` with `on_error: "allow"`.
- `k8s/on_start.py` `render_on_start`: the pip install and `plugins install` failures are logged to stderr (one line naming the step) and swallowed; the script exits 0 for them and never exits 2; `.ref` is written only after a successful package install; `--help` runs only after a successful install. Other failures (writing the config) keep failing as today.
- Tests no longer accurate, to update: `tests/test_render.py::test_on_start_hook_and_startup_probe` asserts `on_error: deny`; the golden files `tests/golden/session_single.yaml` and `tests/golden/session_two_peers.yaml` are regenerated with `UPDATE_GOLDEN=1` (the rendered hook changes).
- New script tests in `tests/test_on_start.py` run the rendered script with fake `python3`/`pip`/`any-mcp` on PATH (pattern of `tests/test_render.py::test_on_start_script_installs_once_and_writes_json_config`).

Steps: tests first, seen failing; then the change; regenerate goldens; run the verify.

Notes: the wrapper denies on an exit 2 regardless of on_error (`hooks.py:407-409`), so exit 2 must never escape. The config hash changes, so agent pods roll under the replacer of task orch-rollout-replacer (same release). MEMORY.md dated entry.

#### Acceptance conditions

- AC1: the onStart hook is blocking with on_error allow [evidence: test:tests/test_render.py::test_on_start_hook_and_startup_probe]
- AC2: a failing plugins install is logged naming the step and the script exits 0 [evidence: test:tests/test_on_start.py::test_plugin_install_failure_logged_and_exits_zero]
- AC3: a failing any-mcp package install is logged, exits 0, writes no .ref and skips the --help check [evidence: test:tests/test_on_start.py::test_any_mcp_install_failure_logged_and_retried_next_start]
- AC4: an install tool exiting 2 never makes the script exit 2 or non-zero [evidence: test:tests/test_on_start.py::test_install_exit_two_never_propagates]
- AC5: the golden renders are regenerated [evidence: command:uv run pytest -q tests/test_render.py -k golden]
- AC6: MEMORY.md records the decision [evidence: command:grep -q "on_error allow" MEMORY.md]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_render.py`
- `tests/test_on_start.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_render.py tests/test_on_start.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_render.py tests/test_on_start.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S7: orch sessions backup save

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/cache/presign.py`, `src/agents_orchestrator/reconciler/loop.py`, `tests/test_sessions_backup.py`, `tests/test_cache_jobs_render.py`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_sessions_backup.py tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 65f92de1c9e6df13862a14a3e38d564f93267749

#### Requirement

Design D7, user decision verbatim: "Transcript backup: reuse the cache Job/runner/archive/transfer/presign (parameterised, no second S3 client). At discard, after the workdir save, save the PVC `sessions/` subtree as its own S3 object for that session; at create, when the object exists for the same slug, restore it before agent pods start; the bootstrapper then adopts the restored wrapper session of each ordinal (pod names are stable per slug) and resumes it instead of creating a new one. Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so. Status exposes the last sessions backup (finished_at, bytes)."

This task delivers the save half. Design D7 (my call), verbatim: "Object `<cache_s3_prefix>sessions/<slug>.tar.zst`: cache keys match `^[a-z0-9][a-z0-9._-]{0,62}$` (`spec.py:173`, no `/`), so it never collides with a workspace key. Jobs `agent-<slug>-sessions-save|restore`, label `agents.szymonrichert.pl/cache: sessions-save|sessions-restore`, mount PVC subPath `sessions`, no excludes, the same `cache_max_bytes` cap and hardening. Status `status.cache.sessions_save|sessions_restore` in the existing run shape (`state`, `started_at`, `finished_at`, `bytes`, `reason`, `job`)." and "A save runs only after a sessions restore in `restored`, `miss` or `reset` (the workdir rule, `SAVE_OK_RESTORE_STATES`); a session whose StatefulSet already existed when the feature arrived records the restore `skipped` with reason `pods_exist` and still saves at discard."

Goal G6, verbatim: "Claude transcripts (/sessions) are backed up to S3 with the workdir at discard and restored on recreate, and a recreated session resumes the restored conversation."

Scope (agents-orchestrator):
- `reconciler/cache.py`: `render_cache_job` and `CacheRunner` take a target (workdir or sessions) instead of hard-coding the workdir: mount (`workdir_mount` or the PVC subPath `sessions`, read-only for a save), `CACHE_DIR`, `CACHE_EXCLUDE` (`[]` for sessions), object name, Job name, cache label and status key. No copy of the runner: one parameterised implementation.
- `cache/presign.py`: the object name per target (`object_name` for a workspace key, `<cache_s3_prefix>sessions/<slug>.tar.zst` for sessions); one `_client`, one `presign`.
- `reconciler/loop.py` `_discard`: after `cache.save_step` (workdir) has finished, the sessions save step runs, then `pre_discard` and the prunes. Like the workdir save it never holds the discard on failure or timeout; while running it holds the discard.
- Sessions save condition: `spec.cache` set and `settings.cache_available`; skipped (recorded `skipped` with the reason, no Job) when `status.cache.sessions_restore` exists with a state other than `restored`, `miss`, `reset` or `skipped` with reason `pods_exist`. An absent sessions restore record (a session older than this feature) saves.
- `status.cache.sessions_save` records `finished_at` and `bytes` on success (the CLI outcome line, parsed as for the workdir).

Interfaces: `render_cache_job(session, settings, action, url, target=...)` or an equivalent parameter object; `status.cache.sessions_save` run dict as above; the CLI `orch cache save|restore` is unchanged (it already reads `CACHE_DIR`).

Steps: tests first in `tests/test_sessions_backup.py` (fake kube and real Postgres, as `tests/test_cache_save.py`), seen failing; then the parameterisation; `tests/test_cache_jobs_render.py` and `tests/test_cache_restore.py` keep passing unchanged (workdir behaviour is unchanged); `tests/test_cache_save.py` is no longer accurate in one assumption (the discard ends one tick after the workdir save, which no longer holds once a sessions save follows it): only its session setup helper changes, giving each session a sessions restore record whose state skips the sessions save, so it keeps testing the workdir save alone with no assertion changed; run the verify.

Notes: reuse.md do-not-build: "A second S3 client or credential path - presign.py (Job gets one URL, no Secret)". The Job never gets a Secret, `spec.env` or a service account token (module docstring D4). DB tests need Docker: PR CI is the evidence. MEMORY.md: dated entry on the object name and the save condition.

#### Acceptance conditions

- AC1: the sessions save Job mounts only the PVC subPath sessions read-only, sets CACHE_DIR to it, carries one presigned PUT URL for <prefix>sessions/<slug>.tar.zst and the workdir Job's hardening [evidence: test:tests/test_sessions_backup.py::test_sessions_save_job_render]
- AC2: at discard the sessions save runs after the workdir save has finished and before pre_discard and the prunes [evidence: test:tests/test_sessions_backup.py::test_discard_saves_sessions_after_workdir]
- AC3: a successful sessions save records finished_at and bytes in status.cache.sessions_save [evidence: test:tests/test_sessions_backup.py::test_sessions_save_status_records_bytes]
- AC4: a failed or timed-out sessions save is recorded and never holds the discard [evidence: test:tests/test_sessions_backup.py::test_sessions_save_failure_does_not_hold_discard]
- AC5: without spec.cache or with the cache unavailable no sessions Job is created [evidence: test:tests/test_sessions_backup.py::test_no_sessions_save_without_session_cache]
- AC6: a sessions restore state that does not allow a save skips it with the reason; an absent record or skipped pods_exist saves [evidence: test:tests/test_sessions_backup.py::test_sessions_save_skip_rules]
- AC7: the sessions save carries CACHE_MAX_BYTES and an emptyDir scratch sized to it, as the workdir save [evidence: test:tests/test_sessions_backup.py::test_sessions_save_respects_max_bytes]
- AC8: the sessions object name never equals a workspace key's object and both are signed by the one presign client [evidence: test:tests/test_sessions_backup.py::test_sessions_object_name_distinct_from_cache_keys]
- AC9: the workdir cache suites pass, unchanged except the tests/test_cache_save.py session setup helper (sessions restore record that skips the sessions save; no assertion changed) [evidence: command:uv run pytest -q tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py]
- AC10: MEMORY.md records the decision [evidence: command:grep -q "sessions/<slug>.tar.zst" MEMORY.md]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_sessions_backup.py`
- `tests/test_cache_jobs_render.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_sessions_backup.py tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_sessions_backup.py tests/test_cache_jobs_render.py tests/test_cache_save.py tests/test_cache_restore.py tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: test_cache_save.py assumes discard ends one tick after the workdir save; the required sessions save (absent restore record saves) contradicts 'unchanged'. Setup-helper-only change accepted (supervisor, standing approval).

- 2026-10-28 done

### S8: web ci publish gate

- Status: done
- Files: `.github/workflows/ci.yaml`, `scripts/ci.test.mjs`
- Verify: `node --test scripts/ci.test.mjs`
- Verified head: eec81ddc874dd2a3b626e042e099b04a0747a225

#### Requirement

Design D9, user decision verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator, web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no override flag. Its tests use fakes like tests/test_smoke_script.py."

Goal G8, verbatim: "No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green."

This task is the agents-web part: "agents-web image push and chart-publish need the `web` job."

Scope (agents-web):
- `.github/workflows/ci.yaml`: the `images` job (whose main-only step pushes to Harbor) gets `needs: [web]`; `chart-publish` needs `chart`, `images` and `web`. The build and smoke steps stay unconditional; the push and login stay main-only. `chart-publish-tag` is unchanged (it requires an image a passing main build pushed).
- `scripts/ci.test.mjs`: test no longer accurate, to update: "chart-publish: main only, needs chart and images, versions and pushes" asserts `needs` is exactly `[chart, images]`; it now asserts `[chart, images, web]`. A new test asserts `images` needs `web`. "exactly the five jobs" stays true.

Steps: change the tests first and see them fail; then the workflow; run `node --test scripts/ci.test.mjs`.

Notes: run with `node --test scripts/ci.test.mjs` (vitest only includes `src/**`). No em dashes.

#### Acceptance conditions

- AC1: the images job, which pushes the image on main, needs the web job [evidence: command:node --test --test-name-pattern "images job needs web" scripts/ci.test.mjs]
- AC2: chart-publish needs chart, images and web [evidence: command:node --test --test-name-pattern "chart-publish" scripts/ci.test.mjs]
- AC3: every workflow test passes [evidence: command:node --test scripts/ci.test.mjs]

#### Files

- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `node --test scripts/ci.test.mjs` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `node --test scripts/ci.test.mjs` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S9: wrapper shutdown turn resume

- Status: done
- Files: `src/claude_code_wrapper/manager.py`, `src/claude_code_wrapper/session.py`, `src/claude_code_wrapper/turns.py`, `src/claude_code_wrapper/router.py`, `tests/test_shutdown_turn_resume.py`, `README.md`
- Verify: `uv run pytest -q tests/test_shutdown_turn_resume.py tests/test_e2e_resume.py tests/test_turn_continuity.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 91d785dddb0601fef9cf33ac3d18816b6bbafbdb

#### Requirement

Design D5, user decision verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next patch, 0.3.2) and pyproject version fixed to match."

Design D5 (my call), verbatim: "Mechanism: on service shutdown the running turn stays `running` in turns.jsonl with a marker (`interrupted: "shutdown"`), no `turn_failed` is emitted; a user stop or delete keeps ending it `failed` with `session_stopped`. On resume with `restart_continue_prompt` set, the fresh Session adopts that record and continues the same `turn_id` (a `turn_resumed` event, cause `resume`), so the orchestrator's turn row and message complete normally; without the prompt it ends `failed` with error `service_shutdown`. A turn left `running` by a killed process is treated the same way. Alternative rejected: end the turn `failed` at shutdown and start a new turn on resume (the orchestrator would record a failure and the message would not complete)."

Goal G4, verbatim: "A wrapper session resumed after a shutdown that interrupted a turn continues that turn with the continue prompt, and the orchestrator renders a default continue prompt."

Scope (claude-code-wrapper):
- `manager.py`: `shutdown` stops sessions with cause shutdown; `resume` and `load_persisted` hand an interrupted `running` record (TurnStore.current) to the fresh Session.
- `session.py`: `stop(grace, cause=...)` keeps the turn running with the marker on shutdown and ends it `session_stopped` otherwise; a resumed Session holds the record and, once ready, continues it with `continue_turn` (reuse `_continue_held`), or fails it `service_shutdown` when no prompt is configured.
- `turns.py`: the marker persisted in turns.jsonl (a `TurnRecord` field or equivalent) and readable after a restart.
- `router.py`: `turn_resumed` with cause `resume` (the in-process relaunch keeps cause `restart`).
- README: the turn states, the marker, `service_shutdown` and the resume continuation.
- `tests/test_shutdown_turn_resume.py` (new), fake claude only.

Steps: tests first, seen failing; then the code; run the verify.

Notes: the event seq continues across resume (`events.py:157-158`); the orchestrator's re-attach (task orch-ingester-reattach) relies on it, pin it here. In-progress epic slash-commands-from-chat also edits `session.py`, `manager.py` and `router.py`: rebase on its merge first. Only the fake-claude task edits `tests/conftest.py` (repo convention).

#### Acceptance conditions

- AC1: a graceful service shutdown during a turn leaves the turn running with the shutdown marker and emits no turn_failed [evidence: test:tests/test_shutdown_turn_resume.py::test_shutdown_marks_running_turn_interrupted]
- AC2: a user stop or delete of a busy session still ends the turn failed session_stopped and it is never continued [evidence: test:tests/test_shutdown_turn_resume.py::test_user_stop_turn_not_continued]
- AC3: an API resume with restart_continue_prompt continues the same turn_id with the prompt, emits turn_resumed cause resume, and the turn completes [evidence: test:tests/test_shutdown_turn_resume.py::test_api_resume_continues_interrupted_turn]
- AC4: load_persisted with resume_on_start continues a turn a killed process left running [evidence: test:tests/test_shutdown_turn_resume.py::test_load_persisted_continues_interrupted_turn]
- AC5: a resume without restart_continue_prompt ends the interrupted turn failed with service_shutdown [evidence: test:tests/test_shutdown_turn_resume.py::test_resume_without_prompt_fails_interrupted_turn]
- AC6: the event seq continues across shutdown and resume [evidence: test:tests/test_shutdown_turn_resume.py::test_event_seq_continues_across_resume]
- AC7: README documents the marker and service_shutdown [evidence: command:grep -q "service_shutdown" README.md]
- AC8: the resume, continuity and turn suites pass [evidence: command:uv run pytest -q tests/test_e2e_resume.py tests/test_turn_continuity.py tests/test_session_turns.py tests/test_manager.py tests/test_command_turn_resume.py]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/manager.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/turns.py`
- `src/claude_code_wrapper/router.py`
- `tests/test_shutdown_turn_resume.py`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_shutdown_turn_resume.py tests/test_e2e_resume.py tests/test_turn_continuity.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_shutdown_turn_resume.py tests/test_e2e_resume.py tests/test_turn_continuity.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S10: helmfile-pin-check-attempts

- Status: done
- Files: `scripts/check_pins.py`, `tests/test_check_pins.py`, `tests/fixtures`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_check_pins.py`
- Verified head: 5a726d0868e5090af7dbc3656f89ebedfa603ed2

#### Requirement

`mise run check-pins` (scripts/check_pins.py, task helmfile-pin-check) refuses two live, correctly published pins: agents-webhook 838ba1f (run 40223858394) and agents-schedule 0.1.0 = tag v0.1.0 = 6cfa955 (run 40233933676). In both runs attempt 1 succeeded on 2026-10-25 (chart and images published); a manual re-run (attempt 2, 2026-10-28 05:31) failed only because the chart-publish guard refuses to re-push an already published chart version ("chart version ... already published"). check_pins.py reads only the latest attempt, so the pin is refused although its build was green and published (evidence: .scratchpad/session-loss/check-pins-refusal.md). Rule fix (my call, option b): a gated job counts as green when it succeeded in any attempt of the same workflow run for the pinned commit; a job that never succeeded in any attempt still refuses the pin. Use the GitHub API's per-attempt jobs (`/repos/{o}/{r}/actions/runs/{id}/attempts/{n}/jobs`) or equivalent; test first with fixtures (an attempt-1-green, attempt-2-red run is accepted; a run red in every attempt is refused). Record the rule in MEMORY.md with the date and why.

#### Acceptance conditions

- AC1: a pin whose gated job succeeded in an earlier attempt and failed in the latest attempt is accepted [evidence: test:tests/test_check_pins.py::test_earlier_green_attempt_accepts_pin]
- AC2: a pin whose gated job failed in every attempt is refused [evidence: test:tests/test_check_pins.py::test_red_in_every_attempt_refuses_pin]
- AC3: check-pins passes on the live and new pins [evidence: command:mise run check-pins]
- AC4: MEMORY.md records the attempt rule [evidence: command:grep -q "earlier attempt" MEMORY.md]

#### Files

- `scripts/check_pins.py`
- `tests/test_check_pins.py`
- `tests/fixtures`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Red: add the attempt fixtures and tests AC1 and AC2; run the verify and see AC1 fail (latest attempt only).
- Green: read every attempt's jobs of the pinned run in scripts/check_pins.py; run the verify, expect all passed.
- Run `mise run check-pins` and expect every pin ok; add the dated MEMORY.md rule.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S11: orch ci publish gate

- Status: done
- Files: `.github/workflows/ci.yaml`, `tests/test_chart_ci.py`, `tests/test_images.py`, `README.md`
- Verify: `uv run pytest -q tests/test_chart_ci.py tests/test_images.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: ca39f8ee5baa654247c08ce641a8a9021bec4500

#### Requirement

Design D9, user decision verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator, web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no override flag. Its tests use fakes like tests/test_smoke_script.py."

Design D9, checked, verbatim: "the e2e job builds and loads its own images (`mise run test:e2e`, `scripts/e2e.sh`); it does not pull the pushed orchestrator image, so `e2e` may stop needing `images`."

This task is the agents-orchestrator part. Goal G8, verbatim: "No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green."

Scope (agents-orchestrator):
- `.github/workflows/ci.yaml`: nothing reaches Harbor (image push or chart push) before `lint`, `test` and `e2e` pass. Either a separate main-only push job that needs `lint`, `test`, `e2e` (and builds or receives the image), or the push step gated in a job that needs them; `e2e` no longer needs `images` when it does not use the pushed image. `chart-publish` and `chart-publish-tag` need `lint`, `test` and `e2e` too (plus the push job for main).
- Tests no longer accurate, to update: `tests/test_chart_ci.py::test_publish_only_main_and_tags_after_images` asserts `needs` exactly `{chart, images}` and `["chart"]`; `tests/test_images.py::test_ci_pushes_orchestrator_image_on_main_only` asserts the push step lives in the `images` job (update only if the push moves).
- README releasing section reflects the gate (`tests/test_chart_ci.py::test_readme_documents_releasing`).

Steps: tests first, seen failing; then the workflow; run the verify.

Notes: depends on orch-e2e-main-failure so the first gated main run is green. Keep the 50MB chunked `regctl image import` (Cloudflare 413).

#### Acceptance conditions

- AC1: the image push runs only on main and only after lint, test and e2e passed [evidence: test:tests/test_chart_ci.py::test_image_push_needs_lint_test_e2e]
- AC2: chart-publish and chart-publish-tag need lint, test and e2e [evidence: test:tests/test_chart_ci.py::test_publish_only_main_and_tags_after_images]
- AC3: the e2e job does not need the pushed image [evidence: test:tests/test_chart_ci.py::test_e2e_does_not_need_pushed_image]
- AC4: exactly one image reference is pushed, on main only, in 50MB chunks [evidence: test:tests/test_images.py::test_ci_pushes_orchestrator_image_on_main_only]
- AC5: README documents the gated release [evidence: test:tests/test_chart_ci.py::test_readme_documents_releasing]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `.github/workflows/ci.yaml`
- `tests/test_chart_ci.py`
- `tests/test_images.py`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_chart_ci.py tests/test_images.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_chart_ci.py tests/test_images.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S12: orch default continue prompt

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `src/agents_orchestrator/k8s/render.py`, `tests/test_render.py`, `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`, `README.md`
- Verify: `uv run pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 6982b3be4ba76d42889e6254d69086055de58f1e

#### Requirement

Design D5, user decision verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next patch, 0.3.2) and pyproject version fixed to match."

This task is the orchestrator part: "the orchestrator renders a default restart_continue_prompt (render.py:130)". Design D5 (my call), verbatim: "The default prompt is an orchestrator setting `ORCH_DEFAULT_RESTART_CONTINUE_PROMPT` (default "Claude was restarted. Continue the task where you left off.", the wrapper's own example text), overridden by `spec.wrapper.restart_continue_prompt`."

Goal G4, verbatim: "A wrapper session resumed after a shutdown that interrupted a turn continues that turn with the continue prompt, and the orchestrator renders a default continue prompt."

Scope (agents-orchestrator):
- `settings.py`: `default_restart_continue_prompt: str` with the default above.
- `k8s/render.py` `_ccw_config`: `sessions.restart_continue_prompt` is always rendered, from the spec when set, else the setting.
- Tests no longer accurate, to update: `tests/test_render.py::test_no_wrapper_block_renders_unchanged` (its `sessions` dict gains the default prompt); goldens regenerated with `UPDATE_GOLDEN=1`.
- README settings table: `ORCH_DEFAULT_RESTART_CONTINUE_PROMPT`.

Steps: tests first, seen failing; then the change; regenerate goldens; run the verify.

Notes: the rendered config is validated against the pinned wrapper in `tests/test_render.py`; `restart_continue_prompt` is an existing wrapper key (`config.py:582`). `tests/test_settings.py` is not touched (in-progress epic slash-commands-from-chat owns it).

#### Acceptance conditions

- AC1: a session with no wrapper block renders the default restart_continue_prompt [evidence: test:tests/test_render.py::test_default_restart_continue_prompt_rendered]
- AC2: spec.wrapper.restart_continue_prompt overrides the default [evidence: test:tests/test_render.py::test_spec_restart_continue_prompt_overrides_default]
- AC3: the no-wrapper-block render lists the default prompt in sessions [evidence: test:tests/test_render.py::test_no_wrapper_block_renders_unchanged]
- AC4: the golden renders are regenerated [evidence: command:uv run pytest -q tests/test_render.py -k golden]
- AC5: README documents the setting [evidence: command:grep -q "ORCH_DEFAULT_RESTART_CONTINUE_PROMPT" README.md]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S13: orch sessions backup restore

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/reconciler/loop.py`, `src/agents_orchestrator/reconciler/wrapper_sessions.py`, `tests/test_sessions_restore.py`, `tests/fakes/fake_wrapper.py`, `tests/test_wrapper_session_bootstrap.py`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_sessions_restore.py tests/test_wrapper_session_bootstrap.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 10ba36a63946b59d2926fbc4fe03675ba03874c9

#### Requirement

Design D7, user decision verbatim: "Transcript backup: reuse the cache Job/runner/archive/transfer/presign (parameterised, no second S3 client). At discard, after the workdir save, save the PVC `sessions/` subtree as its own S3 object for that session; at create, when the object exists for the same slug, restore it before agent pods start; the bootstrapper then adopts the restored wrapper session of each ordinal (pod names are stable per slug) and resumes it instead of creating a new one. Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so. Status exposes the last sessions backup (finished_at, bytes)."

This task delivers the restore half. Design D7 (my call), verbatim: "A save runs only after a sessions restore in `restored`, `miss` or `reset` (the workdir rule, `SAVE_OK_RESTORE_STATES`); a session whose StatefulSet already existed when the feature arrived records the restore `skipped` with reason `pods_exist` and still saves at discard. A restore never runs once a pod of the session exists." and ""Before agent pods start": while the sessions restore is pending the StatefulSet is applied with `replicas: 0`."

Goal G6, verbatim: "Claude transcripts (/sessions) are backed up to S3 with the workdir at discard and restored on recreate, and a recreated session resumes the restored conversation."

Scope (agents-orchestrator):
- `reconciler/cache.py`: a sessions restore step on the parameterised runner of task orch-sessions-backup-save (Job `agent-<slug>-sessions-restore`, PVC subPath `sessions`, presigned GET of `<cache_s3_prefix>sessions/<slug>.tar.zst`), recorded in `status.cache.sessions_restore` (`restored` with bytes, `miss` when the object does not exist, `reset`, `failed`, or `skipped` with reason `pods_exist`).
- `reconciler/loop.py` `_converge`: on a session's first converge with `spec.cache` set and the cache available, the StatefulSet is applied with `replicas: 0` until the sessions restore has an outcome; a session whose StatefulSet or any pod already exists records `skipped`/`pods_exist` and never restores. A failed restore starts the pods anyway with a degraded message (as the workdir restore does).
- `reconciler/wrapper_sessions.py`: a new agent row of a recreated session adopts the restored wrapper session of its pod (the wrapper lists it from `/sessions/<pod>/`) and resumes it; it is never replaced by `create_session` while a restored session with a transcript is listed. Change the code only where the existing `_pick` order does not already do this; the test pins it either way.
- `tests/fakes/fake_wrapper.py`: the fake can start with a persisted stopped session (as the real wrapper's `load_persisted` lists one).

Interfaces: `status.cache.sessions_restore` run dict (same shape as `status.cache.restore`); `WrapperSessionBootstrapper._bootstrap` / `_pick` keep their signatures.

Steps: tests first in `tests/test_sessions_restore.py` and the adoption test in `tests/test_wrapper_session_bootstrap.py`, seen failing; then the code; run the verify.

Notes: the workdir restore keeps running as today; the two restores are independent Jobs. The wrapper refuses a resume whose config dir, transcript or workdir is missing (`_check_resumable`); the workdir path is the same per slug. DB tests need Docker: PR CI is the evidence. MEMORY.md: dated entry on the replicas-0 hold and `pods_exist`.

#### Acceptance conditions

- AC1: a new cache-enabled session whose sessions object exists runs the sessions restore before any agent pod exists: the StatefulSet stays at replicas 0 until the restore has an outcome [evidence: test:tests/test_sessions_restore.py::test_restore_runs_before_agent_pods_start]
- AC2: the sessions restore Job mounts the PVC subPath sessions and carries one presigned GET URL for <prefix>sessions/<slug>.tar.zst [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_job_render]
- AC3: a missing object records miss and the pods start [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_miss_starts_pods]
- AC4: a failed restore starts the pods with a degraded message and the later sessions save is skipped [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_failure_starts_pods_and_skips_save]
- AC5: a session whose StatefulSet or pod already exists never restores, records skipped pods_exist and still saves at discard [evidence: test:tests/test_sessions_restore.py::test_existing_session_skips_restore_and_still_saves]
- AC6: status.cache.sessions_restore records the outcome, finished_at and bytes [evidence: test:tests/test_sessions_restore.py::test_sessions_restore_status_recorded]
- AC7: without spec.cache or with the cache unavailable no sessions restore runs and the pods start at once [evidence: test:tests/test_sessions_restore.py::test_no_sessions_restore_without_session_cache]
- AC8: each new agent adopts and resumes the restored stopped wrapper session of its pod and create_session is never called [evidence: test:tests/test_wrapper_session_bootstrap.py::test_restored_stopped_session_resumed_not_created]
- AC9: the bootstrap and cache suites pass [evidence: command:uv run pytest -q tests/test_wrapper_session_bootstrap.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_reconciler.py]
- AC10: MEMORY.md records the decision [evidence: command:grep -q "pods_exist" MEMORY.md]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `src/agents_orchestrator/reconciler/wrapper_sessions.py`
- `tests/test_sessions_restore.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_wrapper_session_bootstrap.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_sessions_restore.py tests/test_wrapper_session_bootstrap.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_sessions_restore.py tests/test_wrapper_session_bootstrap.py tests/test_cache_restore.py tests/test_cache_save.py tests/test_reconciler.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S14: orch-sessions-save-unconverged

- Status: done
- Files: `src/agents_orchestrator/cache/save_rule.py`, `tests/test_cache_save.py`, `README.md`
- Verify: `uv run pytest tests/test_cache_save.py -q`
- Verified head: bd1024124be889099be4208a4b883572973a493a

#### Requirement

Discarding a session that was discarded before its first converge (no sessions restore record, no PVC or no pod ever wrote /sessions) must not start a sessions save Job. Today `cache/save_rule.py` (`_pods_wrote_sessions`, about line 31) treats a missing restore record as "the session predates the restore", so the reconciler renders a sessions save Job against a PVC that does not exist and the discard waits up to the Job timeout (about 30 minutes) (epic review finding, .scratchpad/session-loss/review/orchestrator.md "Consider" save_rule.py:31). Distinguish "predates the sessions restore feature" from "never converged": skip the sessions save with a recorded skip reason when the session never converged (no PVC / never had a pod), keep saving for sessions that predate the feature and did run pods. Read how the reconciler records converge and PVC creation before choosing the signal; ask instead of guessing if no reliable signal exists. Also fix README.md (about line 119): it still says "A failed install fails the onStart hook, which blocks the session"; since orch-onstart-nonfatal the install failure is logged, onStart exits 0 and the hook is on_error allow, so the sentence must describe that. Test first.

#### Acceptance conditions

- AC1: a session discarded before its first converge gets no sessions save Job and its cache status records the skip reason [evidence: test:tests/test_cache_save.py::test_sessions_save_skipped_when_never_converged]
- AC2: a session that predates the sessions restore and ran pods still gets a sessions save [evidence: test:tests/test_cache_save.py::test_sessions_save_runs_for_session_predating_restore]
- AC3: README no longer says a failed install blocks the session [evidence: command:! grep -q "which blocks the session" README.md]

#### Files

- `src/agents_orchestrator/cache/save_rule.py`
- `tests/test_cache_save.py`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Red: write the tests the acceptance conditions name; run `uv run pytest tests/test_cache_save.py -q` and see them fail for the expected reason.
- Green: implement the requirement as written; run `uv run pytest tests/test_cache_save.py -q` and expect every test to pass.
- Refactor with the verify green; add a dated MEMORY.md entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S15: wrapper patch release

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py`
- Verify: `uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 5fd93ff52236790a7131755141d328b25826213a

#### Requirement

Design D5, user decision verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next patch, 0.3.2) and pyproject version fixed to match."

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Open question Q1 decides the number when slash-commands-from-chat tags v0.4.0 first (recommended: the next patch above the latest tag); otherwise 0.3.2.

Scope (claude-code-wrapper):
- Version `0.3.2` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py` (pyproject says 0.3.0 at tag v0.3.1 today); `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject`: pyproject, `__version__` and the installed metadata agree (the same test name slash-commands-from-chat uses, so the later bump only changes the number).
- The wrapper PR of this epic merges to `main` through the normal PR flow before the orchestrator pin task starts.
- Release steps, run by the orchestrator session (never a subagent) once merged: wait for `build.yaml` to push `claude-code-wrapper:<sha7>`, push tag `v0.3.2` on the merge commit (`release.yaml` retags `:0.3.2` and `:latest`; irreversible, listed in design.md), then amend orch-wrapper-pin-patch with the merge sha.
- AC3 is checked by the orchestrator session after it pushed the tag; implementer and reviewer check AC1, AC2 and AC4.

Notes: precedent: done epic leader-auto-handover task wrapper-release-0-3-0; retro: Harbor prunes sha7 tags, so the helmfile pins the release tag.

#### Acceptance conditions

- AC1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- AC2: the version is 0.3.2 [evidence: command:grep -q '^version = "0.3.2"' pyproject.toml]
- AC3: tag v0.3.2 exists on origin (orchestrator session, after the push) [evidence: command:git ls-remote --exit-code --tags origin v0.3.2]
- AC4: packaging tests and lint pass [evidence: command:uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 in-progress: AC1 AC2 AC4 reviewed clean on cb51746 (CI 40650156587 green); merging PR #7, tag pending

- 2026-10-28 done: merged PR #7 as 5fd93ff (main CI 40651891291 green), tag v0.3.2 pushed, release run 40653754978 success

- 2026-10-28 in-progress: tag v0.3.2 pushed; release run 40653754978 concluded cancelled - investigating

- 2026-10-28 done: merged PR #7 as 5fd93ff (main CI 40651891291 green); tag v0.3.2 pushed; release run 40653754978 attempt 1 cancelled (Harbor pull stalled to the 15 min timeout), attempt 2 success; AC3 git ls-remote shows v0.3.2

### S16: orch api session safety

- Status: done
- Files: `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/sessions.py`, `src/agents_orchestrator/api/streams.py`, `src/agents_orchestrator/db/views.py`, `openapi.json`, `tests/test_api_session_safety.py`, `README.md`
- Verify: `uv run pytest -q tests/test_api_session_safety.py tests/test_readme_api.py tests/test_api_sessions.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 07fce279e134fe8caa398d301bd0889cd2c5be31

#### Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Design D7 (part), verbatim: "Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so. Status exposes the last sessions backup (finished_at, bytes)."

Design D8 (my call), verbatim: "API: `SessionSummary.oldest_queued_at` (null when none), also carried by the `message_status` stream frame so the banner stays live; `SessionView.backup` `{workdir: bool, transcripts: bool, reason: str|null, last_transcripts_backup: {finished_at, bytes}|null}`, where each flag is true only when the discard would really save it (spec.cache set, `cache_available`, its restore state allows the save) and `reason` names why not (`no_session_cache`, `cache_not_configured`, or the skip reason)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

Scope (agents-orchestrator):
- `db/views.py`: `_AGGREGATES` adds the oldest queued `created_at`; `summarize` returns `oldest_queued_at`.
- `api/schemas.py`: `SessionSummary.oldest_queued_at: datetime | None`; `SessionBackup` and `BackupRun` models; `SessionView.backup`.
- `api/sessions.py`: builds `backup` from `spec.cache`, `settings.cache_available` and `status.cache` (`restore`, `sessions_restore`, `sessions_save`), with the save rules of tasks orch-sessions-backup-save and orch-sessions-backup-restore (one shared rule, not a copy: reuse the runner's skip function).
- `api/streams.py`: the `message_status` frame carries `oldest_queued_at`.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`); README API sections document the fields.
- `tests/test_api_session_safety.py` (new).

Steps: tests first, seen failing; then the code; regenerate openapi.json; run the verify.

Notes: DB tests need Docker: PR CI is the evidence. The web consumes this through task web-sync-session-safety-api.

#### Acceptance conditions

- AC1: summary.oldest_queued_at is the created_at of the oldest queued message and null when none is queued [evidence: test:tests/test_api_session_safety.py::test_summary_oldest_queued_at]
- AC2: the message_status stream frame carries oldest_queued_at [evidence: test:tests/test_api_session_safety.py::test_message_status_frame_carries_oldest_queued_at]
- AC3: with spec.cache, the cache available and restores that allow saving, backup.workdir and backup.transcripts are true [evidence: test:tests/test_api_session_safety.py::test_backup_view_when_cache_configured]
- AC4: without spec.cache both flags are false with reason no_session_cache; with the cache unavailable, reason cache_not_configured [evidence: test:tests/test_api_session_safety.py::test_backup_view_without_cache]
- AC5: a restore state that skips a save sets that flag false with the skip reason [evidence: test:tests/test_api_session_safety.py::test_backup_view_reports_skipped_save]
- AC6: backup.last_transcripts_backup carries finished_at and bytes of a finished sessions save [evidence: test:tests/test_api_session_safety.py::test_backup_view_last_transcripts_backup]
- AC7: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC8: README documents the new fields [evidence: command:grep -q "oldest_queued_at" README.md && grep -q "last_transcripts_backup" README.md]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/streams.py`
- `src/agents_orchestrator/db/views.py`
- `openapi.json`
- `tests/test_api_session_safety.py`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_api_session_safety.py tests/test_readme_api.py tests/test_api_sessions.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_api_session_safety.py tests/test_readme_api.py tests/test_api_sessions.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S17: orch rollout replacer

- Status: done
- Files: `src/agents_orchestrator/k8s/render.py`, `src/agents_orchestrator/reconciler/rollout.py`, `src/agents_orchestrator/reconciler/loop.py`, `tests/fakes/fake_kube.py`, `tests/test_rollout.py`, `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_rollout.py tests/test_reconciler.py tests/test_render.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: ba2ef3b8434e23bb0d9b5f02b2b1cbd09dcb605f

#### Requirement

Design D1, user decision verbatim: "Rollouts: agent StatefulSet updateStrategy OnDelete; the reconciler replaces outdated pods (pod controller-revision-hash != status.updateRevision) one pod at a time per session, only when that agent is idle (reuse the _draining busy predicate; no dispatching/verifying message), the leader last and only after leadership moved to an idle eligible member (existing handover), a single-agent session rolls when idle. Never force-replace a busy pod (no deadline); the session status exposes the pending roll. Partition/PDB/maxUnavailable rejected (research.md). Any pod that dies anyway comes back on the new template (accepted)."

Design D2, user decision verbatim: ""A deploy never runs inside a pod that the same deploy rolls" is satisfied by D1: the deployer's pod is busy for the whole apply+smoke turn so it is not rolled until idle; an in-cluster Job runner is a non-goal. Add an orchestrator test that pins this (busy pod with outdated revision is not deleted across reconcile ticks)."

Design D1 (my call), verbatim: "The busy SQL of `_draining` is extracted once and shared by the drain and the replacer (reuse.md do-not-build: "a second drain/busy query"); the replacer's idle test is "not busy, no `dispatching`/`verifying` message, not the leader"." / ""Existing handover": the reconciler queues a `leadership_requests` handover row from the current leader (`db/leadership.py:insert_request`, kind `handover`, reason `rollout`, no target) only when every other outdated pod is replaced and an idle eligible member exists; the dispatcher's pass applies it as it applies every handover (`leader_reason` `handover: rollout`). The leader pod is deleted only after `session_leaders` names another agent." / "`status.rollout` (written with the other status fields, dropped when nothing is pending): `{"revision": <updateRevision>, "pending": [ordinals], "waiting": [ordinals held busy], "leader_pending": bool}`." / "The switch to OnDelete and any template change of the same release reach the StatefulSet in one server-side apply, so the deploy of this epic itself rolls no pod by the controller."

Goal G3, verbatim: "Agent StatefulSet template changes never replace a busy agent pod or the current leader mid-turn: updateStrategy OnDelete plus a reconciler replacer that deletes one outdated pod at a time, only when idle, leader last after handover; a pod running a deploy is therefore never rolled by that deploy."

Scope (agents-orchestrator):
- `k8s/render.py`: the StatefulSet spec gets `updateStrategy: {type: OnDelete}`; goldens regenerated (`UPDATE_GOLDEN=1`).
- `reconciler/rollout.py` (new) or functions in `reconciler/loop.py` (builder's choice): per session, read the StatefulSet's `status.updateRevision` and its pods' `controller-revision-hash` label; at most one outdated pod deleted per session per tick (`kube.delete_pod`), never while its agent is busy (shared busy predicate), holds a `dispatching`/`verifying` message, or leads; the leader last: queue the handover request once every other pod is current and an idle eligible member exists, delete the old leader's pod only after the leader row names another agent; a non-hive or single-agent session deletes its pod when idle. No deadline. A pod that is not yet current and not Ready is never deleted twice (wait for the previous replacement to be Ready).
- `reconciler/loop.py`: `_converge` runs the step and writes `status.rollout`; `_draining` uses the shared busy fragment.
- `tests/fakes/fake_kube.py`: models revisions: an applied StatefulSet gets `status.updateRevision` from its template; a new pod is labelled with it; under OnDelete a template change leaves existing pods on their old revision until deleted; a deleted pod returns at the update revision; RollingUpdate keeps today's behaviour.
- `tests/test_rollout.py` (new): the conditions below, with the drain tests of `tests/test_reconciler.py` still passing.

Interfaces: `status.rollout` dict as above; `leadership.insert_request(conn, session_id, kind="handover", from_agent_id=leader, to_agent_id=None, reason="rollout", epoch=leader_epoch)`.

Steps: fake kube revisions and the tests first, seen failing; then render and replacer; regenerate goldens; run the verify.

Notes: the window between the idle check and the delete: a message claimed in between is retried by the existing verify path, never dropped (Review focus). Real-cluster label behaviour is confirmed by task orch-e2e-rollout-mid-turn. DB tests need Docker: PR CI is the evidence. MEMORY.md dated entry (OnDelete, no deadline, leader last).

#### Acceptance conditions

- AC1: the rendered agent StatefulSet has updateStrategy OnDelete [evidence: test:tests/test_rollout.py::test_statefulset_update_strategy_on_delete]
- AC2: the fake kube keeps pods on their revision under OnDelete and recreates a deleted pod at the update revision [evidence: test:tests/test_rollout.py::test_fake_kube_on_delete_revisions]
- AC3: idle outdated pods are replaced one at a time per session, the next only after the previous is Ready on the new revision [evidence: test:tests/test_rollout.py::test_idle_outdated_pods_replaced_one_at_a_time]
- AC4: an outdated pod whose agent is busy is not replaced [evidence: test:tests/test_rollout.py::test_busy_outdated_pod_not_replaced]
- AC5: an outdated pod holding a dispatching or verifying message is not replaced [evidence: test:tests/test_rollout.py::test_outdated_pod_with_inflight_message_not_replaced]
- AC6: a busy outdated pod is never deleted across many reconcile ticks, with no deadline (a deployer pod is never rolled by its own deploy) [evidence: test:tests/test_rollout.py::test_busy_outdated_pod_kept_across_ticks]
- AC7: the leader's pod is replaced last, only after a rollout handover moved leadership to an idle eligible member [evidence: test:tests/test_rollout.py::test_leader_rolled_last_after_handover]
- AC8: the leader's pod is held while no idle eligible member exists [evidence: test:tests/test_rollout.py::test_leader_held_without_idle_eligible_member]
- AC9: a single-agent session rolls its pod when idle [evidence: test:tests/test_rollout.py::test_single_agent_session_rolls_when_idle]
- AC10: status.rollout exposes the revision, pending and waiting ordinals and is dropped once nothing is pending [evidence: test:tests/test_rollout.py::test_status_exposes_pending_roll]
- AC11: the drain and the replacer embed one busy predicate [evidence: test:tests/test_rollout.py::test_drain_and_rollout_share_busy_predicate]
- AC12: the reconciler and render suites pass, goldens regenerated [evidence: command:uv run pytest -q tests/test_reconciler.py tests/test_render.py]
- AC13: MEMORY.md records the decision [evidence: command:grep -q "OnDelete" MEMORY.md]
- AC14: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/reconciler/rollout.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/fakes/fake_kube.py`
- `tests/test_rollout.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_rollout.py tests/test_reconciler.py tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_rollout.py tests/test_reconciler.py tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S18: orch-security-hardening

- Status: done
- Files: `src/agents_orchestrator/reconciler/cache.py`, `src/agents_orchestrator/spec.py`, `tests/test_cache_jobs_render.py`, `tests/test_cache_archive.py`, `.github/workflows/ci.yaml`, `MEMORY.md`
- Verify: `uv run pytest tests/test_cache_jobs_render.py tests/test_cache_archive.py -q`
- Verified head: 28459cc92129977fdcb13079796badfc4a5474ed

#### Requirement

Two security findings of the epic review (.scratchpad/session-loss/review/security.md), my call to fix before merge:
1. The /sessions backup (`reconciler/cache.py`, sessions target renders `CACHE_EXCLUDE` as `[]`) archives every file under /sessions into S3, including Claude credential files (for example `<ses>/config/.credentials.json`). Exclude credential files from the sessions archive (a fixed exclude list for the sessions target, fnmatch globs on the relative path, covering `.credentials.json` at any depth). First read how agent pods get their Claude credentials (wrapper settings, chart, secret mounts) and confirm a restore without those files leaves the pod authenticated; if credentials exist only inside /sessions, stop and return that as a question instead of excluding. Test first.
2. `.github/workflows/ci.yaml` uses `regclient/actions/regctl-installer@main` (about lines 38, 99, 137) in jobs that hold the Harbor push secrets. Pin it to the same commit SHA agents-web uses (`dd58ad94f76adb73d8ac1bf75ed25f01545d5b32`, comment with the date) and add a top-level `permissions: contents: read` block (raise per job only where a job needs more; read each job first).
Record both decisions in MEMORY.md with the date and why.

#### Acceptance conditions

- AC1: the sessions save Job renders a CACHE_EXCLUDE that excludes credential files at any depth [evidence: test:tests/test_cache_jobs_render.py::test_sessions_save_excludes_credentials]
- AC2: archive.pack with the sessions exclude list leaves out a nested config/.credentials.json and keeps transcripts [evidence: test:tests/test_cache_archive.py::test_sessions_exclude_drops_credentials]
- AC3: no workflow step uses a moving regctl-installer ref [evidence: command:! grep -n "regctl-installer@main" .github/workflows/ci.yaml]
- AC4: the workflow declares top-level permissions [evidence: command:grep -q "^permissions:" .github/workflows/ci.yaml]
- AC5: MEMORY.md records the credential exclude [evidence: command:grep -q "credentials" MEMORY.md]

#### Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/spec.py`
- `tests/test_cache_jobs_render.py`
- `tests/test_cache_archive.py`
- `.github/workflows/ci.yaml`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Red: write the tests the acceptance conditions name; run `uv run pytest tests/test_cache_jobs_render.py tests/test_cache_archive.py -q` and see them fail for the expected reason.
- Green: implement the requirement as written; run `uv run pytest tests/test_cache_jobs_render.py tests/test_cache_archive.py -q` and expect every test to pass.
- Refactor with the verify green; add a dated MEMORY.md entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S19: orch wrapper pin patch

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint`
- Verified head: 288d9afdc6e4d6c53c26a99e5458d2fdcf17b402

#### Requirement

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Design D13, verbatim: "Precedent: leader-auto-handover tasks wrapper-release-0-3-0, orch-wrapper-pin-0-3-0, helmfile-deploy-pin, helmfile-apply-smoke. Live applies and the tag push are run by the orchestrator session, never a subagent."

Needs a merged upstream: the claude-code-wrapper PR of this epic merged on `main` and tagged (task wrapper-patch-release). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@5fd93ff52236790a7131755141d328b25826213a`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `5fd93ff` and `WRAPPER_SHA` `5fd93ff52236790a7131755141d328b25826213a` (`scripts/e2e.sh` builds the wrapper from source when the sha7 image was pruned).
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:5fd93ff` (`tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha` requires the sha7 form; the release tag `0.3.2` is what agents-helmfile pins).

Steps: pin, `uv lock`, run the verify; the real contract leg runs in CI.

Notes: in-progress epic slash-commands-from-chat pins the wrapper in the same files (task orch-wrapper-pin-0-4-0); rebase on it and keep the higher wrapper commit that carries both epics' changes.

#### Acceptance conditions

- AC1: pyproject, uv.lock and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the dev dependency matches the README agent image [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the pinned wrapper is the release [evidence: command:uv run --frozen python -c "import claude_code_wrapper; assert claude_code_wrapper.__version__ == '0.3.2'"]
- AC4: (Docker host or CI) the real contract leg passes [evidence: command:mise run test:integration]
- AC5: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: wrapper PR #7 merged as 5fd93ff, tagged v0.3.2 (release image retagged)

- 2026-10-28 done

### S20: orch e2e rollout mid turn

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `e2e/agent-test.scenario.json`, `scripts/e2e.sh`, `e2e/values-kind.yaml`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: e0b6e127060a598e8c8b7d38248a36ab929de184

#### Requirement

Design D11, user decision verbatim: "Regression e2e (kind, tests/e2e/test_e2e_kind.py): roll the agent image (helm upgrade to a second tag of the same image) while a slow turn runs; assert the busy pod is not replaced until idle, the leader rolls last, the wrapper session id is unchanged, the interrupted/queued messages are delivered and the agent never stays dead. Lengthen the fake "slow" turn as needed."

Design D11 (my call), verbatim: "A new scenario turn (its own match text) holds the long turn, so the 4 s "slow" turn other tests rely on is unchanged. For "interrupted" messages the test also deletes one busy pod by hand (a crash, accepted under D1): it returns on the new template, its wrapper session id is unchanged and its interrupted turn completes through the D5 continuation."

Goal G9, verbatim: "A kind e2e rolls the agent image while a turn is running and proves no busy pod is replaced, the turn continues, and queued messages are delivered."

Scope (agents-orchestrator):
- `e2e/agent-test.scenario.json`: a long turn (its own match text, long enough to span the roll) and a turn matching the rendered default continue prompt so a continued turn completes.
- `scripts/e2e.sh`: also tags and loads the agent-test image under a second tag; `e2e/values-kind.yaml`: `ORCH_AGENT_IMAGES` allows both tags.
- `tests/e2e/test_e2e_kind.py`, API only plus kubectl for pod uids and revisions: a 2-replica hive; a long turn runs on the non-leader; `helm upgrade --reuse-values --set agentImage=<second tag>`; assert: the busy pod keeps its uid until its turn completed, then is replaced; the leader's pod is replaced last and after the leader moved; every agent's wrapper session id (events API `wrapper_session_id`) is unchanged; messages posted during the roll reach `sent` with completed turns and none is `failed`; no agent stays `dead` past a deadline; then a busy pod deleted by hand returns on the new revision with the same wrapper session id and its interrupted turn completes. Every session is discarded in teardown; the release is upgraded back to the first tag.

Steps: scenario and script first; then the test; `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`; the PR CI e2e job passes.

Notes: run with `mise run test:e2e` (kind; or the PR CI e2e job; `E2E_HOLD_FILE` for one test). Reuse `wait_for`, `pods_of`, `scale_session`, the message helpers and `test_scale_down_waits_for_busy_agent` (mid-turn pattern). Needs the pinned wrapper with the continuation (task orch-wrapper-pin-patch) and the replacer, re-attach and default prompt tasks.


Amendment 2026-10-28 (supervisor, design D1 transition bullet): the test also proves the RollingUpdate-to-OnDelete transition on a real API server: with a busy agent, `kubectl patch` its StatefulSet to `updateStrategy: {type: RollingUpdate}` (strategy only, as a StatefulSet created by the previous release has it, partition defaulted), then trigger a template change (`helm upgrade ... --set agentImage=<second tag>`); assert the orchestrator's apply succeeds (no reconciler apply error in its logs or session status), the StatefulSet ends `type: OnDelete` without `rollingUpdate`, and the busy pod keeps its uid until its turn completed (the controller rolled nothing).

#### Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: on kind, a helm upgrade to a second agent image tag does not replace the busy pod until its turn completed [evidence: command:mise run test:e2e]
- AC3: on kind, the leader's pod is replaced last, after leadership moved [evidence: command:mise run test:e2e]
- AC4: on kind, every agent keeps its wrapper session id across the roll and no agent stays dead [evidence: command:mise run test:e2e]
- AC5: on kind, messages posted during the roll are delivered and none fails [evidence: command:mise run test:e2e]
- AC6: on kind, a busy pod deleted by hand returns on the new revision with the same wrapper session id and its interrupted turn completes [evidence: command:mise run test:e2e]
- AC7: the scenario stays valid JSON and keeps the 4 s slow turn [evidence: command:python3 -c "import json; d = json.load(open('e2e/agent-test.scenario.json')); t = [x for x in d['turns'] if x['match'] == 'slow'][0]; assert {'sleep': 4} in t['steps'] and len(d['turns']) >= 5"]
- AC9: on kind, a StatefulSet left on RollingUpdate is switched to OnDelete by a template-changing apply without the controller replacing the busy pod [evidence: command:mise run test:e2e]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/agent-test.scenario.json`
- `scripts/e2e.sh`
- `e2e/values-kind.yaml`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: D1 transition amendment: prove RollingUpdate->OnDelete switch on a real API server

- 2026-10-28 done

### S21: orch-rollout-dispatch-reservation

- Status: done
- Files: `src/agents_orchestrator/reconciler/rollout.py`, `tests/test_rollout.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_rollout.py -q`
- Verified head: 053d32353328e02739e32e0df6f14ae1b5ca4a4d

#### Requirement

The rollout replacer must never delete an agent pod that holds a dispatch reservation. Today `reconciler/rollout.py` (the `BUSY` predicate at about line 50, shared with the scale-down drain) treats an agent as idle when `agent_status.state` is not `busy` and it has no message in `dispatching`/`verifying`, but the dispatcher has already handed the agent a turn once its last dispatch is newer than the moment it became free (`free_since > last_dispatched_at` is the dispatcher's idle condition; read `db/queue.py` `_PICK` and the agent/agent_status columns for the exact names). Between the dispatch and the wrapper reporting busy, the replacer can delete the pod mid-handoff (epic review finding, .scratchpad/session-loss/review/orchestrator.md "Consider" rollout.py:50). Make the shared busy predicate also count an agent whose last dispatch is newer than its free_since (the same reservation the dispatcher honours), so neither the replacer nor the scale-down drain removes it. Test first. Record the decision in MEMORY.md with the date and why.

#### Acceptance conditions

- AC1: an idle agent whose last dispatch is newer than its free_since is busy for the replacer and its pod is not deleted [evidence: test:tests/test_rollout.py::test_replacer_skips_agent_with_dispatch_reservation]
- AC2: an idle agent whose free_since is newer than its last dispatch is still replaced [evidence: test:tests/test_rollout.py::test_replacer_replaces_idle_agent_without_reservation]
- AC3: MEMORY.md records the dispatch reservation in the busy predicate [evidence: command:grep -q "dispatch reservation" MEMORY.md]

#### Files

- `src/agents_orchestrator/reconciler/rollout.py`
- `tests/test_rollout.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Red: write the tests the acceptance conditions name; run `uv run pytest tests/test_rollout.py -q` and see them fail for the expected reason.
- Green: implement the requirement as written; run `uv run pytest tests/test_rollout.py -q` and expect every test to pass.
- Refactor with the verify green; add a dated MEMORY.md entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S22: web sync session safety api

- Status: done
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`
- Verify: `npm run check:api && npx tsc -b && npm run lint`
- Verified head: ace35f85df49e5319f62e52cadd0065a84ea2a75

#### Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

This task is the re-sync: "Re-sync the vendored OpenAPI (npm run sync:api)."

Scope (agents-web): `npm run sync:api -- orchestrator --from <agents-orchestrator integration tree>` after task orch-api-session-safety; commit `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` as generated; no hand edits.

Notes: `npm run check:api` fails on drift in CI. In-progress epic slash-commands-from-chat also re-syncs these files (task web-sync-message-kind): regenerate from the orchestrator tree that carries both epics' changes, never merge the generated files by hand.

#### Acceptance conditions

- AC1: the vendored orchestrator OpenAPI and generated types are in sync [evidence: command:npm run check:api]
- AC2: the types carry oldest_queued_at and the backup view [evidence: command:grep -q "oldest_queued_at" src/api/schema.d.ts && grep -q "last_transcripts_backup" src/api/schema.d.ts]
- AC3: the app typechecks [evidence: command:npx tsc -b]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"npm run check:api && npx tsc -b && npm run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"npm run check:api && npx tsc -b && npm run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S23: web agent unavailable banner

- Status: done
- Files: `src/chat/AgentUnavailableBanner.tsx`, `src/chat/AgentUnavailableBanner.test.tsx`, `src/chat/ChatView.tsx`, `src/ribbon/stateMark.tsx`, `src/ribbon/stateMark.test.ts`, `src/api/stream.ts`, `src/api/stream.test.ts`, `src/ribbon/useSessions.ts`
- Verify: `npx vitest run src/chat/AgentUnavailableBanner.test.tsx src/ribbon/stateMark.test.ts src/api/stream.test.ts && npm run lint && npx tsc -b`
- Verified head: d3be27faa9138dff98812231a256e1b2f4fdbef9

#### Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

Design D8 (my call), verbatim: "`agentMarkState('dead', ready)` returns `error`. The banner shows when `summary.queued > 0` and no agent is ready and `idle` (Q2 asks whether busy-only hives should show it)."

Q2 answer (my call, design.md Open questions): "The banner shows when messages are queued and either no agent is ready and alive (none ready, or all `dead`), or the oldest queued message is older than 10 minutes. A queue behind a busy leader is normal and stays quiet; a stuck busy agent still surfaces after 10 minutes."

Scope (agents-web):
- `src/chat/AgentUnavailableBanner.tsx` (new): an MUI Alert "Agent unavailable: N messages queued, oldest <age> ago" when `summary.queued > 0` and either no agent is `ready` with a state other than `dead`, or the oldest queued message is older than 10 minutes; the age from `summary.oldest_queued_at` through `formatAge`/`useNow` (`src/chat/agentAge.ts`); hidden otherwise.
- `src/chat/ChatView.tsx`: renders it above QueueStrip.
- `src/ribbon/stateMark.tsx`: `agentMarkState` maps `dead` to `error`; `src/ribbon/stateMark.test.ts` (new).
- `src/api/stream.ts` and `src/api/stream.test.ts`: the `message_status` event carries `oldestQueuedAt` (from `oldest_queued_at`); `src/ribbon/useSessions.ts` applies it to the session summary so the banner stays live.
- `src/chat/AgentUnavailableBanner.test.tsx`: tests named "shows when messages are queued and no agent is alive", "shows when the oldest queued message is older than 10 minutes", "hidden when a ready agent is busy and the queue is younger than 10 minutes", "hidden when an agent is ready and idle", "hidden when nothing is queued", "updates the age from the status stream".

Steps: tests first, seen failing; then the code; run the verify.

Notes: on the first full-suite failure, save the failing test name and output tail before any rerun (retro). Depends on web-sync-session-safety-api for the types.

#### Acceptance conditions

- AC1: the banner shows with the queued count and the oldest message's age when messages are queued and no agent is ready and alive [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "shows when messages are queued and no agent is alive"]
- AC2: the banner shows when the oldest queued message is older than 10 minutes even with a ready busy agent [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "shows when the oldest queued message is older than 10 minutes"]
- AC3: the banner is hidden when a ready agent is busy and the oldest queued message is younger than 10 minutes [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "hidden when a ready agent is busy and the queue is younger than 10 minutes"]
- AC4: the banner is hidden when an agent is ready and idle [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "hidden when an agent is ready and idle"]
- AC5: the banner is hidden when nothing is queued [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx -t "hidden when nothing is queued"]
- AC6: the age follows oldest_queued_at from the message_status frame [evidence: command:npx vitest run src/chat/AgentUnavailableBanner.test.tsx src/api/stream.test.ts]
- AC7: agentMarkState maps dead to error [evidence: command:npx vitest run src/ribbon/stateMark.test.ts]
- AC8: lint and typecheck pass [evidence: command:npm run lint && npx tsc -b]

#### Files

- `src/chat/AgentUnavailableBanner.tsx`
- `src/chat/AgentUnavailableBanner.test.tsx`
- `src/chat/ChatView.tsx`
- `src/ribbon/stateMark.tsx`
- `src/ribbon/stateMark.test.ts`
- `src/api/stream.ts`
- `src/api/stream.test.ts`
- `src/ribbon/useSessions.ts`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests named in the requirement; run the verify, expect them to fail.
- Green: implement the banner, the stateMark mapping and the stream field; run the verify, expect all passed.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-27 amended: Q2 settled: narrowed banner rule

- 2026-10-28 done

### S24: web discard backup notice

- Status: done
- Files: `src/sessions/DiscardSessionDialog.tsx`, `src/sessions/DiscardSessionDialog.test.tsx`, `MEMORY.md`
- Verify: `npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint && npx tsc -b`
- Verified head: 29e97bed08ea753cf8f055331123e59e4df30bbf

#### Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

Design D8 (my call), verbatim: "API: `SessionSummary.oldest_queued_at` (null when none), also carried by the `message_status` stream frame so the banner stays live; `SessionView.backup` `{workdir: bool, transcripts: bool, reason: str|null, last_transcripts_backup: {finished_at, bytes}|null}`, where each flag is true only when the discard would really save it (spec.cache set, `cache_available`, its restore state allows the save) and `reason` names why not (`no_session_cache`, `cache_not_configured`, or the skip reason)."

This task is the discard dialog: "the discard dialog states exactly what is lost vs backed up (from the new status/meta fields)".

Scope (agents-web):
- `src/sessions/DiscardSessionDialog.tsx`: two lists from `session.backup`: "Deleted" (agents, the workspace PVC, the chat history, the Claude transcripts unless backed up, the workspace files unless backed up) and "Backed up" (workspace files to the S3 cache under its key, Claude transcripts to the S3 cache, both restored when a session with the same slug is created), or a line "Nothing is backed up: <reason in words>". The existing hook line (history export) and the hook-failed alert stay. The typed-slug confirm stays.
- `src/sessions/DiscardSessionDialog.test.tsx`: tests named "states what is backed up when the session cache is configured", "states nothing is backed up without a session cache", "names the reason a backup is skipped"; existing tests keep passing (the static "Everything is deleted" body changes only where backups now apply: a test asserting that body is no longer accurate and is updated, naming it).
- MEMORY.md (agents-web): dated entry on D8.

Steps: tests first, seen failing; then the component; run the verify.

Notes: on the first full-suite failure, save the failing test name and output tail before any rerun (retro, recurring vitest load flake). No em dashes. Depends on web-sync-session-safety-api for the types.

#### Acceptance conditions

- AC1: with the session cache configured the dialog lists workspace files and Claude transcripts as backed up and restored on recreating the same slug, and the rest as deleted [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "states what is backed up when the session cache is configured"]
- AC2: without a session cache the dialog says nothing is backed up and why [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "states nothing is backed up without a session cache"]
- AC3: a skipped backup names its reason [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the reason a backup is skipped"]
- AC4: every dialog test passes [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx]
- AC5: MEMORY.md records the decision [evidence: command:grep -q "backed up" MEMORY.md]
- AC6: lint and typecheck pass [evidence: command:npm run lint && npx tsc -b]

#### Files

- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint && npx tsc -b"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"npx vitest run src/sessions/DiscardSessionDialog.test.tsx && npm run lint && npx tsc -b"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S25: web-review-fixes

- Status: done
- Files: `.github/workflows/ci.yaml`, `scripts/ci.test.mjs`, `src/sessions/DiscardSessionDialog.tsx`, `src/sessions/DiscardSessionDialog.test.tsx`, `src/chat/ChatView.test.tsx`
- Verify: `npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs`
- Verified head: 454e1aa2a40f252bfdcbca82a5ebabe74140195c

#### Requirement

Epic review findings for agents-web (.scratchpad/session-loss/review/web.md and security.md), my call to fix before merge:
1. `.github/workflows/ci.yaml` job `chart-publish-tag` needs only `[chart]`, so a tag build publishes the chart even when the `web` job (lint, tests) or `images` is red; make it need `[chart, images, web]` like `chart-publish`, and add a top-level `permissions: contents: read` block (raise per job only where needed). Extend scripts/ci.test.mjs so the gate is asserted for the tag job too.
2. `src/sessions/DiscardSessionDialog.tsx` (about lines 30-36): the `restore_failed` / `restore_skipped` wording always says the workspace is not saved, even when the side that is not backed up is the transcripts; name the right subject (workspace files vs chat history) per side.
3. No test asserts that `src/chat/ChatView.tsx` mounts `AgentUnavailableBanner`; add one.
Test first.

#### Acceptance conditions

- AC1: chart-publish-tag needs web, images and chart [evidence: command:node --test scripts/ci.test.mjs]
- AC2: the discard dialog names the chat history when the transcripts side is not backed up [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the chat history when transcripts are not backed up"]
- AC3: the discard dialog names the workspace files when the workdir side is not backed up [evidence: command:npx vitest run src/sessions/DiscardSessionDialog.test.tsx -t "names the workspace files when the workdir is not backed up"]
- AC4: ChatView renders the agent-unavailable banner when messages are queued and no agent is alive [evidence: command:npx vitest run src/chat/ChatView.test.tsx -t "mounts the agent unavailable banner"]
- AC5: the workflow declares top-level permissions [evidence: command:grep -q "^permissions:" .github/workflows/ci.yaml]

#### Files

- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`
- `src/sessions/DiscardSessionDialog.tsx`
- `src/sessions/DiscardSessionDialog.test.tsx`
- `src/chat/ChatView.test.tsx`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Red: write the tests the acceptance conditions name; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs` and see them fail for the expected reason.
- Green: implement the requirement as written; run `npx vitest run src/sessions/DiscardSessionDialog.test.tsx src/chat/ChatView.test.tsx && node --test scripts/ci.test.mjs` and expect every test to pass.
- Refactor with the verify green; add a dated MEMORY.md entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S26: helmfile deploy pins

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint`
- Verified head: 3b1bc0b

#### Requirement

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Goal G10, verbatim: "Released and deployed: wrapper release tag, orchestrator and web pins, agents-helmfile bump, apply and smoke green, with a live check that the deploy did not roll a busy agent."

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.b451f08`; agents-web chart `0.1.0-main.4d066a4`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `b451f08`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:0.3.2` (a release tag: Harbor prunes sha7 tags).
- `values/agents-web/common.yaml`: `image.tag` `4d066a4`.
- Tests: `tests/test_orchestrator_release.py` and `tests/test_web_release.py` keep the pins in agreement.
- `mise run check-pins` (task helmfile-pin-check) passes on the new pins: their main CI runs are green.

Merged shas (2026-10-28): agents-orchestrator PR #28 merge commit b451f08 (main CI run 40716752343 green, images and chart-publish), agents-web PR #20 merge commit 4d066a4 (main CI run 40722375652 green). claude-code-wrapper v0.3.2 released. The helmfile epic branch must contain origin/main (hotfix pins #36); rebase on it first if it does not.

Notes: `tests/test_orchestrator_release.py` holds `test_values_dir_moved`; it must pass so the apply is not stopped by a stale test (retro). Chart-pull tests blocked by a container network policy may be deselected locally (precedent); they run unblocked before the apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on the wrapper release [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC4: the agent image is the 0.3.2 release [evidence: command:grep -q "claude-code-wrapper:0.3.2" values/agents-orchestrator/common.yaml]
- AC5: every pin's main CI is green [evidence: command:mise run check-pins]
- AC6: the release test files and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: fill merged shas b451f08 and 4d066a4

- 2026-10-28 done

### S27: helmfile apply live check

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run smoke`
- Verified head: 2bc3ddd2228605a3c1d204bd502bffd3fbee1d54

#### Requirement

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Goal G10, verbatim: "Released and deployed: wrapper release tag, orchestrator and web pins, agents-helmfile bump, apply and smoke green, with a live check that the deploy did not roll a busy agent."

Design D2, user decision verbatim: ""A deploy never runs inside a pod that the same deploy rolls" is satisfied by D1: the deployer's pod is busy for the whole apply+smoke turn so it is not rolled until idle; an in-cluster Job runner is a non-goal. Add an orchestrator test that pins this (busy pod with outdated revision is not deleted across reconcile ticks)."

Live applies are run by the orchestrator session only, never by a subagent. Steps, after the agents-helmfile PR merges, in `code/agents-helmfile` on `main`, least destructive first:
1. Before: record every agent pod (namespace `agents`, StatefulSets `agent-*`) with uid, start time, its agent's state and leader flag (API), and the deployer's own pod name.
2. `mise run check-pins` green; `mise run diff`: only the orchestrator and agents-web chart versions and image tags and the agent image 0.3.2 change; anything else stops the task.
3. `mise run apply` (live; listed in design.md). The orchestrator applies the re-attach migration on start.
4. `mise run smoke` green, the session-continuity step included.
5. Live check: every agent StatefulSet is `OnDelete`; no pod whose agent was busy was deleted while busy (pod uids and start times against the step 1 record and the agent states, reconciler rollout log lines); the deployer's pod kept its uid through the apply and smoke turn; `status.rollout` drains to empty as agents go idle; no agent stays `dead`; a message to a rolled agent is answered.
6. MEMORY.md entry (containing the words `deploy-safe live check`) dated with the applied orchestrator chart and image, agents-web chart, wrapper image `0.3.2`, and the step 5 evidence.

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run. `gh` must be authenticated in the deploying pod for check-pins.

#### Acceptance conditions

- AC1: the smoke passes against the applied release, the session-continuity step included [evidence: command:mise run smoke]
- AC2: every agent StatefulSet is OnDelete live [evidence: command:test "$(kubectl -n agents get statefulset -o jsonpath='{range .items[*]}{.metadata.name}={.spec.updateStrategy.type}{"\n"}{end}' | grep '^agent-' | grep -vc '=OnDelete$')" = 0]
- AC3: MEMORY.md records the applied versions [evidence: command:grep -q "claude-code-wrapper:0.3.2" MEMORY.md]
- AC4: MEMORY.md records the live check that no busy agent pod was replaced and the deployer pod kept its uid [evidence: command:grep -q "deploy-safe live check" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `mise run smoke` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `mise run smoke` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done: applied 16:34Z by tatara-0 from main 030c93d; smoke OK incl. continuity; MEMORY entry PR #38 merged c9ba047; evidence .logs/deploy-safe-2026-10-28/live-check.md

- 2026-10-28 actuals: no agent records

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
