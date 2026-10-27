---
title: scale down staying peer
status: done
repo: agents-orchestrator
value: a scale-down below the leader is accepted whenever another ready agent can lead
files: [src/agents_orchestrator/db/sessions.py, tests/test_sessions_repo.py, tests/test_api_scale.py, tests/test_agent_scale.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_sessions_repo.py tests/test_api_scale.py tests/test_agent_scale.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [leadership-auto-handover]
model: opus
review: ""
verified_head: 8d03b3830508c724abff19565ade9a7c82c4dae7
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: 3
actual_minutes: 8
actual_tokens: 1678149
actual_roles: "impl 7, review 1"
actual_role_tokens: "impl 1510053, review 168096"
---

# scale down staying peer

## Requirement

Goal G2, verbatim: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks; with no such agent it is refused as today." User decision: "Scale-down that would remove the leader's pod: hand over first, then shrink. If no ready peer that stays is available, the scale-down is still refused."

Design D5, verbatim: `db/sessions.set_replicas` refuses `leader_would_leave` only when the leader's ordinal is at or above the new replica count and no staying peer exists: another agent of the session that is ready, not gone, has a wrapper session and has `ordinal < replicas` (the same predicate as the pick, D7). Otherwise it writes `spec.replicas` as today and answers 202. The api never moves the leader; the dispatcher derives the move from `spec.replicas` (D6). The error code keeps its name and now means "the leader would leave and no ready agent that stays can take over". Refusal order and every other code are unchanged.

Design D15, verbatim (api half): `set_replicas` sends `NOTIFY leadership_requested {session_id}` when it accepts a count at or below the leader's ordinal.

Scope:
- `src/agents_orchestrator/db/sessions.py` `set_replicas`: the refusal above, reading `agents` only (never writing `session_leaders` or `agents`); one predicate shared with the pick of `db/leadership.py` (where it lives is left to the builder); in the same transaction, after the write, `NOTIFY leadership_requested {session_id}` when the accepted count is at or below the leader's ordinal (no NOTIFY otherwise beyond today's `session_changed`). Docstrings updated.
- Tests:
  - `tests/test_sessions_repo.py`: a new test that a scale-down below the leader is written when a staying peer exists (no `session_leaders` change, one `leadership_requested` NOTIFY), and refused `leader_would_leave` when the only other agents are not ready, gone, without a wrapper session, or themselves leaving.
  - `tests/test_api_scale.py`: a new test that `POST /api/v1/sessions/{id}/scale` below the leader answers 202 with a staying ready peer.
  - `tests/test_agent_scale.py`: a new test that the leader's `POST /agent/v1/scale` below its own ordinal answers 202 with a staying ready peer.
- Tests no longer accurate, to update (each asserted "a scale-down below the leader is always refused", which the user's decision replaces):
  - `tests/test_sessions_repo.py::test_set_replicas_leader_rules`: its `leader_would_leave` cases must use a session with no eligible staying agent (ordinal 0 not ready or without a wrapper session); the `not_leader` case and the accepted 4 to 3 case stay.
  - `tests/test_api_scale.py::test_scale_leader_would_leave`: agents 0 and 1 are ready, so 3 to 2 is now accepted; it keeps asserting 409 `leader_would_leave` with agents 0 and 1 made ineligible.
  - `tests/test_agent_scale.py::test_agent_scale_refusals`: its `leader_would_leave` case (leader ordinal 1, scale to 1) must make ordinal 0 ineligible; the other refusals stay.
- README: the error code list (`leader_would_leave` (409, a scale-down that would remove the leader while no ready agent that stays can take over)), `POST /api/v1/sessions/{session_id}/scale`, `POST /agent/v1/scale`, and the Scaling bullet "The leader is never removed ..." replaced by: a scale-down below the leader's ordinal hands leadership to a ready agent that stays (reason `scale_down`, see Leadership), then shrinks; with no such agent it is 409 `leader_would_leave`.
- MEMORY.md: a dated entry (2026-10-26, leader-auto-handover) amending the 2026-10-24 cluster-scaling entry's `leader_would_leave` rule.

Notes: `hive()` in `tests/test_agent_scale.py` and the `insert_agent` factory decide readiness and the wrapper session; check them before writing fixtures. openapi.json does not list `leader_would_leave`, so it does not change (verify with `tests/test_readme_api.py`).

## Acceptance conditions

- AC1: `set_replicas` below the leader's ordinal writes `spec.replicas` when another ready, not gone agent with a wrapper session and `ordinal < replicas` exists, touches no `session_leaders` row, and sends `NOTIFY leadership_requested {session_id}`; a scale that leaves the leader in place sends none [evidence: test:tests/test_sessions_repo.py::test_set_replicas_below_leader_with_staying_peer]
- AC2: with no such agent (others not ready, gone, without a wrapper session, or leaving) it is refused `leader_would_leave` and nothing is written [evidence: test:tests/test_sessions_repo.py::test_set_replicas_leader_rules]
- AC3: the public scale route answers 202 below the leader with a staying ready peer [evidence: test:tests/test_api_scale.py::test_scale_below_leader_accepted]
- AC4: the public scale route still answers 409 `leader_would_leave` with no staying ready peer [evidence: test:tests/test_api_scale.py::test_scale_leader_would_leave]
- AC5: the leader's agent scale route answers 202 below its own ordinal with a staying ready peer, and the refusals stay [evidence: command:uv run --frozen pytest -q tests/test_agent_scale.py]
- AC6: README and openapi stay in sync and MEMORY.md records the amendment [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py && grep -q "leader_would_leave" MEMORY.md]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/sessions.py`
- `tests/test_sessions_repo.py`
- `tests/test_api_scale.py`
- `tests/test_agent_scale.py`
- `README.md`
- `MEMORY.md`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: add the new tests and update the three named inaccurate tests; run `uv run --frozen pytest -q tests/test_sessions_repo.py tests/test_api_scale.py tests/test_agent_scale.py`: the new acceptance tests fail (still refused, no NOTIFY).
- Green: change `set_replicas` (shared predicate, NOTIFY), README and MEMORY.md; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): finding 2 (set_replicas wakes the dispatcher)

- 2026-10-26 done
