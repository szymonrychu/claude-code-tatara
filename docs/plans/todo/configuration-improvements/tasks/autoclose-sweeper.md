---
title: autoclose sweeper
status: todo
repo: agent-orchestrator
value: a cluster closes itself after a set time through the normal discard
files: [src/agent_orchestrator/db/clusters.py, src/agent_orchestrator/api/autoclose.py, src/agent_orchestrator/api/app.py, tests/test_autoclose.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_autoclose.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-config-fields]
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# autoclose sweeper

## Requirement

Close clusters whose autoclose time has come, through the existing discard path (design D5; approval A4). 

- `src/agent_orchestrator/db/clusters.py`: `close_expired(conn) -> list[uuid.UUID]` runs one statement, `UPDATE clusters SET desired = 'deleting', generation = generation + 1 WHERE desired = 'active' AND spec ? 'autoclose_after_seconds' AND created_at + make_interval(secs => (spec->>'autoclose_after_seconds')::int) <= now() RETURNING id`, and NOTIFYs `cluster_changed` for each id in the same transaction (the same write `request_delete` makes). It writes no other column.
- `src/agent_orchestrator/api/autoclose.py`: `AUTOCLOSE_POLL_SECONDS = 10` (module constant) and a sweeper coroutine that calls `close_expired` every poll until stopped, logging each closed cluster id and surviving a failed pass (logged, retried next poll).
- `src/agent_orchestrator/api/app.py`: the lifespan starts the sweeper after the listener and cancels it cleanly on shutdown.

The reconciler is unchanged: it discards `deleting` clusters as today (quiesce, discard hook export, delete objects, purge). The api stays the only writer of `clusters.desired`; several api replicas are safe because the update is status-guarded.

README.md: `### Autoclose` under `## Discard`: the field, counted from `created_at`, the floor `ORCH_AUTOCLOSE_MIN_SECONDS` (default 300), the poll lag (about 10 s), that it is the same discard as `DELETE /api/v1/clusters/{id}` (discard hook export included, no handoff turn), and the single-writer table note that the api sweeper writes `desired`. MEMORY.md: a dated entry for choosing the api sweeper over a derived predicate or a reconciler write, with the why.

## Acceptance conditions

- AC1: close_expired flips only active clusters past created_at plus autoclose_after_seconds to deleting with generation plus one, notifies cluster_changed, and leaves clusters without the field, not yet due or already deleting untouched, with no other column written [evidence: test:tests/test_autoclose.py::test_close_expired_flips_only_due_clusters]
- AC2: two concurrent close_expired calls flip each due cluster exactly once [evidence: test:tests/test_autoclose.py::test_close_expired_is_idempotent]
- AC3: the api lifespan runs the sweeper, a due cluster becomes deleting within one poll, and shutdown cancels the sweeper cleanly [evidence: test:tests/test_autoclose.py::test_sweeper_runs_in_api_lifespan]
- AC4: README documents autoclose and the single-writer note [evidence: doc-section:README.md#Autoclose]
- AC5: MEMORY.md records the writer choice with the date and why [evidence: judgement:MEMORY.md entry reviewed]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/db/clusters.py`
- `src/agent_orchestrator/api/autoclose.py`
- `src/agent_orchestrator/api/app.py`
- `tests/test_autoclose.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Builds part `orch-cluster-autoclose` (`db/clusters.py::close_expired`, `api/autoclose.py::AUTOCLOSE_POLL_SECONDS`); uses `orch-spec-config-fields`.

## Expected outcome

A cluster with `autoclose_after_seconds` turns `deleting` within about 10 s of its deadline and is discarded exactly as by `DELETE /api/v1/clusters/{id}`.

## Steps

- Red, write `tests/test_autoclose.py` (backdate `created_at` with SQL; LISTEN on `cluster_changed`; two concurrent calls for the idempotence test; the app lifespan with a short poll patched in)
- Green, implement
- Run the verify command.

## Notes

Decisions are in design.md; nothing beyond the requirement.
