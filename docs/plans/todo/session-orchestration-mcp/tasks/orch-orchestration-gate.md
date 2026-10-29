---
title: orch orchestration gate
status: todo
repo: agents-orchestrator
value: "only a flagged leader acting on the user's request can write, every write is audited and limited"
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/api/orchestration.py, src/agents_orchestrator/db/orchestration.py, src/agents_orchestrator/api/app.py, README.md, openapi.json, tests/test_orchestration_gate.py, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_orchestration_gate.py tests/test_settings.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-orchestration-flag]
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

# orch orchestration gate

## Requirement

README Goal G2, verbatim: "\"On user request\" is checked by the server: a write is allowed only in a turn delivered by a message from the user (agents-web) or the Matrix connector by default; turns started by session messages, webhooks, schedules or no message are refused `not_user_turn`."

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

README Goal G4, verbatim: "Every write call, refusals included, is recorded in an orchestrator audit table readable on the main API and by the caller through a tool; writes and owned objects are rate- and count-limited."

Design D2, verbatim: "Every `/agent/v1/orchestration/*` route: 1. `require_agent`; 2. the flag on the caller's session, else 403 `not_orchestrator`; 3. `_leads`, else 403 `not_leader`; 4. for writes only, the user-turn gate (D3). [...] One FastAPI dependency carries the chain (my call)."

Design D3, verbatim: "A write is allowed only while every message that delivered the caller's current turn (`agent_status.current_turn_id`, same join as `db/queue.py:turn_hop`) has an origin in `ORCH_ORCHESTRATION_ORIGINS`, default `user,service:agents-matrix-connector`; else 403 `not_user_turn`. Rejected by default: session messages, `service:agents-webhook`, `service:agents-schedule`, and turns with no message (background completions, peer sends). [...] Reads skip the gate."

Design D5, verbatim: "`session_orchestration: true` is always refused; `kube_access` or `session_messaging` true only if the caller's own session has that same flag. Refusal: 403 `privilege_escalation`."

Design D8, verbatim: "One row per write call that passed `require_agent`, refusals included, plus one log line in the `ServiceGate` style (never a token or a body). Read through `GET /api/v1/orchestration/actions` (main port) and the agent tool `orchestration_actions` (the caller's own rows)."

Design D9, verbatim: "Counts from `orchestration_actions`, advisory like cross-session-messaging D10. `ORCH_ORCHESTRATION_ACTIONS_PER_HOUR` (30): ok writes per caller, else 429 `rate_limited`. `ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS` (5): live owned sessions, else 409 `owned_limit`; the global `max_sessions` still applies."

Design D14, verbatim: "Every orchestration write route and the schedule relay cap the request body at 256 KiB (413 `payload_too_large`, before parsing, no upstream call)."

Architect fix-as-ac, verbatim: "Writes refused in non-user turns (`not_user_turn`), tested for each origin." and "An audit row for every write, refusals included."

Scope (agents-orchestrator): `settings.py` (`orchestration_origins`, `orchestration_actions_per_hour`, `orchestration_max_owned_sessions`); new `api/orchestration.py` (the dependency chain, the no-escalation check, the audit and log helper, the body cap, `GET /agent/v1/orchestration/actions` and the main-port `GET /api/v1/orchestration/actions`); new `db/orchestration.py` (insert action, list actions, count ok writes in the last hour); `api/app.py` (routers); README (`### Orchestration` under `## Agent API`, Configuration rows); `openapi.json`. The resource routes are later tasks; the owned-session count helper is used by orch-orchestration-sessions.

User settlement B2 (2026-10-27), verbatim: "schedule_run counts as an ok write against ORCH_ORCHESTRATION_ACTIONS_PER_HOUR. The global max_sessions is the only bound on fired sessions." So `count_ok_writes` counts every `ok` row whatever its action, `schedule_run` included, and no per-run or per-owner cap on fired sessions is added anywhere.

User settlement B4 (2026-10-27), verbatim: "Command-kind messages and orchestrator-internal enqueues (no sender, no port) store NULL and never pass the user-turn gate." The gate reads `db/queue.py:turn_origin` (orch-message-origin), which returns the origins of every message linked to the current turn; one origin outside the setting refuses the write. A NULL origin is refused `not_user_turn` whatever `ORCH_ORCHESTRATION_ORIGINS` holds; the setting accepts only `user`, `session` and `service:<name>`, never an empty or NULL entry.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". This task adds the one shared predicate `api/orchestration.py:require_own_preset(preset, caller_session_id)` that orch-orchestration-sessions (create from preset_id) and orch-schedule-relay (the preset of a schedule) both call; it raises 403 `not_owner`.

## Acceptance conditions

