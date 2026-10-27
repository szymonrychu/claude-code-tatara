---
title: orch eligibility single source
status: done
repo: agents-orchestrator
value: "the pass, the claim hold and set_replicas cannot drift apart on who may lead"
files: [src/agents_orchestrator/db/eligibility.py, src/agents_orchestrator/db/leadership.py, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/db/sessions.py]
verify: "uv run ruff check . && uv run ruff format --check . && uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py tests/test_queue_leader_routing.py tests/test_sessions_repo.py tests/test_agent_scale.py tests/test_api_scale.py tests/test_reconciler.py"
depends_on: []
model: sonnet
review: ""
verified_head: 059372fcd3ce0453be243bd7b62ad1a15fd67d56
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: 3
actual_minutes: 15
actual_tokens: 900392
actual_roles: "impl 10, review 5"
actual_role_tokens: "impl 695880, review 204512"
---

# orch eligibility single source

## Requirement

Epic review finding (leader-auto-handover review, 2026-10-27, Consider 2, scope-auditor duplicate sweep), accepted by the hive leader as a task: "orchestrator single source for eligibility/handover-pending predicates (agents-orchestrator, sonnet, behaviour unchanged)".

Evidence from the review (main b3a2975):
- `db/leadership.py` `_CANDIDATES` respells the eligible predicate inline (alias `x`: ready, gone_at IS NULL, wrapper_session_id IS NOT NULL, ordinal < REPLICAS) instead of `eligibility.ELIGIBLE`.
- `db/leadership.py` `_target_ready` respells ready / gone next to `STAYS` (it does not require `wrapper_session_id`; keep that exactly).
- The "compacted in its term or leaving" trigger is spelled three times: `_CANDIDATES`, `_leader` (`leaving`, `compacted` columns), `db/queue.py` `_HANDOVER_PENDING`.
- `eligibility.REPLICAS` repeats the `2147483647` literal instead of `NO_LIMIT`.

Scope: `db/eligibility.py` becomes the single source of these SQL fragments (stays / ready-and-stays / eligible, the compacted-or-leaving trigger, REPLICAS built from NO_LIMIT); `_CANDIDATES`, `_target_ready`, `_leader` and `_HANDOVER_PENDING` (and `sessions.set_replicas` if it respells any) use them. Behaviour unchanged: no SQL semantics change, no test edited or weakened; the existing tests (tests/test_leadership_pass.py, test_dispatcher_auto_handover.py, test_queue_leader_routing.py, test_sessions_repo.py, test_agent_scale.py, test_api_scale.py, test_reconciler.py) are the guard. This is a pure refactor (TDD exception: behaviour-preserving refactor under existing tests); add a unit test pinning that the shared fragments are what the call sites embed only if cheap.

Environment note: the DB tests use testcontainers and need Docker, which this pod lacks (no docker, no dockerd). Run lint and every test that does not need Docker locally; the PR's GitHub CI `test` job (`mise run test`) is the evidence for the DB tests and is checked by the orchestrator before merge.

## Acceptance conditions

- AC1: eligibility.py holds the stays, ready-and-stays, eligible and compacted-or-leaving fragments and REPLICAS uses NO_LIMIT [evidence: symbol:src/agents_orchestrator/db/eligibility.py:ELIGIBLE]
- AC2: leadership.py and queue.py contain no inline respelling of those predicates [evidence: command:! grep -nE "x\.ready|2147483647" src/agents_orchestrator/db/leadership.py src/agents_orchestrator/db/queue.py]
- AC3: the leadership, queue and scale tests pass unchanged [evidence: command:uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py tests/test_queue_leader_routing.py tests/test_sessions_repo.py tests/test_agent_scale.py tests/test_api_scale.py tests/test_reconciler.py]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/eligibility.py`
- `src/agents_orchestrator/db/leadership.py`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/db/sessions.py`

## Interfaces

- `src/agents_orchestrator/db/eligibility.py`: module constants (SQL fragments) `NO_LIMIT`, `REPLICAS`, `STAYS`, `ELIGIBLE`, plus new fragments for ready-and-stays and the compacted-or-leaving trigger; aliases documented as today.
- Kept unchanged: `leadership._CANDIDATES`, `leadership._leader` result columns (`leaving`, `compacted`), `leadership._target_ready`, `queue._HANDOVER_PENDING`, `sessions.set_replicas` semantics.

## Expected outcome

Every eligibility and handover-pending predicate is spelled once in `eligibility.py`; the call sites embed the shared fragments; SQL semantics and all tests are unchanged.

## Steps

- Read eligibility.py, leadership.py, queue.py, sessions.py and the guard tests in one pass.
- Behaviour-preserving refactor (TDD exception: refactor under existing tests). Baseline: `uv run ruff check . && uv run ruff format --check .` passes; non-Docker tests pass.
- Move the fragments into eligibility.py and replace the inline spellings; run AC2's grep: no output.
- `uv run ruff check . && uv run ruff format --check .`: `All checks passed!`.
- Run the task verify; DB tests need Docker (absent in this pod), so they error locally and the PR CI `test` job is the evidence.

## Notes

Keep `_target_ready` without the `wrapper_session_id` requirement (manual make-leader target), exactly as today. `_CANDIDATES` uses alias `c` for the session and `REPLICAS`; `ELIGIBLE` uses a subquery `STAYS` - equivalent, choose the shared fragment that preserves semantics. The module docstring explains why eligibility.py lives apart from leadership.py (import cycle with queue.py).

- 2026-10-27 done: reviewer clean (SQL equivalence); PR #25 CI test '1083 passed, 56 deselected' and kind e2e pass on 059372f (DB tests need Docker, absent in this pod)
