---
title: orch rollout replacer
status: in-progress
repo: agents-orchestrator
value: deploys never replace a busy or leading agent pod mid-turn
files: [src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/reconciler/rollout.py, src/agents_orchestrator/reconciler/loop.py, tests/fakes/fake_kube.py, tests/test_rollout.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, MEMORY.md]
verify: "uv run pytest -q tests/test_rollout.py tests/test_reconciler.py tests/test_render.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-default-continue-prompt, orch-dead-agent-ineligible]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 14
expected_tokens: 3155191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch rollout replacer

## Requirement

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

## Acceptance conditions

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

## Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/reconciler/rollout.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `tests/fakes/fake_kube.py`
- `tests/test_rollout.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_rollout.py tests/test_reconciler.py tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_rollout.py tests/test_reconciler.py tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
