---
title: smoke scale below leader
status: done
repo: agents-helmfile
value: every deploy proves a scale-down below the leader hands over and shrinks
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint"
depends_on: [scale-down-staying-peer, leader-changed-reason]
model: sonnet
review: ""
verified_head: f73dc2c2148b1ea2ee36d03398e2530eb7428198
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: 3
actual_minutes: 21
actual_tokens: 694284
actual_roles: "impl 18, review 3"
actual_role_tokens: "impl 505872, review 188412"
---

# smoke scale below leader

## Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Goal G2: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks".

Scope, in `scripts/smoke.sh` step 7 (scale 1 to 2 to 1 through the public route, pod-0 must never restart):
- After pod-1 is Ready, read the agents of the smoke session (`GET /api/v1/sessions/{id}/agents`), make pod-1's agent the leader with `POST /api/v1/sessions/{id}/leader {agent_id}` (expects 202) and wait within `SMOKE_TIMEOUT_S` until the session view's `leader_agent_id` is pod-1's agent.
- `scale 1` still expects 202 (it was refused before this epic). Then wait within `SMOKE_TIMEOUT_S` until the session view's `leader_agent_id` is pod-0's agent and `leader_reason` is `scale_down`, and then until pod-1 is gone; each timeout fails with a named message (`scale down: leader did not move to pod-0 with reason scale_down`, `scale down: <pod1> still present`).
- pod-0's uid check stays. Cleanup stays in the existing trap.
- `tests/test_smoke_script.py`: the fake API serves the leader route, the agents list and a leader that moves to pod-0 with reason `scale_down` after the scale to 1; new tests for a leader that never moves and a wrong reason; the happy path stays green.
- README smoke section: the scale step makes pod-1 the leader and proves a scale-down below the leader hands leadership to pod-0 (reason `scale_down`) before pod-1 goes.

Notes: the smoke's header comment (lines 1-7) names the steps; update it. Keep the script strict, bounded and shellcheck clean (`test_script_is_shellcheck_clean`, `test_script_is_strict_bounded_and_traps`). Live runs happen only in task helmfile-apply-smoke, by the orchestrator session.

## Acceptance conditions

- AC1: the happy path makes pod-1 leader, scales to 1 with 202, sees the leader move to pod-0 with reason scale_down, sees pod-1 gone and exits 0 with cleanup [evidence: test:tests/test_smoke_script.py::test_happy_path_exits_zero_and_cleans_up]
- AC2: a leader that never moves to pod-0 after the scale-down fails with a named message and cleans up [evidence: test:tests/test_smoke_script.py::test_scale_down_leader_not_moved_fails]
- AC3: a leader that moves with a reason other than scale_down fails with a named message [evidence: test:tests/test_smoke_script.py::test_scale_down_wrong_reason_fails]
- AC4: a scale answer other than 202 still fails [evidence: test:tests/test_smoke_script.py::test_scale_refused_fails]
- AC5: the script stays strict, bounded and shellcheck clean [evidence: test:tests/test_smoke_script.py::test_script_is_shellcheck_clean]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: extend the fake API in `tests/test_smoke_script.py` (agents list, leader route, leader moving with reason `scale_down`) and add the two failure tests; run `uv run --frozen pytest -q tests/test_smoke_script.py`: the happy path and the new tests fail.
- Green: extend step 7 of `scripts/smoke.sh`, its header and the README smoke section; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done
