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

User settlement B2 (2026-10-27), verbatim: "schedule_run counts as an ok write against ORCH_ORCHESTRATION_ACTIONS_PER_HOUR. The global max_sessions is the only bound on fired sessions." The relay run-now adds no cap of its own on how often an owned schedule may be run; the orchestrator counts it against the hourly write limit.

User settlement B3 (2026-10-27), verbatim: "agent-created schedules may be created enabled. Orphans after the owner's deletion are managed from the UI." Relay create stores `enabled` as the body says (true is accepted and the schedule fires at once as the cron says); the listener never forces a schedule disabled.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". Only the orchestrator knows who created a preset, so it enforces the rule (orch-schedule-relay, `require_own_preset`) before it calls the listener; this task makes the contract say so: the README `## Relay API` section and the `openapi-relay.json` create and update descriptions state that `preset_id` must name a preset the calling session created and that the orchestrator enforces it, and the listener keeps `_check_preset` for existence only.

## Acceptance conditions

- ac1: GET /relay/v1/schedules lists every schedule with its owner_slug [evidence: test:tests/test_relay_schedules.py::test_list_all]
- ac2: POST /relay/v1/schedules validates like the UI create (cron, timezone, the preset through _check_preset), records the owner from X-Orch-Session and X-Orch-Slug and answers 201 [evidence: test:tests/test_relay_schedules.py::test_create_owned]
- ac3: PUT, DELETE, run and runs act only on schedules the caller owns, and a schedule owned by another session, made in the UI or missing answers 404 not_found [evidence: test:tests/test_relay_schedules.py::test_owned_only]
- ac4: POST /relay/v1/schedules/{id}/run on an owned schedule enqueues a run exactly like the UI run-now (runs_new notified) and adds no cap of its own, so repeated calls each succeed, and a create with enabled true stores the schedule enabled [evidence: test:tests/test_relay_schedules.py::test_run_now_uncapped_and_create_enabled]
- ac5: a caller owning SCHED_RELAY_MAX_PER_OWNER schedules gets 409 owned_limit on create [evidence: test:tests/test_relay_schedules.py::test_max_per_owner]
- ac6: a cron whose next three fires are less than SCHED_RELAY_MIN_INTERVAL_MINUTES apart is refused 422 too_frequent on create and update [evidence: test:tests/test_relay_schedules.py::test_too_frequent]
- ac7: the committed openapi-relay.json matches the relay app [evidence: test:tests/test_readme_api.py::test_openapi_relay_matches_app]
- ac8: the README documents every relay route [evidence: test:tests/test_readme_api.py::test_every_relay_route_documented]
- ac9: the README Relay API section and the openapi-relay.json create and update descriptions state that preset_id must name a preset the calling session created, enforced by the orchestrator before the call, while the listener checks only that the preset exists [evidence: test:tests/test_readme_api.py::test_relay_documents_preset_rule]
- ac10: the UI routes are unchanged [evidence: command:uv run pytest tests/test_api_schedules.py tests/test_api_runs.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_relay_schedules.py tests/test_readme_api.py tests/test_api_schedules.py tests/test_api_runs.py && mise run lint]

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

- Relay bodies: create and update take `ScheduleIn`; views are `ScheduleView` (with `owner_slug`) and `RunView`; errors `{error: {code, message}}` like the UI API.
- `api/openapi.py`: writes `openapi.json` (UI) and `openapi-relay.json` (relay).

## Expected outcome

The orchestrator can list all schedules and manage its callers' own through one documented contract.

## Steps

- Red: write `tests/test_relay_schedules.py` and the two readme tests; run them: fail.
- Green: routes on the relay app reusing the UI handler bodies, the openapi generator, `openapi-relay.json`, README; run the task's verify. Quote the summary line.

## Notes

- Reuse `_validate_cron`, `_check_preset` and the run-now path; do not copy them. The run-now path must NOTIFY `runs_new` like the UI route (MEMORY 2026-10-25).
- The fire-interval check uses the repo's cron module over the schedule's timezone.
- DB cases run in CI (no Docker in agent pods).

- 2026-10-27 amended: builder check B2, B3 and Q9: run-now uncapped, create enabled, preset-ownership rule in the contract
