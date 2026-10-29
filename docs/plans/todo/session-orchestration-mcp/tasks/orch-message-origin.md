---
title: orch message origin
status: todo
repo: agents-orchestrator
value: "every message records whether the user, a service or a session sent it, and the epic's schema exists"
files: [src/agents_orchestrator/db/migrations/0013_session_orchestration.sql, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/api/messages.py, src/agents_orchestrator/api/agent.py, README.md, tests/test_migrations.py, tests/test_message_origin.py, tests/test_service_port.py]
verify: "uv run --frozen pytest tests/test_migrations.py tests/test_message_origin.py tests/test_service_port.py && mise run lint"
depends_on: [baseline-facts]
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

Design D3, verbatim: "New column `messages.origin text`, written at insert: `user` on the main port; `service:<name>` on the service port (the name `ServiceGate` already hands to the routes, `api/service_auth.py:calling_service`, landed with migration 0009); `session` in `enqueue_message` when a sender is present; NULL for command-kind messages (builder check B4, below). Rows from before the migration stay NULL and never pass the gate (my call)." and "Every message that delivered the turn counts, not only the newest (my call, staleness refresh 2026-10-29): immediate-message-delivery-w, which builds on this epic, lets several messages share one turn_id, and one disallowed message in the turn refuses the write."

Design D4, verbatim: "Writes only on objects owned by the caller session: `sessions.created_by_session_id` and `created_by_slug`; `presets.created_by_session_id` and `created_by_slug`; schedules `owner_session_id` and `owner_slug` (D7)."

Design D8, verbatim: "New table `orchestration_actions`; the orchestrator api is the only writer; no FK, so rows outlive purged sessions. Columns: `id bigserial`, `caller_session_id`, `caller_slug`, `message_id` (the turn's triggering message), `action`, `target_kind`, `target_id`, `target_name`, `outcome` (`ok` or the refusal code), `created_at`."

Design D13, verbatim: "`0013_session_orchestration.sql` (negotiated 2026-10-29, mx-34 #469/#470; slash-commands-from-chat ships 0010 and 0012, main ends at 0011) adds `messages.origin`, the two `created_by_*` pairs and `orchestration_actions` in the first task, so later tasks consume no migration numbers and cannot collide with another epic's. [...] Idempotent like 0003-0007, no down step."

Architect fix-as-ac, verbatim: "`messages.origin` recorded on every insert path: main port, service port with the service name, session." and "Service name passed from ServiceGate to the app." The second is already on main: `api/service_auth.py` sets `scope["state"]["service"]` (`STATE_KEY`) and `calling_service(request)` reads it (used by `api/sessions.py` for `created_by_service`); this task reuses it and does not edit `ServiceGate`.

