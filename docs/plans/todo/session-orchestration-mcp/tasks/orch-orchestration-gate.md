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

Design D3, verbatim: "A write is allowed only while the caller's current turn (`agent_status.current_turn_id`, same join as `db/queue.py:turn_hop`) was delivered by a message whose origin is in `ORCH_ORCHESTRATION_ORIGINS`, default `user,service:agents-matrix-connector`; else 403 `not_user_turn`. Rejected by default: session messages, `service:agents-webhook`, `service:agents-schedule`, and turns with no message (background completions, peer sends). [...] Reads skip the gate."

Design D5, verbatim: "`session_orchestration: true` is always refused; `kube_access` or `session_messaging` true only if the caller's own session has that same flag. Refusal: 403 `privilege_escalation`."

Design D8, verbatim: "One row per write call that passed `require_agent`, refusals included, plus one log line in the `ServiceGate` style (never a token or a body). Read through `GET /api/v1/orchestration/actions` (main port) and the agent tool `orchestration_actions` (the caller's own rows)."

Design D9, verbatim: "Counts from `orchestration_actions`, advisory like cross-session-messaging D10. `ORCH_ORCHESTRATION_ACTIONS_PER_HOUR` (30): ok writes per caller, else 429 `rate_limited`. `ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS` (5): live owned sessions, else 409 `owned_limit`; the global `max_sessions` still applies."

Design D14, verbatim: "Every orchestration write route and the schedule relay cap the request body at 256 KiB (413 `payload_too_large`, before parsing, no upstream call)."

Architect fix-as-ac, verbatim: "Writes refused in non-user turns (`not_user_turn`), tested for each origin." and "An audit row for every write, refusals included."

Scope (agents-orchestrator): `settings.py` (`orchestration_origins`, `orchestration_actions_per_hour`, `orchestration_max_owned_sessions`); new `api/orchestration.py` (the dependency chain, the no-escalation check, the audit and log helper, the body cap, `GET /agent/v1/orchestration/actions` and the main-port `GET /api/v1/orchestration/actions`); new `db/orchestration.py` (insert action, list actions, count ok writes in the last hour); `api/app.py` (routers); README (`### Orchestration` under `## Agent API`, Configuration rows); `openapi.json`. The resource routes are later tasks; the owned-session count helper is used by orch-orchestration-sessions.

## Acceptance conditions

- ac1: ORCH_ORCHESTRATION_ORIGINS defaults to user,service:agents-matrix-connector and accepts only user, session or service:<name> entries, else a settings error naming it; ORCH_ORCHESTRATION_ACTIONS_PER_HOUR defaults to 30 and ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS to 5, both at least 1 [evidence: test:tests/test_settings.py::test_orchestration_settings]
- ac2: the README Configuration section names every ORCH_ variable, the three new ones included [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- ac3: an orchestration route checks in order require_agent (401 or 403), the caller's session_orchestration (403 not_orchestrator), the leader (403 not_leader) and, for writes only, the user turn (403 not_user_turn) [evidence: test:tests/test_orchestration_gate.py::test_check_order]
- ac4: a write passes in turns delivered by origin user and service:agents-matrix-connector and is refused not_user_turn for origin session, service:agents-webhook, service:agents-schedule, a NULL origin and a turn that delivered no message, while a read passes in every one of these turns [evidence: test:tests/test_orchestration_gate.py::test_user_turn_gate_per_origin]
- ac5: every write call past require_agent writes one orchestration_actions row with caller, message_id, action, target kind, id and name and outcome ok or the refusal code, refusals included, and one log line without token or body [evidence: test:tests/test_orchestration_gate.py::test_audit_row_per_write]
- ac6: a caller with ORCH_ORCHESTRATION_ACTIONS_PER_HOUR ok writes in the last hour gets 429 rate_limited, audited [evidence: test:tests/test_orchestration_gate.py::test_rate_limited]
- ac7: GET /agent/v1/orchestration/actions returns only the caller's rows newest first, GET /api/v1/orchestration/actions on the main port returns every row, and the agent route is served only on the agent port [evidence: test:tests/test_orchestration_gate.py::test_actions_views]
- ac8: an agent-supplied spec with session_orchestration true is refused privilege_escalation always, and kube_access or session_messaging true unless the caller's own session has that flag [evidence: test:tests/test_orchestration_gate.py::test_no_escalation]
- ac9: a write body over 256 KiB answers 413 payload_too_large before parsing and changes nothing [evidence: test:tests/test_orchestration_gate.py::test_body_cap]
- ac10: the README documents the orchestration checks in order, the origins, the refusal codes, the limits and both actions routes, and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_gate.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
