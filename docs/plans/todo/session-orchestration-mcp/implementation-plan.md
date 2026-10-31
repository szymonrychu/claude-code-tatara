# session orchestration mcp implementation plan

## Agreed rung

Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it after the gate.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: baseline facts

- Status: todo
- Files: `MEMORY.md`
- Verify: `grep -q 'Baseline for session-orchestration-mcp' MEMORY.md`
- Verified head: none

#### Requirement

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs."

Negotiated numbers (mx-34 #469/#470, 2026-10-29), as recorded in design.md Constraints: orchestrator migration 0013 (slash-commands-from-chat ships 0010 and 0012; main ends at 0011), any-mcp-tatara-plugins release v0.6.0 (latest tag v0.5.1), agents-schedule migration 0002 and agents-schedule release v0.2.0 (negotiated, user answer pending).

Build order (accepted queue, 2026-10-29): this epic runs right after slash-commands-from-chat, its only README blocker; hive-decoupling and matrix-connector-agent-initi are done.

Scope: this task changes no behaviour. It runs only after slash-commands-from-chat has merged to main. It reads, on the main branch of each repo (never from memory or an old design):

- agents-orchestrator: the highest file in `src/agents_orchestrator/db/migrations/` (0012 expected, so 0013 free); every call site of `queue.enqueue_message` and every other `INSERT INTO messages` with its file and line (expected: `api/messages.py:post_message` and `api/agent.py:session_send`, the only `INSERT INTO messages` in `db/queue.py:enqueue_message`); the `any_mcp_plugins_ref` default in `settings.py` (v0.5.1 expected).
- any-mcp-tatara-plugins: `len(ALL_TOOLS)` in `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (16 expected, asserted by `test_lists_all_tools`), the version in `orchestration/orchestrator/pyproject.toml` (0.5.1 expected) and the latest tag on origin (v0.5.1 expected).
- agents-schedule: the highest file in `src/agents_schedule/migrations/` (0001 expected, so 0002 free), the version in `chart/agents-schedule/Chart.yaml` and the latest tag on origin (0.1.0 and v0.1.0 expected).

It records them in one dated agents-orchestrator `MEMORY.md` entry headed "Baseline for session-orchestration-mcp". When every value matches the negotiated numbers, the dependent tasks stand as written. When one differs, the orchestrator session stops, proposes the new number on mx-34 and waits for its confirmation (standing rule: numbers and tags are negotiated, never taken silently), then amends the dependent tasks (orch-message-origin, sched-schedule-owner, plugin-orchestration-tools, plugins-release-orch-tools, orch-orchestration-tools-pin, sched-release-0-2-0, helmfile-orchestration-pins) with `ticket.py amend`.

#### Acceptance conditions

- ac1: slash-commands-from-chat is merged to the main branch of every repo it touches (its README repos: claude-code-wrapper, agents-orchestrator, agents-web, any-mcp-tatara-plugins, agents-common, agents-webhook, agents-schedule, agents-matrix-connector) before anything else in this epic is dispatched [evidence: judgement:reviewer lists the merged slash-commands-from-chat pull requests with gh pr list --state merged in each repo and confirms each merge commit is on main]
- ac2: MEMORY.md has a dated entry "Baseline for session-orchestration-mcp" naming the highest and next free agents-orchestrator migration, the highest and next free agents-schedule migration, the plugins version and latest origin tag, len(ALL_TOOLS) of the plugin test, the any_mcp_plugins_ref default, the agents-schedule chart version and latest tag, and every enqueue_message call site and INSERT INTO messages with its file [evidence: command:grep -q "Baseline for session-orchestration-mcp" MEMORY.md]
- ac3: each recorded value matches main: the next free migrations are one above the highest file in each directory, the versions are the ones in pyproject.toml and Chart.yaml, the tags the latest on origin [evidence: judgement:reviewer re-derives each value from the repos' main branches with git ls-tree, git grep and git ls-remote --tags and compares it with the entry]
- ac4: the entry states whether every value matches the negotiated numbers (orchestrator migration 0013, schedule migration 0002, plugins v0.6.0 from v0.5.1, schedule v0.2.0 from v0.1.0, 16 plugin tools); on a mismatch the dependent tasks carry the number confirmed on mx-34 and no other [evidence: judgement:reviewer compares the entry with the negotiated numbers in design.md Constraints and, on a mismatch, with the amended task files and the mx-34 confirmation quoted in their Notes]

#### Files

- `MEMORY.md`

#### Interfaces

- agents-orchestrator `MEMORY.md`: one dated entry "Baseline for session-orchestration-mcp" (values, each with the file or command it came from, and a matches-negotiated yes or no per value).
- No code, test or schema changes.

#### Expected outcome

The numbers the epic builds on (orchestrator migration 0013, schedule migration 0002, plugins v0.6.0 from v0.5.1, schedule v0.2.0 from v0.1.0, 16 plugin tools, the two enqueue call sites) are confirmed on main and recorded, or a mismatch is renegotiated on mx-34 before any dependent task is dispatched.

#### Steps

No behaviour change, so no red-green cycle (doc-only exception).

- Confirm slash-commands-from-chat merged: `gh pr list --state merged --search slash-commands-from-chat` in each repo of its README; stop and report if any is open.
- In agents-orchestrator: `git fetch origin && git ls-tree --name-only origin/main src/agents_orchestrator/db/migrations/` (expect 0012 highest), `git grep -n "enqueue_message(\|INSERT INTO messages" origin/main -- src` (expect `api/messages.py`, `api/agent.py`, `db/queue.py`), `git grep -n "any_mcp_plugins_ref: str" origin/main -- src` (expect `v0.5.1`).
- In any-mcp-tatara-plugins: count `ALL_TOOLS` in `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (expect 16), read the pyproject version (expect 0.5.1), `git ls-remote --tags origin` (expect v0.5.1 latest).
- In agents-schedule: `git ls-tree --name-only origin/main src/agents_schedule/migrations/` (expect 0001 highest), Chart.yaml version (expect 0.1.0), latest tag (expect v0.1.0).
- Write the MEMORY.md entry; run `grep -q 'Baseline for session-orchestration-mcp' MEMORY.md` (exit 0).

#### Notes

- Read from origin/main after `git fetch`, never from a local branch or the slash worktrees.
- A mismatch is not fixed by this task: report it; the orchestrator session renegotiates on mx-34 (standing rule) and amends the dependents.
- immediate-message-delivery-w builds on this epic's 0013 and v0.6.0 (it takes 0014 and v0.7.0); a renegotiated number here moves its numbers too, so the mx-34 proposal names both epics.

- 2026-10-29 amended: staleness refresh: negotiated numbers (mx-34 #469/#470) confirmed, not derived; slash-commands-from-chat the only blocker; ALL_TOOLS count, not a test name; Interfaces, Expected outcome, Steps and Notes filled

### S2: orch message origin

- Status: todo
- Files: `src/agents_orchestrator/db/migrations/0013_session_orchestration.sql`, `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/api/messages.py`, `src/agents_orchestrator/api/agent.py`, `README.md`, `tests/test_migrations.py`, `tests/test_message_origin.py`, `tests/test_service_port.py`
- Verify: `uv run --frozen pytest tests/test_migrations.py tests/test_message_origin.py tests/test_service_port.py && mise run lint`
- Verified head: none

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `src/agents_orchestrator/db/migrations/0013_session_orchestration.sql`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/api/messages.py`
- `src/agents_orchestrator/api/agent.py`
- `README.md`
- `tests/test_migrations.py`
- `tests/test_message_origin.py`
- `tests/test_service_port.py`

#### Interfaces

- Migration `0013_session_orchestration.sql`: `ALTER TABLE messages ADD COLUMN IF NOT EXISTS origin text`; `ALTER TABLE sessions ADD COLUMN IF NOT EXISTS created_by_session_id uuid`, `created_by_slug text`; same pair on `presets`; `CREATE TABLE IF NOT EXISTS orchestration_actions (id bigserial PRIMARY KEY, caller_session_id uuid NOT NULL, caller_slug text NOT NULL, message_id bigint, action text NOT NULL, target_kind text NOT NULL, target_id text, target_name text, outcome text NOT NULL, created_at timestamptz NOT NULL DEFAULT now())` plus an index on `(caller_session_id, created_at)`. No FK anywhere.
- `db/queue.py:enqueue_message(conn, session_id, text, target_agent_id=None, *, origin: str | None, kind: str = "turn", sender_session_id=None, sender_slug=None, hop=0) -> int` (slash-commands-from-chat's signature plus the required keyword `origin`, no default).
- `db/queue.py:turn_origin(conn, agent_id) -> TurnOrigin | None` with `TurnOrigin(message_id: int, origins: tuple[str | None, ...])`: `message_id` is the lowest id among the messages whose `turn_id` is the agent's `agent_status.current_turn_id` (the triggering message, D8), `origins` the origin of every one of them; same join as `turn_hop` (`db/queue.py`) without the sender filter and without `ORDER BY m.id DESC LIMIT 1`.
- `api/messages.py:post_message(session_id, body, pool, request: Request)`: origin `None` when `slash.parse(body.text)` makes it a command, else `f"service:{name}"` when `api/service_auth.py:calling_service(request)` returns a name, else `user`.
- `api/agent.py:session_send`: origin `None` when `kind == "command"` (a superleader's slash text), else `session`.
- `api/service_auth.py` is read, not edited: `STATE_KEY = "service"`, `calling_service(request)`.

#### Expected outcome

Every message row records where it came from, the turn lookup sees every message of a turn, and the schema of the whole epic exists.

#### Steps

- Confirm the number: `ls src/agents_orchestrator/db/migrations/` shows 0012 as the highest file (0010 and 0012 from slash-commands-from-chat, 0011 from hive-decoupling); stop and report if it does not.
- Red: add the migration and origin tests and update the four named migration-list tests to end at 0013 and count 13; run `uv run --frozen pytest tests/test_message_origin.py tests/test_migrations.py`: the new non-DB tests fail (DB tests run in CI; see Notes).
- Green: migration, queue, messages, agent, README; run the task's verify. Quote the summary line.

#### Notes

- No Docker in agent pods: the DB tests (ac1-ac6, ac10) run in CI; keep ac9 (the signature check with `inspect.signature` and the two call sites) and the origin choice of post_message and session_send non-DB (a stubbed `enqueue_message`) so the local verify has signal.
- The connector's service token name `agents-matrix-connector` is confirmed (agents-helmfile `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`); the default origins setting lands in orch-orchestration-gate.
- `ServiceGate` already hands the service name to the routes (`calling_service`, landed with migration 0009, used by `api/sessions.py` for `created_by_service`); do not edit `api/service_auth.py`.
- `turn_hop` keeps its own query and semantics (session-message hops); `turn_origin` is a separate query. immediate-message-delivery-w (built after this epic) merges several messages into one turn, which is why every origin is returned.
- Do not touch `tests/test_service_port.py` assertions unless one is no longer accurate; name it if so.

- 2026-10-27 amended: builder check B4 and B6 settlements: explicit origin on every enqueue path, NULL for command and internal messages, migration number from baseline-facts

- 2026-10-29 amended: staleness refresh: migration 0013; reuse calling_service, no ServiceGate edit; the two real call sites; turn_origin over every message of the turn; named test_migrations list tests

### S3: sched schedule owner

- Status: todo
- Files: `src/agents_schedule/migrations/0002_schedule_owner.sql`, `src/agents_schedule/db/schedules.py`, `src/agents_schedule/api/schemas.py`, `src/agents_schedule/api/schedules.py`, `openapi.json`, `tests/test_migrations.py`, `tests/test_schedules_repo.py`, `tests/test_api_schedules.py`
- Verify: `uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "Migration 0002 (the next free agents-schedule number; only `0001_schedules.sql` exists and no other epic claims one) adds `owner_session_id uuid NULL` and `owner_slug text NULL`. [...] The UI API is unchanged except the schedule view gains `owner_slug` (additive); UI writes never change the owner (my call)."

Scope (agents-schedule): `src/agents_schedule/migrations/0002_schedule_owner.sql` (the number baseline-facts confirmed), `db/schedules.py` (owner fields on create and read, owned count, owned lookup), `api/schemas.py` (`ScheduleView.owner_slug`), `api/schedules.py` (the view carries it; UI create and replace never set or clear it), `openapi.json`, `tests/test_migrations.py`, `tests/test_schedules_repo.py`, `tests/test_api_schedules.py`. The relay listener and routes are later tasks.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The migration number is 0002, as baseline-facts confirmed; on a mismatch the orchestrator session amends it.

User settlement B3 (2026-10-27), verbatim: "agent-created schedules may be created enabled. Orphans after the owner's deletion are managed from the UI." The UI routes therefore treat a schedule whose owner session no longer exists like any other: the owner columns are never validated against a live session.


Tests no longer accurate (named): `tests/test_migrations.py::test_migrate_idempotent` and `::test_concurrent_migrate_applies_once` assert the applied list `== ["0001_schedules.sql"]`; with the new migration each asserts `["0001_schedules.sql", "0002_schedule_owner.sql"]`, nothing else changes.

#### Acceptance conditions

- ac1: the migration 0002_schedule_owner.sql adds owner_session_id uuid NULL and owner_slug text NULL to schedules and a rerun is a no-op [evidence: test:tests/test_migrations.py::test_schedule_owner_columns]
- ac2: the repository stores and reads the owner, lists schedules owned by a session and counts them [evidence: test:tests/test_schedules_repo.py::test_owner_round_trip]
- ac3: the UI schedule view carries owner_slug, null for schedules made in the UI, and a UI replace of an owned schedule keeps its owner, and a UI replace and a UI delete of an owned schedule succeed when its owner session no longer exists [evidence: test:tests/test_api_schedules.py::test_owner_slug_in_view]
- ac4: the existing UI routes are otherwise unchanged [evidence: command:uv run pytest tests/test_api_schedules.py]
- ac5: openapi.json matches the app [evidence: command:uv run pytest tests/test_readme_api.py::test_openapi_matches_app]
- ac6: a fresh migrate and a concurrent migrate apply exactly 0001_schedules.sql and 0002_schedule_owner.sql (updated) [evidence: test:tests/test_migrations.py::test_migrate_idempotent]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_schedule/migrations/0002_schedule_owner.sql`
- `src/agents_schedule/db/schedules.py`
- `src/agents_schedule/api/schemas.py`
- `src/agents_schedule/api/schedules.py`
- `openapi.json`
- `tests/test_migrations.py`
- `tests/test_schedules_repo.py`
- `tests/test_api_schedules.py`

#### Interfaces

- `db/schedules.py:Schedule.owner_session_id: uuid.UUID | None`, `owner_slug: str | None`; `create(conn, data, *, owner_session_id=None, owner_slug=None)`; `count_owned(conn, owner_session_id) -> int`; `get_owned(conn, schedule_id, owner_session_id) -> Schedule | None`.
- `api/schemas.py:ScheduleView.owner_slug: str | None`.

#### Expected outcome

Each schedule records which session created it, and the UI can show it.

#### Steps

- Confirm the number: `ls src/agents_schedule/migrations/` shows only `0001_schedules.sql`; stop and report otherwise.
- Red: add the three tests and update the two named migration tests; run `uv run pytest tests/test_migrations.py tests/test_schedules_repo.py tests/test_api_schedules.py`: fail.
- Green: migration, repo, view, `openapi.json` (the repo's generator, as in README); run the task's verify. Quote the summary line.

#### Notes

- No Docker in agent pods: the DB tests run in CI.
- `tests/test_api_schedules.py::test_crud` may compare whole views; if `owner_slug` makes such an assertion no longer accurate, name it and why.

- 2026-10-27 amended: builder check B6 and B3: migration number from baseline-facts, orphaned owned schedules stay manageable from the UI

- 2026-10-29 amended: staleness refresh: migration 0002 confirmed; named test_migrate_idempotent and test_concurrent_migrate_applies_once

### S4: orch orchestration flag

- Status: todo
- Files: `src/agents_orchestrator/spec.py`, `src/agents_orchestrator/api/agent.py`, `README.md`, `openapi.json`, `tests/test_spec_session_options.py`, `tests/test_api_agent.py`
- Verify: `uv run --frozen pytest tests/test_spec_session_options.py tests/test_api_agent.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

Design D1, verbatim: "`SessionSpec.session_orchestration: bool | None = Field(default=None, strict=True)`, sparse like `session_messaging` and `kube_access`. Settable only through the public API or UI (preset, or spec at create). [...] `me` gains `orchestration: bool`."

Architect do-not-build, verbatim: "Making the flag editable in place on a running session."

Scope (agents-orchestrator): `spec.py` (the field, with a comment like its siblings), `api/agent.py` (`Me.orchestration`), README (spec option and `GET /agent/v1/me`), committed `openapi.json`. The allow list is orch-orchestration-tools-pin; agent-side refusal of the flag is orch-orchestration-gate (D5).

Tests no longer accurate (named): `tests/test_spec_session_options.py::test_options_sparse_and_strict` and `::test_preset_carries_options_to_session` cover the sibling flags; they are extended with `session_orchestration`.

#### Acceptance conditions

- ac1: session_orchestration is a sparse strict bool: unset is neither stored nor dumped in a preset and a non-bool value is refused 422 (extended) [evidence: test:tests/test_spec_session_options.py::test_options_sparse_and_strict]
- ac2: a preset with session_orchestration true carries it to a session created from it (extended) [evidence: test:tests/test_spec_session_options.py::test_preset_carries_options_to_session]
- ac3: GET /agent/v1/me answers orchestration true for a flagged session and false otherwise [evidence: test:tests/test_api_agent.py::test_me_orchestration_flag]
- ac4: the flag stays immutable on a running session: no route changes it after create [evidence: test:tests/test_spec_session_options.py::test_session_orchestration_immutable]
- ac5: the README documents session_orchestration and me.orchestration, and openapi.json matches the app [evidence: command:grep -q session_orchestration README.md && uv run --frozen pytest tests/test_readme_api.py::test_openapi_json_matches_app]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_spec_session_options.py tests/test_api_agent.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/agent.py`
- `README.md`
- `openapi.json`
- `tests/test_spec_session_options.py`
- `tests/test_api_agent.py`

#### Interfaces

- `spec.py:SessionSpec.session_orchestration: bool | None = Field(default=None, strict=True)`.
- `api/agent.py:Me.orchestration: bool` (`bool(session.spec.session_orchestration)`).

#### Expected outcome

The user can set session_orchestration on a preset or a spec at create, and an agent can read whether its own session carries it.

#### Steps

- Red: extend the two spec tests, add `test_me_orchestration_flag` and `test_session_orchestration_immutable`; run `uv run --frozen pytest tests/test_spec_session_options.py tests/test_api_agent.py`: the new cases fail.
- Green: spec field, `Me`, README, `uv run python -m agents_orchestrator.api.openapi > openapi.json`; run the task's verify. Quote the summary line.

#### Notes

- Mirror `session_messaging` exactly (sparse, strict, preset round trip).
- DB cases run in CI (no Docker in agent pods).

### S5: sched relay listener

- Status: todo
- Files: `src/agents_schedule/settings.py`, `src/agents_schedule/runtime.py`, `src/agents_schedule/api/relay.py`, `README.md`, `tests/test_settings.py`, `tests/test_relay_gate.py`, `tests/test_entrypoints.py`
- Verify: `uv run pytest tests/test_settings.py tests/test_relay_gate.py tests/test_entrypoints.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "agents-schedule: a second listener `SCHED_RELAY_PORT` with a bearer gate on `SCHED_RELAY_TOKEN_SHA256`, mirroring the connector's agent listener and `ServiceGate`, not bound when the hash is empty."

Design D9, verbatim: "Schedule side: `SCHED_RELAY_MAX_PER_OWNER` (10) owned schedules, else 409 `owned_limit` (my call on the code); `SCHED_RELAY_MIN_INTERVAL_MINUTES` (15): the next three fires must be at least this far apart, else 422 `too_frequent`."

Design D15, verbatim: "Port 8001 is free in the api container."

Scope (agents-schedule): `settings.py` (`relay_port` 8001, `relay_token_sha256`, `relay_max_per_owner` 10, `relay_min_interval_minutes` 15), `runtime.py` (`sched api` serves the relay app on `SCHED_RELAY_PORT` next to the UI app when the hash is set), new `api/relay.py` (the relay app: bearer gate, `X-Orch-Session` and `X-Orch-Slug` required, `/healthz`, `/readyz`, the `/relay/v1` prefix with no routes yet), README (settings and the listener), `tests/test_settings.py`, new `tests/test_relay_gate.py`, `tests/test_entrypoints.py`.

#### Acceptance conditions

- ac1: SCHED_RELAY_PORT defaults to 8001, SCHED_RELAY_TOKEN_SHA256 is empty or 64 lowercase hex characters (else an error naming it) and never in repr, SCHED_RELAY_MAX_PER_OWNER defaults to 10 and SCHED_RELAY_MIN_INTERVAL_MINUTES to 15, both at least 1 [evidence: test:tests/test_settings.py::test_relay_settings]
- ac2: the relay app accepts a request only when the sha256 of its bearer token equals SCHED_RELAY_TOKEN_SHA256 (constant-time), else 401 unauthorized with WWW-Authenticate, and the token never reaches a log line or an error body [evidence: test:tests/test_relay_gate.py::test_bearer_gate]
- ac3: a relay request without a UUID X-Orch-Session or a non-empty X-Orch-Slug is refused 422 invalid_request, and /healthz and /readyz answer without a token [evidence: test:tests/test_relay_gate.py::test_caller_headers_required]
- ac4: the relay app has no source allowlist and serves only /relay/v1, /healthz and /readyz, and the UI app on SCHED_HTTP_PORT serves no relay route and keeps its allowlist [evidence: test:tests/test_relay_gate.py::test_ports_separate]
- ac5: sched api binds the relay listener on SCHED_RELAY_PORT when the hash is set and not at all when it is empty, and both listeners stop on SIGTERM [evidence: test:tests/test_entrypoints.py::test_api_binds_relay_listener_only_with_hash]
- ac6: the README documents the four settings and the relay listener [evidence: command:grep -q SCHED_RELAY_TOKEN_SHA256 README.md && grep -q SCHED_RELAY_MIN_INTERVAL_MINUTES README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_settings.py tests/test_relay_gate.py tests/test_entrypoints.py && mise run lint]

#### Files

- `src/agents_schedule/settings.py`
- `src/agents_schedule/runtime.py`
- `src/agents_schedule/api/relay.py`
- `README.md`
- `tests/test_settings.py`
- `tests/test_relay_gate.py`
- `tests/test_entrypoints.py`

#### Interfaces

- `settings.py:Settings.relay_port: int = 8001`, `relay_token_sha256: str = Field("", repr=False)`, `relay_max_per_owner: int = Field(10, ge=1)`, `relay_min_interval_minutes: int = Field(15, ge=1)`.
- `api/relay.py:create_relay_app(settings, pool, client) -> FastAPI` with `RelayGate` middleware (sha256 hex compare with `hmac.compare_digest`) and `RELAY_PREFIX = "/relay/v1"`; `caller(request) -> RelayCaller(session_id: uuid.UUID, slug: str)` dependency.
- `runtime.py`: a second `_Server` on `settings.relay_port` sharing the pool and client, started only when `relay_token_sha256` is set.

#### Expected outcome

agents-schedule can be reached by the orchestrator on its own token-protected port without opening the SSO-protected UI API.

#### Steps

- Red: write `tests/test_relay_gate.py`, add `test_relay_settings` and the entrypoint test; run them: fail.
- Green: settings, relay app, runtime, README; run the task's verify. Quote the summary line.

#### Notes

- Mirror the orchestrator's `api/service_auth.py:ServiceGate` (constant-time compare, no early exit, no token in logs) and the connector's agent listener (Matrix mxc-agent-listener).
- `proxy_headers=False` on the relay server too.
- The relay app is a separate ASGI app on its own listener; it is not wrapped by `api/app.py:SourceAllowlist` (the UI listener's CIDR allowlist), its only gate is the bearer hash.
- Build fake tokens at runtime in tests (GitGuardian). The entrypoint test needs a DB and runs in CI.

### S6: orch orchestration gate

- Status: todo
- Files: `src/agents_orchestrator/settings.py`, `src/agents_orchestrator/api/orchestration.py`, `src/agents_orchestrator/db/orchestration.py`, `src/agents_orchestrator/api/app.py`, `README.md`, `openapi.json`, `tests/test_orchestration_gate.py`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_orchestration_gate.py tests/test_settings.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/orchestration.py`
- `src/agents_orchestrator/db/orchestration.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_gate.py`
- `tests/test_settings.py`

#### Interfaces

- `settings.py:Settings.orchestration_origins: CsvList = ["user", "service:agents-matrix-connector"]`, `orchestration_actions_per_hour: int = Field(30, ge=1)`, `orchestration_max_owned_sessions: int = Field(5, ge=1)`.
- `api/orchestration.py`: `router = APIRouter(prefix="/agent/v1/orchestration", tags=["agent"])`; `public_router` for `GET /api/v1/orchestration/actions`; dependencies `orchestration_reader` and `orchestration_writer(action, target_kind)` returning an `OrchestrationCaller(agent, session, message_id)`; `check_no_escalation(spec: SessionSpec, caller: SessionSpec) -> None` raising 403 `privilege_escalation`; `record(conn, caller, action, target_kind, target_id, target_name, outcome)`.
- `db/orchestration.py`: `insert_action(...)`, `list_actions(conn, caller_session_id | None, limit)`, `count_ok_writes(conn, caller_session_id, seconds)`, `count_live_owned_sessions(conn, owner_session_id)` (one predicate; used by orch-orchestration-sessions).
- Error codes added: 403 `not_orchestrator`, `not_leader`, `not_user_turn`, `privilege_escalation`; 429 `rate_limited`; 413 `payload_too_large`.

#### Expected outcome

One dependency proves who may orchestrate, in which turn, records every write and enforces the limits; the resource routes plug into it.

#### Steps

- Red: write `tests/test_orchestration_gate.py` with a test-only write and read route mounted on the agent app (non-DB cases with `require_agent` overridden for ac3, ac8, ac9; DB cases like `tests/test_agent_session_messaging.py` for ac4-ac7), add `test_orchestration_settings`; run `uv run --frozen pytest tests/test_orchestration_gate.py tests/test_settings.py`: the new tests fail.
- Green: settings, modules, app wiring, README, `openapi.json`; run the task's verify. Quote the summary line.

#### Notes

- Import `require_agent`, `_leads` from `api/agent.py`; do not copy them. The current-turn lookup is `db/queue.py:turn_origin` (orch-message-origin): the write passes only when `origins` is non-empty and every entry is in `ORCH_ORCHESTRATION_ORIGINS`; `TurnOrigin.message_id` is the audit row's `message_id`.
- The refusal order is part of the contract: a non-leader of a flagged session gets not_leader, never not_user_turn.
- 401 answers write no audit row (no proven caller); every later refusal does.
- No Docker in agent pods: DB cases run in CI; keep the order and escalation cases non-DB.
- Build fake tokens at runtime in tests (GitGuardian).

- 2026-10-27 amended: builder check B2 and B4 settlements: schedule_run counts as an ok write, NULL origin never passes the gate

- 2026-10-27 amended: Q9: one shared require_own_preset predicate

- 2026-10-29 amended: staleness refresh: the gate requires every message of the turn to have an allowed origin

### S7: sched relay routes

- Status: todo
- Files: `src/agents_schedule/api/relay.py`, `src/agents_schedule/api/schedules.py`, `src/agents_schedule/api/runs.py`, `src/agents_schedule/api/openapi.py`, `openapi-relay.json`, `README.md`, `tests/test_relay_schedules.py`, `tests/test_readme_api.py`
- Verify: `uv run pytest tests/test_relay_schedules.py tests/test_readme_api.py tests/test_api_schedules.py tests/test_api_runs.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "Relay routes: list all (read); create, update, delete, run-now and runs on owned schedules (404 `not_found` when not owned). [...] The listener contract is committed as `openapi-relay.json` and vendored by the orchestrator, like Matrix D16."

Design D9, verbatim: "Schedule side: `SCHED_RELAY_MAX_PER_OWNER` (10) owned schedules, else 409 `owned_limit` (my call on the code); `SCHED_RELAY_MIN_INTERVAL_MINUTES` (15): the next three fires must be at least this far apart, else 422 `too_frequent`."

Open question Q5 (pending; the plan follows the recommended answer), verbatim: "Agent-created schedules may fire at most every 15 minutes, at most 10 per session; at most 5 live owned sessions and 30 writes per hour?" recommended "yes".

Architect reuse, verbatim: "agents-schedule `api/schedules.py` handlers and `_check_preset`."

Scope (agents-schedule): `api/relay.py` (routes `GET /relay/v1/schedules`, `POST /relay/v1/schedules`, `PUT /relay/v1/schedules/{id}`, `DELETE /relay/v1/schedules/{id}`, `POST /relay/v1/schedules/{id}/run`, `GET /relay/v1/schedules/{id}/runs`), `api/schedules.py` and `api/runs.py` (shared handler bodies taking an owner), `api/openapi.py` (also writes the relay document), committed `openapi-relay.json`, README (`## Relay API`, every route), new `tests/test_relay_schedules.py`, `tests/test_readme_api.py`.

User settlement B2 (2026-10-27), verbatim: "schedule_run counts as an ok write against ORCH_ORCHESTRATION_ACTIONS_PER_HOUR. The global max_sessions is the only bound on fired sessions." The relay run-now adds no cap of its own on how often an owned schedule may be run; the orchestrator counts it against the hourly write limit.

User settlement B3 (2026-10-27), verbatim: "agent-created schedules may be created enabled. Orphans after the owner's deletion are managed from the UI." Relay create stores `enabled` as the body says (true is accepted and the schedule fires at once as the cron says); the listener never forces a schedule disabled.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". Only the orchestrator knows who created a preset, so it enforces the rule (orch-schedule-relay, `require_own_preset`) before it calls the listener; this task makes the contract say so: the README `## Relay API` section and the `openapi-relay.json` create and update descriptions state that `preset_id` must name a preset the calling session created and that the orchestrator enforces it, and the listener keeps `_check_preset` for existence only.

#### Acceptance conditions

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

#### Files

- `src/agents_schedule/api/relay.py`
- `src/agents_schedule/api/schedules.py`
- `src/agents_schedule/api/runs.py`
- `src/agents_schedule/api/openapi.py`
- `openapi-relay.json`
- `README.md`
- `tests/test_relay_schedules.py`
- `tests/test_readme_api.py`

#### Interfaces

- Relay bodies: create and update take `ScheduleIn`; views are `ScheduleView` (with `owner_slug`) and `RunView`; errors `{error: {code, message}}` like the UI API.
- `api/openapi.py`: writes `openapi.json` (UI) and `openapi-relay.json` (relay).

#### Expected outcome

The orchestrator can list all schedules and manage its callers' own through one documented contract.

#### Steps

- Red: write `tests/test_relay_schedules.py` and the two readme tests; run them: fail.
- Green: routes on the relay app reusing the UI handler bodies, the openapi generator, `openapi-relay.json`, README; run the task's verify. Quote the summary line.

#### Notes

- Reuse `_validate_cron`, `_check_preset` and the run-now path; do not copy them. The run-now path must NOTIFY `runs_new` like the UI route (MEMORY 2026-10-25).
- The fire-interval check uses the repo's cron module over the schedule's timezone.
- DB cases run in CI (no Docker in agent pods).

- 2026-10-27 amended: builder check B2, B3 and Q9: run-now uncapped, create enabled, preset-ownership rule in the contract

### S8: orch orchestration presets

- Status: todo
- Files: `src/agents_orchestrator/api/orchestration_presets.py`, `src/agents_orchestrator/db/presets.py`, `src/agents_orchestrator/api/presets.py`, `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/app.py`, `README.md`, `openapi.json`, `tests/test_orchestration_presets.py`
- Verify: `uv run --frozen pytest tests/test_orchestration_presets.py tests/test_api_presets.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

Design D4, verbatim: "Writes only on objects owned by the caller session: [...] `presets.created_by_session_id` and `created_by_slug` [...]. Otherwise 403 `not_owner` [...]. Presets: spec with `env` values, `wrapper.hooks.*.secret`, header values and command `env` values masked, except on own presets. No copy tool. [...] The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects the user made) so agents-web can show it (Q7; my call pending the gate)."

Design D5, verbatim: "Applies to an agent-written preset spec, an agent-created session spec (from a spec or a preset) and the preset named by an agent-written schedule (the relay reads it first)."

Design D6, verbatim: "Preset delete: own only; the `PresetDefault` and `LastPreset` refusals still apply."

Architect fix-as-ac, verbatim: "Masked secrets in non-owned preset views." and "No escalation through presets, specs or schedule presets (`privilege_escalation`)."

Architect do-not-build, verbatim: "A preset copy tool."

Scope (agents-orchestrator): new `api/orchestration_presets.py` (`GET /presets`, `GET /presets/{id}`, `POST /presets`, `PUT /presets/{id}`, `DELETE /presets/{id}` under `/agent/v1/orchestration`), `db/presets.py` (store and read `created_by_*`), `api/presets.py` and `api/schemas.py` (`PresetView.created_by_slug`), `api/app.py`, README, `openapi.json`.

#### Acceptance conditions

- ac1: the preset list and get return every preset, and on presets the caller did not create the env values, wrapper hook secrets, webhook and MCP header values and command and MCP stdio env values are masked with their keys kept, while the caller's own presets are unmasked [evidence: test:tests/test_orchestration_presets.py::test_masked_except_own]
- ac2: preset create validates like POST /api/v1/presets, stores the caller's created_by_session_id and created_by_slug and refuses privilege_escalation [evidence: test:tests/test_orchestration_presets.py::test_create_owned_and_validated]
- ac3: preset update and delete act only on presets the caller created (403 not_owner, 404 not_found for a missing id), update refuses privilege_escalation, and the PresetDefault and LastPreset refusals still apply [evidence: test:tests/test_orchestration_presets.py::test_update_delete_own_only]
- ac4: no copy route exists under /agent/v1/orchestration [evidence: test:tests/test_orchestration_presets.py::test_no_copy_route]
- ac5: every preset write, refusals included, writes an audit row with target_kind preset and the preset id and name [evidence: test:tests/test_orchestration_presets.py::test_preset_writes_audited]
- ac6: the public PresetView carries created_by_slug, null for presets the user made [evidence: test:tests/test_orchestration_presets.py::test_public_view_created_by]
- ac7: the README documents every preset orchestration route and the masked fields, and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac8: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_presets.py tests/test_api_presets.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_orchestrator/api/orchestration_presets.py`
- `src/agents_orchestrator/db/presets.py`
- `src/agents_orchestrator/api/presets.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_presets.py`

#### Interfaces

- `api/orchestration_presets.py`: `router = APIRouter(prefix="/agent/v1/orchestration/presets", tags=["agent"])`; reads use `orchestration_reader`, writes `orchestration_writer`.
- `mask_spec(spec: dict) -> dict`: one function, one placeholder string, covering `SessionSpec.env`, `WrapperSettings` hooks (`WebhookHook.secret`, `WebhookHook.headers`, `CommandHook.env`), `McpStdio.env`, `McpRemote.headers`.
- `db/presets.py`: `create(..., created_by_session_id=None, created_by_slug=None)`; `Preset.created_by_session_id`, `created_by_slug`.
- `schemas.PresetView.created_by_slug: str | None`.

#### Expected outcome

A flagged leader can list and read every preset safely and create, edit and delete only its own.

#### Steps

- Red: write `tests/test_orchestration_presets.py`; run `uv run --frozen pytest tests/test_orchestration_presets.py`: fails.
- Green: module, repo, view, app wiring, README, `openapi.json`; run the task's verify. Quote the summary line.

#### Notes

- Reuse `api/presets.py:_validated` and the default and last-preset refusal mapping; do not copy the validation.
- kubernetes-secret-backed-pre (todo, unplanned) may later move preset env storage; this task masks the spec fields as they are on main.
- `check_no_escalation` and the audit helper come from `api/orchestration.py` (orch-orchestration-gate).
- `tests/test_api_presets.py` must stay green; if an assertion on the exact `PresetView` keys is no longer accurate because of `created_by_slug`, name it and why.
- DB cases run in CI (no Docker in agent pods); `mask_spec` cases are non-DB.

### S9: sched chart relay port

- Status: todo
- Files: `chart/agents-schedule/values.yaml`, `chart/agents-schedule/templates/service-relay.yaml`, `chart/agents-schedule/templates/deployment.yaml`, `chart/agents-schedule/templates/_config.tpl`, `chart/agents-schedule/templates/secret.yaml`, `README.md`, `tests/test_chart.py`
- Verify: `uv run pytest tests/test_chart.py tests/test_chart_ingress.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D15, verbatim: "Port 8001 is free in the api container. The relay gets its own Service `agents-schedule-api-relay`, port 8001 to container port `relay` 8001, selecting only the api component (my call, mirrors the connector's `-api-agents` Service)."

Design D16, verbatim: "the schedule chart takes `relay.tokenSha256` or `relay.tokenSecret`."

Scope (agents-schedule chart): `chart/agents-schedule/values.yaml` (`relay.port: 8001`, `relay.tokenSha256`, `relay.tokenSecret.{name,key}`), new `templates/service-relay.yaml` (`<fullname>-api-relay`), `templates/deployment.yaml` (container port `relay` and `SCHED_RELAY_TOKEN_SHA256` secretKeyRef on the api container only), `templates/_config.tpl` (`SCHED_RELAY_PORT`), `templates/secret.yaml` (the hash Secret when `relay.tokenSha256` is set), README (chart values), `tests/test_chart.py`. The relay is on only when a hash source is set.

#### Acceptance conditions

- ac1: with a relay hash set the chart renders the -api and -api-relay Services, the relay Service on port 8001 targeting port relay and selecting only the api component [evidence: test:tests/test_chart.py::test_relay_service]
- ac2: the api container exposes port relay 8001 and the worker container does not [evidence: test:tests/test_chart.py::test_relay_port_on_api_only]
- ac3: SCHED_RELAY_TOKEN_SHA256 reaches only the api container through a secretKeyRef (chart Secret from relay.tokenSha256, or relay.tokenSecret, which wins), never the ConfigMap, and a malformed hash fails the render [evidence: test:tests/test_chart.py::test_relay_hash_secret_on_api_only]
- ac4: the ConfigMap renders SCHED_RELAY_PORT, and without relay values no relay Service, port or variable is rendered [evidence: test:tests/test_chart.py::test_relay_absent_by_default]
- ac5: helm lint passes [evidence: command:mise run lint:chart]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_chart.py tests/test_chart_ingress.py && mise run lint]

#### Files

- `chart/agents-schedule/values.yaml`
- `chart/agents-schedule/templates/service-relay.yaml`
- `chart/agents-schedule/templates/deployment.yaml`
- `chart/agents-schedule/templates/_config.tpl`
- `chart/agents-schedule/templates/secret.yaml`
- `README.md`
- `tests/test_chart.py`

#### Interfaces

- Values: `relay: {port: 8001, tokenSha256: "", tokenSecret: {name: "", key: tokenSha256}}`.
- Service `{{ fullname }}-api-relay`, port name `relay`, port 8001, `targetPort: relay`.

#### Expected outcome

The deployed agents-schedule exposes its relay listener to the orchestrator through its own Service, the hash only in a Secret.

#### Steps

- Red: add the four chart tests; run `uv run pytest tests/test_chart.py`: fail.
- Green: values, templates, README; run the task's verify and `mise run lint:chart`. Quote the summary line.

#### Notes

- Mirror Matrix mxc-chart-agent-port (the connector's agent Service and hash Secret).
- The Ingress keeps routing only `/schedules` to the -api Service (`tests/test_chart_ingress.py` stays green).

### S10: orch orchestration sessions

- Status: todo
- Files: `src/agents_orchestrator/api/orchestration_sessions.py`, `src/agents_orchestrator/api/sessions.py`, `src/agents_orchestrator/db/sessions.py`, `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/app.py`, `README.md`, `openapi.json`, `tests/test_orchestration_sessions.py`
- Verify: `uv run --frozen pytest tests/test_orchestration_sessions.py tests/test_api_sessions.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

README Goal G3, verbatim: "A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session."

Design D4, verbatim: "Reads cover everything through trimmed views. Sessions: slug, id, preset, state, replicas, superleader, orchestration, created_by, no spec. [...] Ownership is by session id; when the owner is deleted, its objects stay and are managed from the UI. [...] The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects the user made) so agents-web can show it (Q7; my call pending the gate)."

Design D5, verbatim: "Applies to an agent-written preset spec, an agent-created session spec (from a spec or a preset) and the preset named by an agent-written schedule (the relay reads it first). `session_orchestration: true` is always refused; `kube_access` or `session_messaging` true only if the caller's own session has that same flag. Refusal: 403 `privilege_escalation`."

Design D6, verbatim: "1. 404 `not_found`; 2. 422 `self_delete`; 3. 403 `not_owner`; 4. 409 `protected_target` (the target has `session_orchestration` or `session_messaging`); 5. 409 `session_deleting`. Then `request_delete`. [...] Owned-session scale goes through `set_replicas`."

Design D9, verbatim: "`ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS` (5): live owned sessions, else 409 `owned_limit`; the global `max_sessions` still applies."

Design D10, verbatim: "`session_create` takes an optional `prompt`, queued as a session message: sender the caller, hop the caller's hop plus 1, origin `session`."

Design D12, verbatim: "a session cannot delete itself, so mx-5 never releases its own room binding; deleting an owned session bound to a room releases that binding through the existing Matrix Q10 sweep (intended)."

Architect fix-as-ac, verbatim: "`self_delete`, `not_owner`, `protected_target` refusals."

Scope (agents-orchestrator): new `api/orchestration_sessions.py` (`GET /sessions`, `POST /sessions`, `POST /sessions/{slug}/scale`, `DELETE /sessions/{slug}` under `/agent/v1/orchestration`), `api/sessions.py` (the create path takes provenance; no copy of `check_spec` or `_create_from_preset`), `db/sessions.py` (store and read `created_by_*`), `api/schemas.py` (`SessionView.created_by_slug`), `api/app.py`, README, `openapi.json`.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". Session create with `preset_id` calls `api/orchestration.py:require_own_preset` (orch-orchestration-gate) before any create work, so a preset the user made in the UI, or another session made, is refused 403 `not_owner`; a `spec` in the body is not restricted by it (the caller can only write what it can read, and reads mask other presets' secrets) and still passes `check_no_escalation`.

User settlement B4 (2026-10-27), verbatim: "Store origin `session` or `user` the same way on every enqueue path." The prompt of session_create is enqueued with the explicit origin `session` through the `origin` argument orch-message-origin made required.

#### Acceptance conditions

- ac1: the sessions overview lists every session with slug, id, preset, state, replicas, superleader, orchestration and created_by, and no spec [evidence: test:tests/test_orchestration_sessions.py::test_overview_trimmed]
- ac2: session create from a preset id or a spec runs the same checks as POST /api/v1/sessions (check_spec, the create lock, max_sessions), stores the caller as created_by and refuses privilege_escalation for a preset or spec carrying session_orchestration or a flag the caller lacks [evidence: test:tests/test_orchestration_sessions.py::test_create_owned_no_escalation]
- ac3: session create with a preset_id the caller did not create (made in the UI, or by another session) is refused 403 not_owner with an audit row and no session, create from the caller's own preset and from an explicit spec pass, and the answer names no preset env value [evidence: test:tests/test_orchestration_sessions.py::test_create_from_foreign_preset_refused]
- ac4: with ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS live owned sessions a create is refused 409 owned_limit, and deleting or purged sessions do not count [evidence: test:tests/test_orchestration_sessions.py::test_owned_limit]
- ac5: a create with prompt queues the prompt to the new session as a session message from the caller with hop the caller's hop plus 1 and origin session, passed explicitly [evidence: test:tests/test_orchestration_sessions.py::test_create_with_prompt]
- ac6: session delete checks in order 404 not_found, 422 self_delete, 403 not_owner, 409 protected_target for a target with session_orchestration or session_messaging, 409 session_deleting, then requests the delete [evidence: test:tests/test_orchestration_sessions.py::test_delete_checks_in_order]
- ac7: session scale changes only owned sessions through set_replicas with its existing refusal codes, and 403 not_owner otherwise [evidence: test:tests/test_orchestration_sessions.py::test_scale_owned_only]
- ac8: the public SessionView carries created_by_slug, null for sessions the user made [evidence: test:tests/test_orchestration_sessions.py::test_public_view_created_by]
- ac9: every session write, refusals included, writes an audit row with target_kind session and the target id and slug [evidence: test:tests/test_orchestration_sessions.py::test_session_writes_audited]
- ac10: the README documents every session orchestration route with its checks in order, and openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_orchestration_sessions.py tests/test_api_sessions.py tests/test_api_create_from_preset.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_orchestrator/api/orchestration_sessions.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/db/sessions.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_sessions.py`

#### Interfaces

- `api/orchestration_sessions.py`: `router = APIRouter(prefix="/agent/v1/orchestration/sessions", tags=["agent"])`; body of create `{preset_id?: uuid, spec?: object, slug?: str, prompt?: str (<= 16000 chars)}`, exactly one of `preset_id` and `spec`.
- `api/sessions.py:_insert(conn, slug, spec, **provenance)` gains `created_by_session_id`, `created_by_slug`; the public create path passes none.
- `db/sessions.py:Session.created_by_session_id`, `created_by_slug`; owned check by session id.
- `schemas.SessionView.created_by_slug: str | None`.

#### Expected outcome

A flagged leader can see every session and create, scale and delete only the ones it created, never itself or a protected one.

#### Steps

- Red: write `tests/test_orchestration_sessions.py`; run `uv run --frozen pytest tests/test_orchestration_sessions.py`: fails.
- Green: module, create-path provenance, repo, view, app wiring, README, `openapi.json`; run the task's verify. Quote the summary line.

#### Notes

- Reuse `check_spec`, `_create_from_preset`, `_CREATE_LOCK`, `request_delete`, `set_replicas`; import, never copy.
- `api/sessions.py:_insert(conn, slug, spec, **provenance)` already carries `created_by_service` (migration 0009); pass `created_by_session_id` and `created_by_slug` the same way, no second insert path. The prompt enqueue passes `origin="session"` and `kind="turn"` explicitly.
- decouple-s3-session-cache-fr (todo, not blocked on this epic) also edits `_create_from_preset`; re-read it at build time if it merged first.
- The live-owned count is `db/orchestration.py:count_live_owned_sessions` (one predicate; retro: duplicate predicates were found late). The owned check is one predicate too.
- Prompt hop: `db/queue.py:turn_hop` of the caller plus 1 (1 in a user turn); origin `session`.
- `tests/test_api_sessions.py` and `tests/test_api_create_from_preset.py` must stay green; name any assertion on exact view keys that `created_by_slug` makes no longer accurate.
- DB cases run in CI (no Docker in agent pods).

- 2026-10-27 amended: Q9: create from own presets only; B4: explicit session origin

### S11: sched release 0.2.0

- Status: todo
- Files: `chart/agents-schedule/Chart.yaml`, `pyproject.toml`, `uv.lock`, `src/agents_schedule/__init__.py`, `README.md`, `tests/test_chart.py`
- Verify: `uv run pytest tests/test_chart.py tests/test_cli.py tests/test_ci_workflow.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D17, verbatim: "agents-schedule is pinned by its release tag v0.2.0 (negotiated, user answer pending): chart `0.2.0`, published by the tag's `chart-publish-tag` job, and image `<sha7>` of the tagged commit, published by its main build, the way v0.1.0 is pinned today (chart `0.1.0`, image `6cfa955`). The orchestrator and agents-web are pinned by main sha7 as today; the agent image stays on its release tag. `mise run check-pins` resolves `0.2.0` through tag `v0.2.0` and must pass before any apply."

Standing user rule (2026-10-29, design.md Constraints), verbatim: "every release tag is proposed via mx-34 and confirmed before tagging."

Negotiated (mx-34 #469/#470, 2026-10-29; tatara agreed, the user's direct answer is pending): agents-schedule v0.2.0, the next minor after the latest tag v0.1.0.

Scope (agents-schedule), after every other agents-schedule task of this epic has merged:
- Confirm the baseline: the latest tag on origin is v0.1.0 and `chart/agents-schedule/Chart.yaml` says 0.1.0 (baseline-facts); stop and report on a mismatch, never pick another number.
- `chart/agents-schedule/Chart.yaml`: `version: 0.2.0`, `appVersion: "0.2.0"`; `scripts/chart-version.sh` refuses a tag whose version differs from Chart.yaml, so the tag needs this bump on main first.
- `pyproject.toml` version 0.2.0, `src/agents_schedule/__init__.py` `__version__ = "0.2.0"`, `uv lock` updates `uv.lock`.
- README `## Releases`: a v0.2.0 line in the shape of the v0.1.0 line: tag v0.2.0 on the merge commit of this release, image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7 of that commit>`, chart version 0.2.0 (the sha is not known before the merge, so the line names the rule, not the value).
- Test no longer accurate (named): `tests/test_chart.py::test_image_tag_defaults_to_app_version` asserts the default image ends with `:0.1.0` (the Chart.yaml appVersion); it asserts `:0.2.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI and the main build pushed the image `<sha7>` of the merge commit: propose the tag v0.2.0 on that merge commit on mx-34 and wait for the confirmation, then `git tag -a v0.2.0 <merge sha> -m v0.2.0 && git push origin v0.2.0` (irreversible, listed in design.md); the `chart-publish-tag` job then publishes chart 0.2.0. ac5, ac6 and ac7 are checked by the orchestrator after that push.

#### Acceptance conditions

- ac1: Chart.yaml version and appVersion, pyproject.toml and __version__ all say 0.2.0, and the default image tag follows the appVersion (updated) [evidence: test:tests/test_chart.py::test_image_tag_defaults_to_app_version]
- ac2: README Releases has a v0.2.0 line naming the tag, the image rule and chart 0.2.0 [evidence: command:grep -q "v0.2.0" README.md]
- ac3: scripts/chart-version.sh accepts tag v0.2.0 and prints 0.2.0 [evidence: command:test "$(scripts/chart-version.sh tag v0.2.0 0123456789abcdef)" = 0.2.0 && grep -q '^version = "0.2.0"' pyproject.toml]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_chart.py tests/test_cli.py tests/test_ci_workflow.py && mise run lint]
- ac5: (orchestrator session) the tag v0.2.0 was proposed on mx-34 and confirmed there before it was pushed [evidence: judgement:orchestrator quotes the mx-34 proposal and confirmation message ids, both older than the tag push, in the task Notes]
- ac6: (orchestrator session) the tag v0.2.0 exists on origin at the merge commit, and its chart-publish-tag job and the merge commit's images job succeeded [evidence: command:git ls-remote --tags origin | grep -q 'refs/tags/v0.2.0']
- ac7: (orchestrator session) chart 0.2.0 and image <sha7 of the tagged commit> exist in Harbor [evidence: judgement:orchestrator quotes helm show chart oci://harbor.szymonrichert.pl/charts/agents-schedule --version 0.2.0 and the image digest in the task Notes]

#### Files

- `chart/agents-schedule/Chart.yaml`
- `pyproject.toml`
- `uv.lock`
- `src/agents_schedule/__init__.py`
- `README.md`
- `tests/test_chart.py`

#### Interfaces

- `chart/agents-schedule/Chart.yaml`: `version: 0.2.0`, `appVersion: "0.2.0"`.
- `pyproject.toml:version = "0.2.0"`, `src/agents_schedule/__init__.py:__version__ = "0.2.0"` (printed by `sched --version`, `tests/test_cli.py`).
- `scripts/chart-version.sh tag v0.2.0 <sha>` prints `0.2.0` (unchanged script; it refuses a tag that differs from Chart.yaml).
- Git tag `v0.2.0` (annotated, like v0.1.0) on the merge commit; chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` 0.2.0 (appVersion the sha7) from `chart-publish-tag`; image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` from the merge commit's main `images` job.

#### Expected outcome

agents-schedule v0.2.0 exists as a tag, a published chart 0.2.0 and an image, carrying the owner columns, the relay listener and routes and the relay Service of this epic, for helmfile-orchestration-pins to pin.

#### Steps

- Confirm the baseline: `git fetch --tags origin && git tag --sort=-v:refname | head -1` prints `v0.1.0`; `grep -n "^version" chart/agents-schedule/Chart.yaml` prints `0.1.0`; stop and report otherwise.
- Red: change `tests/test_chart.py::test_image_tag_defaults_to_app_version` to `:0.2.0`; run `uv run pytest tests/test_chart.py::test_image_tag_defaults_to_app_version`: fails on `:0.1.0`.
- Green: bump Chart.yaml, pyproject, `__version__`, `uv lock`, README `## Releases`; run the task's verify. Quote the summary line.
- After the merge (orchestrator session): wait for the main run green (images and chart-publish jobs), propose v0.2.0 on mx-34 and wait for the confirmation, push the annotated tag, wait for `chart-publish-tag` green, check ac5 to ac7.

#### Notes

- Dependency-bump TDD exception for the version values beyond the named test.
- Runs last among the agents-schedule tasks (depends on sched-chart-relay-port, which depends on the routes, listener and owner tasks), so the tag carries all of them.
- The image stays a sha7 tag (CI pushes images only on main pushes); Harbor retention pruned sha7 image tags within hours in the 2026-10-28 incident while chart versions survive. orchestration-live-smoke checks the image in Harbor right before the apply; semver image tags are semver-image-tags-at-the-end's scope (it later removes `chart-publish-tag` and the tag mode of `chart-version.sh`, so this task must land before it).
- The README Releases line names the image rule, not the sha (unknown before the merge); the supervisor never edits repo files after the merge.

### S12: orch creator messaging

- Status: todo
- Files: `src/agents_orchestrator/api/agent.py`, `README.md`, `MEMORY.md`, `tests/test_agent_session_messaging.py`
- Verify: `uv run --frozen pytest tests/test_agent_session_messaging.py && mise run lint`
- Verified head: none

#### Requirement

Design D10, verbatim: "The `session_send` rule gains \"or one session created the other\", so replies can come back to a non-superleader owner (Q4, pending the gate)."

Open question Q4 (pending; the plan follows the recommended answer), verbatim: "A session and the sessions it created may message each other even when neither is a superleader?" recommended "yes".

Scope (agents-orchestrator): `api/agent.py:session_send` (the target_not_superleader check also passes when the caller created the target or the target created the caller), README (the `session_send` rule), `MEMORY.md` (dated entry for the epic's decisions: the flag, the user-turn gate, ownership, the schedule relay).

#### Acceptance conditions

- ac1: a non-superleader session may send to a session it created and that session may send back, while two unrelated non-superleader sessions are still refused target_not_superleader [evidence: test:tests/test_agent_session_messaging.py::test_creator_and_created_may_message]
- ac2: every other session_send refusal and limit is unchanged [evidence: command:uv run --frozen pytest tests/test_agent_session_messaging.py]
- ac3: the README session_send rule says one session created the other is enough [evidence: command:grep -q "one session created the other" README.md]
- ac4: MEMORY.md records the session orchestration decisions, dated [evidence: command:grep -q "session_orchestration" MEMORY.md]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_agent_session_messaging.py && mise run lint]

#### Files

- `src/agents_orchestrator/api/agent.py`
- `README.md`
- `MEMORY.md`
- `tests/test_agent_session_messaging.py`

#### Interfaces

- `api/agent.py:session_send`: `if not (own.spec.session_messaging or target.spec.session_messaging or target.created_by_session_id == own.id or own.created_by_session_id == target.id)`.

#### Expected outcome

An orchestrating session and the sessions it created can talk to each other without either being a superleader.

#### Steps

- Red: add `test_creator_and_created_may_message`; run `uv run --frozen pytest tests/test_agent_session_messaging.py`: fails.
- Green: the rule, README, MEMORY; run the task's verify. Quote the summary line.

#### Notes

- Re-read `api/agent.py:session_send` on main at build time (slash-commands-from-chat added `kind`; the rule is `if not (own.spec.session_messaging or target.spec.session_messaging)`). The creator rule widens who may send a turn only: `kind` stays `command` only for a superleader's slash text, so a non-superleader creator still sends a framed turn.
- `sessions_list` peer listing is unchanged (D10 changes the send rule only; `sessions_overview` lists every session for a flagged caller).
- DB test runs in CI (no Docker in agent pods).

### S13: orch schedule relay

- Status: todo
- Files: `src/agents_orchestrator/settings.py`, `src/agents_orchestrator/api/orchestration_relay.py`, `src/agents_orchestrator/api/chat.py`, `src/agents_orchestrator/api/app.py`, `README.md`, `openapi.json`, `tests/test_orchestration_relay.py`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_orchestration_relay.py tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/orchestration_relay.py`
- `src/agents_orchestrator/api/chat.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `tests/test_orchestration_relay.py`
- `tests/test_settings.py`

#### Interfaces

- `settings.py:Settings.schedule_url: str = ""`, `schedule_token: str = Field(default="", repr=False)`; validator for both-or-neither and the scheme, next to the chat pair.
- `api/orchestration_relay.py`: `router = APIRouter(prefix="/agent/v1/orchestration/schedules", tags=["agent"])`; its own `httpx.AsyncClient` on `app.state` (timeout 10 s), closed in the `api/app.py` lifespan next to `chat.close_client`.
- `api/chat.py`: today `forward(request, method, path, body, session, slug)` reads `settings.chat_url`, `chat_token`, `UPSTREAM_PREFIX` and raises `chat_unavailable`, and `_capped_body(request)` caps at `MAX_BODY_BYTES` (256 KiB); generalise them to take the upstream base URL, prefix, token, client, unavailable code and whether an empty 204 passes (yes for schedules, no for chat), so both relays call one helper; the chat routes keep their answers.
- Agent-facing errors added: 503 `schedules_unconfigured`, 503 `schedules_unavailable`; everything else is the upstream's or the gate's.

#### Expected outcome

A flagged leader can manage its schedules through the orchestrator, which proves who calls and keeps the agent token to itself.

#### Steps

- Red: write `tests/test_orchestration_relay.py` (an `httpx.MockTransport` upstream; non-DB cases for ac3-ac6 and ac9; DB cases for ac7 and ac8), add `test_schedule_relay_settings`; run them: fail.
- Green: settings, module, the shared helper in `api/chat.py`, app wiring and lifespan close, README, `openapi.json`; run the task's verify. Quote the summary line.

#### Notes

- Matrix did not extract a shared helper: `forward`, `_capped_body`, `new_client`, `client`, `close_client` live in `api/chat.py` (Matrix orch-chat-relay). Share them (boy scout, `api/chat.py` is in Files) rather than copying; `tests/test_agent_chat.py` and `tests/test_chat_contract.py` stay green unchanged.
- The relay reads the preset by id through `db/presets.py` before forwarding create and update (D5) and applies `check_no_escalation`.
- Never log the relay token, the agent token or a body; log method, path, status only.
- `X-Orch-Slug` is the caller session's slug from the sessions repo, never from the request.
- Build fake tokens at runtime in tests (GitGuardian). DB cases run in CI.

- 2026-10-27 amended: builder check B2, B3 and Q9: schedule_run counted, enabled forwarded, own presets only

- 2026-10-29 amended: staleness refresh: reuse the chat.py forward helper, empty 204 and 202 pass through, chat relay unchanged

### S14: orch schedule relay contract

- Status: todo
- Files: `tests/fakes/schedule_relay_openapi.json`, `tests/fakes/schedule_relay_openapi.source`, `tests/fakes/schedule_relay.py`, `tests/test_schedule_relay_contract.py`, `tests/test_orchestration_relay.py`
- Verify: `uv run --frozen pytest tests/test_schedule_relay_contract.py tests/test_orchestration_relay.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D7, verbatim: "The listener contract is committed as `openapi-relay.json` and vendored by the orchestrator, like Matrix D16."

Retro proposal (generic-any-mcp-with-git-and), verbatim: "any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it."

Needs a merged upstream: agents-schedule main carrying sched-relay-routes (`openapi-relay.json`).

Scope (agents-orchestrator): vendor `openapi-relay.json` from agents-schedule main as `tests/fakes/schedule_relay_openapi.json` with `tests/fakes/schedule_relay_openapi.source` (`agents-schedule <40-hex sha>`); new fake upstream `tests/fakes/schedule_relay.py` whose answers follow the vendored schemas; `tests/test_schedule_relay_contract.py`; `tests/test_orchestration_relay.py` moves its upstream to the fake where it used ad-hoc bodies.

#### Acceptance conditions

- ac1: tests/fakes/schedule_relay_openapi.json is byte-identical to openapi-relay.json at the agents-schedule commit named in tests/fakes/schedule_relay_openapi.source, which is on that repo's main [evidence: judgement:reviewer runs git show <sha>:openapi-relay.json in agents-schedule and compares it with the vendored file]
- ac2: every orchestrator schedule route maps to a path and method of the vendored document [evidence: test:tests/test_schedule_relay_contract.py::test_relay_routes_exist_upstream]
- ac3: every success and error answer of the fake validates against the vendored response schemas [evidence: test:tests/test_schedule_relay_contract.py::test_fake_relay_matches_vendored_schema]
- ac4: the bodies the relay forwards for create, update and run validate against the vendored request schemas [evidence: test:tests/test_schedule_relay_contract.py::test_relay_requests_match_vendored_schema]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_schedule_relay_contract.py tests/test_orchestration_relay.py && mise run lint]

#### Files

- `tests/fakes/schedule_relay_openapi.json`
- `tests/fakes/schedule_relay_openapi.source`
- `tests/fakes/schedule_relay.py`
- `tests/test_schedule_relay_contract.py`
- `tests/test_orchestration_relay.py`

#### Interfaces

- `tests/fakes/schedule_relay.py`: an ASGI fake of `/relay/v1/schedules*` (in-memory, owner from `X-Orch-Session`), mountable as an `httpx.ASGITransport`.
- `tests/fakes/schedule_relay_openapi.source`: one line `agents-schedule <sha>`.

#### Expected outcome

The orchestrator's relay and its fake are pinned to the contract agents-schedule actually serves.

#### Steps

- Confirm agents-schedule main carries `openapi-relay.json` (sched-relay-routes merged); stop and report if not.
- Red: write `tests/test_schedule_relay_contract.py` against the vendored file; run it: fails.
- Green: vendor the file and source, write the fake, point the relay tests at it; run the task's verify. Quote the summary line.

#### Notes

- Follow the chat contract pattern on main: `tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`, `tests/fakes/fake_chat.py`, `tests/test_chat_contract.py`; reuse its validation helpers rather than copying them.

### S15: plugin orchestration tools

- Status: todo
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`
- Verify: `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

Design D11, verbatim: "Plugin tools (prefix `orchestrator_`, leader-only, rendered only when flagged): presets `presets_list`, `preset_get`, `preset_create`, `preset_update`, `preset_delete`; sessions `sessions_overview`, `session_create`, `session_scale`, `session_delete`; schedules `schedules_list`, `schedule_create`, `schedule_update`, `schedule_delete`, `schedule_run`, `schedule_runs`; audit `orchestration_actions`."

Design D3, verbatim: "Tool descriptions require the agent to name the target to the user before deleting."

Architect reuse, verbatim: "`OrchestratorPlugin.on_error`."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py` (sixteen `ToolSpec`s bound to `/agent/v1/orchestration/*`, their descriptions), `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`. No new file: `tests/test_nomenclature.py` pins the plugin to these three files and bans the words matching `cluster|agent[-_]orchestrator` in them, so names, descriptions and README text avoid both. `orchestrator_activity` (the hive digest) and the new `orchestrator_orchestration_actions` (the caller's audit rows) are different tools; their descriptions say which is which.

Test no longer accurate (named): `orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_all_tools` asserts the listed tools equal the `ALL_TOOLS` set, sixteen tools on main at v0.5.1 (`orchestrator_activity` included); `ALL_TOOLS` gains the sixteen orchestration tools, thirty-two in all, and the test is otherwise unchanged. The plugin README line "The plugin always lists all sixteen tools" and its tool table become no longer accurate the same way: thirty-two tools.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The count in this task is the baseline-facts count (16) plus sixteen: 32.

Open question Q9 (pending; the plan follows the recommended answer), verbatim: "A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls?" recommended "yes". The descriptions of session_create, schedule_create and schedule_update say so.

#### Acceptance conditions

- ac1: ALL_TOOLS holds the sixteen tools main holds plus the sixteen orchestration tools, 32 in all, and the plugin lists exactly that set with hive true and false (updated) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_all_tools]
- ac2: each orchestration tool calls its /agent/v1/orchestration route with the D11 method, path and body and the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_tools_call_agent_routes]
- ac3: the refusals not_orchestrator, not_leader, not_user_turn, not_owner, not_found, privilege_escalation, self_delete, protected_target, session_deleting, owned_limit, rate_limited, too_frequent, payload_too_large, schedules_unconfigured and schedules_unavailable surface their code and status with the token redacted [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_errors_surface_code]
- ac4: the descriptions say writes are only for the user's own request in a turn the user started, changes are limited to objects this session created, the delete tools require naming the target to the user before deleting, and preset reads mask other presets' secrets, and session_create, schedule_create and schedule_update say a session or schedule may be created only from a preset this session created or from an explicit spec, and the descriptions of orchestrator_activity and orchestrator_orchestration_actions tell the hive digest from the caller's audit rows [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_orchestration_descriptions]
- ac5: the plugin README lists the sixteen orchestration tools, says the plugin lists thirty-two tools, and says the orchestration tools render only for sessions flagged session_orchestration [evidence: command:grep -q orchestrator_session_delete orchestration/orchestrator/README.md && grep -q session_orchestration orchestration/orchestrator/README.md]
- ac6: the three plugin files carry none of the banned words and stay the only tracked plugin files [evidence: test:tests/test_nomenclature.py::test_no_old_nomenclature]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

#### Interfaces

- Tool to route map (prefix `/agent/v1/orchestration`): `presets_list` GET `/presets`; `preset_get` GET `/presets/{id}`; `preset_create` POST `/presets` `{name, spec}`; `preset_update` PUT `/presets/{id}` `{name, spec}`; `preset_delete` DELETE `/presets/{id}`; `sessions_overview` GET `/sessions`; `session_create` POST `/sessions` `{preset_id?, spec?, slug?, prompt?}`; `session_scale` POST `/sessions/{slug}/scale` `{replicas}`; `session_delete` DELETE `/sessions/{slug}`; `schedules_list` GET `/schedules`; `schedule_create` POST `/schedules`; `schedule_update` PUT `/schedules/{id}`; `schedule_delete` DELETE `/schedules/{id}`; `schedule_run` POST `/schedules/{id}/run`; `schedule_runs` GET `/schedules/{id}/runs`; `orchestration_actions` GET `/actions`.
- Read the final paths and bodies from the orchestrator README `### Orchestration` on agents-orchestrator main; the map above is the design's.

#### Expected outcome

Agents of flagged sessions get sixteen tools that drive the orchestration routes, with descriptions that keep them on the user's request.

#### Steps

- Red: add the sixteen names to `ALL_TOOLS` (32 in all) so `test_lists_all_tools` fails, add the three new tests; run `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: fails.
- Green: tool specs, descriptions, README; run the task's verify. Quote the summary line.

#### Notes

- Builds on main's `__init__.py` at v0.5.1 (hive-decoupling, Matrix and slash-commands-from-chat landed: 16 tools, `orchestrator_activity` the last); read it first.
- `tests/test_nomenclature.py` (repo root) bans `cluster` and `agent-orchestrator`/`agent_orchestrator` in the three plugin files; say "session" and "orchestrator", never the banned words, in names, descriptions and the README.
- Rewrite the README sentence "The plugin always lists all sixteen tools" to thirty-two and extend its tool table.
- The plugin does no I/O at load (`test_no_io_at_load` stays green).

- 2026-10-27 amended: builder check B6 and Q9: counts from baseline-facts, own-preset rule in descriptions

- 2026-10-29 amended: staleness refresh: test_lists_all_tools over ALL_TOOLS (16 to 32), nomenclature test, activity vs actions descriptions

### S16: web orchestration switch

- Status: todo
- Files: `src/presets/PresetForm.tsx`, `src/sessions/sessionSpecForm.ts`, `src/presets/PresetForm.test.tsx`, `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`
- Verify: `npx vitest run src/presets && npm run lint`
- Verified head: none

#### Requirement

README Goal G6, verbatim: "agents-web has the \"Session orchestration\" switch on the preset form (sessions take the flag from their preset), and shows \"created by <slug>\" on sessions, presets and schedules."

Design D1, verbatim: "Settable only through the public API or UI (preset, or spec at create)."

Architect discovery, verbatim: "The \"Superleader\" switch lives in `src/presets/PresetForm.tsx:288` and `src/sessions/sessionSpecForm.ts:181,403`. `kube_access` follows the same pattern, so a new flag needs the same switch."

Needs a merged upstream: agents-orchestrator main carrying orch-schedule-relay (the final orchestrator API of this epic: `session_orchestration`, `created_by_slug`).

Scope (agents-web): `src/presets/PresetForm.tsx` (a "Session orchestration" switch next to Superleader with a help text naming what it grants), `src/sessions/sessionSpecForm.ts` (value, load and sparse save), `src/presets/PresetForm.test.tsx`, `openapi/orchestrator.json` and `openapi/orchestrator.source` (`npm run sync:api -- orchestrator`), `src/api/schema.d.ts`.

Tests no longer accurate (named): `src/presets/PresetForm.test.tsx` "session options default off and stay sparse" and "session options save and round-trip" cover the sibling switches; they are extended with session_orchestration.

#### Acceptance conditions

- ac1: the preset form shows a "Session orchestration" switch, off by default with its help text, and an untouched switch leaves session_orchestration out of the saved spec (extended) [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "session options default off and stay sparse"]
- ac2: switched on, the preset saves session_orchestration true, and a stored true loads on and round-trips (extended) [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "session options save and round-trip"]
- ac3: the vendored orchestrator OpenAPI document and the generated types match, orchestrator.source names an agents-orchestrator main commit, and the document carries session_orchestration and created_by_slug [evidence: command:npm run check:api && grep -q '^agents-orchestrator [0-9a-f]\{40\}$' openapi/orchestrator.source && grep -q session_orchestration openapi/orchestrator.json && grep -q created_by_slug openapi/orchestrator.json]
- ac4: the preset tests and lint pass [evidence: command:npx vitest run src/presets && npm run lint]

#### Files

- `src/presets/PresetForm.tsx`
- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.test.tsx`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

#### Interfaces

- `sessionSpecForm.ts`: value key `sessionOrchestration: boolean`; `spec.session_orchestration = true` only when set and on.

#### Expected outcome

The user can flag a preset for session orchestration in the UI; sessions created from it get the tools.

#### Steps

- Confirm agents-orchestrator main carries orch-schedule-relay; stop and report if not.
- Red: extend the two tests; run `npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: `npm run sync:api -- orchestrator`, the switch, the mapping; run the task's verify. Quote the summary line.

#### Notes

- The help text says the session's leader may create, change and delete presets, sessions and schedules it created, on the user's request.
- Retro: PresetForm tests are load-sensitive (name_rules_default_name_and_pvc timed out at 5 s once); the extended tests keep their 15000 ms timeouts. On a first-run failure save the failing test name and output tail before any rerun.

### S17: orch chart schedule relay

- Status: todo
- Files: `chart/agents-orchestrator/values.yaml`, `chart/agents-orchestrator/templates/secret.yaml`, `chart/agents-orchestrator/templates/_config.tpl`, `chart/agents-orchestrator/templates/deployment.yaml`, `README.md`, `tests/test_chart_config.py`
- Verify: `uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D16, verbatim: "The orchestrator chart takes `schedule.url`, `schedule.token` or `schedule.existingSecret`; the schedule chart takes `relay.tokenSha256` or `relay.tokenSecret`." and (staleness refresh 2026-10-29) "`ORCH_SCHEDULE_URL` and `ORCH_SCHEDULE_TOKEN` are env of the api main container only, always together, rendered by one `agents-orchestrator.scheduleEnv` helper next to `agents-orchestrator.chatEnv`, never in the shared settings ConfigMap, the migrate init containers or the other components (orchestrator MEMORY 2026-10-28, orch-chat-env-scope: the chart once put `ORCH_CHAT_URL` in the shared ConfigMap with the token on the api only, and every migrate init container crash-looped on a URL without its token)."

Design D7, verbatim: "Settings both set or both empty; both empty gives 503 `schedules_unconfigured`".

Scope (agents-orchestrator chart): `chart/agents-orchestrator/values.yaml` (`schedule.url`, `schedule.token`, `schedule.existingSecret`, `schedule.existingSecretKey`, documented like the `chat` block), `templates/secret.yaml` (the chart Secret `<fullname>-schedule`), `templates/_config.tpl` (`scheduleEnabled`, `scheduleSecretName`, `scheduleEnv` next to the chat helpers), `templates/deployment.yaml` (`scheduleEnv` included in the api main container only, a `checksum/schedule-secret` pod annotation so the api pod rolls when the chart-made token changes), README (Configuration and Secrets), `tests/test_chart_config.py`. The settings ConfigMap is not touched. Mirrors the chat block (`chatEnabled`, `chatSecretName`, `chatEnv`); if both blocks repeat the same helper logic, factor one named template both use (boy scout, same files).

#### Acceptance conditions

- ac1: with schedule values set (inline token or existingSecret) the settings ConfigMap carries neither ORCH_SCHEDULE_URL nor ORCH_SCHEDULE_TOKEN [evidence: test:tests/test_chart_config.py::test_configmap_has_no_schedule_url]
- ac2: in every container of every component, init containers included, ORCH_SCHEDULE_URL is present exactly when ORCH_SCHEDULE_TOKEN is, and only in the api main container [evidence: test:tests/test_chart_config.py::test_schedule_pair_rendered_together_per_container]
- ac3: the api main container gets ORCH_SCHEDULE_URL as a plain value and ORCH_SCHEDULE_TOKEN as a secretKeyRef to the chart Secret <fullname>-schedule key schedule-token, or to schedule.existingSecret and schedule.existingSecretKey, which win [evidence: test:tests/test_chart_config.py::test_api_container_has_schedule_pair]
- ac4: schedule.token renders the chart Secret <fullname>-schedule and the api pod template carries a checksum/schedule-secret annotation that changes with the token [evidence: test:tests/test_chart_config.py::test_schedule_token_secret_on_api_only]
- ac5: a schedule URL without a token source, or a token source without a URL, fails the render with a message naming schedule.url, schedule.token and schedule.existingSecret [evidence: test:tests/test_chart_config.py::test_schedule_url_and_token_together]
- ac6: without schedule values neither variable nor the schedule Secret is rendered anywhere [evidence: test:tests/test_chart_config.py::test_schedule_absent_by_default]
- ac7: the chat block keeps rendering as before (its per-container and ConfigMap tests stay green) [evidence: command:uv run --frozen pytest tests/test_chart_config.py -k chat]
- ac8: README documents schedule.url, schedule.token, schedule.existingSecret and that both variables are env of the api main container only, never in the ConfigMap [evidence: command:grep -q 'schedule.existingSecret' README.md && grep -q 'ORCH_SCHEDULE_TOKEN' README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint]

#### Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/secret.yaml`
- `chart/agents-orchestrator/templates/_config.tpl`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `README.md`
- `tests/test_chart_config.py`

#### Interfaces

- Values: `schedule: {url: "", token: "", existingSecret: "", existingSecretKey: schedule-token}`, documented like the `chat` block (`values.yaml`).
- `_config.tpl`: `agents-orchestrator.scheduleEnabled` (fails the render on half a pair, naming schedule.url, schedule.token and schedule.existingSecret), `agents-orchestrator.scheduleSecretName` (existingSecret wins over `<fullname>-schedule`), `agents-orchestrator.scheduleEnv` (the `ORCH_SCHEDULE_URL` value and the `ORCH_SCHEDULE_TOKEN` secretKeyRef, empty when off), next to `chatEnabled`, `chatSecretName`, `chatEnv`.
- `deployment.yaml`: `scheduleEnv` included only under `{{- if eq $component "api" }}` in the main container, right after `chatEnv`; pod annotation `checksum/schedule-secret` next to `checksum/chat-secret`.
- Tests in `tests/test_chart_config.py` reuse `_containers` (init containers included), `_env_names`, `_is_api_main` and the `CHAT_VALUES` parametrize pattern.

#### Expected outcome

The orchestrator chart can turn the schedule relay on with its token kept in a Secret, and no container other than the api main one ever sees half of the pair.

#### Steps

- Red: add the six schedule chart tests; run `uv run --frozen pytest tests/test_chart_config.py -k schedule`: they fail.
- Green: values, helpers, Secret, deployment, README; run the task's verify and `mise run lint:chart`. Quote the summary line.

#### Notes

- Copy the shape of the chat block next to it; if both blocks repeat the same helper logic, factor one named template both use (boy scout, same files).
- Never touch `templates/configmap.yaml` or the `agents-orchestrator.settings` data: the 2026-10-28 incident (orchestrator MEMORY, orch-chat-env-scope) came from a relay URL in the shared ConfigMap, which every migrate init container loads; `Settings` refuses a URL without its token, so they crash-looped.
- helmfile MEMORY gotcha (a changed service Secret does not restart the api pods) is why the `checksum/schedule-secret` annotation is in scope.

- 2026-10-29 amended: staleness refresh: schedule pair api-main-only via scheduleEnv, never the ConfigMap (2026-10-28 chat env incident)

### S18: plugins release orch tools

- Status: todo
- Files: `orchestration/orchestrator/pyproject.toml`, `uv.lock`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py`
- Verify: `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D11, verbatim: "The release is any-mcp-tatara-plugins v0.6.0, the next minor after the latest tag v0.5.1 that slash-commands-from-chat leaves pinned (negotiated 2026-10-29, mx-34 #469/#470)."

Standing user rule (2026-10-29, design.md Constraints), verbatim: "every release tag is proposed via mx-34 and confirmed before tagging."

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- Confirm the baseline: the latest tag on origin is v0.5.1 and `orchestration/orchestrator/pyproject.toml` says 0.5.1 (baseline-facts); stop and report on a mismatch, never pick another number.
- `orchestration/orchestrator/pyproject.toml`: version 0.6.0; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.6.0` (was `v0.5.1`).
- Tests no longer accurate (named): `tests/test_source_install.py::test_orchestrator_distribution_metadata` asserts version 0.5.1 for the pyproject metadata and the installed distribution; it asserts 0.6.0.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: propose the tag v0.6.0 on the merge commit on mx-34 and wait for the confirmation (the number was negotiated in mx-34 #469/#470; the tag itself is still proposed and confirmed before it is pushed), then `git tag v0.6.0 <merge sha> && git push origin v0.6.0` (irreversible, listed in design.md). ac3 and ac5 are checked by the orchestrator after that push.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The version this task bumps from and to is the one baseline-facts confirmed (0.5.1 to 0.6.0).

#### Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.6.0 (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins ?ref=v0.6.0 and no older tag [evidence: command:grep -q 'ref=v0.6.0' orchestration/orchestrator/README.md && ! grep -q 'ref=v0.5' orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) the tag v0.6.0 exists on origin at the merge commit [evidence: command:git ls-remote --tags origin | grep -q "refs/tags/v$(sed -n 's/^version = .\([0-9.]*\)./\1/p' orchestration/orchestrator/pyproject.toml)$"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]
- ac5: (orchestrator session) the tag v0.6.0 was proposed on mx-34 and confirmed there before it was pushed [evidence: judgement:orchestrator quotes the mx-34 proposal and confirmation message ids, both older than the tag push, in the task Notes]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

#### Interfaces

- Distribution `any-mcp-tatara-orchestrator` version 0.6.0 (was 0.5.1); git tag `v0.6.0` on the `main` merge commit, pushed only after its mx-34 confirmation.

#### Expected outcome

The plugin with the orchestration tools is released as a tag the orchestrator can pin.

#### Steps

- Confirm the baseline: `git ls-remote --tags origin` lists v0.5.1 as the highest tag and `orchestration/orchestrator/pyproject.toml` says 0.5.1; stop and report on a mismatch.
- Red: change `test_orchestrator_distribution_metadata` to the new version; run it: fails.
- Green: bump pyproject, `uv lock`, README example; run the task's verify. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, propose `v0.6.0 on <merge sha7>` on mx-34 and wait for the confirmation, push the tag, check ac3 and record ac5's message ids in Notes.

#### Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- Standing rule since 2026-10-29 14:27Z: every tag is proposed on mx-34 and confirmed before it is pushed; v0.5.1 was once tagged without it and mx-34 reported it to the user (handover note 2026-10-29). The number negotiation (mx-34 #469/#470) does not replace the per-tag proposal.
- immediate-message-delivery-w takes v0.7.0 on top of this v0.6.0.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in this pod with git 2.39 (`--end-of-options`, environmental per Matrix); CI is its gate.

- 2026-10-27 amended: builder check B6: version from baseline-facts

- 2026-10-29 amended: staleness refresh: v0.6.0 from v0.5.1; mx-34 proposal and confirmation before tagging

### S19: web created by

- Status: todo
- Files: `src/sessions/SessionsPage.tsx`, `src/sessions/SessionsPage.test.tsx`, `src/presets/PresetsPage.tsx`, `src/presets/PresetsPage.test.tsx`
- Verify: `npx vitest run src/sessions/SessionsPage.test.tsx src/presets/PresetsPage.test.tsx && npm run lint`
- Verified head: none

#### Requirement

README Goal G6, verbatim: "agents-web has the \"Session orchestration\" switch on the preset form (sessions take the flag from their preset), and shows \"created by <slug>\" on sessions, presets and schedules."

Open question Q7 (pending; the plan follows the recommended answer), verbatim: "agents-web shows 'created by <slug>' on sessions, presets and schedules?" recommended "yes".

Design D4, verbatim: "The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects the user made) so agents-web can show it (Q7; my call pending the gate)."

Scope (agents-web): `src/sessions/SessionsPage.tsx` and `src/presets/PresetsPage.tsx` show "created by <slug>" for rows whose `created_by_slug` is set and nothing for the others; their tests. Schedules are web-schedule-owner.

#### Acceptance conditions

- ac1: the sessions list shows "created by <slug>" on a session with created_by_slug and nothing on one without [evidence: command:npx vitest run src/sessions/SessionsPage.test.tsx -t "created by"]
- ac2: the presets list shows "created by <slug>" on a preset with created_by_slug and nothing on one without [evidence: command:npx vitest run src/presets/PresetsPage.test.tsx -t "created by"]
- ac3: the sessions and presets tests and lint pass [evidence: command:npx vitest run src/sessions/SessionsPage.test.tsx src/presets/PresetsPage.test.tsx && npm run lint]

#### Files

- `src/sessions/SessionsPage.tsx`
- `src/sessions/SessionsPage.test.tsx`
- `src/presets/PresetsPage.tsx`
- `src/presets/PresetsPage.test.tsx`

#### Interfaces

- Reads `SessionView.created_by_slug` and `PresetView.created_by_slug` from the vendored types (web-orchestration-switch).

#### Expected outcome

The user sees which session created a session or a preset.

#### Steps

- Red: add one "created by" test to each page test; run them: fail.
- Green: render the label; run the task's verify. Quote the summary line.

#### Notes

- Keep the label secondary text in the existing row layout; no new column needed.

### S20: helmfile relay secrets

- Status: todo
- Files: `scripts/bootstrap-secrets.sh`, `helmfile.yaml.gotmpl`, `values/agents-orchestrator/schedule-token.secrets.yaml`, `values/agents-schedule/relay-token.secrets.yaml`, `tests/test_secrets.py`, `README.md`
- Verify: `uv run pytest tests/test_secrets.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D16, verbatim: "`scripts/bootstrap-secrets.sh` generates one relay token: the orchestrator file `values/agents-orchestrator/schedule-token.secrets.yaml` (`schedule.token`) and the schedule file `values/agents-schedule/relay-token.secrets.yaml` (`relay.tokenSha256`, its sha256), both SOPS-encrypted, both or neither, never rotated."

Scope (agents-helmfile): `scripts/bootstrap-secrets.sh` (a `bootstrap_schedule_relay` step), `helmfile.yaml.gotmpl` (the two files listed on their releases), the two committed SOPS files (written by the orchestrator session, which holds the SOPS key), `tests/test_secrets.py`, README (the new secret). Mirrors Matrix helmfile-chat-secrets.

#### Acceptance conditions

- ac1: the script writes both files, and the hash file's relay.tokenSha256 is the sha256 of the token file's schedule.token (fake sops) [evidence: test:tests/test_secrets.py::test_schedule_relay_token_bootstrapped]
- ac2: with both files present nothing is rewritten, and with exactly one present the script exits 1 naming both and writes nothing [evidence: test:tests/test_secrets.py::test_schedule_relay_token_never_rotates]
- ac3: the token and its hash never reach stdout, stderr or a trace [evidence: test:tests/test_secrets.py::test_schedule_relay_token_not_printed]
- ac4: the two committed files are SOPS-encrypted with exactly the expected keys [evidence: test:tests/test_secrets.py::test_secrets_files_encrypted_with_expected_keys]
- ac5: helmfile.yaml.gotmpl lists schedule-token.secrets.yaml on agents-orchestrator and relay-token.secrets.yaml with default.secrets.yaml on agents-schedule [evidence: test:tests/test_secrets.py::test_schedule_relay_files_listed_on_releases]
- ac6: (orchestrator session, needs the SOPS key) the decrypted hash matches the decrypted token [evidence: test:tests/test_secrets.py::test_schedule_relay_token_hash_matches]
- ac7: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_secrets.py && mise run lint]

#### Files

- `scripts/bootstrap-secrets.sh`
- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/schedule-token.secrets.yaml`
- `values/agents-schedule/relay-token.secrets.yaml`
- `tests/test_secrets.py`
- `README.md`

#### Interfaces

- `values/agents-orchestrator/schedule-token.secrets.yaml`: `schedule: {token: <secret>}`.
- `values/agents-schedule/relay-token.secrets.yaml`: `relay: {tokenSha256: <hex>}`.

#### Expected outcome

The one relay token exists, encrypted, in the shape both charts read, and never rotates.

#### Steps

- Red: add the tests (fake sops as the existing schedule service-token tests do); run `uv run pytest tests/test_secrets.py`: fail.
- Green: the bootstrap step, helmfile listing, README; the orchestrator session runs the script with the SOPS key and commits both encrypted files; run the task's verify. Quote the summary line.

#### Notes

- `test_secrets_files_encrypted_with_expected_keys` is parametrized; add the two files to its table (extended, not weakened).
- agents-helmfile has no CI (retro): the local verify is the only evidence; ac6 needs the SOPS key and is run by the orchestrator session.
- Build fake tokens at runtime in tests (GitGuardian).

### S21: orch orchestration tools pin

- Status: todo
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `src/agents_orchestrator/k8s/on_start.py`, `README.md`, `tests/test_settings.py`, `tests/test_on_start.py`, `tests/test_orchestration_tools_parity.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_orchestration_tools_parity.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools."

Design D1, verbatim: "The orchestrator tools render only when the flag is true: `orchestrator_allow` adds `ORCHESTRATION_TOOLS`, as with `scale`."

Design D11, verbatim: "The release is any-mcp-tatara-plugins v0.6.0, the next minor after the latest tag v0.5.1 that slash-commands-from-chat leaves pinned (negotiated 2026-10-29, mx-34 #469/#470). The allow-list change lands with the pin in one task, per Matrix D13 (`test_allowed_tools_exist_in_plugin` needs both)."

Needs a merged upstream: the any-mcp-tatara-plugins tag v0.6.0 pushed by plugins-release-orch-tools.

Scope (agents-orchestrator): `settings.py` (`any_mcp_plugins_ref` default `v0.6.0`, was `v0.5.1` after slash-commands-from-chat), `pyproject.toml` and `uv.lock` (dev dependency `any-mcp-tatara-orchestrator` at `v0.6.0`), `k8s/on_start.py` (`ORCHESTRATION_TOOLS`, appended to a flagged session's list in both branches of `orchestrator_allow(spec, *, chat=True)`, the alone/non-hive early return and the hive return, whatever `chat` is; `chat=False` still drops only the chat tools), README (the default ref, the `## Images` plugins tag, the tools only for flagged sessions), `tests/test_settings.py`, `tests/test_on_start.py`, new `tests/test_orchestration_tools_parity.py`.

Test no longer accurate (named): `tests/test_settings.py::test_defaults` asserts `any_mcp_plugins_ref == "v0.5.1"`; it asserts `v0.6.0`.

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs." The tag is v0.6.0 as baseline-facts confirmed; the sixteen is this epic's own tool count (32 plugin tools in all).

#### Acceptance conditions

- ac1: the plugins ref settings default is v0.6.0, the tag released by plugins-release-orch-tools (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin v0.6.0, the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: a flagged session's allow list ends with the sixteen orchestration tools for an alone session and a hive, each with chat true and with chat false (a trigger-service session), and an unflagged session's list has none of them in any of these cases [evidence: test:tests/test_on_start.py::test_orchestration_tools_only_when_flagged]
- ac4: every allowed tool, the orchestration tools included, exists in the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac5: the released plugin drives every orchestration tool against the real agent routes and the fake schedule relay, and each result equals the direct route answer [evidence: test:tests/test_orchestration_tools_parity.py::test_orchestration_tools_parity]
- ac6: the README documents the new default ref and that the orchestration tools render only for flagged sessions [evidence: command:grep -q "orchestrator_session_create" README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_orchestration_tools_parity.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `src/agents_orchestrator/k8s/on_start.py`
- `README.md`
- `tests/test_settings.py`
- `tests/test_on_start.py`
- `tests/test_orchestration_tools_parity.py`

#### Interfaces

- `k8s/on_start.py:ORCHESTRATION_TOOLS = ["presets_list", "preset_get", "preset_create", "preset_update", "preset_delete", "sessions_overview", "session_create", "session_scale", "session_delete", "schedules_list", "schedule_create", "schedule_update", "schedule_delete", "schedule_run", "schedule_runs", "orchestration_actions"]`; `orchestrator_allow(spec, *, chat=True)` appends it when `spec.session_orchestration`, in the early return for non-hive sessions (`shared`) and in the hive return alike, whatever `chat` is.
- `Settings.any_mcp_plugins_ref` default: `v0.6.0` (`ORCH_ANY_MCP_PLUGINS_REF`, `v0.5.1` after slash-commands-from-chat).
- `pyproject.toml` dev group: `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.6.0#subdirectory=orchestration/orchestrator`; `tests/test_images.py::test_plugins_dev_pin_matches_settings_ref` ties it to the settings default and `uv.lock`.

#### Expected outcome

Agent pods of flagged sessions install the plugins release with the orchestration tools and may call them; no other session sees them.

#### Steps

- Confirm the tag on any-mcp-tatara-plugins origin: `git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.6.0` prints one line; stop and report if absent.
- Red: update `test_defaults`, add `test_orchestration_tools_only_when_flagged` and the parity test; run them: fail.
- Green: settings default, pyproject pin, `uv lock`, `on_start.py`, README; run the task's verify. Quote the summary line.

#### Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties them to one tag.
- Builds on the merged slash-commands-from-chat versions of `on_start.py` and `settings.py` (hive-decoupling and Matrix already landed); read them first.
- The flag does not change for a running session, so the render stays fixed (D1).
- Changing the default changes the rendered config hash; on deploy the OnDelete rollout reconciler replaces each agent pod once it is idle (orchestration-live-smoke).
- The parity test's DB cases run in CI.

- 2026-10-27 amended: builder check B6: tag from baseline-facts

- 2026-10-29 amended: staleness refresh: pin v0.6.0 from v0.5.1; both orchestrator_allow branches and chat=False

### S22: web schedule owner

- Status: todo
- Files: `openapi/schedules.json`, `openapi/schedules.source`, `src/api/schedules-schema.d.ts`, `src/schedules/SchedulesPage.tsx`, `src/schedules/SchedulesPage.test.tsx`
- Verify: `npx vitest run src/schedules && npm run lint`
- Verified head: none

#### Requirement

README Goal G6, verbatim: "agents-web has the \"Session orchestration\" switch on the preset form (sessions take the flag from their preset), and shows \"created by <slug>\" on sessions, presets and schedules."

Open question Q7 (pending; the plan follows the recommended answer), verbatim: "agents-web shows 'created by <slug>' on sessions, presets and schedules?" recommended "yes".

Design D7, verbatim: "The UI API is unchanged except the schedule view gains `owner_slug` (additive)".

Needs a merged upstream: agents-schedule main carrying sched-schedule-owner.

Scope (agents-web): `openapi/schedules.json` and `openapi/schedules.source` (`npm run sync:api -- schedules`), `src/api/schedules-schema.d.ts`, `src/schedules/SchedulesPage.tsx` ("created by <slug>" for owned schedules), `src/schedules/SchedulesPage.test.tsx`.

#### Acceptance conditions

- ac1: the schedules list shows "created by <slug>" on a schedule with owner_slug and nothing on one without [evidence: command:npx vitest run src/schedules/SchedulesPage.test.tsx -t "created by"]
- ac2: the vendored schedules OpenAPI document and the generated types match, schedules.source names an agents-schedule main commit, and the document carries owner_slug [evidence: command:npm run check:api && grep -q '^agents-schedule [0-9a-f]\{40\}$' openapi/schedules.source && grep -q owner_slug openapi/schedules.json]
- ac3: the schedules tests and lint pass [evidence: command:npx vitest run src/schedules && npm run lint]

#### Files

- `openapi/schedules.json`
- `openapi/schedules.source`
- `src/api/schedules-schema.d.ts`
- `src/schedules/SchedulesPage.tsx`
- `src/schedules/SchedulesPage.test.tsx`

#### Interfaces

- Reads `ScheduleView.owner_slug` from the regenerated `schedules-schema.d.ts`.

#### Expected outcome

The user sees which session created a schedule.

#### Steps

- Confirm agents-schedule main carries sched-schedule-owner; stop and report if not.
- Red: add the "created by" test; run it: fails.
- Green: `npm run sync:api -- schedules`, the label; run the task's verify. Quote the summary line.

#### Notes

- Same label style as web-created-by.

### S23: helmfile orchestration pins

- Status: todo
- Files: `values/agents-orchestrator/common.yaml`, `values/agents-schedule/common.yaml`, `values/agents-web/common.yaml`, `helmfile.yaml.gotmpl`, `tests/test_orchestrator_release.py`, `tests/test_schedule_release.py`, `tests/test_web_release.py`
- Verify: `uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py && mise run check-pins && mise run lint`
- Verified head: none

#### Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D15, verbatim: "The orchestrator values set `schedule.url: http://agents-schedule-api-relay:8001`."

Design D17, verbatim: "agents-schedule is pinned by its release tag v0.2.0 (negotiated, user answer pending): chart `0.2.0`, published by the tag's `chart-publish-tag` job, and image `<sha7>` of the tagged commit, published by its main build, the way v0.1.0 is pinned today (chart `0.1.0`, image `6cfa955`). The orchestrator and agents-web are pinned by main sha7 as today; the agent image stays on its release tag. `mise run check-pins` resolves `0.2.0` through tag `v0.2.0` and must pass before any apply."

Standing user rule (2026-10-27), verbatim from the lead: "Deploy whenever possible: live applies need no approval, so include the agents-helmfile values, apply and live smoke tasks in this epic."

Design D16 (staleness refresh 2026-10-29), verbatim: "`ORCH_SCHEDULE_URL` and `ORCH_SCHEDULE_TOKEN` are env of the api main container only, always together, rendered by one `agents-orchestrator.scheduleEnv` helper next to `agents-orchestrator.chatEnv`, never in the shared settings ConfigMap, the migrate init containers or the other components (orchestrator MEMORY 2026-10-28, orch-chat-env-scope: the chart once put `ORCH_CHAT_URL` in the shared ConfigMap with the token on the api only, and every migrate init container crash-looped on a URL without its token)."

Scope (agents-helmfile): `values/agents-orchestrator/common.yaml` (image tag, `schedule.url`, `ORCH_ANY_MCP_PLUGINS_REF` `v0.6.0`, was `v0.5.1` after the slash-commands-from-chat deploy), `values/agents-schedule/common.yaml` (image tag the sha7 of the commit tagged v0.2.0, relay on), `values/agents-web/common.yaml` (image tag), `helmfile.yaml.gotmpl` (orchestrator and web chart versions `0.1.0-main.<sha7>`, schedule chart version `0.2.0`), `tests/test_orchestrator_release.py`, `tests/test_schedule_release.py`, `tests/test_web_release.py`.

Tests no longer accurate (named): `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` (its `PIN`) and `::test_any_mcp_configured_for_new_sessions` (the plugins ref), `tests/test_schedule_release.py::test_release_declared` and `::test_schedule_pin_matches_release` (they pin chart `0.1.0` and image `6cfa955`), `tests/test_web_release.py::test_web_pin_matches_image` (its pin); each asserts the new pin.

#### Acceptance conditions

- ac1: the orchestrator image tag and chart version name the same orchestrator main sha7 (updated) [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: the orchestrator values set schedule.url to http://agents-schedule-api-relay:8001 and no plaintext schedule token, the token coming from the encrypted schedule-token.secrets.yaml listed in the release [evidence: test:tests/test_orchestrator_release.py::test_schedule_relay_wired]
- ac3: new sessions install the orchestrator plugin at v0.6.0 (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac4: the schedule chart version is 0.2.0 and the image tag the sha7 of the commit tagged v0.2.0, and the release still needs its database and the orchestrator (updated) [evidence: test:tests/test_schedule_release.py::test_schedule_pin_matches_release]
- ac5: the schedule release is still declared with its chart, namespace, labels and the orchestrator service token file (updated) [evidence: test:tests/test_schedule_release.py::test_release_declared]
- ac6: the schedule values turn the relay listener on with its hash from relay-token.secrets.yaml and no plaintext hash [evidence: test:tests/test_schedule_release.py::test_relay_listener_enabled]
- ac7: the web image tag and chart version name the same agents-web main sha7 (updated) [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac8: the pinned orchestrator sha7 contains orch-orchestration-tools-pin and orch-chart-schedule-relay, the commit tagged v0.2.0 contains sched-release-0-2-0 and sched-chart-relay-port, and the web sha7 contains web-created-by and web-schedule-owner, each on its repo's main [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha or the tagged commit]
- ac9: the rendered agents-orchestrator release has no ORCH_SCHEDULE_URL in any ConfigMap and puts ORCH_SCHEDULE_URL and ORCH_SCHEDULE_TOKEN together on the api main container only, with one -schedule Secret [evidence: test:tests/test_orchestrator_release.py::test_schedule_url_and_token_render_together]
- ac10: every pinned build, the schedule chart 0.2.0 through tag v0.2.0 included, has all-green check runs [evidence: command:mise run check-pins]
- ac11: the targeted tests, check-pins and lint pass [evidence: command:uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py && mise run check-pins && mise run lint]

#### Files

- `values/agents-orchestrator/common.yaml`
- `values/agents-schedule/common.yaml`
- `values/agents-web/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_orchestrator_release.py`
- `tests/test_schedule_release.py`
- `tests/test_web_release.py`

#### Interfaces

- `values/agents-orchestrator/common.yaml`: `image.tag` the orchestrator main sha7, `schedule.url: http://agents-schedule-api-relay:8001`, `env.ORCH_ANY_MCP_PLUGINS_REF: v0.6.0`; the token from `schedule-token.secrets.yaml` (helmfile-relay-secrets lists it in the release).
- `helmfile.yaml.gotmpl`: agents-orchestrator `version: 0.1.0-main.<sha7>`, agents-web `version: 0.1.0-main.<sha7>`, agents-schedule `version: 0.2.0`.
- `values/agents-schedule/common.yaml`: `image.tag` the sha7 of the commit tagged v0.2.0, relay on (`relay.port: 8001`), hash from `relay-token.secrets.yaml`.
- `tests/test_orchestrator_release.py::test_schedule_url_and_token_render_together` mirrors `::test_chat_url_and_token_render_together` (helmfile template of the release, no ConfigMap carrier, the pair together on `agents-orchestrator-api/api` only, one `-schedule` Secret).

#### Expected outcome

agents-helmfile pins the orchestrator and web main builds and the agents-schedule v0.2.0 release of this epic, the plugins v0.6.0 ref, and wires the relay with the URL and token on the orchestrator api main container only.

#### Steps

- Read each repo's main sha7 carrying the tasks named in ac8 and the commit tagged v0.2.0 (`git rev-parse --short=7 v0.2.0^{commit}` in agents-schedule); confirm CI green on each; stop and report if not.
- Red: update the named tests and add `test_schedule_relay_wired`, `test_relay_listener_enabled` and `test_schedule_url_and_token_render_together`; run `uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py`: they fail.
- Green: values and chart versions; run the task's verify (including `mise run check-pins`, which needs `gh` auth). Quote the summary lines.

#### Notes

- The images and charts are checked in Harbor by orchestration-live-smoke before any apply; this task does not apply.
- Builds on the orchestrator values the slash-commands-from-chat deploy leaves (plugins ref v0.5.1, wrapper agent image 0.4.1 or 0.4.2; live today before it: orchestrator 2d6d722, plugins v0.4.0, agent image 0.3.3): keep the chat and other settings, change only what this task names.
- The schedule image stays a sha7 tag (agents-schedule CI pushes images only on main); Harbor retention pruned sha7 image tags within hours on 2026-10-28, chart versions survive. orchestration-live-smoke checks the image in Harbor right before the apply.
- agents-helmfile has no CI on main (agents-helmfile-ci-test-job is in progress): the local verify, check-pins included, is the evidence.

- 2026-10-29 amended: staleness refresh: schedule pinned by release v0.2.0 (negotiated, user answer pending); plugins v0.6.0; check-pins; schedule pair render test

### S24: orchestration smoke script

- Status: todo
- Files: `scripts/orchestration-smoke.sh`, `scripts/lib/smoke-common.sh`, `mise.toml`, `README.md`, `tests/test_orchestration_smoke_script.py`, `tests/test_mise_tasks.py`
- Verify: `uv run pytest tests/test_orchestration_smoke_script.py tests/test_mise_tasks.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D18, verbatim: "`scripts/orchestration-smoke.sh` (mise task `orchestration-smoke`), separate from `scripts/smoke.sh`. It creates a throwaway alone session with `session_orchestration` true through the public API, posts it a user message (main port, origin `user`) that keeps the turn open (the agent runs a bounded `sleep`), waits until that turn is current, and from the session's pod (its own `ORCH_AGENT_*` env, never printed) calls the orchestration routes: `me`, presets list, preset create and update, a refused `privilege_escalation` preset, session create from the own preset, overview, session delete, schedule create (disabled, `0 3 * * *`), update, runs and delete, preset delete, and the actions list; after the turn ends it checks one write is refused `not_user_turn`. Each wait has its own deadline; a trap deletes everything the script created through the public API on success, failure and interrupt."

Retro proposals, verbatim: "for smoke-script tasks the reviewer checks every timeout or deadline against the AC and the MEMORY claim" and "any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it."

Scope (agents-helmfile): new `scripts/orchestration-smoke.sh` (env `RELEASE`, `NAMESPACE`, `ORCH_SMOKE_PRESET` or the default preset as the base spec, `ORCH_SMOKE_TIMEOUT_S` per wait, `ORCH_SMOKE_HOLD_S` for the held turn, `SMOKE_LOCAL_PORT`), new mise task `orchestration-smoke`, README (names the task and what it creates and deletes), `tests/test_orchestration_smoke_script.py` with kubectl and curl fakes, `tests/test_mise_tasks.py`.

#### Acceptance conditions

- ac1: against fakes the script creates the flagged throwaway session, holds a user turn, runs every D18 step in order from the session's pod, prints each step's status and the ids, and exits 0 [evidence: test:tests/test_orchestration_smoke_script.py::test_happy_path]
- ac2: the privilege_escalation preset and the write after the held turn ends must be refused with those codes, and any other answer exits 1 naming the step [evidence: test:tests/test_orchestration_smoke_script.py::test_refusals_required]
- ac3: the actions list must show an ok row for every write step and the privilege_escalation row, else exit 1 [evidence: test:tests/test_orchestration_smoke_script.py::test_actions_checked]
- ac4: every wait (pod Ready, turn current, turn ended, each delete) has its own ORCH_SMOKE_TIMEOUT_S deadline, and a timeout exits 1 naming the step [evidence: test:tests/test_orchestration_smoke_script.py::test_each_wait_has_its_own_deadline]
- ac5: the trap deletes every session, preset and schedule the script created, and only those, through the public API on success, failure and interrupt, kills its port-forwards, and a stale port-forward on its port is killed first [evidence: test:tests/test_orchestration_smoke_script.py::test_cleanup_only_own_objects]
- ac6: no token or ORCH_AGENT_* value is printed [evidence: test:tests/test_orchestration_smoke_script.py::test_no_secrets_printed]
- ac7: the fakes replay bodies with the shapes of the orchestrator README Orchestration section and the committed agents-schedule openapi-relay.json [evidence: judgement:reviewer compares the fake bodies with the agents-orchestrator README and agents-schedule openapi-relay.json on their main]
- ac8: the mise task orchestration-smoke runs the script and README names it [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- ac9: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_orchestration_smoke_script.py tests/test_mise_tasks.py && mise run lint]

#### Files

- `scripts/orchestration-smoke.sh`
- `scripts/lib/smoke-common.sh`
- `mise.toml`
- `README.md`
- `tests/test_orchestration_smoke_script.py`
- `tests/test_mise_tasks.py`

#### Interfaces

- `mise run orchestration-smoke` (env above); output one `orchestration-smoke: <step> <status> <id>` line per step, ending `orchestration-smoke: OK`.
- Throwaway names: `orch-smoke-<ts>` (session and caller preset base), `orch-smoke-<ts>-p` (owned preset), `orch-smoke-<ts>-s` (owned session), `orch-smoke-<ts>` (schedule, disabled).

#### Expected outcome

One command proves the orchestration tools live end to end and leaves nothing behind but audit rows.

#### Steps

- Red: write `tests/test_orchestration_smoke_script.py` (fakebin kubectl and curl, as `tests/test_smoke_script.py` does); run it: fails.
- Green: the script, mise task, README; run the task's verify. Quote the summary line.

#### Notes

- Source `scripts/lib/smoke-common.sh` like `scripts/smoke.sh` and `scripts/chat-smoke.sh` do (`SMOKE_LOG_PREFIX`, `log`, `fail`, `now`, `agent_call` for the pod exec with the pod's own `ORCH_AGENT_*` env, `stale_pids`, `kill_stale_port_forward`); extend the lib only for a helper both other scripts could use, and keep `tests/test_smoke_script.py` and `tests/test_chat_smoke_script.py` green.
- `tests/test_smoke_script.py` and `tests/test_chat_smoke_script.py` are the fakebin patterns for the new test.
- The held turn: the user message asks the agent to run `sleep $ORCH_SMOKE_HOLD_S` and then reply ok; the script waits until the message's turn is the agent's current turn before the first write, and until it ends before the not_user_turn check.
- The owned session is created from the owned preset (alone, 1 replica) and deleted before the owned preset.
- Never print `ORCH_AGENT_TOKEN`; read it inside the pod exec only.

### S25: orchestration live smoke

- Status: todo
- Files: `MEMORY.md`
- Verify: `mise run lint && grep -q orchestration-smoke MEMORY.md`
- Verified head: none

#### Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Standing user rule (2026-10-27), verbatim from the lead: "Deploy whenever possible: live applies need no approval, so include the agents-helmfile values, apply and live smoke tasks in this epic."

Design D17, verbatim: "Every image tag and chart version is checked in Harbor before any apply (retro proposal). Apply order, `--selector` per release, `mise run diff` reviewed before each (`mise run apply` runs lint, test and check-pins first): agents-schedule (its migration 0002 runs in the init container; the relay listener comes up), agents-orchestrator (its migration 0013; the new plugins ref changes the rendered config hash, and the OnDelete rollout reconciler replaces each agent pod once it is idle, one per session, leaders last, mx-5 included: one line to mx-5 first), agents-web."

Design D19, verbatim: "After the deploy the orchestrator session sends mx-5 one line: flag mx-5's preset in the UI and recreate mx-5 to get the tools; it does not edit mx-5's preset or recreate mx-5 itself (recreating drops mx-5's context). The live smoke probes and records mx-5's preset name and whether the owner DM is bound to mx-5 (facts the repos do not hold)."

Open questions Q2 and Q8 (pending; the plan follows the recommended answers), verbatim: "Grant mx-5 by flagging its preset in the UI and recreating the session (spec stays immutable)?" recommended "yes"; "After the deploy you flag mx-5's preset in the UI and recreate mx-5 yourself (the orchestrator sends mx-5 one line and never edits mx-5's preset or recreates it, since that drops mx-5's context), and the epic closes on the throwaway-session live smoke without waiting for the grant?" recommended "yes".

Scope: run by the orchestrator session (live cluster, SOPS key); the only file written is agents-helmfile `MEMORY.md`.

#### Acceptance conditions

- ac1: (orchestrator session) every new image tag and chart version (orchestrator, schedule, web) exists in Harbor before any apply [evidence: judgement:orchestrator records the registry check of each tag and chart version in the task Notes]
- ac2: (orchestrator session) after the applies in D17 order helmfile reports no pending change [evidence: command:mise run diff]
- ac3: (orchestrator session) the regular smoke passes on the new deployment [evidence: judgement:orchestrator quotes the final line of mise run smoke with exit 0 in the task Notes]
- ac4: (orchestrator session) mise run orchestration-smoke exits 0 and a GET of sessions, presets and schedules afterwards shows none of its objects [evidence: judgement:orchestrator quotes the step lines, the final OK line and the empty leftover check in the task Notes]
- ac5: (orchestrator session) mx-5's preset name and whether the owner DM is bound to mx-5 are probed live and recorded [evidence: judgement:orchestrator quotes GET /api/v1/sessions for mx-5 and the owner DM binding from the connector rooms API in the task Notes]
- ac6: (orchestrator session) mx-5 got one line before the orchestrator apply and one line after the smoke with the grant step of D19, and the epic does not wait for the grant [evidence: judgement:orchestrator quotes both message ids in the task Notes]
- ac7: agents-helmfile MEMORY.md records the live results, dated: the pins, the migrations applied, the orchestration-smoke result, mx-5's preset name and the owner DM binding [evidence: command:grep -q "orchestration-smoke" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

- Live releases: agents-schedule, agents-orchestrator, agents-web in namespace agents.

#### Expected outcome

The orchestration tools are live, proven by the smoke, and mx-5 knows how to get them.

#### Steps

- Check every tag in Harbor (`crane digest` or `helm show chart`); stop and report a missing one.
- `mise run diff -- --selector name=agents-schedule`, review, `mise run apply -- --selector name=agents-schedule` (apply runs lint, test and check-pins first); wait for the api and worker Ready (the init container ran migration 0002).
- Send mx-5 one line, then the same for agents-orchestrator; then agents-web.
- `mise run diff` (expect no change), `mise run smoke`, `mise run orchestration-smoke`; probe mx-5's preset and the owner DM binding; message mx-5 the grant line; write MEMORY.md.

#### Notes

- Apply from the pod per the deploy procedure (kubeconfig from the service account, a short GNUPGHOME under /tmp for SOPS, the regcred Harbor helm login, the `agents-helmfile-apply` lease held only during the apply, a `--selector` per release).
- The orchestrator apply (migration 0013, plugins ref v0.6.0) changes the agent config hash; the OnDelete rollout reconciler replaces each agent pod once it is idle, one per session, leaders last. An idle leader with a running subagent loses it on replacement (hive-decoupling retro): check the busy and subagent state of the live leaders before the orchestrator apply.
- Live before this epic: whatever the slash-commands-from-chat deploy leaves (plugins v0.5.1, wrapper agent image 0.4.1 or 0.4.2); today orchestrator 2d6d722, plugins v0.4.0, agent image 0.3.3. The agent image does not change in this epic.
- The agents-schedule image is a sha7 tag (pruned by Harbor retention within hours on 2026-10-28; chart versions survive): check it right before the schedule apply, not only at the start.
- helmfile MEMORY gotcha: a new or changed service Secret does not restart the orchestrator api pods; when the relay answers schedules_unconfigured or an upstream 401, run `kubectl rollout restart deploy/agents-orchestrator-api` (least destructive first), then rerun the smoke.
- Live and irreversible operations are listed in design.md (applies, both migrations, the relay token, the smoke objects). Standing rule: deploy whenever possible; live applies need no approval.
- Live apply and smoke tasks have run 3-4x over the minutes seed in past epics (retro); several runs are likely.
- Never edit mx-5's preset or recreate mx-5 (D19).

- 2026-10-29 amended: staleness refresh: D17 apply order cites check-pins, migrations 0002 and 0013 and the idle-only OnDelete rollout

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