Scope (agents-orchestrator): the migration `src/agents_orchestrator/db/migrations/0013_session_orchestration.sql` (the number baseline-facts confirmed); `db/queue.py` (`enqueue_message` takes and stores `origin`; new `turn_origin` over every message of the current turn); `api/messages.py` (`post_message` gains `request: Request` and stores `user` on the main port, `service:<name>` from `calling_service(request)` on the service port, NULL for a command-kind message); `api/agent.py` (`session_send` stores `session`, NULL for a superleader's command-kind message); README (messages origin values). The created_by and audit columns are only created here; later tasks write them.

User settlement B4 (2026-10-27), verbatim: "build on the merged slash-commands code. Store origin `session` or `user` the same way on every enqueue path. Command-kind messages and orchestrator-internal enqueues (no sender, no port) store NULL and never pass the user-turn gate."

Reading of B4 against main after slash-commands-from-chat: `enqueue_message` takes `origin: str | None` as a required keyword argument with no default, so no caller can forget it. Main has exactly two call sites, both in scope: `api/messages.py:post_message` (main and service port; `kind` is `command` for slash text) and `api/agent.py:session_send` (sender present; `kind` is `command` only for a superleader's slash text). No orchestrator-internal enqueue exists; if baseline-facts recorded another call site, it is in scope too and passes its origin explicitly. Origins per path: main-port turn `user`, service-port turn `service:<name>`, session turn `session`, any command-kind message NULL. NULL never passes the gate (orch-orchestration-gate).

Tests no longer accurate (named): `tests/test_migrations.py::test_fresh_database_gets_all_tables`, `::test_presets_migration_on_existing_sessions`, `::test_concurrent_migrate_serialises` and `::test_0005_renames_clusters_to_sessions` hard-code the migration list ending at 0012 and the count 12; with 0013 added each asserts the list ending at 0013 and the count 13, nothing else changes.

## Acceptance conditions

- ac1: the migration 0013_session_orchestration.sql adds messages.origin text, sessions.created_by_session_id uuid and created_by_slug text, presets.created_by_session_id uuid and created_by_slug text, and table orchestration_actions with the D8 columns and no foreign key, and a rerun is a no-op [evidence: test:tests/test_migrations.py::test_session_orchestration_schema]
- ac2: an orchestration_actions row stays after its caller session is purged [evidence: test:tests/test_migrations.py::test_orchestration_actions_outlive_sessions]
- ac3: a turn message posted on the main port is stored with origin user [evidence: test:tests/test_message_origin.py::test_main_port_origin_user]
- ac4: a turn message posted on the service port is stored with origin service:<name>, the authenticated service name read through calling_service(request), and ServiceGate is unchanged [evidence: test:tests/test_message_origin.py::test_service_port_origin_names_service]
- ac5: a session message enqueued by session_send with a sender is stored with origin session [evidence: test:tests/test_message_origin.py::test_session_message_origin]
- ac6: turn_origin returns the id of the first message and the origins of every message linked to the agent's current turn, and None when the current turn delivered no message [evidence: test:tests/test_message_origin.py::test_turn_origin]
- ac7: the service port's routes, 401 and 403 answers and log lines are unchanged [evidence: command:uv run --frozen pytest tests/test_service_port.py]
- ac8: the README documents the origin values user, session, service:<name> and NULL (command-kind messages) [evidence: command:grep -q 'service:<name>' README.md]
- ac9: enqueue_message's origin is a keyword-only parameter with no default, and both call sites, post_message and session_send, pass it explicitly [evidence: test:tests/test_message_origin.py::test_every_enqueue_path_states_origin]
- ac10: a command-kind message posted on the main port, posted on the service port and sent by a superleader through session_send is stored with origin NULL, and turn_origin reports NULL for a turn it delivered [evidence: test:tests/test_message_origin.py::test_command_messages_store_null]
- ac11: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_migrations.py tests/test_message_origin.py tests/test_service_port.py && mise run lint]

## Files

- `src/agents_orchestrator/db/migrations/0013_session_orchestration.sql`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/api/messages.py`
- `src/agents_orchestrator/api/agent.py`
- `README.md`
- `tests/test_migrations.py`
- `tests/test_message_origin.py`
- `tests/test_service_port.py`

## Interfaces

- Migration `0013_session_orchestration.sql`: `ALTER TABLE messages ADD COLUMN IF NOT EXISTS origin text`; `ALTER TABLE sessions ADD COLUMN IF NOT EXISTS created_by_session_id uuid`, `created_by_slug text`; same pair on `presets`; `CREATE TABLE IF NOT EXISTS orchestration_actions (id bigserial PRIMARY KEY, caller_session_id uuid NOT NULL, caller_slug text NOT NULL, message_id bigint, action text NOT NULL, target_kind text NOT NULL, target_id text, target_name text, outcome text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())` plus an index on `(caller_session_id, created_at)`. No FK anywhere.
- `db/queue.py:enqueue_message(conn, session_id, text, target_agent_id=None, *, origin: str | None, kind: str = "turn", sender_session_id=None, sender_slug=None, hop=0) -> int` (slash-commands-from-chat's signature plus the required keyword `origin`, no default).
- `db/queue.py:turn_origin(conn, agent_id) -> TurnOrigin | None` with `TurnOrigin(message_id: int, origins: tuple[str | None, ...])`: `message_id` is the lowest id among the messages whose `turn_id` is the agent's `agent_status.current_turn_id` (the triggering message, D8), `origins` the origin of every one of them; same join as `turn_hop` (`db/queue.py`) without the sender filter and without `ORDER BY m.id DESC LIMIT 1`.
- `api/messages.py:post_message(session_id, body, pool, request: Request)`: origin `None` when `slash.parse(body.text)` makes it a command, else `f"service:{name}"` when `api/service_auth.py:calling_service(request)` returns a name, else `user`.
- `api/agent.py:session_send`: origin `None` when `kind == "command"` (a superleader's slash text), else `session`.
- `api/service_auth.py` is read, not edited: `STATE_KEY = "service"`, `calling_service(request)`.

## Expected outcome

Every message row records where it came from, the turn lookup sees every message of a turn, and the schema of the whole epic exists.

## Steps

- Confirm the number: `ls src/agents_orchestrator/db/migrations/` shows 0012 as the highest file (0010 and 0012 from slash-commands-from-chat, 0011 from hive-decoupling); stop and report if it does not.
- Red: add the migration and origin tests and update the four named migration-list tests to end at 0013 and count 13; run `uv run --frozen pytest tests/test_message_origin.py tests/test_migrations.py`: the new non-DB tests fail (DB tests run in CI; see Notes).
- Green: migration, queue, messages, agent, README; run the task's verify. Quote the summary line.

## Notes

- No Docker in agent pods: the DB tests (ac1-ac6, ac10) run in CI; keep ac9 (the signature check with `inspect.signature` and the two call sites) and the origin choice of post_message and session_send non-DB (a stubbed `enqueue_message`) so the local verify has signal.
- The connector's service token name `agents-matrix-connector` is confirmed (agents-helmfile `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`); the default origins setting lands in orch-orchestration-gate.
- `ServiceGate` already hands the service name to the routes (`calling_service`, landed with migration 0009, used by `api/sessions.py` for `created_by_service`); do not edit `api/service_auth.py`.
- `turn_hop` keeps its own query and semantics (session-message hops); `turn_origin` is a separate query. immediate-message-delivery-w (built after this epic) merges several messages into one turn, which is why every origin is returned.
- Do not touch `tests/test_service_port.py` assertions unless one is no longer accurate; name it if so.

- 2026-10-27 amended: builder check B4 and B6 settlements: explicit origin on every enqueue path, NULL for command and internal messages, migration number from baseline-facts

- 2026-10-29 amended: staleness refresh: migration 0013; reuse calling_service, no ServiceGate edit; the two real call sites; turn_origin over every message of the turn; named test_migrations list tests