- ac1: ORCH_ORCHESTRATION_ORIGINS defaults to user,service:agents-matrix-connector and accepts only user, session or service:<name> entries (never NULL), else a settings error naming it; ORCH_ORCHESTRATION_ACTIONS_PER_HOUR defaults to 30 and ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS to 5, both at least 1 [evidence: test:tests/test_settings.py::test_orchestration_settings]
- ac2: the README Configuration section names every ORCH_ variable, the three new ones included [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- ac3: an orchestration route checks in order require_agent (401 or 403), the caller's session_orchestration (403 not_orchestrator), the leader (403 not_leader) and, for writes only, the user turn (403 not_user_turn) [evidence: test:tests/test_orchestration_gate.py::test_check_order]
- ac4: a write passes in turns delivered by origin user and service:agents-matrix-connector and is refused not_user_turn for origin session, service:agents-webhook, service:agents-schedule, a NULL origin (command-kind messages) and a turn that delivered no message, and in a turn delivered by several messages it passes only when every one has an allowed origin (a user message plus a session message in one turn is refused), while a read passes in every one of these turns [evidence: test:tests/test_orchestration_gate.py::test_user_turn_gate_per_origin]
- ac5: every write call past require_agent writes one orchestration_actions row with caller, message_id, action, target kind, id and name and outcome ok or the refusal code, refusals included, and one log line without token or body [evidence: test:tests/test_orchestration_gate.py::test_audit_row_per_write]
- ac6: a caller with ORCH_ORCHESTRATION_ACTIONS_PER_HOUR ok writes in the last hour, of any action, gets 429 rate_limited, audited [evidence: test:tests/test_orchestration_gate.py::test_rate_limited]
- ac7: the hourly count includes ok rows whose action is schedule_run and excludes refused rows, so a caller whose last ORCH_ORCHESTRATION_ACTIONS_PER_HOUR ok writes were all schedule_run is refused rate_limited and a caller with that many refusals is not [evidence: test:tests/test_orchestration_gate.py::test_rate_limit_counts_schedule_run_not_refusals]
- ac8: GET /agent/v1/orchestration/actions returns only the caller's rows newest first, GET /api/v1/orchestration/actions on the main port returns every row, and the agent route is served only on the agent port [evidence: test:tests/test_orchestration_gate.py::test_actions_views]
- ac9: an agent-supplied spec with session_orchestration true is refused privilege_escalation always, and kube_access or session_messaging true unless the caller's own session has that flag [evidence: test:tests/test_orchestration_gate.py::test_no_escalation]
- ac10: require_own_preset passes a preset whose created_by_session_id equals the caller session id and raises 403 not_owner for a preset the user made (created_by_session_id NULL) and for a preset another session created, naming no secret in the answer [evidence: test:tests/test_orchestration_gate.py::test_require_own_preset]
- ac11: a write body over 256 KiB answers 413 payload_too_large before parsing and changes nothing [evidence: test:tests/test_orchestration_gate.py::test_body_cap]
- ac12: the README documents the orchestration checks in order, the origins, the refusal codes, the limits and both actions routes, and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac13: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_gate.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/orchestration.py`
- `src/agents_orchestrator/db/orchestration.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_gate.py`
- `tests/test_settings.py`

## Interfaces

- `settings.py:Settings.orchestration_origins: CsvList = ["user", "service:agents-matrix-connector"]`, `orchestration_actions_per_hour: int = Field(30, ge=1)`, `orchestration_max_owned_sessions: int = Field(5, ge=1)`.
- `api/orchestration.py`: `router = APIRouter(prefix="/agent/v1/orchestration", tags=["agent"])`; `public_router` for `GET /api/v1/orchestration/actions`; dependencies `orchestration_reader` and `orchestration_writer(action, target_kind)` returning an `OrchestrationCaller(agent, session, message_id)`; `check_no_escalation(spec: SessionSpec, caller: SessionSpec) -> None` raising 403 `privilege_escalation`; `record(conn, caller, action, target_kind, target_id, target_name, outcome)`.
- `db/orchestration.py`: `insert_action(...)`, `list_actions(conn, caller_session_id | None, limit)`, `count_ok_writes(conn, caller_session_id, seconds)`, `count_live_owned_sessions(conn, owner_session_id)` (one predicate; used by orch-orchestration-sessions).
- Error codes added: 403 `not_orchestrator`, `not_leader`, `not_user_turn`, `privilege_escalation`; 429 `rate_limited`; 413 `payload_too_large`.

## Expected outcome

One dependency proves who may orchestrate, in which turn, records every write and enforces the limits; the resource routes plug into it.

## Steps

- Red: write `tests/test_orchestration_gate.py` with a test-only write and read route mounted on the agent app (non-DB cases with `require_agent` overridden for ac3, ac8, ac9; DB cases like `tests/test_agent_session_messaging.py` for ac4-ac7), add `test_orchestration_settings`; run `uv run --frozen pytest tests/test_orchestration_gate.py tests/test_settings.py`: the new tests fail.
- Green: settings, modules, app wiring, README, `openapi.json`; run the task's verify. Quote the summary line.

## Notes

- Import `require_agent`, `_leads` from `api/agent.py`; do not copy them. The current-turn lookup is `db/queue.py:turn_origin` (orch-message-origin).
- The refusal order is part of the contract: a non-leader of a flagged session gets not_leader, never not_user_turn.
- 401 answers write no audit row (no proven caller); every later refusal does.
- No Docker in agent pods: DB cases run in CI; keep the order and escalation cases non-DB.
- Build fake tokens at runtime in tests (GitGuardian).

- 2026-10-27 amended: builder check B2 and B4 settlements: schedule_run counts as an ok write, NULL origin never passes the gate

- 2026-10-27 amended: Q9: one shared require_own_preset predicate

- 2026-10-29 amended: staleness refresh: the gate requires every message of the turn to have an allowed origin
