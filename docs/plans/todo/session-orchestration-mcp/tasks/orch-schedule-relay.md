---
title: orch schedule relay
status: todo
repo: agents-orchestrator
value: "a flagged leader manages its schedules through the orchestrator, which keeps the agent token to itself"
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/api/orchestration_relay.py, src/agents_orchestrator/api/chat.py, src/agents_orchestrator/api/app.py, README.md, openapi.json, tests/test_orchestration_relay.py, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_orchestration_relay.py tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint"
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

Design D7 (staleness refresh 2026-10-29), verbatim: "agents-schedule answers DELETE with an empty 204 and run-now with 202: the relay passes an empty 204 through unchanged; any other non-JSON answer is 503 `schedules_unavailable`. The relay reuses the forward and body-cap code of `api/chat.py` (`forward`, `_capped_body`, `new_client`, `close_client`), generalised to take the upstream URL, token and unavailable code, instead of a second copy; the schedule client is closed in the app lifespan like the chat client."

Design D5, verbatim: "Applies to an agent-written preset spec, an agent-created session spec (from a spec or a preset) and the preset named by an agent-written schedule (the relay reads it first)."

Design D12, verbatim: "The relay module mirrors `api/chat.py`; `settings.py` gains `ORCH_SCHEDULE_*` next to `ORCH_CHAT_*`."

Design D14, verbatim: "Every orchestration write route and the schedule relay cap the request body at 256 KiB (413 `payload_too_large`, before parsing, no upstream call)."

Architect fix-as-ac, verbatim: "The agent token never forwarded to agents-schedule (header assertion)."

Architect do-not-build, verbatim: "Agents calling agents-schedule directly." and "Orchestrator-side schedule storage."

Route table (agent port, prefix `/agent/v1/orchestration`): `GET /schedules` to `GET /relay/v1/schedules` (read); `POST /schedules` to `POST /relay/v1/schedules`; `PUT /schedules/{id}` to `PUT /relay/v1/schedules/{id}`; `DELETE /schedules/{id}` to `DELETE /relay/v1/schedules/{id}`; `POST /schedules/{id}/run` to `POST /relay/v1/schedules/{id}/run`; `GET /schedules/{id}/runs` to `GET /relay/v1/schedules/{id}/runs` (read).

Scope (agents-orchestrator): `settings.py` (`schedule_url`, `schedule_token`), new `api/orchestration_relay.py`, `api/chat.py` (its forward helper generalised and shared; the chat routes, codes and answers unchanged), `api/app.py` (router, client close in the lifespan), README (Configuration rows; the schedule routes in `### Orchestration`), `openapi.json`. Nothing is stored except the audit rows.

User settlement B2 (2026-10-27), verbatim: "schedule_run counts as an ok write against ORCH_ORCHESTRATION_ACTIONS_PER_HOUR. The global max_sessions is the only bound on fired sessions." `POST /schedules/{id}/run` is a write: it goes through the write gate, is audited with action `schedule_run` and an `ok` row when the upstream accepts it, and that row counts toward the hourly limit. The relay adds no cap of its own on runs.

User settlement B3 (2026-10-27), verbatim: "agent-created schedules may be created enabled. Orphans after the owner's deletion are managed from the UI." The relay forwards `enabled` untouched and never forces a schedule disabled.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". Create and update of a schedule read the named preset and call `api/orchestration.py:require_own_preset` (orch-orchestration-gate) besides `check_no_escalation`; the preset check is the only place that knows who created a preset, agents-schedule cannot tell, so this is the single enforcement point for schedules.

## Acceptance conditions

