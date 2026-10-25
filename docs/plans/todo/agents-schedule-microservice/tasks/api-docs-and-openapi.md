---
title: api docs and openapi
status: todo
repo: agents-schedule
value: the schedule API is documented and its contract cannot drift silently
files: [openapi.json, README.md, src/agents_schedule/api/openapi.py, tests/test_readme_api.py]
verify: "uv run --frozen pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [runs-api-routes]
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

# api docs and openapi

## Requirement

Document the API (design D11; approval A5), the pattern of `code/agent-orchestrator/tests/test_readme_api.py`:

- `python -m agents_schedule.api.openapi` prints the OpenAPI document; `openapi.json` is committed.
- `tests/test_readme_api.py`: the committed `openapi.json` equals the generated one (drift test), and every route in it is named in README `## API` with method and path.
- README `## API`: base path `/schedules/api/v1`, each route with request body, response, status codes and error codes; the run statuses and reasons (`previous_running`, `schedule_disabled`, `preset_missing`, `orchestrator_refused`, `orchestrator_unavailable`, `message_failed`, `message_cancelled`, `turn_failed`, `message_gone`); the placeholders `{schedule_name}`, `{fired_at}`; and a `### Versioning` note that `/schedules/api/v1` is additive-only. README `## Commands` names `sched migrate|api|worker`.

## Acceptance conditions

- AC1: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_matches_app]
- AC2: every route is documented in README ## API [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- AC3: README documents the API, run reasons and versioning [evidence: doc-section:README.md#API]

## Files

- `openapi.json`
- `README.md`
- `src/agents_schedule/api/openapi.py`
- `tests/test_readme_api.py`

## Interfaces

- Contract `agents-schedule-api` (file `code/agents-schedule/README.md`, `openapi.json`): consumed by agents-web (vendored as `openapi/agents-schedule.json`) and the agents-helmfile smoke.

## Expected outcome

Anything the UI can do is documented as an HTTP call, and a route change without regenerating openapi.json fails the tests.

## Steps

- Write tests/test_readme_api.py; run: fails (no openapi.json).
- Write openapi.py, generate openapi.json, write README ## API; `uv run --frozen pytest tests/test_readme_api.py -q`: `2 passed`.
- Lint clean.

## Notes

- `/schedules/api/v1` is additive-only from its first release; agents-web vendors this file.
