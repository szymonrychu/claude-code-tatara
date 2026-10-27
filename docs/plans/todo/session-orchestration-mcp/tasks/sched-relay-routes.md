---
title: sched relay routes
status: todo
repo: agents-schedule
value: "the orchestrator can list all schedules and manage each caller's own through one documented contract"
files: [src/agents_schedule/api/relay.py, src/agents_schedule/api/schedules.py, src/agents_schedule/api/runs.py, src/agents_schedule/api/openapi.py, openapi-relay.json, README.md, tests/test_relay_schedules.py, tests/test_readme_api.py]
verify: "uv run pytest tests/test_relay_schedules.py tests/test_readme_api.py tests/test_api_schedules.py tests/test_api_runs.py && mise run lint"
depends_on: [sched-relay-listener]
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

# sched relay routes

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "Relay routes: list all (read); create, update, delete, run-now and runs on owned schedules (404 `not_found` when not owned). [...] The listener contract is committed as `openapi-relay.json` and vendored by the orchestrator, like Matrix D16."

Design D9, verbatim: "Schedule side: `SCHED_RELAY_MAX_PER_OWNER` (10) owned schedules, else 409 `owned_limit` (my call on the code); `SCHED_RELAY_MIN_INTERVAL_MINUTES` (15): the next three fires must be at least this far apart, else 422 `too_frequent`."

Open question Q5 (pending; the plan follows the recommended answer), verbatim: "Agent-created schedules may fire at most every 15 minutes, at most 10 per session; at most 5 live owned sessions and 30 writes per hour?" recommended "yes".

Architect reuse, verbatim: "agents-schedule `api/schedules.py` handlers and `_check_preset`."

Scope (agents-schedule): `api/relay.py` (routes `GET /relay/v1/schedules`, `POST /relay/v1/schedules`, `PUT /relay/v1/schedules/{id}`, `DELETE /relay/v1/schedules/{id}`, `POST /relay/v1/schedules/{id}/run`, `GET /relay/v1/schedules/{id}/runs`), `api/schedules.py` and `api/runs.py` (shared handler bodies taking an owner), `api/openapi.py` (also writes the relay document), committed `openapi-relay.json`, README (`## Relay API`, every route), new `tests/test_relay_schedules.py`, `tests/test_readme_api.py`.

## Acceptance conditions

- ac1: GET /relay/v1/schedules lists every schedule with its owner_slug [evidence: test:tests/test_relay_schedules.py::test_list_all]
- ac2: POST /relay/v1/schedules validates like the UI create (cron, timezone, the preset through _check_preset), records the owner from X-Orch-Session and X-Orch-Slug and answers 201 [evidence: test:tests/test_relay_schedules.py::test_create_owned]
- ac3: PUT, DELETE, run and runs act only on schedules the caller owns, and a schedule owned by another session, made in the UI or missing answers 404 not_found [evidence: test:tests/test_relay_schedules.py::test_owned_only]
- ac4: a caller owning SCHED_RELAY_MAX_PER_OWNER schedules gets 409 owned_limit on create [evidence: test:tests/test_relay_schedules.py::test_max_per_owner]
- ac5: a cron whose next three fires are less than SCHED_RELAY_MIN_INTERVAL_MINUTES apart is refused 422 too_frequent on create and update [evidence: test:tests/test_relay_schedules.py::test_too_frequent]
- ac6: the committed openapi-relay.json matches the relay app [evidence: test:tests/test_readme_api.py::test_openapi_relay_matches_app]
- ac7: the README documents every relay route [evidence: test:tests/test_readme_api.py::test_every_relay_route_documented]
- ac8: the UI routes are unchanged [evidence: command:uv run pytest tests/test_api_schedules.py tests/test_api_runs.py]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_relay_schedules.py tests/test_readme_api.py tests/test_api_schedules.py tests/test_api_runs.py && mise run lint]

## Files

- `src/agents_schedule/api/relay.py`
- `src/agents_schedule/api/schedules.py`
- `src/agents_schedule/api/runs.py`
- `src/agents_schedule/api/openapi.py`
- `openapi-relay.json`
- `README.md`
- `tests/test_relay_schedules.py`
- `tests/test_readme_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