- ac1: ORCH_SCHEDULE_URL (http or https) and ORCH_SCHEDULE_TOKEN default empty, one set without the other is a settings error naming both, and the token never appears in repr [evidence: test:tests/test_settings.py::test_schedule_relay_settings]
- ac2: the README Configuration section names every ORCH_ variable, the two new ones included [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- ac3: each schedule route forwards its method, path, query and body (unchanged, enabled included) to ORCH_SCHEDULE_URL/relay/v1 with the relay bearer and the caller's X-Orch-Session and X-Orch-Slug, and the forwarded request carries neither the agent token nor any other inbound header [evidence: test:tests/test_orchestration_relay.py::test_forwards_with_relay_token_never_agent_token]
- ac4: the upstream status and body (200, 201, 202 for run-now, an empty 204 for delete, 404 not_found, 409 owned_limit, 422 too_frequent) reach the agent unchanged [evidence: test:tests/test_orchestration_relay.py::test_upstream_pass_through]
- ac5: a connection error, a timeout and a non-JSON upstream answer other than an empty 204 give 503 schedules_unavailable without echoing upstream text [evidence: test:tests/test_orchestration_relay.py::test_upstream_failure_is_unavailable]
- ac6: with the relay unconfigured every schedule route answers 503 schedules_unconfigured and makes no upstream call [evidence: test:tests/test_orchestration_relay.py::test_unconfigured]
- ac7: create and update read the named preset first and refuse privilege_escalation without an upstream call when it carries session_orchestration or a flag the caller lacks [evidence: test:tests/test_orchestration_relay.py::test_schedule_preset_no_escalation]
- ac8: create and update refuse 403 not_owner, audited and without an upstream call, when the named preset was made in the UI or by another session, and pass for a preset the caller created [evidence: test:tests/test_orchestration_relay.py::test_schedule_preset_must_be_own]
- ac9: schedule writes pass the orchestration checks and the user-turn gate, reads pass the checks without the gate, and every write writes an audit row with target_kind schedule and the upstream outcome [evidence: test:tests/test_orchestration_relay.py::test_relay_checks_and_audit]
- ac10: POST /schedules/{id}/run passes the write gate, writes an audit row with action schedule_run and outcome ok on an upstream 2xx or the upstream refusal code otherwise, the ok row counts toward ORCH_ORCHESTRATION_ACTIONS_PER_HOUR, and a create with enabled true is forwarded with enabled true [evidence: test:tests/test_orchestration_relay.py::test_schedule_run_counted_and_enabled_create_forwarded]
- ac11: a body over 256 KiB answers 413 payload_too_large with no upstream call, and a schedule with a 16384-character prompt of 4-byte characters escaped as surrogate pairs passes [evidence: test:tests/test_orchestration_relay.py::test_body_cap]
- ac12: the chat relay keeps its routes, codes (chat_unconfigured, chat_unavailable, payload_too_large) and answers after its forward helper is shared [evidence: command:uv run --frozen pytest tests/test_agent_chat.py tests/test_chat_contract.py]
- ac13: the README documents every schedule relay route and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac14: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_relay.py tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/orchestration_relay.py`
- `src/agents_orchestrator/api/chat.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_relay.py`
- `tests/test_settings.py`

## Interfaces

- `settings.py:Settings.schedule_url: str = ""`, `schedule_token: str = Field(default="", repr=False)`; validator for both-or-neither and the scheme, next to the chat pair.
- `api/orchestration_relay.py`: `router = APIRouter(prefix="/agent/v1/orchestration/schedules", tags=["agent"])`; its own `httpx.AsyncClient` on `app.state` (timeout 10 s), closed in the `api/app.py` lifespan next to `chat.close_client`.
- `api/chat.py`: today `forward(request, method, path, body, session, slug)` reads `settings.chat_url`, `chat_token`, `UPSTREAM_PREFIX` and raises `chat_unavailable`, and `_capped_body(request)` caps at `MAX_BODY_BYTES` (256 KiB); generalise them to take the upstream base URL, prefix, token, client, unavailable code and whether an empty 204 passes (yes for schedules, no for chat), so both relays call one helper; the chat routes keep their answers.
- Agent-facing errors added: 503 `schedules_unconfigured`, 503 `schedules_unavailable`; everything else is the upstream's or the gate's.

## Expected outcome

A flagged leader can manage its schedules through the orchestrator, which proves who calls and keeps the agent token to itself.

## Steps

- Red: write `tests/test_orchestration_relay.py` (an `httpx.MockTransport` upstream; non-DB cases for ac3-ac6 and ac9; DB cases for ac7 and ac8), add `test_schedule_relay_settings`; run them: fail.
- Green: settings, module, the shared helper in `api/chat.py`, app wiring and lifespan close, README, `openapi.json`; run the task's verify. Quote the summary line.

## Notes

- Matrix did not extract a shared helper: `forward`, `_capped_body`, `new_client`, `client`, `close_client` live in `api/chat.py` (Matrix orch-chat-relay). Share them (boy scout, `api/chat.py` is in Files) rather than copying; `tests/test_agent_chat.py` and `tests/test_chat_contract.py` stay green unchanged.
- The relay reads the preset by id through `db/presets.py` before forwarding create and update (D5) and applies `check_no_escalation`.
- Never log the relay token, the agent token or a body; log method, path, status only.
- `X-Orch-Slug` is the caller session's slug from the sessions repo, never from the request.
- Build fake tokens at runtime in tests (GitGuardian). DB cases run in CI.

- 2026-10-27 amended: builder check B2, B3 and Q9: schedule_run counted, enabled forwarded, own presets only

- 2026-10-29 amended: staleness refresh: reuse the chat.py forward helper, empty 204 and 202 pass through, chat relay unchanged
