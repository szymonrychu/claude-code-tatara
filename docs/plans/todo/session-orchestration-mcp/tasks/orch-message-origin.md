---
title: orch message origin
status: todo
repo: agents-orchestrator
value: "every message records whether the user, a service or a session sent it, and the epic's schema exists"
files: [src/agents_orchestrator/db/migrations/NNNN_session_orchestration.sql, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/api/messages.py, src/agents_orchestrator/api/service_auth.py, README.md, tests/test_migrations.py, tests/test_message_origin.py, tests/test_service_port.py]
verify: "uv run --frozen pytest tests/test_migrations.py tests/test_message_origin.py tests/test_service_port.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch message origin

## Requirement

README Goal G2, verbatim: "\"On user request\" is checked by the server: a write is allowed only in a turn delivered by a message from the user (agents-web) or the Matrix connector by default; turns started by session messages, webhooks, schedules or no message are refused `not_user_turn`."

README Goal G4, verbatim: "Every write call, refusals included, is recorded in an orchestrator audit table readable on the main API and by the caller through a tool; writes and owned objects are rate- and count-limited."

Design D3, verbatim: "New column `messages.origin text`, written at insert: `user` on the main port; `service:<name>` on the service port (ServiceGate puts the service name in `scope[\"state\"]`); `session` in `enqueue_message` when a sender is present. Rows from before the migration stay NULL and never pass the gate (my call)."

Design D4, verbatim: "Writes only on objects owned by the caller session: `sessions.created_by_session_id` and `created_by_slug`; `presets.created_by_session_id` and `created_by_slug`; schedules `owner_session_id` and `owner_slug` (D7)."

Design D8, verbatim: "New table `orchestration_actions`; the orchestrator api is the only writer; no FK, so rows outlive purged sessions. Columns: `id bigserial`, `caller_session_id`, `caller_slug`, `message_id` (the turn's triggering message), `action`, `target_kind`, `target_id`, `target_name`, `outcome` (`ok` or the refusal code), `created_at`."

Design D13, verbatim: "`NNNN_session_orchestration.sql` (next free number at build time) adds `messages.origin`, the two `created_by_*` pairs and `orchestration_actions` in the first task, so later tasks consume no migration numbers and cannot collide with another epic's. [...] Idempotent like 0003-0007, no down step."

Architect fix-as-ac, verbatim: "`messages.origin` recorded on every insert path: main port, service port with the service name, session." and "Service name passed from ServiceGate to the app."

Scope (agents-orchestrator): the migration `src/agents_orchestrator/db/migrations/NNNN_session_orchestration.sql`, where NNNN is the next free number in that directory at build time (after slash-commands' 0008 and any hive-decoupling migration; never guessed); `db/queue.py` (`enqueue_message` takes and stores `origin`; new `turn_origin`); `api/messages.py` (main-port post stores `user`, service-port post stores `service:<name>`); `api/service_auth.py` (`ServiceGate` sets `scope["state"]["service"]`); README (messages origin values). The created_by and audit columns are only created here; later tasks write them.

## Acceptance conditions

- ac1: the migration NNNN_session_orchestration.sql (next free number at build time) adds messages.origin text, sessions.created_by_session_id uuid and created_by_slug text, presets.created_by_session_id uuid and created_by_slug text, and table orchestration_actions with the D8 columns and no foreign key, and a rerun is a no-op [evidence: test:tests/test_migrations.py::test_session_orchestration_schema]
- ac2: an orchestration_actions row stays after its caller session is purged [evidence: test:tests/test_migrations.py::test_orchestration_actions_outlive_sessions]
- ac3: a message posted on the main port is stored with origin user [evidence: test:tests/test_message_origin.py::test_main_port_origin_user]
- ac4: a message posted on the service port is stored with origin service:<name>, the name of the authenticated service token, which ServiceGate puts in scope["state"] [evidence: test:tests/test_message_origin.py::test_service_port_origin_names_service]
- ac5: a session message enqueued with a sender is stored with origin session [evidence: test:tests/test_message_origin.py::test_session_message_origin]
- ac6: turn_origin returns the origin and id of the message the agent's current turn delivered, and None when the current turn delivered no message [evidence: test:tests/test_message_origin.py::test_turn_origin]
- ac7: the service port's routes, 401 and 403 answers and log lines are unchanged [evidence: command:uv run --frozen pytest tests/test_service_port.py]
- ac8: the README documents the origin values user, session and service:<name> [evidence: command:grep -q 'service:<name>' README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_migrations.py tests/test_message_origin.py tests/test_service_port.py && mise run lint]

## Files

- `src/agents_orchestrator/db/migrations/NNNN_session_orchestration.sql`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/api/messages.py`
- `src/agents_orchestrator/api/service_auth.py`
- `README.md`
- `tests/test_migrations.py`
- `tests/test_message_origin.py`
- `tests/test_service_port.py`

## Interfaces

- Migration `NNNN_session_orchestration.sql`: `ALTER TABLE messages ADD COLUMN IF NOT EXISTS origin text`; `ALTER TABLE sessions ADD COLUMN IF NOT EXISTS created_by_session_id uuid`, `created_by_slug text`; same pair on `presets`; `CREATE TABLE IF NOT EXISTS orchestration_actions (id bigserial PRIMARY KEY, caller_session_id uuid NOT NULL, caller_slug text NOT NULL, message_id bigint, action text NOT NULL, target_kind text NOT NULL, target_id text, target_name text, outcome text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())` plus an index on `(caller_session_id, created_at)`. No FK anywhere.
- `db/queue.py:enqueue_message(conn, session_id, text, target_agent_id=None, *, sender_session_id=None, sender_slug=None, hop=0, origin: str)`; origin `session` when a sender is present.
- `db/queue.py:turn_origin(conn, agent_id) -> TurnOrigin | None` with `TurnOrigin(message_id: int, origin: str | None)`, same join as `turn_hop` without the sender filter.
- `ServiceGate`: `scope.setdefault("state", {})["service"] = <name>` before calling the app; `api/messages.py:post_message` reads `request.state.service` (absent on the main port).

## Expected outcome

Every message row records where it came from, and the schema of the whole epic exists.

## Steps

- Read `ls src/agents_orchestrator/db/migrations/` and pick the next free number; stop and report if another epic's migration with that number is in flight on another branch.
- Red: add the migration and origin tests; run `uv run --frozen pytest tests/test_message_origin.py tests/test_migrations.py`: the new tests fail (DB tests run in CI; see Notes).
- Green: migration, queue, messages, ServiceGate, README; run the task's verify. Quote the summary line.

## Notes

- No Docker in agent pods: the DB tests (ac1-ac6) run in CI; keep the ServiceGate state assertion (ac4's scope part) non-DB with a stub app so the local verify has signal.
- Confirm the connector's service token name from `ORCH_SERVICE_TOKENS` handling and the helmfile file `service-token-agents-matrix-connector.secrets.yaml` (design Assumptions); the default origins setting lands in orch-orchestration-gate.
- Do not touch `tests/test_service_port.py` assertions unless one is no longer accurate; name it if so.
