---
title: Smoke waits for agent readiness before make-leader
status: todo
repo: agents-helmfile
value: "The live smoke no longer fails on the orchestrator's agent-ready lag, so the deploy can be verified"
files: [scripts/smoke.sh, tests/test_smoke_script.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts=\"\" tests/test_smoke_script.py && mise run lint"
depends_on: [helmfile-deploy-pin]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Smoke waits for agent readiness before make-leader

## Requirement

Discovered at deploy (2026-10-27, live `mise run smoke` after the R3 apply, investigation in .scratchpad/cluster-options/leader-debug.md): scripts/smoke.sh's scale-down-below-leader step POSTs /api/v1/sessions/{id}/leader for pod-1's agent as soon as the pod is Kubernetes-Ready and its agent row exists (agent_of, smoke.sh ~528-541), but the orchestrator's agents.ready flag lags pod readiness, so the dispatcher rejects the request `target_not_ready` within milliseconds (db/leadership.py _target_ready) and the smoke waits 600s for a leader change that never comes. Fix the smoke: wait until pod-1's agent is listed with `ready: true` (and not gone) before POSTing /leader; if the leader still has not become pod-1 after a short bounded wait (for example 30s), POST /leader again, up to the step's deadline, so a rejected request is retried. Every failure still names the step and its cause.

## Acceptance conditions

- ac1: no POST /leader is sent while the fake agents list reports pod-1 ready false; it is sent once pod-1 turns ready true and the step passes [evidence: test:tests/test_smoke_script.py::test_make_leader_waits_for_agent_ready]
- ac2: when the first make-leader request is rejected (leader unchanged), the smoke POSTs /leader again and passes once the leader moves [evidence: test:tests/test_smoke_script.py::test_make_leader_retries_rejected_request]
- ac3: the smoke, nomenclature and hygiene tests and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_smoke_script.py && mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
