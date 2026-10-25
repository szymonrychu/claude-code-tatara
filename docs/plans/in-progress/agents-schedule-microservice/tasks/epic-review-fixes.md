---
title: epic review fixes
status: todo
repo: agents-schedule
value: "one bad run never stops all schedules, and the api allowlist really sees the socket peer behind the SSO sidecar"
files: [src/agents_schedule/dispatcher.py, src/agents_schedule/tracker.py, src/agents_schedule/scheduler.py, src/agents_schedule/db/runs.py, src/agents_schedule/api/runs.py, src/agents_schedule/runtime.py, Dockerfile, tests/test_dispatcher.py, tests/test_tracker.py, tests/test_entrypoints.py, tests/test_ci_workflow.py]
verify: "uv run --frozen pytest tests/test_dispatcher.py tests/test_tracker.py tests/test_scheduler.py tests/test_api_runs.py tests/test_entrypoints.py tests/test_ci_workflow.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [kind-e2e-api]
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 494911
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# epic review fixes

## Requirement

Fix the findings of the phase 5 epic review and security review of agents-schedule-microservice (design D9, D11; review focus: exactly-once, the allowlist reads only the socket peer).

- Per-run fault isolation: in `agents_schedule.dispatcher` (`resume_pending`, `dispatch_once`) and `agents_schedule.tracker` (the `track_once` loop), an unexpected exception while handling one run (anything other than the orchestrator errors already handled, for example a malformed orchestrator payload or a DB error on that run) is logged with `log.exception` naming the run id and the loop continues with the next run; it never escapes into the worker TaskGroup (`runtime.py:_hold_and_run`) and never kills the scheduler, dispatcher and tracker together. The same run is retried on a later pass, not skipped forever and not posted twice.
- The per-schedule fire lock shared by the scheduler and the run-now route is a public helper, `agents_schedule.db.runs.fire_lock(conn, schedule_id)` (or a public `FIRE_LOCK` in `scheduler.py`), used by both `scheduler.py` and `api/runs.py`; no module imports a private name of another.
- The api server never rewrites the client address from forwarded headers: `runtime.py` builds `uvicorn.Config(..., proxy_headers=False)`, so `SourceAllowlist` sees the socket peer (the oauth2-proxy sidecar on 127.0.0.1) even when the request carries `X-Forwarded-For`.
- The Dockerfile pins the uv build image to an exact version tag (no `:latest`).

## Acceptance conditions

- AC1: an unexpected exception on one run is logged and the dispatcher continues with the next run [evidence: test:tests/test_dispatcher.py::test_unexpected_error_isolated_per_run]
- AC2: an unexpected exception on one run is logged and the tracker continues with the next run [evidence: test:tests/test_tracker.py::test_unexpected_error_isolated_per_run]
- AC3: the scheduler and the run-now route share one public fire-lock helper [evidence: judgement:no `_FIRE_LOCK` or other private cross-module import in src/agents_schedule/api/runs.py]
- AC4: a request through a real uvicorn server from 127.0.0.1 carrying X-Forwarded-For of an outside address is admitted by the default allowlist, and the allowlist decision uses the socket peer [evidence: test:tests/test_entrypoints.py::test_api_ignores_forwarded_headers]
- AC5: the Dockerfile pins the uv image to an exact version [evidence: test:tests/test_ci_workflow.py::test_dockerfile_pins_uv]

## Files

- `src/agents_schedule/dispatcher.py`
- `src/agents_schedule/tracker.py`
- `src/agents_schedule/scheduler.py`
- `src/agents_schedule/db/runs.py`
- `src/agents_schedule/api/runs.py`
- `src/agents_schedule/runtime.py`
- `Dockerfile`
- `tests/test_dispatcher.py`
- `tests/test_tracker.py`
- `tests/test_entrypoints.py`
- `tests/test_ci_workflow.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
