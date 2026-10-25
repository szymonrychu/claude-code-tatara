---
title: schedules api routes
status: in-progress
repo: agents-schedule
value: "schedules are created, edited, previewed, enabled, disabled and deleted over HTTP with reasons for every refusal"
files: [src/agents_schedule/api/__init__.py, src/agents_schedule/api/app.py, src/agents_schedule/api/schemas.py, src/agents_schedule/api/schedules.py, tests/test_api_schedules.py]
verify: "uv run --frozen pytest tests/test_api_schedules.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [schedules-repository, runs-repository, cron-expressions, schedule-settings-model]
model: ""
review: ""
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

# schedules api routes

## Requirement

Add the FastAPI app (design D11; approvals A2, A5). Every route is under `/schedules/api/v1` (gate Q9; the path layout contract of frontend-decoupling); `/healthz` and `/readyz` sit at the root for probes.

- `create_app(settings, pool, client) -> FastAPI` with a source allowlist middleware on `SCHED_ALLOWED_CIDRS` that checks the socket peer only, never forwarded headers (the agents-common one if it ships it, else the pattern of `code/agents-orchestrator/src/agents_orchestrator/api/allowlist.py:SourceAllowlist`). Errors use `{"error": {"code", "message"}}` (as `code/agents-orchestrator/src/agents_orchestrator/api/errors.py`).
- `GET /schedules` -> `list[ScheduleView]` by name; `POST /schedules` -> 201; `GET /schedules/{id}`; `PUT /schedules/{id}` (full replace of `name, cron, timezone, preset_id, prompt, enabled`); `DELETE /schedules/{id}` -> 204; `POST /schedules/preview {cron, timezone}` -> `{next_fires: [3 ISO times]}`.
- `ScheduleIn {name, cron, timezone (default SCHED_DEFAULT_TIMEZONE), preset_id, prompt, enabled = true}`; `ScheduleView {id, name, cron, timezone, preset_id, prompt, enabled, next_fires (3, empty when disabled), last_run: RunView | null, created_at, updated_at}`; `RunView {id, schedule_id, trigger, fire_time, status, reason, session_id, session_slug, message_id, reuse, created_at, updated_at, started_at, finished_at}`.
- Validation on every write: cron via `sched-cron` (422 `invalid_cron` with the reason), timezone (422 `invalid_timezone`), prompt 1..16384 chars and name 1..100 (422 `invalid_request`), preset exists via the orchestrator client `GET /api/v1/presets/{id}` (contract `orch-presets-api`; 422 `unknown_preset`; orchestrator unreachable 503 `orchestrator_unavailable`). Duplicate name 409 `conflict`; missing id 404 `not_found`.
- Each write notifies `schedules_changed` so the scheduler wakes.
- `/readyz` checks the DB; `/healthz` is liveness only.

## Acceptance conditions

- AC1: create, list, get, replace and delete round-trip a schedule [evidence: test:tests/test_api_schedules.py::test_crud]
- AC2: an invalid cron or timezone answers 422 with its code and reason [evidence: test:tests/test_api_schedules.py::test_validation_422]
- AC3: an unknown preset answers 422 unknown_preset and an unreachable orchestrator 503 [evidence: test:tests/test_api_schedules.py::test_preset_checked]
- AC4: preview returns the next 3 fire times in the given zone [evidence: test:tests/test_api_schedules.py::test_preview]
- AC5: a duplicate name answers 409 and a missing id 404 [evidence: test:tests/test_api_schedules.py::test_conflict_and_not_found]
- AC6: a peer outside SCHED_ALLOWED_CIDRS gets 403 and X-Forwarded-For is ignored [evidence: test:tests/test_api_schedules.py::test_source_allowlist]

## Files

- `src/agents_schedule/api/__init__.py`
- `src/agents_schedule/api/app.py`
- `src/agents_schedule/api/schemas.py`
- `src/agents_schedule/api/schedules.py`
- `tests/test_api_schedules.py`

## Interfaces

- `agents_schedule.api.app:create_app(settings, pool, client) -> FastAPI` (part `sched-api-app`), routers mounted under `/schedules/api/v1`.
- `agents_schedule.api.schemas`: `ScheduleIn`, `ScheduleView`, `RunView`, `PreviewIn`, `PreviewView`.

## Expected outcome

Schedules are managed headlessly over HTTP with the same validation the UI shows.

## Steps

- Write tests/test_api_schedules.py with httpx ASGI transport, a migrated DB and a fake orchestrator client; run: fails.
- Write the api package; `uv run --frozen pytest tests/test_api_schedules.py -q`: `6 passed`.
- Lint clean.

## Notes

- The api is the only writer of `schedules`.
- `/schedules/api/v1` is the reserved prefix of the frontend-decoupling URL layout (contract `agents-web-url-layout`: each later service owns `/<prefix>/`, its UI-facing API at `/<prefix>/api/v1`, reserved `schedules`).
- Tests use `agents_common.fake_orchestrator` for the preset check.

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
