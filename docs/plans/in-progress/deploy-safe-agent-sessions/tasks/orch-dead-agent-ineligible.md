---
title: orch dead agent ineligible
status: done
repo: agents-orchestrator
value: "a dead agent never holds leadership, so untargeted messages reach a live leader"
files: [src/agents_orchestrator/db/eligibility.py, src/agents_orchestrator/db/leadership.py, tests/test_dead_agent_eligibility.py, tests/test_eligibility_fragments.py, MEMORY.md]
verify: "uv run pytest -q tests/test_dead_agent_eligibility.py tests/test_eligibility_fragments.py tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: c822ff50fd66d41c7ce30089ca9f5151fd7a8559
points: 3
expected_minutes: 6
expected_tokens: 940114
points_actual: 3
actual_minutes: 37
actual_tokens: 1862484
actual_roles: "impl 3, review 31"
actual_role_tokens: "impl 1167668, review 694816"
---

# orch dead agent ineligible

## Requirement

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

## Acceptance conditions

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

## Files

- `src/agents_orchestrator/db/eligibility.py`
- `src/agents_orchestrator/db/leadership.py`
- `tests/test_dead_agent_eligibility.py`
- `tests/test_eligibility_fragments.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_dead_agent_eligibility.py tests/test_eligibility_fragments.py tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_dead_agent_eligibility.py tests/test_eligibility_fragments.py tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done
