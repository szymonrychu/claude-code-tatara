---
title: orch schedule relay
status: todo
repo: agents-orchestrator
value: "a flagged leader manages its schedules through the orchestrator, which keeps the agent token to itself"
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/api/orchestration_relay.py, src/agents_orchestrator/api/app.py, README.md, openapi.json, tests/test_orchestration_relay.py, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_orchestration_relay.py tests/test_settings.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-creator-messaging]
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

# orch schedule relay

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "Orchestrator `api/orchestration_relay.py` forwards `/agent/v1/orchestration/schedules*` to `{ORCH_SCHEDULE_URL}/relay/v1/schedules*` with `Authorization: Bearer <ORCH_SCHEDULE_TOKEN>`, `X-Orch-Session` and `X-Orch-Slug`, never the agent token. Settings both set or both empty; both empty gives 503 `schedules_unconfigured`; a connection error, timeout or non-JSON answer gives 503 `schedules_unavailable` (my call, mirrors Matrix D2 `chat_unavailable`)."

Design D5, verbatim: "Applies to an agent-written preset spec, an agent-created session spec (from a spec or a preset) and the preset named by an agent-written schedule (the relay reads it first)."

Design D12, verbatim: "The relay module mirrors `api/chat.py`; `settings.py` gains `ORCH_SCHEDULE_*` next to `ORCH_CHAT_*`."

Design D14, verbatim: "Every orchestration write route and the schedule relay cap the request body at 256 KiB (413 `payload_too_large`, before parsing, no upstream call)."

Architect fix-as-ac, verbatim: "The agent token never forwarded to agents-schedule (header assertion)."

Architect do-not-build, verbatim: "Agents calling agents-schedule directly." and "Orchestrator-side schedule storage."

Route table (agent port, prefix `/agent/v1/orchestration`): `GET /schedules` to `GET /relay/v1/schedules` (read); `POST /schedules` to `POST /relay/v1/schedules`; `PUT /schedules/{id}` to `PUT /relay/v1/schedules/{id}`; `DELETE /schedules/{id}` to `DELETE /relay/v1/schedules/{id}`; `POST /schedules/{id}/run` to `POST /relay/v1/schedules/{id}/run`; `GET /schedules/{id}/runs` to `GET /relay/v1/schedules/{id}/runs` (read).

Scope (agents-orchestrator): `settings.py` (`schedule_url`, `schedule_token`), new `api/orchestration_relay.py`, `api/app.py`, README (Configuration rows; the schedule routes in `### Orchestration`), `openapi.json`. Nothing is stored except the audit rows.

## Acceptance conditions

- ac1: ORCH_SCHEDULE_URL (http or https) and ORCH_SCHEDULE_TOKEN default empty, one set without the other is a settings error naming both, and the token never appears in repr [evidence: test:tests/test_settings.py::test_schedule_relay_settings]
- ac2: the README Configuration section names every ORCH_ variable, the two new ones included [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- ac3: each schedule route forwards its method, path, query and body to ORCH_SCHEDULE_URL/relay/v1 with the relay bearer and the caller's X-Orch-Session and X-Orch-Slug, and the forwarded request carries neither the agent token nor any other inbound header [evidence: test:tests/test_orchestration_relay.py::test_forwards_with_relay_token_never_agent_token]
- ac4: the upstream status and JSON body (200, 201, 204, 404 not_found, 409 owned_limit, 422 too_frequent) reach the agent unchanged [evidence: test:tests/test_orchestration_relay.py::test_upstream_pass_through]
- ac5: a connection error, a timeout and a non-JSON upstream answer give 503 schedules_unavailable without echoing upstream text [evidence: test:tests/test_orchestration_relay.py::test_upstream_failure_is_unavailable]
- ac6: with the relay unconfigured every schedule route answers 503 schedules_unconfigured and makes no upstream call [evidence: test:tests/test_orchestration_relay.py::test_unconfigured]
- ac7: create and update read the named preset first and refuse privilege_escalation without an upstream call when it carries session_orchestration or a flag the caller lacks [evidence: test:tests/test_orchestration_relay.py::test_schedule_preset_no_escalation]
- ac8: schedule writes pass the orchestration checks and the user-turn gate, reads pass the checks without the gate, and every write writes an audit row with target_kind schedule and the upstream outcome [evidence: test:tests/test_orchestration_relay.py::test_relay_checks_and_audit]
- ac9: a body over 256 KiB answers 413 payload_too_large with no upstream call, and a schedule with a 16384-character prompt of 4-byte characters escaped as surrogate pairs passes [evidence: test:tests/test_orchestration_relay.py::test_body_cap]
- ac10: the README documents every schedule relay route and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_relay.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/orchestration_relay.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_relay.py`
- `tests/test_settings.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
