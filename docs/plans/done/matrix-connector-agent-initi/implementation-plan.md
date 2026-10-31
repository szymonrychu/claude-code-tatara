# matrix connector agent-initiated and follow-up messages implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: helmfile-smoke-helpers

- Status: done
- Files: `scripts/chat-smoke.sh`, `scripts/smoke.sh`, `scripts/lib/smoke-common.sh`, `tests/test_chat_smoke_script.py`, `tests/test_smoke_script.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_chat_smoke_script.py`
- Verified head: 9233d08a0a5dfd2d7f98469d28347a98b1ff4bbd

#### Requirement

Epic review findings for agents-helmfile, my call to fix:
1. `scripts/chat-smoke.sh:93`: `< "$d/cmdline" 2> /dev/null` opens the file before stderr is silenced, so a process that exits during the scan prints `/proc/<pid>/cmdline: No such file or directory` (seen live 2026-10-28). Put the stderr redirect first; a test runs the scan against a vanished pid and asserts no output on stderr.
2. Scope audit duplicate (.scratchpad/matrix/review/scope-audit.md): the in-pod `agent_py` snippet and `agent_call`, plus the log/fail/cleanup and stale port-forward helpers, are copied between `scripts/chat-smoke.sh` and `scripts/smoke.sh`. Move them into one sourced script (for example `scripts/lib/smoke-common.sh`) used by both, without changing either script's output or behaviour (their existing tests stay green unchanged).
Test first.

#### Acceptance conditions

- AC1: the stale port-forward scan prints nothing on stderr for a vanished pid [evidence: test:tests/test_chat_smoke_script.py::test_stale_scan_silent_for_vanished_pid]
- AC2: chat-smoke.sh and smoke.sh source one shared helper file and define no copy of agent_call [evidence: test:tests/test_smoke_script.py::test_smoke_scripts_share_helpers]
- AC3: the existing smoke and chat-smoke script tests pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_chat_smoke_script.py]

#### Files

- `scripts/chat-smoke.sh`
- `scripts/smoke.sh`
- `scripts/lib/smoke-common.sh`
- `tests/test_chat_smoke_script.py`
- `tests/test_smoke_script.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Read every file the step touches, write the AC tests first and run the task verify: the new tests fail for the expected reason.
- Implement the smallest change that passes, rerun the verify and `mise run lint`: green.
- Commit, push, open or update the PR and quote its CI result per job.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S2: mxc agent listener

- Status: done
- Files: `src/agents_matrix_connector/settings.py`, `src/agents_matrix_connector/cli.py`, `src/agents_matrix_connector/api/agent.py`, `README.md`, `tests/test_settings.py`, `tests/test_cli.py`, `tests/test_agent_gate.py`
- Verify: `uv run pytest tests/test_settings.py tests/test_agent_gate.py tests/test_cli.py && mise run lint`
- Verified head: 221c793e1b2354ea68e3f700931ad5355eafb671

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D3, verbatim: "`agents-matrix-connector api` binds a second listener, `MATRIX_AGENT_PORT` (default 8001), serving only `/chat/v1/*`, `/healthz` and `/readyz`, behind a bearer gate: the sha256 hex of the presented token must equal `MATRIX_AGENT_TOKEN_SHA256` (constant-time compare, mirroring the orchestrator's `api/service_auth.py:ServiceGate`). With `MATRIX_AGENT_TOKEN_SHA256` empty the listener is not bound (my call). The token never reaches a log line or an error body."

Design D3, verbatim (probe): "The agent listener therefore skips the source allowlist and authenticates by token alone, exactly like the orchestrator's agent and service ports (`api/allowlist.py:SourceAllowlist`, "the agent and service ports authenticate on their own and are skipped"). The UI app and its allowlist are unchanged."

Design D5, verbatim (rate setting): "Rate: at most `MATRIX_AGENT_RATE_PER_MINUTE` (default 20, gate question Q5) sends (messages and reactions together) per session in the last 60 s".

Open question Q5 (pending gate), verbatim: "Per-session limit of 20 messages a minute (my call, pending gate)?" recommended "yes".

Scope (agents-matrix-connector): settings `MATRIX_AGENT_PORT` (int, default 8001, must differ from `MATRIX_HTTP_PORT`), `MATRIX_AGENT_TOKEN_SHA256` (empty, or 64 lowercase hex characters; never in repr), `MATRIX_AGENT_RATE_PER_MINUTE` (int >= 1, default 20); new module `api/agent.py` with the bearer gate and `create_agent_app(pool, settings)` serving `/healthz`, `/readyz` and a `/chat/v1` router (empty here; the routes are task mxc-agent-routes); `cli.py` runs the agent app on its own listener next to the UI app when the hash is set; README Configuration rows for the three variables. The routes, the chart and the helmfile are later tasks.

#### Acceptance conditions

- ac1: the three settings parse with their defaults and bounds, a malformed hash or an agent port equal to the http port is a settings error naming the variable, and the hash never appears in repr [evidence: test:tests/test_settings.py::test_agent_listener_settings]
- ac2: the README Configuration section lists every MATRIX_ variable, the three new ones included [evidence: test:tests/test_settings.py::test_readme_lists_every_variable]
- ac3: the gate answers 401 unauthorized with WWW-Authenticate Bearer for a missing, malformed or wrong bearer and passes the token whose sha256 matches; the token and hash never appear in a log line or response body [evidence: test:tests/test_agent_gate.py::test_gate_accepts_only_the_hashed_token]
- ac4: the agent app serves only /chat/v1/*, /healthz and /readyz (anything else 404 not_found) and admits a non-loopback peer that presents the token, so no source allowlist applies to it [evidence: test:tests/test_agent_gate.py::test_agent_app_paths_and_no_source_allowlist]
- ac5: the UI app still refuses a non-loopback peer with 403 forbidden and serves no /chat/v1 path [evidence: test:tests/test_agent_gate.py::test_ui_app_keeps_source_allowlist]
- ac6: `agents-matrix-connector api` serves the agent app on MATRIX_AGENT_PORT only when MATRIX_AGENT_TOKEN_SHA256 is set, and only the UI app otherwise [evidence: test:tests/test_cli.py::test_api_binds_agent_listener_only_with_hash]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_settings.py tests/test_agent_gate.py tests/test_cli.py && mise run lint]

#### Files

- `src/agents_matrix_connector/settings.py`
- `src/agents_matrix_connector/cli.py`
- `src/agents_matrix_connector/api/agent.py`
- `README.md`
- `tests/test_settings.py`
- `tests/test_cli.py`
- `tests/test_agent_gate.py`

#### Interfaces

- `settings.py:ConnectorSettings` gains `agent_port: int = 8001`, `agent_token_sha256: SecretStr` or a repr-hidden str (empty default), `agent_rate_per_minute: int = Field(20, ge=1)`.
- `api/agent.py` (new): `AgentGate(app, token_sha256)` ASGI middleware; `create_agent_app(pool, settings) -> FastAPI` with `openapi_url="/chat/v1/openapi.json"`, docs off, the `{error: {code, message}}` handlers of `api/app.py`, and an `APIRouter(prefix="/chat/v1")` that mxc-agent-routes fills.
- `cli.py:_cmd_api` serves both apps until `stop` (two `serve_asgi` calls or one server per socket; left to the builder).

#### Expected outcome

The api process can expose a token-protected agent listener that the orchestrator reaches directly, without opening the SSO-protected UI app to the pod network.

#### Steps

- Red: write `tests/test_agent_gate.py`, add `test_agent_listener_settings` and `test_api_binds_agent_listener_only_with_hash`; run `uv run pytest tests/test_settings.py tests/test_agent_gate.py tests/test_cli.py`: the new tests fail.
- Green: settings, `api/agent.py`, `cli.py`, README rows; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Mirror `agents_orchestrator/api/service_auth.py:ServiceGate`: sha256 hex of the presented bearer compared with `hmac.compare_digest`; one shared 401 message.
- Build fake tokens at runtime in tests (for example `secrets.token_hex(32)`), never a literal that a secret scanner flags (retro proposal, GitGuardian).
- `/healthz` and `/readyz` on the agent app stay open (probes), like the orchestrator's `EXEMPT_PATHS`.
- The UI app's `SourceAllowlist` and `MATRIX_API_ALLOWED_CIDRS` stay exactly as they are.
- Non-DB tests: use `httpx.ASGITransport(app=..., client=("10.0.0.5", 1234))` to set the peer.

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S3: mxc matrix send event

- Status: done
- Files: `src/agents_matrix_connector/matrix.py`, `tests/test_matrix_client.py`
- Verify: `uv run pytest tests/test_matrix_client.py && mise run lint`
- Verified head: 1153021ade112e9725cba092b91a8fc82e2b493a

#### Requirement

README Goal, verbatim: "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."

Design D8, verbatim: "Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id": E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676; removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation", "event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is the one PUT; `send_text` becomes a call of it."

Interrogate verdict Act on 5 (tracker test spy) moved `tests/test_tracker.py` into mxc-bot-sends-delivery; to keep that task within 8 files, the `MatrixClient.send_event` part of it is this task (planner, 2026-10-27).

Scope (agents-matrix-connector): `matrix.py` (`MatrixClient.send_event`; `send_text` calls it), `tests/test_matrix_client.py`. The callers (`Tracker._send_pending`, the sender) are mxc-bot-sends-delivery.

#### Acceptance conditions

- ac1: `MatrixClient.send_event` PUTs the given event type, txn id and content and returns the event id, and `send_text` sends the same request it sent before through it [evidence: test:tests/test_matrix_client.py::test_send_event_type_and_content]
- ac2: send_event maps homeserver errors to the existing MatrixError taxonomy (MatrixUnavailable, MatrixAuthError, MatrixForbidden, MatrixNotFound) exactly as send_text did [evidence: test:tests/test_matrix_client.py::test_send_event_errors]
- ac3: the existing Matrix client tests pass unchanged [evidence: command:uv run pytest tests/test_matrix_client.py -k "not send_event"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_matrix_client.py && mise run lint]

#### Files

- `src/agents_matrix_connector/matrix.py`
- `tests/test_matrix_client.py`

#### Interfaces

- `matrix.py:MatrixClient.send_event(room_id: str, event_type: str, txn_id: str, content: dict) -> str`: `PUT /_matrix/client/v3/rooms/{room_id}/send/{event_type}/{txn_id}` through `_request`, returning the event id.
- `send_text(room_id, txn_id, body)` calls `send_event(room_id, "m.room.message", txn_id, {"msgtype": "m.text", "body": body})`; its signature and callers are unchanged.

#### Expected outcome

The bot has one PUT for every event type, so quoted replies and reactions can be sent with the same error handling and txn-id dedup as replies today.

#### Steps

- Red: add `test_send_event_type_and_content` and `test_send_event_errors` to `tests/test_matrix_client.py`; run `uv run pytest tests/test_matrix_client.py`: they fail (no method).
- Green: `send_event`, `send_text` through it; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Reuse `MatrixClient._request` and its error taxonomy; build the path with `_path("rooms", room_id, "send", event_type, txn_id)` as `send_text` does today.
- `tests/test_matrix_client.py` runs locally (no DB).

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S4: mxc-outbound-limits

- Status: done
- Files: `src/agents_matrix_connector/api/agent.py`, `src/agents_matrix_connector/settings.py`, `tests/test_api_agent.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_api_agent.py -q`
- Verified head: 5c8583de1edb10a25375225ef45f935f1234da73

#### Requirement

Epic review findings (security review .scratchpad/matrix/review/security.md MEDIUM 2 and LOW 2/3), my call to fix: outbound messages reach a real Messenger user, so abuse limits must hold.
1. `api/agent.py` (about lines 48-51, 293-301): the per-session rate check counts recent sends and inserts in separate statements, so parallel requests exceed `agent_rate_per_minute`; and one 16000-char send splits into 4 chunks, so a session can push about 80 Messenger messages a minute. Make the check and the insert atomic per session (for example a transaction-scoped advisory lock keyed on the session id, or one guarded INSERT ... SELECT), and add a per-room cap on outbound chunks per hour (a new setting with a conservative default, documented), counted in chunks, enforced atomically with the per-session limit; a refused send answers 429 with a distinct error code.
2. `api/agent.py` (about 208-225): the `X-Orch-Slug` header is stored unvalidated and unbounded; validate it as a session slug (the orchestrator's slug rules, length cap) and answer 400 otherwise.
3. `api/agent.py` (about 239-247): an `m<n>` reference to an inbound message of another room answers 409 when the room is bound elsewhere and 422 when unknown, which lets a session probe other rooms; answer the same status and error code for both.
Test first. Record the limits and their defaults in MEMORY.md with the date and why.

#### Acceptance conditions

- AC1: parallel sends from one session never exceed the per-minute limit [evidence: test:tests/test_api_agent.py::test_parallel_sends_respect_rate_limit]
- AC2: outbound chunks to one room are capped per hour and the refusal is a 429 with its own error code [evidence: test:tests/test_api_agent.py::test_room_hourly_chunk_cap]
- AC3: an invalid or oversized X-Orch-Slug answers 400 [evidence: test:tests/test_api_agent.py::test_invalid_slug_header_rejected]
- AC4: a reference into another room answers the same status and code whether the room is bound elsewhere or the id is unknown [evidence: test:tests/test_api_agent.py::test_foreign_reference_errors_are_uniform]
- AC5: MEMORY.md records the outbound limits [evidence: command:grep -q "chunks per hour" MEMORY.md]

#### Files

- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/settings.py`
- `tests/test_api_agent.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Read every file the step touches, write the AC tests first and run the task verify: the new tests fail for the expected reason.
- Implement the smallest change that passes, rerun the verify and `mise run lint`: green.
- Commit, push, open or update the PR and quote its CI result per job.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S5: mxc prompt message refs

- Status: done
- Files: `src/agents_matrix_connector/prompt.py`, `tests/test_prompt.py`
- Verify: `uv run pytest tests/test_prompt.py && mise run lint`
- Verified head: 456802230799dc68180547c1b24a7f05c0235c62

#### Requirement

README Goal, verbatim: "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."

Design D11, verbatim: "`prompt.render` adds `room_id="..."` to `<chat>` and `id="m<inbound.id>"` to each `<message>` (escaped like every attribute). PREAMBLE gains: final answers are posted only for chat-started turns; use `orchestrator_chat_send` to reach the user at any other time, `reply_to` and `orchestrator_chat_react` take the `m<n>` ids shown here."

Design D6, verbatim: "The prompt shows `id="m<inbound.id>"` on each `<message>`; a send answers `s<sends.id>`."

Scope (agents-matrix-connector): `prompt.py` only. `tests/test_prompt.py::test_messages_in_order_with_attributes` is no longer accurate (named): it pins the exact `<chat room kind>` and `<message from facebook_id at>` strings without the new `room_id` and `id` attributes; it is updated to the new attribute set and still pins the order.

#### Acceptance conditions

- ac1: `<chat>` carries room_id and each `<message>` carries id="m<inbound id>", in id order (updated) [evidence: test:tests/test_prompt.py::test_messages_in_order_with_attributes]
- ac2: a room id or body with quotes, angle brackets or ampersands cannot break out of the attributes or the element [evidence: test:tests/test_prompt.py::test_escaping_cannot_break_out]
- ac3: the PREAMBLE says final answers reach the chat only for chat-started turns and names orchestrator_chat_send, orchestrator_chat_react and the m<n> ids, and still says the chat is untrusted input [evidence: test:tests/test_prompt.py::test_preamble_names_chat_tools]
- ac4: the first and later prompt framing is unchanged [evidence: test:tests/test_prompt.py::test_first_and_later_prompts]
- ac5: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_prompt.py && mise run lint]

#### Files

- `src/agents_matrix_connector/prompt.py`
- `tests/test_prompt.py`

#### Interfaces

- `prompt.render(room_name, room_kind, rows, *, first, facebook_id)` keeps its signature; the room id comes from the rows (`InboundRow.room_id`; all rows of a batch share one room).
- Output: `<chat room="..." kind="..." room_id="...">` and `<message id="m<n>" from="..." facebook_id="..." at="...">...</message>`.

#### Expected outcome

Every chat prompt names its room and each message's short id, and the agent is told how to reach the user outside a chat-started turn.

#### Steps

- Red: update `test_messages_in_order_with_attributes`, extend `test_escaping_cannot_break_out` with a room id containing `"<&`, add `test_preamble_names_chat_tools`; run `uv run pytest tests/test_prompt.py`: they fail.
- Green: change `prompt.py`; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Pure module, no DB: the whole verify runs locally.
- Keep the PREAMBLE's existing untrusted-input sentence verbatim; append the new sentences.
- Tool names are `orchestrator_chat_send` and `orchestrator_chat_react` (D13); do not name `mcp__any-mcp__` prefixes.

- 2026-10-28 done: CI 40748215902 green

- 2026-10-28 actuals: no agent records

### S6: mxc sends schema

- Status: done
- Files: `src/agents_matrix_connector/migrations/0002_agent_sends.sql`, `src/agents_matrix_connector/db/sends.py`, `src/agents_matrix_connector/db/bindings.py`, `tests/test_schema.py`, `tests/test_sends_repo.py`, `tests/test_bindings_repo.py`
- Verify: `uv run pytest tests/test_schema.py tests/test_sends_repo.py tests/test_bindings_repo.py && mise run lint`
- Verified head: bb794edaf29ff524d8c895c943cdacb03d287f75

#### Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."
- "A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Design D7, verbatim (the schema part): "`sends` (new queue, COMMENT `queue: inserted by api, transitions by bot worker`): `id bigserial`, `session_id uuid NOT NULL`, `slug text NULL`, `kind` CHECK `message|reaction`, `room_id text NOT NULL`, `text text NULL`, `key text NULL`, `reply_to text NULL` (the `m<n>`/`s<n>` the agent gave), `ref_event_id text NULL`, `event_id text NULL`, `status` CHECK `queued|sending|sent|failed|refused`, `reason text NULL`, `created_at`, `claimed_at`, `sent_at`; indexes for queued rows, per session and time (rate), and per room and status. `outbound` keeps the bot worker as its only writer and gains `send_id bigint NULL`, `event_type text NOT NULL DEFAULT 'm.room.message'`, `relates_to jsonb NULL`; its kind CHECK gains `agent` and `reaction`. `runs` gets an index on `(session_id, room_id)` for the "other run of this session in this room" check (D9 PREAMBLE), and `runs.preset_id` drops NOT NULL with a new CHECK `kind <> 'first' OR preset_id IS NOT NULL` (D9). `room_settings` gains `agents_may_initiate`. The same migration creates `room_bindings` with its two partial unique indexes and the backfill (D9)."

Design D9, verbatim (storage): "Storage: the uniqueness lives in the connector's own database. Migration 0002 creates `room_bindings` (COMMENT `writer: bot worker`): `id bigserial`, `room_id text NOT NULL`, `session_id uuid NULL`, `slug text NULL`, `origin` CHECK `inbound|agent`, `run_id bigint NULL` (the first run that bound it), `send_id bigint NULL` (the send that bound it), `created_at`, `released_at timestamptz NULL`, `release_reason text NULL`. A binding is active while `released_at` is NULL. A partial unique index on `room_id WHERE released_at IS NULL` and one on `session_id WHERE released_at IS NULL AND session_id IS NOT NULL` make two active bindings of one room, or of one session, impossible; CHECKs: an `inbound` binding has a `run_id`, an `agent` binding a `session_id` and a `send_id`. The bot worker (its worker and sender steps, one bot process) is the only writer; the api only reads it. A release is a guarded UPDATE (`released_at IS NULL`, plus the expected session); released rows stay as history and are pruned with the daily retention (my call). `runs.latest_session` is removed: the binding replaces it."

Design D9, verbatim (backfill): "Backfill (my call, gate question Q12): 0002 inserts one active `inbound` binding per room from its newest run that has a session (its session id, slug and run id), or a reservation for a room whose newest run is an in-progress first run without a session yet, so existing chats keep their session. A session that is the newest of several rooms (not expected: the worker creates one `mx-` session per room) binds only the room of its newest run. A backfilled binding of a session already deleted is released by the first binding sweep (below)."

Design D9, verbatim (the binding writes this repository serves): "the worker's claim transaction of a `first` run reserves the room (an active `inbound` binding with the run id and no session yet) [...] when the run stores its session id (`_RoomRunStore.set_session`), the same transaction fills the binding's session id and slug (idempotent for a retried dispatch). A first run that finishes without a session [...] releases its reservation in its finish transaction (`run_failed`)." "the bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active `agent` binding (session id and slug of the send, its send id) when the room is still unbound, still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never makes a second binding."

Design D4, verbatim (binding): "Bound means an active `room_bindings` row pairing R and S (D9); nothing else binds (no `runs` or `sends` row is read as a binding, and the api writes no binding). A room reserved by another session's first run in progress (an active binding without a session yet, D9) counts as bound to another session. `room_settings.agents_may_initiate boolean NOT NULL DEFAULT false` is new; its writer stays the api."

Design D6, verbatim (resolution): "The connector resolves `m<n>` to the inbound row's `event_id` and `s<n>` to the send's delivered `event_id` (first chunk of a message, the reaction event of a reaction)."

Design D5, verbatim (rate count): "at most `MATRIX_AGENT_RATE_PER_MINUTE` (default 20, gate question Q5) sends (messages and reactions together) per session in the last 60 s, counted on `sends` rows of any status".

Design D7, verbatim (retention): "`sends` rows that ended and released `room_bindings` rows are pruned with the existing daily retention."

Design D9, verbatim (preset): "Migration 0002 drops NOT NULL on `runs.preset_id` and adds CHECK `kind <> 'first' OR preset_id IS NOT NULL` (my call: an explicit "no preset" rather than a sentinel uuid; a first run still always has one, and no NOT NULL violation is possible)."

Open question Q12 (pending), verbatim: "Migration 0002 (approved, no down step) also creates room_bindings and backfills one active binding per room from its newest run that has a session, or reserves the room for an in-progress first run without one, so existing chats keep their session; bindings of sessions already deleted are released by the bot's first binding sweep. Approve that backfill as part of migration 0002?" recommended "yes".

Scope (agents-matrix-connector): migration `0002_agent_sends.sql`, the repository module `db/sends.py` (insert, claim, guarded transitions, rate count, reference resolution, prune) and the new repository module `db/bindings.py` (reserve, fill, bind for a send, release, active lookups by room and by session, the active list for the sweep, prune of released rows). The api routes, the bot step and the routing change are later tasks.

`tests/test_schema.py::test_writer_comments` and `tests/test_schema.py::test_check_constraints` are no longer accurate once the new tables and the widened `outbound.kind` CHECK exist (named): they list every table's writer and the accepted kinds; both are extended to the new tables and kinds, nothing they assert today is removed.

#### Acceptance conditions

- ac1: migration 0002 creates `sends` with the D7 columns and its COMMENT names the api as inserter and the bot worker as the only mover, and `room_bindings` with the D9 columns and COMMENT `writer: bot worker` (updated) [evidence: test:tests/test_schema.py::test_writer_comments]
- ac2: the `sends.kind` and `sends.status` CHECKs and the `room_bindings.origin` CHECK refuse other values, and `outbound.kind` accepts agent and reaction besides reply and notice (updated) [evidence: test:tests/test_schema.py::test_check_constraints]
- ac3: applying the migrations twice changes nothing [evidence: test:tests/test_schema.py::test_migration_idempotent]
- ac4: `room_settings.agents_may_initiate` is NOT NULL with default false; `outbound` has `send_id`, `event_type` defaulting to m.room.message and `relates_to` jsonb; the runs `(session_id, room_id)` index exists [evidence: test:tests/test_schema.py::test_agent_sends_columns]
- ac5: a queued send is claimed once (queued to sending), and sent, failed and refused are reached only from sending, every move through `agents_common.db.queue.transition`; a second claim or a move from the wrong status changes nothing [evidence: test:tests/test_sends_repo.py::test_guarded_transitions]
- ac6: the database refuses a second active binding of one room and a second active binding of one session, while released bindings of that room or session do not count; an inbound binding without a run id and an agent binding without a session id or a send id are refused [evidence: test:tests/test_bindings_repo.py::test_one_active_binding_per_room_and_session]
- ac7: reserving a room for a first run, filling its session id and slug (twice with the same id is a no-op) and releasing it with a reason work through guarded updates; a reservation of an already bound room, a fill of a released binding and a second release change nothing [evidence: test:tests/test_bindings_repo.py::test_reserve_fill_release]
- ac8: binding a room for a send answers bound for an unbound room and a session bound to no room, already for the session's own room, room_bound for a room bound to or reserved by another session and session_bound for a session bound elsewhere, writing a row only in the first case [evidence: test:tests/test_bindings_repo.py::test_bind_for_send_outcomes]
- ac9: the active binding of a room and of a session, and the list of active bindings with a session, are read back exactly; no runs or sends row counts as a binding [evidence: test:tests/test_bindings_repo.py::test_active_lookups]
- ac10: applying 0002 over a 0001 database binds each room to the session of its newest run that has one, reserves a room whose newest run is an in-progress first run without a session, binds a session newest in two rooms only to the room of its newest run, and binds nothing for a room without runs [evidence: test:tests/test_schema.py::test_binding_backfill]
- ac11: the rate count counts a session's sends of any status and kind created in the last 60 s and no older ones [evidence: test:tests/test_sends_repo.py::test_rate_count_window]
- ac12: `m<n>` resolves to that inbound row's event_id and room; `s<n>` resolves to that send's room, session, kind, status and event_id; an unknown or malformed reference resolves to nothing [evidence: test:tests/test_sends_repo.py::test_resolve_references]
- ac13: prune deletes sent, failed and refused sends older than the cutoff and keeps queued and sending ones [evidence: test:tests/test_sends_repo.py::test_prune_ended_sends]
- ac14: the bindings prune deletes released bindings released before the cutoff and keeps active ones and newer released ones [evidence: test:tests/test_bindings_repo.py::test_prune_released_bindings]
- ac15: `runs.preset_id` accepts NULL for a follow run and the CHECK refuses a first run without a preset [evidence: test:tests/test_schema.py::test_follow_run_preset_nullable]
- ac16: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_schema.py tests/test_sends_repo.py tests/test_bindings_repo.py && mise run lint]

#### Files

- `src/agents_matrix_connector/migrations/0002_agent_sends.sql`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/bindings.py`
- `tests/test_schema.py`
- `tests/test_sends_repo.py`
- `tests/test_bindings_repo.py`

#### Interfaces

- `src/agents_matrix_connector/migrations/0002_agent_sends.sql`: table `sends` (D7 columns), `outbound` new columns, widened kind CHECK, `room_settings.agents_may_initiate`, indexes, `runs.preset_id` DROP NOT NULL plus CHECK `kind <> 'first' OR preset_id IS NOT NULL`; table `room_bindings` (D9 columns, origin CHECK, the inbound/agent CHECKs, partial unique indexes `(room_id) WHERE released_at IS NULL` and `(session_id) WHERE released_at IS NULL AND session_id IS NOT NULL`) and its backfill; COMMENTs on `sends` and `room_bindings`.
- `src/agents_matrix_connector/db/sends.py` (new): a frozen `SendRow` dataclass; `insert(conn, *, session_id, slug, kind, room_id, text, key, reply_to, ref_event_id) -> int`; `claim_queued(conn) -> list[SendRow]` (queued to sending, sets `claimed_at`); `mark_sent(conn, id, event_id)`, `mark_failed(conn, id, reason)`, `mark_refused(conn, id, reason)` through `queue.transition`; `count_recent(conn, session_id, seconds) -> int`; `resolve(conn, ref) -> Ref | None` for `m<n>`/`s<n>`; `get(conn, id) -> SendRow | None`; `prune(conn, older_than) -> int`. No binding query here: the binding is `db/bindings.py`.
- `src/agents_matrix_connector/db/bindings.py` (new, writer: bot worker; names left to the builder): a frozen `BindingRow(id, room_id, session_id, slug, origin, run_id, send_id, created_at, released_at, release_reason)`; `reserve_for_run(conn, room_id, run_id) -> bool`; `fill_session(conn, run_id, session_id, slug) -> bool` (idempotent for the same id); `bind_for_send(conn, *, room_id, session_id, slug, send_id) -> Literal["bound", "already", "room_bound", "session_bound"]` (a unique violation maps to the matching refusal inside a savepoint, never an exception for the caller's transaction); `release(conn, binding_id, reason, *, session_id=None) -> bool` (guarded on `released_at IS NULL` and the expected session); `active_for_room(conn, room_id) -> BindingRow | None`; `active_for_session(conn, session_id) -> BindingRow | None`; `active_with_session(conn) -> list[BindingRow]` (the sweep); `prune_released(conn, older_than) -> int`. Writers take a connection and never commit, as in `db/runs.py`; the api uses only the readers.

#### Expected outcome

The connector database holds the agent send queue, the room flag and the room-session bindings, and the database itself refuses a second active binding of a room or of a session; two repository modules offer every query the api, the bot step and the routing change need; existing chats keep their session through the backfill.

#### Steps

- Red: add `test_agent_sends_columns`, `test_binding_backfill`, extend `test_writer_comments` and `test_check_constraints`, write `tests/test_sends_repo.py` and `tests/test_bindings_repo.py`; run `uv run pytest tests/test_schema.py tests/test_sends_repo.py tests/test_bindings_repo.py`: the new tests fail (no tables, no modules).
- Green: write the migration, `db/sends.py` and `db/bindings.py`; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- DB tests use testcontainers (Docker); agent pods have none, so they run in GitHub CI (retro proposal: CI is the DB gate). Keep the reference parser (`m<n>`/`s<n>` to kind and id) and the mapping of a unique-index name to `room_bound`/`session_bound` pure functions with their own non-DB tests so the local run has signal.
- Reuse `agents_common.db.queue.transition` exactly as `db/runs.py` does; no raw UPDATE of `sends.status`. `room_bindings` is not a queue; its release is still one guarded UPDATE (`released_at IS NULL`).
- Writers: the api only inserts `sends`; the bot only moves them (D7); `room_bindings` is written only by the bot worker (D9), the api only reads it. Record the writers in the COMMENTs.
- `test_binding_backfill` applies `0001_init.sql`, seeds runs, then applies `0002_agent_sends.sql` on a fresh database; the tiebreak "a session newest in two rooms binds only its newest run's room" is a ruling and this test is its pin (retro proposal).
- The backfill is part of the approved migration 0002 (no down step); gate question Q12 (recommended yes) settles it. The task builds it as recommended; Q12 must be answered before the live apply (chat-live-smoke), and a "no" removes ac10 and the backfill by amend before then.
- Follow `db/runs.py` and `db/inbound.py` style (dict_row, frozen dataclasses, connection-taking writers).

- 2026-10-27 amended: interrogate.md Act 1: runs.preset_id nullable for follow runs with a CHECK that first runs keep one

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): room_bindings table, unique indexes, backfill, db/bindings.py

- 2026-10-28 done: DB tests CI-only (run 40732610268 green); backfill slug from first run (my call)

- 2026-10-28 actuals: no agent records

### S7: orch-chat-env-scope

- Status: done
- Files: `chart/agents-orchestrator/templates/configmap.yaml`, `chart/agents-orchestrator/templates/deployment.yaml`, `chart/agents-orchestrator/templates/_helpers.tpl`, `tests/test_chart_config.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_chart_config.py -q`
- Verified head: df3998301fecec1cf0a757c539bb8a6f423d7130

#### Requirement

Live apply of agents-orchestrator chart 0.1.0-main.37edd58 with chat enabled (agents-helmfile main f4be334, 2026-10-28 21:32Z) failed and helm rolled it back (revision 13 failed, 14 = rollback to 12): the `migrate` init container of every orchestrator Deployment (api, dispatcher, ingester, reconciler) crash-looped. Cause: `templates/configmap.yaml` renders `ORCH_CHAT_URL` into the ConfigMap that every container loads via `configMapRef`, but `templates/deployment.yaml` adds `ORCH_CHAT_TOKEN` (secretKeyRef to the chat Secret) only to the api container; `Settings._check_chat_pair` (settings.py) refuses a URL without its token ("set ORCH_CHAT_URL and ORCH_CHAT_TOKEN together, or neither"), so every process except the api main container fails to start. Evidence: .logs/matrix-deploy-2026-10-28/apply-agents-orchestrator.log and diff-agents-orchestrator.log (one `ORCH_CHAT_TOKEN` env entry).
Fix (my call, least privilege): the chat pair reaches only the containers that serve the chat relay. Render `ORCH_CHAT_URL` and `ORCH_CHAT_TOKEN` together, as env of the api main container only (both the inline-token and the `chat.existingSecret` paths), and never in the shared ConfigMap; the migrate init containers and the dispatcher, ingester and reconciler get neither. First read every template and the settings to confirm no other component needs `chat_url` (for example a reconciler render of agent pods or the plugin config); if one does, give that container the pair too and say why. Test first: a chart test renders with `chat.url` and `chat.token` (and with `chat.existingSecret`) and asserts that every container and init container that has one of the two variables has both, that the api main container has both, and that the ConfigMap has no `ORCH_CHAT_URL`. Record the incident and rule in MEMORY.md with the date and why.

#### Acceptance conditions

- AC1: with chat.url and chat.token set, every rendered container and init container carries ORCH_CHAT_URL and ORCH_CHAT_TOKEN together or neither [evidence: test:tests/test_chart_config.py::test_chat_pair_rendered_together_per_container]
- AC2: the api main container carries both chat variables, for the inline token and for chat.existingSecret [evidence: test:tests/test_chart_config.py::test_api_container_has_chat_pair]
- AC3: the shared ConfigMap carries no ORCH_CHAT_URL [evidence: test:tests/test_chart_config.py::test_configmap_has_no_chat_url]
- AC4: MEMORY.md records the failed chat apply and the rule [evidence: command:grep -q "migrate init" MEMORY.md]

#### Files

- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `chart/agents-orchestrator/templates/_helpers.tpl`
- `tests/test_chart_config.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done

### S8: orch chat relay

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `src/agents_orchestrator/api/chat.py`, `src/agents_orchestrator/api/app.py`, `README.md`, `openapi.json`, `MEMORY.md`, `tests/test_agent_chat.py`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint`
- Verified head: 62e1908f82094202b1193127f5fa0659d8931812

#### Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can list the rooms it may post to and read the delivery status of what it sent."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

README Non-goals, verbatim: "No member-agent (non-leader) chat tools; members report through their leader." and "No other chat channels (Slack, Telegram); one upstream only."

Design D2, verbatim: "The orchestrator stays free of Matrix concepts: it calls a generic chat upstream at `ORCH_CHAT_URL` and the connector's agent listener serves it under `/chat/v1` [...] Every upstream call carries `Authorization: Bearer <ORCH_CHAT_TOKEN>`, `X-Orch-Session: <session uuid>` and `X-Orch-Slug: <slug>`, and never the agent token. [...] The orchestrator passes the upstream status and JSON body through unchanged, and answers 503 `chat_unavailable` on a connection error, timeout or a non-JSON upstream answer. There is one upstream: no multi-channel registry (YAGNI)."

The D2 route table: `GET /agent/v1/chat/rooms` to `GET {ORCH_CHAT_URL}/chat/v1/rooms`; `POST /agent/v1/chat/messages` body `{text, room?, reply_to?}` to `POST {ORCH_CHAT_URL}/chat/v1/messages`; `POST /agent/v1/chat/reactions` body `{to, key}` to `POST {ORCH_CHAT_URL}/chat/v1/reactions`; `GET /agent/v1/chat/messages/{id}` to `GET {ORCH_CHAT_URL}/chat/v1/messages/{id}`.

Design D12, verbatim: "`api/chat.py` (new router, agent port only): every route runs `require_agent`, then `_leads` (403 `not_leader`), then requires chat configured (503 `chat_unconfigured`), then forwards (D2). Settings `ORCH_CHAT_URL` (http or https URL) and `ORCH_CHAT_TOKEN` (secret, never in repr or logs): both set or both empty, else a settings error naming both (my call). Nothing is stored."

Design D5, verbatim (orchestrator caps): "The orchestrator caps the forwarded request body at 256 KiB (413 `payload_too_large`) and the upstream call at 10 s. The cap covers the worst case of a valid maximal request (interrogate Act 6; my call on the figure): 16000 characters of 4 bytes each are 64000 bytes raw (the plugin's httpx encodes JSON as raw UTF-8), and up to 192000 bytes when a client escapes every character as a JSON surrogate pair (12 bytes), plus a room id of up to 255 characters, `reply_to` and the JSON keys; 256 KiB (262144 bytes) covers all of it, where the verdict's example of 80 KiB would refuse the escaped form."

Interrogate verdict, verbatim: "6. Size caps (A,C medium): 16000 characters can exceed the orchestrator's 32 KiB body cap. Make the relay cap cover the worst case (4 bytes per character plus JSON overhead, e.g. 80 KiB) with an AC sending 16000 4-byte characters end to end."

Scope (agents-orchestrator): `settings.py` (`chat_url`, `chat_token`), new `api/chat.py`, `api/app.py` (include the router), README (Configuration rows; `## Agent API` gets a `### Chat` section with one `#### `METHOD /agent/v1/chat/...`` heading per route, the checks in order and the pass-through rule), committed `openapi.json`, `MEMORY.md` (dated entry: the chat upstream relay and why the orchestrator names it chat, not matrix). The chart, the plugin tools and the allow list are later tasks.

#### Acceptance conditions

- ac1: ORCH_CHAT_URL and ORCH_CHAT_TOKEN default empty, the URL must be http or https, one set without the other is a settings error naming both, and the token never appears in repr [evidence: test:tests/test_settings.py::test_chat_settings]
- ac2: the README Configuration section names every ORCH_ variable, the two new ones included [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- ac3: each chat route forwards its method, path, query and body to ORCH_CHAT_URL/chat/v1 with the chat bearer, X-Orch-Session and X-Orch-Slug of the caller, and the forwarded request carries neither the agent token nor any other inbound header [evidence: test:tests/test_agent_chat.py::test_forwards_with_chat_token_never_agent_token]
- ac4: the upstream status and JSON body (202, 403 room_not_allowed, 422 bad_reference, 429 rate_limited) reach the agent unchanged [evidence: test:tests/test_agent_chat.py::test_upstream_status_and_body_pass_through]
- ac5: a connection error, a timeout and a non-JSON upstream answer give 503 chat_unavailable without echoing the upstream text [evidence: test:tests/test_agent_chat.py::test_upstream_failure_is_chat_unavailable]
- ac6: with chat unconfigured every chat route answers 503 chat_unconfigured and makes no upstream call [evidence: test:tests/test_agent_chat.py::test_unconfigured]
- ac7: a request body over 256 KiB answers 413 payload_too_large and makes no upstream call (updated) [evidence: test:tests/test_agent_chat.py::test_body_cap]
- ac8: a message of 16000 4-byte characters, sent as raw UTF-8 JSON and as JSON with every character escaped as a surrogate pair, passes the cap and reaches the upstream with the same text [evidence: test:tests/test_agent_chat.py::test_max_text_passes_cap]
- ac9: a non-leader member gets 403 not_leader, a bad token 401 and a foreign peer IP 403, and none of them reaches the upstream [evidence: test:tests/test_agent_chat.py::test_leader_only_and_identity]
- ac10: the chat routes are served only on the agent port; the main and service ports answer 404 or 403 for them [evidence: test:tests/test_agent_chat.py::test_chat_routes_only_on_agent_port]
- ac11: the README documents every chat route and the committed openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py::test_every_route_documented tests/test_readme_api.py::test_openapi_json_matches_app]
- ac12: MEMORY.md records the chat upstream relay decision, dated [evidence: command:grep -qi "chat upstream" MEMORY.md]
- ac13: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/chat.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `MEMORY.md`
- `tests/test_agent_chat.py`
- `tests/test_settings.py`

#### Interfaces

- `settings.py:Settings.chat_url: str = ""`, `chat_token: str = Field(default="", repr=False)`; a validator for both-or-neither and the URL scheme.
- `api/chat.py` (new): `router = APIRouter(prefix="/agent/v1/chat", tags=["agent"])` with `GET /rooms`, `POST /messages`, `POST /reactions`, `GET /messages/{send_id}`; one `httpx.AsyncClient` (timeout 10 s) owned by the app lifespan or created per app; a `forward(method, path, body, session, slug)` helper.
- Agent-facing errors added: 403 `not_leader`, 503 `chat_unconfigured`, 503 `chat_unavailable`, 413 `payload_too_large`; everything else is the upstream's.

#### Expected outcome

A session leader can call four chat routes on the orchestrator agent port; the orchestrator proves who is calling and relays to the chat upstream with its own token, storing nothing.

#### Steps

- Red: write `tests/test_agent_chat.py` (non-DB cases with `require_agent` overridden and an `httpx.MockTransport` upstream; DB cases for identity and leadership like `tests/test_agent_session_messaging.py`), add `test_chat_settings`; run `uv run --frozen pytest tests/test_agent_chat.py tests/test_settings.py`: the new tests fail.
- Green: settings, router, app wiring, README, `openapi.json` (`uv run python -m agents_orchestrator.api.openapi > openapi.json`), MEMORY; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Reuse `api/agent.py:require_agent` and `_leads` (import them; do not copy). Leader check exactly as `session_send`.
- No Docker in agent pods: the DB-backed cases (ac8) run in CI; ac3-ac7 and ac9 must be non-DB so the local verify has signal (retro proposal).
- Build fake tokens at runtime in tests (retro proposal, GitGuardian).
- Never log the chat token, the agent token or the upstream body; log method, path, status only.
- `X-Orch-Slug` is the caller session's slug from the sessions repo, never from the request.

- 2026-10-27 amended: interrogate.md Act 6: body cap 256 KiB covering 16000 4-byte characters raw and escaped

- 2026-10-28 done: CI test/lint/chart green run 40732285270; e2e pending at review

- 2026-10-28 actuals: no agent records

### S9: orch-chat-untrusted-sessions

- Status: done
- Files: `src/agents_orchestrator/k8s/on_start.py`, `src/agents_orchestrator/api/chat.py`, `tests/test_on_start.py`, `tests/test_agent_chat.py`, `tests/e2e/test_e2e_kind.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_on_start.py tests/test_agent_chat.py -q`
- Verified head: b21a292af86c28366f5288613ceb8eba2743acb2

#### Requirement

Epic review findings for agents-orchestrator, my call to fix:
1. Security MEDIUM 1 (.scratchpad/matrix/review/security.md): `k8s/on_start.py` (about line 41) grants CHAT_TOOLS to every session, so a webhook or schedule session that reads attacker-controlled PR, issue or alert text can be prompt-injected into `chat_send` and message the real Messenger user wherever `agents_may_initiate` is on. Sessions started by the trigger services agents-webhook and agents-schedule (identified by the orchestrator's own record of who created the session, for example the service token name; read how sessions record their creator first, and if no reliable record exists, stop and return that as a question) get no chat tools rendered in onStart, and the chat relay (`api/chat.py`) refuses their calls with 403 and a distinct error code. Every other session keeps today's behaviour (user and connector sessions, including mx-34).
2. Review Consider (.scratchpad/matrix/review/orch-plugins.md): `tests/e2e/test_e2e_kind.py` (about line 292) compares the allow list to `orchestrator_allow()`, i.e. the code to itself; restore a literal expected list there.
Test first. Record the rule in MEMORY.md with the date and why.
Decision (my call, 2026-10-28, answering the implementer's question): the orchestrator records no session creator today (`ServiceGate` in `api/service_auth.py` only logs the service name; `sessions` has no creator column). Add a nullable `created_by_service` column in a new migration (next free number), set it from the authenticated service name when a service creates a session (`create_session`), expose nothing new in the public API unless a test needs it, and treat NULL (user-created and pre-existing sessions) as not a trigger service. Pre-existing webhook and schedule sessions keep chat tools until they end; they are short-lived run sessions, so this is accepted.

#### Acceptance conditions

- AC1: a session created by the agents-webhook or agents-schedule service gets no chat tools in its rendered onStart config [evidence: test:tests/test_on_start.py::test_trigger_service_sessions_get_no_chat_tools]
- AC2: the chat relay refuses a call from a trigger-service session with 403 and its own error code [evidence: test:tests/test_agent_chat.py::test_trigger_service_session_refused]
- AC3: a user-created session still gets the chat tools and may call the relay [evidence: test:tests/test_agent_chat.py::test_user_session_may_use_chat]
- AC4: the kind e2e asserts a literal allow list [evidence: command:! grep -n "orchestrator_allow()" tests/e2e/test_e2e_kind.py]
- AC5: MEMORY.md records the rule [evidence: command:grep -q "trigger-service sessions" MEMORY.md]

#### Files

- `src/agents_orchestrator/k8s/on_start.py`
- `src/agents_orchestrator/api/chat.py`
- `tests/test_on_start.py`
- `tests/test_agent_chat.py`
- `tests/e2e/test_e2e_kind.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Read every file the step touches, write the AC tests first and run the task verify: the new tests fail for the expected reason.
- Implement the smallest change that passes, rerun the verify and `mise run lint`: green.
- Commit, push, open or update the PR and quote its CI result per job.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: creator record decision: created_by_service column

- 2026-10-29 done

### S10: helmfile-orch-chat-fix-pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`
- Verified head: 1f0ca4bab540747c8688b6d9a85212088820f547

#### Requirement

Pin the agents-orchestrator release to the merge commit of task orch-chat-env-scope (chart `0.1.0-main.6b467b7` in helmfile.yaml.gotmpl and `image.tag` `6b467b7` in values/agents-orchestrator/common.yaml; merge commit 6b467b7 of PR #31; its main CI run 40779692636 must be green, including chart-publish). The previous pin 37edd58 with chat enabled crash-looped every migrate init container (live apply 2026-10-28 21:32Z, rolled back). Keep every other pin unchanged, including the agent image claude-code-wrapper:0.3.3 applied by cct2 from helmfile main 260bdc2. Start from origin/main (sync the tree first). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orch-chat-env-scope merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync the tree to origin/main (`git merge --ff-only origin/main`), then change the orchestrator pin assertions in tests/test_orchestrator_release.py to 6b467b7 and run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: the pin tests fail.
- Set the chart version and image tag to 6b467b7, rerun: pass (Harbor-401 template tests may be deselected locally, name them).
- `mise run check-pins`: every pin ok. `mise run lint`: clean.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: fill merged sha 6b467b7

- 2026-10-28 done

### S11: helmfile-orch-untrusted-pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`
- Verified head: 5f0956b6214c710fc3d4bae47692a646c0bc99d4

#### Requirement

Pin agents-orchestrator to the merge commit of PR #32 (task orch-chat-untrusted-sessions; migration 0009 created_by_service): chart `0.1.0-main.a9f936f` in helmfile.yaml.gotmpl and `image.tag` `a9f936f` in values/agents-orchestrator/common.yaml. Merge commit a9f936f; main CI run 40796228385 green incl chart-publish. Keep every other pin unchanged (connector c98c501, web 6ea3457, agent image 0.3.3). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #32 merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync to origin/main, change the orchestrator pin assertions in tests/test_orchestrator_release.py to a9f936f and run the verify: the pin tests fail.
- Set the chart version and image tag to a9f936f, rerun: pass. `mise run check-pins` ok, `mise run lint` clean.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 amended: fill merged sha a9f936f

- 2026-10-29 done

### S12: mxc chart agent port

- Status: done
- Files: `chart/agents-matrix-connector/templates/deployment.yaml`, `chart/agents-matrix-connector/templates/service-agents.yaml`, `chart/agents-matrix-connector/templates/_config.tpl`, `chart/agents-matrix-connector/templates/secret.yaml`, `chart/agents-matrix-connector/values.yaml`, `chart/agents-matrix-connector/ci/lint-values.yaml`, `tests/test_chart_network.py`, `tests/test_chart_workloads.py`
- Verify: `uv run pytest tests/test_chart_network.py tests/test_chart_workloads.py && mise run lint`
- Verified head: cc19c54edeca87373337fb5d2a1a1c4a3b2d94f4

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D3, verbatim (chart): "The chart adds a container port `agents` 8001 on the api pod only and a Service `<fullname>-api-agents`; the bot still has no Service."

Design D3, verbatim: "the sha256 hex of the presented token must equal `MATRIX_AGENT_TOKEN_SHA256` [...] The token never reaches a log line or an error body."

Design D14, verbatim (value shape): "`values/agents-matrix-connector/agent-token.secrets.yaml` (`{agentApi: {tokenSha256}}`)".

Scope (agents-matrix-connector chart): values `agentApi.port` (8001), `agentApi.tokenSha256` (empty) or `agentApi.tokenSecret.{name,key}` (the secret wins), `limits.agentRatePerMinute` (20); the api container gets port `agents` and env `MATRIX_AGENT_TOKEN_SHA256` from the chart Secret or the named Secret (api only, never in the ConfigMap; a value that is not 64 lowercase hex fails the render); the ConfigMap gets `MATRIX_AGENT_PORT` and `MATRIX_AGENT_RATE_PER_MINUTE`; new template `service-agents.yaml` (`<fullname>-api-agents`, ClusterIP, port 8001, targetPort `agents`, api selector). `tests/test_chart_network.py::test_service_selects_api_only` is no longer accurate (named): it asserts the chart has exactly one Service; it is rewritten as `test_services_select_api_only` asserting the two Services, both selecting only the api component, and that no Service selects the bot.

#### Acceptance conditions

- ac1: the chart renders the -api and -api-agents Services, the agents Service on port 8001 targeting port agents, both selecting only the api component, and no Service selects the bot (updated) [evidence: test:tests/test_chart_network.py::test_services_select_api_only]
- ac2: the api container exposes port agents 8001 and the bot container does not [evidence: test:tests/test_chart_workloads.py::test_agent_port_only_on_api]
- ac3: MATRIX_AGENT_TOKEN_SHA256 reaches only the api container through a secretKeyRef (chart Secret from agentApi.tokenSha256, or agentApi.tokenSecret, which wins), never the ConfigMap, and a malformed hash fails the render [evidence: test:tests/test_chart_workloads.py::test_agent_token_hash_secret_on_api_only]
- ac4: the ConfigMap renders MATRIX_AGENT_PORT and MATRIX_AGENT_RATE_PER_MINUTE (extended) [evidence: test:tests/test_chart_workloads.py::test_config_rendered]
- ac5: the Ingress still routes only /matrix/api to the -api Service [evidence: test:tests/test_chart_network.py::test_ingress_routes_api_prefix]
- ac6: helm lint passes with the CI lint values [evidence: command:mise run lint:chart]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_chart_network.py tests/test_chart_workloads.py && mise run lint]

#### Files

- `chart/agents-matrix-connector/templates/deployment.yaml`
- `chart/agents-matrix-connector/templates/service-agents.yaml`
- `chart/agents-matrix-connector/templates/_config.tpl`
- `chart/agents-matrix-connector/templates/secret.yaml`
- `chart/agents-matrix-connector/values.yaml`
- `chart/agents-matrix-connector/ci/lint-values.yaml`
- `tests/test_chart_network.py`
- `tests/test_chart_workloads.py`

#### Interfaces

- `values.yaml`: `agentApi: {port: 8001, tokenSha256: "", tokenSecret: {name: "", key: token-sha256}}`, `limits.agentRatePerMinute: 20`.
- Service `<fullname>-api-agents` (port name `agents`, 8001).
- Chart Secret key `agent-token-sha256` when `agentApi.tokenSha256` is set and no `tokenSecret.name`.

#### Expected outcome

Deploying the chart exposes the connector's agent listener to in-cluster callers through its own Service, with the token hash only in a Secret on the api pod.

#### Steps

- Red: rewrite `test_services_select_api_only`, add the two workload tests, extend `test_config_rendered`; run `uv run pytest tests/test_chart_network.py tests/test_chart_workloads.py`: the new tests fail.
- Green: templates and values; run the task's verify and `mise run lint:chart`: pass. Quote the summary lines.

#### Notes

- Chart tests and `helm lint` need `helm`; this pod has no helm version set ("mise ERROR No version is set for shim: helm"), so the CI `chart` job (`mise run lint:chart`, `mise run test:chart`) is the gate; say so in the hand-back with the CI run link.
- Follow the existing `matrix.accessTokenSecret` pattern in `templates/_helpers.tpl`/`secret.yaml` for the hash secret.
- The oauth2-proxy admission sidecar takes the port name `http`; name the new port `agents` and target it by name.
- Update `ci/lint-values.yaml` only if the lint needs a value (it should render with the defaults).

- 2026-10-28 done: CI 40749340758 green

- 2026-10-28 actuals: no agent records

### S13: mxc-pool-and-binding

- Status: done
- Files: `src/agents_matrix_connector/api/agent.py`, `src/agents_matrix_connector/sender.py`, `tests/test_api_agent.py`, `tests/test_sender.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_api_agent.py tests/test_sender.py -q`
- Verified head: aaa9aa49cea92f56039750cb76e1dc41d48df093

#### Requirement

Epic review findings for agents-matrix-connector (.scratchpad/matrix/review/connector.md, Consider 1 and 2), my call to fix:
1. `api/agent.py` (about 255-257 and 319-326) takes a second pool connection while holding one; with the pool of 10, ten simultaneous agent requests deadlock the pool and end in 503s. Restructure so one request holds at most one pool connection at a time (pass the held connection down, or release before acquiring). Test first with a pool of size N and N concurrent requests completing.
2. `sender.py` (about 116 and 199): when an initiating send fails, the room's binding is released even if a later send in that room was already delivered, so the user's reply goes to a new session. Release the binding on a failed initiating send only when no later send of that binding was delivered. Test first.
Record both in MEMORY.md with the date and why.

#### Acceptance conditions

- AC1: as many concurrent agent requests as the pool size complete without a 503 [evidence: test:tests/test_api_agent.py::test_concurrent_requests_do_not_exhaust_pool]
- AC2: a failed initiating send keeps the binding when a later send in that room was delivered [evidence: test:tests/test_sender.py::test_failed_initiating_send_keeps_binding_after_later_delivery]
- AC3: a failed initiating send with no later delivery still releases the binding [evidence: test:tests/test_sender.py::test_failed_initiating_send_releases_binding]
- AC4: MEMORY.md records the pool rule [evidence: command:grep -q "one pool connection" MEMORY.md]

#### Files

- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/sender.py`
- `tests/test_api_agent.py`
- `tests/test_sender.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Read every file the step touches, write the AC tests first and run the task verify: the new tests fail for the expected reason.
- Implement the smallest change that passes, rerun the verify and `mise run lint`: green.
- Commit, push, open or update the PR and quote its CI result per job.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S14: mxc room initiate flag

- Status: done
- Files: `src/agents_matrix_connector/db/rules.py`, `src/agents_matrix_connector/db/directory.py`, `src/agents_matrix_connector/api/rooms.py`, `src/agents_matrix_connector/api/schemas.py`, `openapi.json`, `README.md`, `tests/test_api_rooms.py`
- Verify: `uv run pytest tests/test_api_rooms.py tests/test_readme_api.py tests/test_rules_repo.py tests/test_directory_repo.py && mise run lint`
- Verified head: 23f0424bc0d26a387f33e7c30a591ce7c0dc6c11

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D4, verbatim (the flag): "`room_settings.agents_may_initiate boolean NOT NULL DEFAULT false` is new; its writer stays the api. `PUT /matrix/api/v1/rooms/{room_id}/settings` takes an optional `agents_may_initiate`; omitted keeps the stored value (my call: the flag is an authorisation grant, so a save of the preset or trigger from an older UI never silently grants or revokes it); `RoomView` and `RoomDetail` return it."

Design D9, verbatim (the binding view): "The room's binding is visible to the user (my call: the live smoke and the operator need it): `RoomView` and `RoomDetail` of the UI API gain `binding: {session_id, slug, origin, since} | null` (the active binding; a reservation shows `session_id` null), next to the unchanged `session` (the latest run). Showing it in agents-web: noted, not doing now."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Open question Q1 (approved by the user 2026-10-27, "All yes"), verbatim: "Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)?" answer "yes".

Scope (agents-matrix-connector): `db/rules.py` (`RoomSettings` and `set_room_settings` carry the flag), `db/directory.py` (the room queries read the active `room_bindings` row; read only, the bot stays its writer), `api/schemas.py` (`RoomSettingsIn.agents_may_initiate: bool | None = None`, `RoomView.agents_may_initiate: bool`, `RoomView.binding: BindingView | None`), `api/rooms.py` (PUT stores the flag, views return the flag, false when the room has no settings row, and the binding), the committed `openapi.json`, and README: the `PUT /matrix/api/v1/rooms/{room_id}/settings` section names the field and its omitted-keeps rule, the `GET /matrix/api/v1/rooms` section names `binding`, and the Operations section gets a step "Let agents start chats in a room" (PUT the flag for the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` through a port-forward to the api container, or the agents-web toggle once deployed; the flag lets an agent start a chat only while the room is unbound).

#### Acceptance conditions

- ac1: a PUT with agents_may_initiate true stores it and GET /rooms/{id} and GET /rooms return it [evidence: test:tests/test_api_rooms.py::test_room_settings_agents_may_initiate]
- ac2: a PUT that omits agents_may_initiate keeps the stored value, and a PUT with false clears it [evidence: test:tests/test_api_rooms.py::test_room_settings_flag_omitted_keeps_value]
- ac3: a room without a settings row reports agents_may_initiate false [evidence: test:tests/test_api_rooms.py::test_agents_may_initiate_default_false]
- ac4: GET /rooms and GET /rooms/{id} return binding {session_id, slug, origin, since} for a room with an active binding, session_id null for a reservation, and null for an unbound room or one with only released bindings, while session (the latest run) is unchanged [evidence: test:tests/test_api_rooms.py::test_room_binding_view]
- ac5: the existing room settings behaviour (preset check, trigger) is unchanged [evidence: test:tests/test_api_rooms.py::test_room_settings]
- ac6: the existing room listing assertions are unchanged [evidence: test:tests/test_api_rooms.py::test_list_rooms]
- ac7: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_committed_matches]
- ac8: the README PUT settings section documents the field, the rooms listing section the binding, and the Operations section the owner DM step [evidence: command:grep -A15 '^### `PUT /matrix/api/v1/rooms/{room_id}/settings`' README.md | grep -q agents_may_initiate && grep -A12 '^### `GET /matrix/api/v1/rooms`' README.md | grep -q binding && grep -q '^### Let agents start chats in a room' README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_rooms.py tests/test_readme_api.py tests/test_rules_repo.py tests/test_directory_repo.py && mise run lint]

#### Files

- `src/agents_matrix_connector/db/rules.py`
- `src/agents_matrix_connector/db/directory.py`
- `src/agents_matrix_connector/api/rooms.py`
- `src/agents_matrix_connector/api/schemas.py`
- `openapi.json`
- `README.md`
- `tests/test_api_rooms.py`

#### Interfaces

- `api/schemas.py:RoomSettingsIn` gains `agents_may_initiate: bool | None = None`; `RoomView` (and so `RoomDetail`) gains `agents_may_initiate: bool` and `binding: BindingView | None`, `BindingView {session_id: uuid | null, slug: str | null, origin: "inbound" | "agent", since: datetime}` (the active `room_bindings` row; `since` is its `created_at`).
- `db/rules.py:RoomSettings` gains `agents_may_initiate: bool`; `set_room_settings(pool, room_id, *, preset_id, trigger, agents_may_initiate: bool | None = None)`: None keeps the stored value (false for a new row).
- `db/directory.py`: the room list and room detail queries join the active `room_bindings` row (read only); `RoomRow` gains a `binding` field defaulting to None, so existing constructions in tests stay valid. `session` (the latest run) is unchanged.
- `PUT /matrix/api/v1/rooms/{room_id}/settings` body `{preset_id?, trigger?, agents_may_initiate?}`; response `RoomDetail` with the flag and the binding.

#### Expected outcome

The user can flag a room so agents may start a chat there while it is unbound; nothing changes for rooms left unflagged, a settings save that does not name the flag leaves it as it was, and every room view shows which session the room is bound to.

#### Steps

- Red: add the four new tests in `tests/test_api_rooms.py`; run `uv run pytest tests/test_api_rooms.py`: they fail.
- Green: schemas, repositories, route; regenerate `openapi.json` with `uv run python -m agents_matrix_connector.api.openapi > openapi.json`; update README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- The omitted-keeps rule is a merge-semantics ruling: its pin test is `test_room_settings_flag_omitted_keeps_value` (retro proposal).
- The column and the `room_bindings` table exist after mxc-sends-schema (migration 0002); do not add another migration. Seed bindings in tests with plain INSERTs (the bot is the writer in production; the api only reads).
- The binding view is read only: no UI API route writes, releases or moves a binding (D9).
- `tests/test_api_rooms.py` and `tests/test_directory_repo.py` are DB-backed (Docker); they run in CI here. `test_readme_api.py` runs locally. `test_directory_repo.py` is in the verify to prove the directory change keeps its assertions; it is not edited.
- `set_room_settings` keeps its single upsert statement; the keep-value rule is `COALESCE(EXCLUDED.agents_may_initiate, room_settings.agents_may_initiate)` or equivalent.
- The vendored schema in agents-web (web-room-initiate-toggle) picks up `binding` with the rest of `openapi.json`; showing it in the UI is noted, not doing now.

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding shown in the room views

- 2026-10-28 done: CI run 40734264708 green

- 2026-10-28 actuals: no agent records

### S15: orch chart chat

- Status: done
- Files: `chart/agents-orchestrator/values.yaml`, `chart/agents-orchestrator/templates/secret.yaml`, `chart/agents-orchestrator/templates/_config.tpl`, `chart/agents-orchestrator/templates/configmap.yaml`, `chart/agents-orchestrator/templates/deployment.yaml`, `README.md`, `tests/test_chart_config.py`
- Verify: `uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint`
- Verified head: 2ff2888056bf4c8eacb105bdb2735ba85fce4703

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D12, verbatim (chart): "The chart takes `chat.url`, `chat.token` or `chat.existingSecret`/`chat.existingSecretKey`, renders `ORCH_CHAT_URL` in the settings ConfigMap and `ORCH_CHAT_TOKEN` from a Secret, on the api container only (my call)."

Design D14, verbatim (value shape): "`values/agents-orchestrator/chat-token.secrets.yaml` (`{chat: {token}}`)".

Scope (agents-orchestrator chart): `values.yaml` (`chat: {url: "", token: "", existingSecret: "", existingSecretKey: chat-token}`), `templates/secret.yaml` (chart Secret `<fullname>-chat` when `chat.token` is set and no `existingSecret`), `templates/_config.tpl` (`ORCH_CHAT_TOKEN` secretKeyRef helper, the Secret name helper; a URL without a token source, or a token without a URL, fails the render), `templates/configmap.yaml` (`ORCH_CHAT_URL`), `templates/deployment.yaml` (the env on the api container only), README `### Secrets` names the chat values.

#### Acceptance conditions

- ac1: chat.url renders ORCH_CHAT_URL in the settings ConfigMap [evidence: test:tests/test_chart_config.py::test_chat_url_in_configmap]
- ac2: chat.token renders a chart Secret and ORCH_CHAT_TOKEN as a secretKeyRef on the api container only, chat.existingSecret wins over it, and the token never appears in the ConfigMap [evidence: test:tests/test_chart_config.py::test_chat_token_secret_on_api_only]
- ac3: a chat URL without a token source, or a token source without a URL, fails the render with a message naming both values [evidence: test:tests/test_chart_config.py::test_chat_url_and_token_together]
- ac4: without chat values neither ORCH_CHAT_URL nor ORCH_CHAT_TOKEN is rendered [evidence: test:tests/test_chart_config.py::test_chat_absent_by_default]
- ac5: no secret value reaches the ConfigMap [evidence: test:tests/test_chart_config.py::test_no_secret_values_in_configmap]
- ac6: README Secrets documents chat.url, chat.token and chat.existingSecret [evidence: command:grep -q 'chat.existingSecret' README.md && grep -q 'ORCH_CHAT_TOKEN' README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint]

#### Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/secret.yaml`
- `chart/agents-orchestrator/templates/_config.tpl`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `README.md`
- `tests/test_chart_config.py`

#### Interfaces

- `values.yaml`: `chat.url`, `chat.token`, `chat.existingSecret`, `chat.existingSecretKey` (default `chat-token`).
- Secret `<fullname>-chat` key `chat-token` (chart-made) or the named existing Secret.

#### Expected outcome

Deploying the orchestrator chart with a chat URL and token turns the chat routes on, with the token only in a Secret mounted on the api container.

#### Steps

- Red: add the four chart tests; run `uv run --frozen pytest tests/test_chart_config.py`: they fail.
- Green: values and templates, README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Mirror the `masterKey` and `serviceApi` patterns already in `templates/secret.yaml` and `_config.tpl`.
- Chart tests render with `helm`; if this pod lacks a helm version (as in the connector), the CI chart job is the gate; quote its run.
- `tests/test_chart_deployments.py` guards the other containers; it must still pass with the env only on the api container.

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S16: plugin chat tools

- Status: done
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`
- Verify: `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint`
- Verified head: 670e021f935418761112c27e3e90a773803d37a7

#### Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."
- "An agent can list the rooms it may post to and read the delivery status of what it sent."

Design D13, verbatim: "The orchestrator plugin gains `chat_rooms`, `chat_send`, `chat_react`, `chat_status` (HttpBinding tools, existing `on_error` mapping); descriptions say the final answer reaches the chat only for chat-started turns, sends are asynchronous and return `s<n>`, `reply_to`/`to` take `m<n>`/`s<n>`, leader only, status via `orchestrator_chat_status`, and the 1:1 binding (D9): a session talks in at most one chat room, its bound room, and starts a chat only in an unbound flagged room while it is bound to none (`room_bound`, `session_bound` otherwise)."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". Design D2, verbatim: "the binding refusals of D4 (b) are 409 `room_bound` and 409 `session_bound`."

Design D2, verbatim (the routes the tools call): "`GET /agent/v1/chat/rooms` [...] `POST /agent/v1/chat/messages` body `{text, room?, reply_to?}` [...] `POST /agent/v1/chat/reactions` body `{to, key}` [...] `GET /agent/v1/chat/messages/{id}`".

Architecture risk, verbatim: "Double output: the agent calls send during a chat-started turn and its final answer is posted too. Mitigation: PREAMBLE and tool description".

Scope (any-mcp-tatara-plugins, `orchestration/orchestrator`): four `spec(...)` entries and descriptions in `any_mcp_tatara_orchestrator/__init__.py`, the plugin docstring, the plugin README's tool list. `tests/test_orchestrator_plugin.py::test_lists_eleven_tools` is no longer accurate (named): it pins eleven tools; it becomes `test_lists_fifteen_tools` pinning the fifteen names. No version bump here (plugins-release-0-3-0).

#### Acceptance conditions

- ac1: the plugin lists fifteen tools, the eleven existing ones plus chat_rooms, chat_send, chat_react and chat_status (updated) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_fifteen_tools]
- ac2: chat_rooms calls GET /agent/v1/chat/rooms, chat_send POST /agent/v1/chat/messages with {text, room?, reply_to?}, chat_react POST /agent/v1/chat/reactions with {to, key}, chat_status GET /agent/v1/chat/messages/{id}, each with the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_tools_call_agent_routes]
- ac3: upstream refusals (room_not_allowed, room_not_authorised, room_bound, session_bound, bad_reference, rate_limited, not_leader, chat_unavailable) surface their code and status, the token redacted [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_errors_surface_code]
- ac4: the chat_send description says the final answer reaches the chat only for chat-started turns, that sends are asynchronous and return s<n>, that reply_to takes m<n> or s<n>, that only the leader may send, and that a session talks in at most one chat room (its bound room) and starts a chat only in an unbound flagged room while bound to none; chat_rooms, chat_react and chat_status descriptions name the binding rule or their references [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac5: the plugin README lists the four chat tools and the one-room-per-session rule [evidence: command:grep -q orchestrator_chat_send orchestration/orchestrator/README.md && grep -q orchestrator_chat_status orchestration/orchestrator/README.md && grep -qi "one room" orchestration/orchestrator/README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

#### Interfaces

- Tools (namespace `orchestrator`, so agents see `orchestrator_chat_*`): `chat_rooms {}`; `chat_send {text: string, room?: string, reply_to?: string}`; `chat_react {to: string, key: string}`; `chat_status {id: string}`; all `additionalProperties: false`.

#### Expected outcome

The orchestrator plugin offers the four chat tools against the orchestrator's chat routes, ready to release.

#### Steps

- Red: rename and update `test_lists_eleven_tools`, add the three chat tests; run `uv run pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: they fail.
- Green: the four specs and descriptions, README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Follow `test_session_tools_call_agent_routes` and `test_scale_and_init_tools_match_contracts` for the route assertions.
- Optional body fields that the agent omits must not be sent as null if the binding would send them; the connector rejects unknown fields, not nulls, so either is accepted, but keep it consistent with `session_send`.
- Depends on orch-chat-relay only for the agreed paths; nothing here imports the orchestrator.

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): descriptions and binding refusal codes

- 2026-10-28 done: CI runs 40734865565, 40734905366 green; test_source_install local fail is pod git version

- 2026-10-28 actuals: no agent records

### S17: helmfile chat secrets

- Status: done
- Files: `scripts/bootstrap-secrets.sh`, `helmfile.yaml.gotmpl`, `values/agents-orchestrator/chat-token.secrets.yaml`, `values/agents-matrix-connector/agent-token.secrets.yaml`, `tests/test_secrets.py`, `README.md`
- Verify: `uv run pytest tests/test_secrets.py && mise run lint`
- Verified head: 4c7ef2aa9c1bebfdc96c825d9f53797b7fd2f3fb

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D14, verbatim: "One new token. `scripts/bootstrap-secrets.sh` gains `bootstrap_chat_token`: both files or neither, never rotates, never prints. (probe) The architecture says the sha256 goes to `values/agents-matrix-connector/default.secrets.yaml`; that file exists and the script never touches an existing target, so the token goes to two new files instead: `values/agents-orchestrator/chat-token.secrets.yaml` (`{chat: {token}}`) and `values/agents-matrix-connector/agent-token.secrets.yaml` (`{agentApi: {tokenSha256}}`), both listed on their releases in `helmfile.yaml.gotmpl`."

Scope (agents-helmfile): `bootstrap_chat_token` in `scripts/bootstrap-secrets.sh` (mirrors `bootstrap_service_token`: `openssl rand -hex 32`, sha256 with `openssl dgst -sha256`, both files or neither, refuses a half state, never prints), called from the script's main list; run the script once to create and commit the two SOPS-encrypted files (encryption needs only the public recipients in `.sops.yaml`); list `values/agents-orchestrator/chat-token.secrets.yaml` on the agents-orchestrator release and `values/agents-matrix-connector/agent-token.secrets.yaml` (with its `default.secrets.yaml`) on the agents-matrix-connector release in `helmfile.yaml.gotmpl`; README bootstrap section names the new files.

#### Acceptance conditions

- ac1: the script writes both files, and the hash file's agentApi.tokenSha256 is the sha256 of the token file's chat.token (fake sops) [evidence: test:tests/test_secrets.py::test_chat_token_bootstrapped]
- ac2: with both files present nothing is rewritten, and with exactly one present the script exits 1 naming both and writes nothing [evidence: test:tests/test_secrets.py::test_chat_token_never_rotates]
- ac3: the token and its hash never reach stdout, stderr or a trace [evidence: test:tests/test_secrets.py::test_chat_token_not_printed]
- ac4: the two committed files are SOPS-encrypted with exactly the expected keys [evidence: test:tests/test_secrets.py::test_secrets_files_encrypted_with_expected_keys]
- ac5: helmfile.yaml.gotmpl lists chat-token.secrets.yaml on agents-orchestrator and agent-token.secrets.yaml with default.secrets.yaml on agents-matrix-connector [evidence: test:tests/test_secrets.py::test_chat_token_files_listed_on_releases]
- ac6: (orchestrator session, needs the SOPS key) the decrypted hash matches the decrypted token [evidence: test:tests/test_secrets.py::test_chat_token_hash_matches]
- ac7: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_secrets.py && mise run lint]

#### Files

- `scripts/bootstrap-secrets.sh`
- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/chat-token.secrets.yaml`
- `values/agents-matrix-connector/agent-token.secrets.yaml`
- `tests/test_secrets.py`
- `README.md`

#### Interfaces

- `values/agents-orchestrator/chat-token.secrets.yaml`: `{chat: {token: <64 hex>}}` (SOPS).
- `values/agents-matrix-connector/agent-token.secrets.yaml`: `{agentApi: {tokenSha256: <64 hex>}}` (SOPS).
- `scripts/bootstrap-secrets.sh:bootstrap_chat_token`.

#### Expected outcome

The one chat token exists, encrypted, in the shape each chart reads, and re-running the bootstrap never rotates it.

#### Steps

- Red: add the five non-decrypting tests and `test_chat_token_hash_matches` (extend the parametrised `test_secrets_files_encrypted_with_expected_keys`); run `uv run pytest tests/test_secrets.py`: the new tests fail.
- Green: the function, the helmfile listing, README; run `bash scripts/bootstrap-secrets.sh` (only the new function writes; every existing file is left untouched) and commit the two encrypted files; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Follow `bootstrap_service_token` and `bootstrap_matrix_connector` exactly (pipes and env of one command only; nothing echoed or traced).
- `test_chat_token_hash_matches` decrypts and needs the SOPS age key, like `test_matrix_connector_token_hash_matches`; if this pod has no key it fails "sops could not decrypt (key unavailable?)": the orchestrator session runs it (ac6) before chat-live-smoke.
- Build fake tokens at runtime in tests (retro proposal, GitGuardian); gitleaks runs in lint.
- agents-helmfile has no CI workflow (retro tech debt): the reviewer's local verify is the evidence; quote it.

- 2026-10-28 done: PR #41 held unmerged until chat-values (my call)

- 2026-10-28 actuals: no agent records

### S18: helmfile-connector-fix-pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-matrix-connector/common.yaml`, `tests/test_matrix_connector_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py`
- Verified head: 051affd5f34b28eb547a765eebee66e45b978c81

#### Requirement

Pin agents-matrix-connector to merge commit c98c501 of PR #4 (review fixes mxc-outbound-limits and mxc-pool-and-binding; main CI run 40792219425 green incl images and chart-publish): chart `0.1.0-main.c98c501` in helmfile.yaml.gotmpl and the image tag `c98c501` in values/agents-matrix-connector/ (wherever the current edfb876 pin lives). The connector now enforces a per-room cap on outbound chunks per hour (new setting, default 60): keep the default unless the chart exposes it with a different value, and say which. Keep every other pin unchanged. Update tests/test_matrix_connector_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the connector chart version and image tag agree on c98c501 [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `tests/test_matrix_connector_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S19: mxc agent room policy

- Status: done
- Files: `src/agents_matrix_connector/policy.py`, `src/agents_matrix_connector/api/rooms.py`, `tests/test_policy.py`, `README.md`
- Verify: `uv run pytest tests/test_policy.py && mise run lint`
- Verified head: fc70272669797c8dc0ae4a18cb0b6ba08b0d22ba

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

README Non-goal, verbatim: "No change to the inbound allow/deny policy model."

Interrogate verdict Act on 2, verbatim: "Policy for agent sends with sender None (A,C high/medium): `policy.evaluate(_room_subject(room))` makes rooms allowed only by facebook:/user: rules default-deny for agents, and ignores deny rules on members. Define D4(a) precisely (my call): a room is policy-allowed for agent sends when a room/alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member; any member matching a deny rule denies. ACs: room allowed via facebook: rule passes; group with a denied member fails under default allow."

Design D4, verbatim: "(a) defined (interrogate Act 2, the lead's call): agents send with no sender, so the room subject alone (`policy.evaluate(_room_subject(R))`) would default-deny a room allowed only by `facebook:` or `user:` rules and would ignore deny rules on its members. R is policy-allowed for agent sends when a room or alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member of R; any member matching a deny rule denies. In order: an infrastructure or encrypted room is refused exactly as for inbound (`room_infrastructure`, `room_encrypted`); a room or alias deny rule denies (`denied: <kind>`); a deny rule (user, facebook or display_name) matching any current non-bot member denies (`denied: <kind>`); a room or alias allow rule allows; one current non-bot member for whom `policy.evaluate` with that member as sender allows makes R allowed; else `not_allowed`. A current non-bot member is a `room_members` row with membership `join` whose user id is not `MATRIX_USER_ID` and not in `MATRIX_SELF_IDENTITIES` or `MATRIX_BRIDGE_BOTS` (my call: the exclusion discovery already applies). One function, `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` over the pure `policy.evaluate_agent_room(room_subject, member_subjects, rules, default_policy)`, serves the api checks, the listing, the bot's claim and the send-time check (task mxc-agent-room-policy). The inbound policy model is unchanged (README Non-goal); this is how its rules read for a sender-less agent message."

Scope (agents-matrix-connector): `policy.py` (the pure `evaluate_agent_room`), `api/rooms.py` (`agent_room_decision`: the member filter and the subjects, built with the existing `_room_subject` and `_member_subject`), README (the access section says how a room is policy-allowed for agent sends). The routes (mxc-agent-routes) and the bot (mxc-bot-sends-delivery) call `agent_room_decision`; this task does not.

#### Acceptance conditions

- ac1: under default deny, a room matching a room or an alias allow rule is allowed for agent sends, with or without members [evidence: test:tests/test_policy.py::test_agent_room_allowed_by_room_rule]
- ac2: under default deny, a room whose only allow rule is a facebook or a user rule matching one current non-bot member is allowed, which the room subject alone would deny [evidence: test:tests/test_policy.py::test_agent_room_allowed_via_member_rule]
- ac3: a group with one member matching a deny rule (user, facebook or display_name) is denied with that rule's reason under default allow, and also when a room allow rule matches it [evidence: test:tests/test_policy.py::test_agent_room_denied_member_denies]
- ac4: a room with no matching rule under default deny, and a room with no current non-bot member and no room or alias allow rule under default allow, answer not_allowed [evidence: test:tests/test_policy.py::test_agent_room_not_allowed]
- ac5: an infrastructure room and an encrypted room are refused with room_infrastructure and room_encrypted, and a room or alias deny rule denies even when a member is allowed [evidence: test:tests/test_policy.py::test_agent_room_room_level_refusals]
- ac6: agent_room_decision counts only members with membership join whose user id is not MATRIX_USER_ID, a MATRIX_SELF_IDENTITIES id or a MATRIX_BRIDGE_BOTS id: a denied member that left, a denied self identity and a denied bridge bot change nothing [evidence: test:tests/test_policy.py::test_agent_room_decision_member_filter]
- ac7: the existing inbound policy tests pass unchanged, evaluate itself is not changed [evidence: command:uv run pytest tests/test_policy.py -k "not agent_room"]
- ac8: README says a room is policy-allowed for agent sends through a room or alias allow rule or an allowed current member, and that any denied member denies [evidence: command:grep -qi "policy-allowed for agent sends" README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_policy.py && mise run lint]

#### Files

- `src/agents_matrix_connector/policy.py`
- `src/agents_matrix_connector/api/rooms.py`
- `tests/test_policy.py`
- `README.md`

#### Interfaces

- `policy.py:evaluate_agent_room(room: Subject, members: Sequence[Subject], rules: Sequence[Rule], default_policy: str) -> Decision` (pure): `room` has `sender_id` None; each member subject carries the member as sender. Order (D4): infrastructure, encrypted, room/alias deny, member deny, room/alias allow, any member allowed by `evaluate`, else `not_allowed`. Reasons reuse `ROOM_INFRASTRUCTURE`, `ROOM_ENCRYPTED`, `denied(kind)`, `NOT_ALLOWED`; `rule_id` and `source` as in `evaluate`.
- `api/rooms.py:agent_room_decision(room: directory.RoomRow, rule_list: list[policy.Rule], settings: ConnectorSettings) -> policy.Decision`: members with `membership == "join"` whose `user_id` is not in `settings.self_ids()` or `settings.bridge_bots`, built with `_member_subject`; the room with `_room_subject`.
- `policy.evaluate` is unchanged.

#### Expected outcome

One function answers whether agents may post to a room under the user's existing rules: a chat allowed through a person's facebook or user rule is reachable, a chat with any denied member is not.

#### Steps

- Red: add the six `test_agent_room_*` tests to `tests/test_policy.py`; run `uv run pytest tests/test_policy.py`: they fail (no function).
- Green: `policy.evaluate_agent_room`, `api/rooms.py:agent_room_decision`, README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Pure and non-DB: build `directory.RoomRow` and `MemberRow` values in memory for the `agent_room_decision` test; the whole file runs locally.
- `room_infrastructure` and `room_encrypted` come first, exactly as `evaluate` does.
- Do not change `evaluate` or the inbound path (README Non-goal: no change to the inbound allow/deny policy model).
- The callers are mxc-agent-routes (routes and listing) and mxc-bot-sends-delivery (claim and send time); this task only provides the function.

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S20: plugins release 0.2.0

- Status: done
- Files: `orchestration/orchestrator/pyproject.toml`, `uv.lock`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py`
- Verify: `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint`
- Verified head: 073328ede436c782f832988ab8d0723e1b4378f8

#### Requirement

README Goal, verbatim: "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."

Design D13, verbatim: "any-mcp-tatara-plugins releases v0.2.0 (the orchestrator session pushes the tag after merge)."

Release number swap (design B2 and Irreversible operations, user decision 2026-10-27): this epic releases any-mcp-tatara-plugins v0.1.0 on top of v0.1.0, and slash-commands-from-chat releases v0.2.0 after it.

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `0.2.0`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.2.0`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): on main it pins `0.1.0`; it asserts `0.2.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.2.0 <merge sha> && git push origin v0.2.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push, not by the implementer or reviewer.

#### Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.2.0 (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:grep -q "ref=v0.2.0" orchestration/orchestrator/README.md && ! grep -q "ref=v0.1.0" orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.2.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.2.0)"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

#### Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `0.2.0`; git tag `v0.2.0` on the `main` merge commit.

#### Expected outcome

The orchestrator plugin with the chat tools is released as tag v0.2.0, so the orchestrator can pin it.

#### Steps

- Confirm the plugins' newest tag on origin is `v0.1.0` and `v0.2.0` does not exist yet (`git ls-remote --tags origin`); stop and report if not.
- Red: change `test_orchestrator_distribution_metadata` to 0.2.0; run `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the plugin README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag v0.2.0 <merge sha> && git push origin v0.2.0`, then check ac3.

#### Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in this pod with git 2.39 (`--end-of-options`); it is environmental (discovery sec 5) and CI is the gate for it.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done: PR #2 merged 4506e70, main CI 40736029763 green, tag v0.2.0 pushed (ac3 ok)

- 2026-10-28 actuals: no agent records

### S21: web room initiate toggle

- Status: done
- Files: `openapi/matrix.json`, `openapi/matrix.source`, `src/api/matrix-schema.d.ts`, `src/matrix/RoomDrawer.tsx`, `src/matrix/ChatsPage.test.tsx`
- Verify: `npx vitest run src/matrix && npm run check:api && npm run lint`
- Verified head: 431f8d23f9cec4a141871c989499f24d1f6309e9

#### Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D15, verbatim: "The room drawer gets an "Agents may start chats" switch bound to `agents_may_initiate`, saved with the preset and trigger in the one PUT (gate question Q4). The vendored `openapi/matrix.json` and generated `src/api/matrix-schema.d.ts` follow the connector's committed `openapi.json`."

Open question Q4 (pending gate), verbatim: "Add an 'agents may start chats' toggle to the agents-web room settings in this epic (my call, pending gate)?" recommended "yes".

Constraint (lead, verbatim): "agents-web toggle lands after markdown-rendering-in-chat and file-editor-with-tabs-and-hi (shared agents-web files)".

Scope (agents-web): `npm run sync:api -- matrix` from the agents-matrix-connector `main` that carries mxc-room-initiate-flag (updates `openapi/matrix.json`, `openapi/matrix.source`, `src/api/matrix-schema.d.ts`); `src/matrix/RoomDrawer.tsx` gets the switch (label "Agents may start chats", initial value from the room detail, saved in the same `setRoomSettings` call). `src/matrix/ChatsPage.test.tsx` test 'saves room settings' is no longer accurate (named): it expects the PUT body `{preset_id, trigger}` only; the body now always carries `agents_may_initiate`, so its two `toHaveBeenCalledWith` expectations gain the field (false here).

#### Acceptance conditions

- ac1: the room drawer shows an "Agents may start chats" switch reflecting agents_may_initiate, and Save sends it with the preset and trigger in one setRoomSettings call [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "agents may start chats"]
- ac2: saving the preset and trigger sends agents_may_initiate as loaded, so an untouched switch never changes the flag (updated) [evidence: command:npx vitest run src/matrix/ChatsPage.test.tsx -t "saves room settings"]
- ac3: the vendored matrix OpenAPI document and the generated types match, and matrix.source names the connector commit they came from [evidence: command:npm run check:api && grep -q '^agents-matrix-connector [0-9a-f]\{40\}$' openapi/matrix.source && grep -q agents_may_initiate openapi/matrix.json]
- ac4: the matrix UI tests and lint pass [evidence: command:npx vitest run src/matrix && npm run lint]

#### Files

- `openapi/matrix.json`
- `openapi/matrix.source`
- `src/api/matrix-schema.d.ts`
- `src/matrix/RoomDrawer.tsx`
- `src/matrix/ChatsPage.test.tsx`

#### Interfaces

- `RoomSettingsIn` (generated) gains `agents_may_initiate?: boolean | null`; `RoomView` gains `agents_may_initiate: boolean`.
- `RoomDrawer`: state `mayInitiate`, loaded from `RoomDetail.agents_may_initiate`, sent as `agents_may_initiate` in `setRoomSettings(roomId, {preset_id, trigger, agents_may_initiate})`.

#### Expected outcome

The user turns "Agents may start chats" on or off per room in the web UI.

#### Steps

- Sync: `npm run sync:api -- matrix` (reads the sibling agents-matrix-connector checkout at its `main`; confirm `main` carries the flag first).
- Red: add the "agents may start chats" test, update 'saves room settings'; run `npx vitest run src/matrix/ChatsPage.test.tsx`: they fail.
- Green: the switch in `RoomDrawer.tsx`; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Held until markdown-rendering-in-chat and file-editor-with-tabs-and-hi are done (README blockers).
- Use the MUI `Switch` with `FormControlLabel` as other drawers do; the label text is the accessible name the test queries.
- The connector keeps the stored flag when the field is omitted (mxc-room-initiate-flag), but the UI always sends it, so what the user sees is what is saved.
- The vendored `openapi/matrix.json` and the generated types also gain the room `binding` field (D9, mxc-room-initiate-flag); this task shows nothing new for it (noted, not doing now: a "bound to session <slug>" hint in the drawer). Under the 1:1 rule the flag lets an agent start a chat only while the room is unbound; the switch label stays "Agents may start chats".
- Retro (markdown-rendering-in-chat): one vitest test is flaky under load with no captured name; on a first-run failure capture the failing test name and the output tail before any rerun.

- 2026-10-28 done: openapi synced from connector branch 23f0424 (my call); CI 40735421358 pending at review

- 2026-10-28 actuals: no agent records

### S22: mxc agent routes

- Status: done
- Files: `src/agents_matrix_connector/api/agent.py`, `src/agents_matrix_connector/db/sends.py`, `src/agents_matrix_connector/db/bindings.py`, `src/agents_matrix_connector/api/openapi.py`, `openapi-agent.json`, `README.md`, `tests/test_api_agent.py`, `tests/test_readme_api.py`
- Verify: `uv run pytest tests/test_api_agent.py tests/test_readme_api.py tests/test_agent_gate.py && mise run lint`
- Verified head: 03801200ffbb1a15d97f63e214238bc6778f75f9

#### Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."
- "An agent can list the rooms it may post to and read the delivery status of what it sent."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

README Non-goal, verbatim: "No posting to arbitrary allowed rooms; no raw Matrix event ids from agents."

Design D2, verbatim (the connector side): "the connector's agent listener serves it under `/chat/v1` [...] Every upstream call carries `Authorization: Bearer <ORCH_CHAT_TOKEN>`, `X-Orch-Session: <session uuid>` and `X-Orch-Slug: <slug>`, and never the agent token. Responses: rooms 200 `{"rooms": [{room_id, name, kind, bound, agents_may_initiate}]}`; messages and reactions 202 `{id: "s<n>", status: "queued"}` (a duplicate, D5: the existing send's id and current status); status 200 `{id, kind, status, reason, room_id, created_at, sent_at}`. Errors use the shared `{"error": {"code", "message"}}` shape; the binding refusals of D4 (b) are 409 `room_bound` and 409 `session_bound`."

Design D4, verbatim: "Session S may post to room R only if both hold (architecture fork 2, pick): (a) R is policy-allowed for agent sends, checked when the api accepts the request, when the bot claims the send, and again right before each of its outbound rows is sent to the homeserver; (b) R is bound to S (D9), or R is unbound, `room_settings.agents_may_initiate` is true for R and S is bound to no room (an initiation: the bot's claim of the send binds R to S, D9). The api checks (b) when it accepts the request; the bot's claim re-checks it and is the authoritative binding step (the database's unique indexes decide a race, D9). [...] R is policy-allowed for agent sends when a room or alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member of R; any member matching a deny rule denies. [...] One function, `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` over the pure `policy.evaluate_agent_room(room_subject, member_subjects, rules, default_policy)`, serves the api checks, the listing, the bot's claim and the send-time check (task mxc-agent-room-policy). [...] Bound means an active `room_bindings` row pairing R and S (D9); nothing else binds (no `runs` or `sends` row is read as a binding, and the api writes no binding). A room reserved by another session's first run in progress (an active binding without a session yet, D9) counts as bound to another session. [...] Room choice for a send: `room` given, that room; `room` omitted and `reply_to` given, the room of the referenced message (my call); both omitted, S's bound room, and when S is bound to no room 422 `room_required`. A reaction's room is always its target's room. A room taken from `reply_to` or from a reaction's target goes through (a) and (b) exactly like a given room: a reply or reaction whose referenced message's room fails (a) answers 403 `room_not_allowed` and one failing (b) its (b) refusal below, including an `m<n>` of an ignored inbound row in a denied room (interrogate Act 4). An unknown room and a room failing (a) answer the same 403 `room_not_allowed` (my call: no probing of room existence). A room passing (a) but failing (b) answers, in this order (my call on the codes): 409 `room_bound` when R is bound to another session (or reserved by another session's first run), 403 `room_not_authorised` when R is unbound and not flagged, 409 `session_bound` when R is unbound and flagged but S is already bound to another room (D9 conflicts). `GET /chat/v1/rooms` lists exactly the rooms passing (a) and (b) for S: S's bound room when it passes (a), else, while S is bound to no room, every unbound flagged room passing (a); `bound` is true only for S's own room; the bound room first, then by name, then room id (my call: tiebreak pinned by a test). One predicate function serves the route checks and the listing."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". Design D9, verbatim (conflicts): "an agent of session S trying to start a chat in a room bound to another session (or reserved by another session's first run in progress) is refused 409 `room_bound`, synchronously at the api, and at the sender's claim as `refused` with reason `room_bound` when the binding appeared after the api accepted the send; a session already bound to a room trying a second, unbound flagged room is refused 409 `session_bound` (claim: `refused`, `session_bound`). Neither stores an outbound row or changes any binding. The room listing shows a bound session only its own room and an unbound session only unbound flagged rooms, so an agent that follows the listing meets neither refusal."

Design D5, verbatim: "`text`: 1 to 16000 characters (same bound as `session_send`) [...] `key`: 1 to 16 code points, no whitespace, no control characters and no ASCII characters; else 422 `invalid_key`. [...] Request bodies reject unknown fields (422 `invalid_request`). Duplicate (interrogate Act 9, the lead's call): an agent that retries after a 503 `chat_unavailable` timeout must not post twice. A request identical to a send of the same session, room and kind, with the same `text` (message) or `key` (reaction) and the same `reply_to` (the `m<n>`/`s<n>` given, or none; a reaction's `to`), compared exactly, with status `queued`, `sending` or `sent` and created within the last 60 s, answers 202 with that send's id and its current status (`{id: "s<n>", status: "queued" | "sending" | "sent"}`) and stores no new row (my call: `sending` is in flight like `queued`; a duplicate is not counted by the rate limit; a `failed` or `refused` send is not a duplicate, so a retry after a failure queues anew). Check order on the connector, a refusal queues nothing: token (401 `unauthorized`), body validation (422 `invalid_request`, `invalid_key`), reference resolution (422 `bad_reference`), room choice (422 `room_required`), (a) 403 `room_not_allowed`, (b) 409 `room_bound`, 403 `room_not_authorised`, 409 `session_bound` (D4), duplicate (202, the existing send), rate 429 `rate_limited`. The (b) check at the api, like the duplicate lookup and the rate count, is not atomic with the insert; the bot's claim re-checks (b) and refuses a send that lost a race (`refused` with reason `room_bound`, `session_bound` or `room_not_authorised`, D9)."

Design D5, verbatim (cap): "16000 characters of 4 bytes each are 64000 bytes raw (the plugin's httpx encodes JSON as raw UTF-8)" (interrogate Act 6: a maximal text of 4-byte characters is accepted end to end).

Design D6, verbatim: "It answers 422 `bad_reference` for an unknown id, an id of another room than the given `room`, an `s<n>` not yet `sent`, and an `s<n>` of another session; replying to a reaction or reacting to a reaction is 422 `bad_reference` too (my call). Raw Matrix event ids are never accepted. `GET /chat/v1/messages/{id}` answers 404 `not_found` for an id that is not one of the caller session's sends."

Design D16, verbatim (contract document): "the connector commits its agent listener OpenAPI document (`openapi-agent.json`, pinned like `openapi.json`)".

Scope (agents-matrix-connector): the four `/chat/v1` routes in `api/agent.py` (the (b) check reads the active binding of the room and of the session through `db/bindings.py`, never writes one) (`GET /chat/v1/rooms`, `POST /chat/v1/messages` body `{text, room?, reply_to?}`, `POST /chat/v1/reactions` body `{to, key}`, `GET /chat/v1/messages/{id}`), the (a) check through `api/rooms.py:agent_room_decision` (mxc-agent-room-policy) for given and derived rooms, the duplicate lookup, the session from `X-Orch-Session` (a uuid; missing or malformed is 401 `unauthorized`) and `X-Orch-Slug`; any helper queries in `db/sends.py`; `api/openapi.py` exports both documents; committed `openapi-agent.json`; README `## Agent API` section with one `### \`METHOD /chat/v1/...\`` heading per route, every error code and the send statuses and reasons.


Interrogate verdict, verbatim: "4. Reaction and reply room authorisation (A high): ACs proving a reaction, and a reply whose room comes from `reply_to`, are refused when the referenced message's room fails (a) or (b), including `m<n>` ids of ignored inbound rows in denied rooms." "9. Duplicate send on timeout retry (C medium): an agent retrying after 503 chat_unavailable can post twice. My call: the connector returns the existing s<n> (no new row) for an identical (session, room, kind, text or key, reply_to) queued or sent within the last 60 s. AC." "2. [...] ACs: room allowed via facebook: rule passes; group with a denied member fails under default allow." "6. [...] with an AC sending 16000 4-byte characters end to end."

#### Acceptance conditions

- ac1: a send to a policy-allowed unbound room flagged agents_may_initiate, from a session bound to no room and with no run and no inbound row there, answers 202 {id: s<n>, status: queued}, stores a queued sends row with the session, slug, room and text, and writes no binding (the bot binds at claim) [evidence: test:tests/test_api_agent.py::test_send_to_flagged_room_without_inbound]
- ac2: the room bound to the session is accepted unflagged; with room omitted the session's bound room is used and a session bound to no room answers 422 room_required; with room omitted and reply_to given the referenced message's room is used [evidence: test:tests/test_api_agent.py::test_room_choice]
- ac3: an unknown room and a policy-denied room answer 403 room_not_allowed, an allowed unbound unflagged room answers 403 room_not_authorised, and no refusal stores a row [evidence: test:tests/test_api_agent.py::test_room_refusals_queue_nothing]
- ac4: a flagged room bound to another session, and one reserved by another session's first run in progress, answer 409 room_bound even when flagged; a session bound to one room sending to a second, unbound flagged room answers 409 session_bound; a room bound to the caller but failing (a) answers 403 room_not_allowed; none stores a row or changes a binding [evidence: test:tests/test_api_agent.py::test_binding_refusals]
- ac5: a flagged room allowed only by a facebook rule matching a current member is accepted under default deny, and a flagged group with a member matching a deny rule answers 403 room_not_allowed under default allow, the routes using agent_room_decision [evidence: test:tests/test_api_agent.py::test_policy_member_rules]
- ac6: a reaction, and a reply with room omitted whose room comes from reply_to, answer 403 room_not_allowed when the referenced message's room fails (a), and 409 room_bound, 403 room_not_authorised or 409 session_bound when it fails (b), including an m<n> of an ignored inbound row in a denied room and an m<n> of a room bound to another session, and store nothing [evidence: test:tests/test_api_agent.py::test_derived_room_authorised]
- ac7: reply_to m<n> and s<n> store the resolved event id; an unknown id, another room's id, an unsent s<n>, another session's s<n>, a reaction target and a raw event id answer 422 bad_reference [evidence: test:tests/test_api_agent.py::test_reply_references]
- ac8: a reaction takes its target's room, stores kind reaction with the key, and a key with ASCII, whitespace, control characters or more than 16 code points answers 422 invalid_key [evidence: test:tests/test_api_agent.py::test_reactions]
- ac9: a request identical in session, room, kind, text or key and reply_to to a queued, sending or sent send created within the last 60 s answers 202 with that send's id and current status and stores no row; a changed field, an older send, or a failed or refused send queues a new row; a duplicate is answered even at the rate limit [evidence: test:tests/test_api_agent.py::test_duplicate_returns_existing_send]
- ac10: after MATRIX_AGENT_RATE_PER_MINUTE sends of one session in 60 s the next answers 429 rate_limited and stores nothing, while another session is unaffected [evidence: test:tests/test_api_agent.py::test_rate_limit]
- ac11: empty or longer than 16000 characters text and unknown body fields answer 422 invalid_request; a text of exactly 16000 4-byte characters is accepted and stored unchanged; a missing or malformed X-Orch-Session answers 401 unauthorized [evidence: test:tests/test_api_agent.py::test_validation]
- ac12: GET /chat/v1/rooms lists for a bound session only its bound room (bound true) when it passes (a), and for a session bound to no room every unbound flagged room passing (a), never a room bound to or reserved by another session, ordered bound room first, then by name, then room id [evidence: test:tests/test_api_agent.py::test_rooms_listing_order]
- ac13: for a matrix of rooms (allowed by a room rule, by a member rule, denied by a room rule, denied by a member; bound to the caller, bound to another session, reserved, flagged unbound, neither) and callers bound and unbound, the listing and the send check agree room by room, because one predicate serves both [evidence: test:tests/test_api_agent.py::test_listing_matches_send_checks]
- ac14: GET /chat/v1/messages/{id} returns the caller session's send with status, reason, room and times, and 404 not_found for another session's or an unknown id [evidence: test:tests/test_api_agent.py::test_status_own_sends_only]
- ac15: the committed openapi-agent.json matches the agent app [evidence: test:tests/test_readme_api.py::test_agent_openapi_committed_matches]
- ac16: README `## Agent API` lists every /chat/v1 route and names every error code (room_bound and session_bound included), send status and reason, the duplicate rule and the 1:1 binding rule [evidence: test:tests/test_readme_api.py::test_readme_lists_every_agent_route]
- ac17: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_agent.py tests/test_readme_api.py tests/test_agent_gate.py && mise run lint]

#### Files

- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/bindings.py`
- `src/agents_matrix_connector/api/openapi.py`
- `openapi-agent.json`
- `README.md`
- `tests/test_api_agent.py`
- `tests/test_readme_api.py`

#### Interfaces

- `GET /chat/v1/rooms` -> 200 `{"rooms": [{"room_id", "name", "kind", "bound", "agents_may_initiate"}]}`: the caller's bound room only (`bound` true), or, for a caller bound to no room, every unbound flagged room passing (a).
- `POST /chat/v1/messages` body `{"text": str, "room": str | null, "reply_to": "m<n>" | "s<n>" | null}` -> 202 `{"id": "s<n>", "status": "queued"}`; a duplicate (D5) -> 202 with the existing id and its status `queued`, `sending` or `sent`.
- `POST /chat/v1/reactions` body `{"to": "m<n>" | "s<n>", "key": str}` -> 202 `{"id": "s<n>", "status": "queued"}`.
- `GET /chat/v1/messages/{id}` (`id` is `s<n>`) -> 200 `{"id", "kind", "status", "reason", "room_id", "created_at", "sent_at"}`.
- Errors `{"error": {"code", "message"}}`: 401 `unauthorized`, 404 `not_found`, 422 `invalid_request`, `invalid_key`, `bad_reference`, `room_required`, 403 `room_not_allowed`, `room_not_authorised`, 409 `room_bound`, `session_bound`, 429 `rate_limited`, 503 `unavailable` (database).
- One predicate, for example `api/agent.py:may_post(conn, session_id, room, rules, settings) -> Literal["ok", "room_not_allowed", "room_bound", "room_not_authorised", "session_bound"]`, used by the send and reaction routes (for given and derived rooms) and by the listing; its (a) part is `api/rooms.py:agent_room_decision` (mxc-agent-room-policy), its (b) part reads `db/bindings.py:active_for_room` and `active_for_session` (mxc-sends-schema) and `room_settings.agents_may_initiate`, in the D4 order (room_bound, room_not_authorised, session_bound).
- `db/sends.py:find_duplicate(conn, *, session_id, room_id, kind, text, key, reply_to, seconds=60) -> SendRow | None` (name left to the builder): the newest queued, sending or sent send matching exactly.
- `api/openapi.py`: `export()` (UI, unchanged) and `export_agent()`; `python -m agents_matrix_connector.api.openapi --agent > openapi-agent.json` (or an equivalent documented command).

#### Expected outcome

The orchestrator can ask the connector, on the session's behalf, which rooms it may post to (its one bound room, or the unbound flagged rooms while it has none), queue a message, a quoted reply or a reaction there, and read back what happened, with every refusal (including `room_bound` and `session_bound`) synchronous and nothing queued on a refusal.

#### Steps

- Red: write `tests/test_api_agent.py` and the two README/OpenAPI tests; run `uv run pytest tests/test_api_agent.py tests/test_readme_api.py`: the new tests fail.
- Green: routes, predicate, any repository helpers, OpenAPI export and README; regenerate both documents; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- (a) is `api/rooms.py:agent_room_decision(room, rules.list_rules(...), settings)`; never `policy.evaluate` on the room subject alone (interrogate Act 2). Import it rather than copying it.
- The room ordering rule is a tiebreak ruling: its pin test is `test_rooms_listing_order` (retro proposal). The single-predicate rule is pinned by `test_listing_matches_send_checks` (retro proposal: duplicate-predicate sweep before the last code task merges).
- The api only inserts `sends`; it never updates them (single writer, D7). It never writes `room_bindings` either: an initiation is accepted with no binding, and the bot binds at claim (D9); seed bindings in tests with plain INSERTs. Any new reader goes in `db/bindings.py`, no writer.
- `tests/test_api_agent.py` is DB-backed (CI); keep the key validator and the reference parser as pure functions with non-DB tests in it too.
- The rate limit, the duplicate lookup and the (b) binding check are advisory like the orchestrator's session-message limits: the lookup or count and the insert are not one atomic step, and the bot's claim re-checks (b) (D5, D9); document that in README.
- A duplicate is checked after (b) and before the rate limit, so a retry at the limit still gets its `s<n>` (D5 check order).

- 2026-10-27 amended: interrogate.md Acts 2, 4, 6, 9: member-aware (a), derived-room authorisation, 16000 4-byte text, duplicate returns the existing send

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): (b) through room_bindings, 409 room_bound and session_bound, listing

- 2026-10-28 done: CI 40740444262 green; MEMORY entries for implementer calls follow in a docs commit

- 2026-10-28 actuals: no agent records

### S23: mxc bot sends delivery

- Status: done
- Files: `src/agents_matrix_connector/sender.py`, `src/agents_matrix_connector/bot.py`, `src/agents_matrix_connector/db/runs.py`, `src/agents_matrix_connector/db/sends.py`, `src/agents_matrix_connector/db/bindings.py`, `src/agents_matrix_connector/tracker.py`, `tests/test_sender.py`, `tests/test_tracker.py`
- Verify: `uv run pytest tests/test_sender.py tests/test_tracker.py && mise run lint`
- Verified head: 18963f2cf28e23055874352f1aa5dd1bde71dcfe

#### Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can send several messages in a row without a user reply in between (follow-ups), including while a chat-started turn is still running."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."

Design D7, verbatim (the flow): "Flow: the api inserts `sends(queued)`; a new bot step (`sender.py`, run in the bot work loop between `Worker.tick` and `Tracker.tick`) claims queued rows `queued -> sending`, re-checks (a) (denied: `refused` with the policy reason, no outbound row) and (b) (D4; a room bound to another session, a session bound elsewhere or an unflagged unbound room: `refused` with reason `room_bound`, `session_bound` or `room_not_authorised`, no outbound row), binds an unbound flagged room to the send's session in the same transaction when (b) holds through the flag (D9), and inserts the outbound rows in the same transaction with transaction ids `mxa-<send id>-<n>` (message chunks) or `mxa-<send id>-r` (reaction); `Tracker._send_pending` sends every pending row with its own event type and content; before it sends a row of a send (kind `agent` or `reaction`) it re-checks (a) for that row's room, and when (a) now fails it marks every still-pending outbound row of that send `failed` with the policy reason and moves the send `sending -> refused` with the same reason, in one transaction, and sends nothing of it (interrogate Act 10: rows already pending while the homeserver was down are not delivered after the policy turned to deny; my call: chunks already sent stay sent); once every outbound row of a `sending` send has ended, the bot marks it `sent` (all sent, `event_id` of the first row) or `failed` (the first failed row's reason); a send that ends `failed` or `refused` with none of its outbound rows sent releases, in that transaction, the binding it created (`send_failed`, D9). Sends never wait on `inbound.rooms_ready`, so follow-ups go out while a chat run is in progress (G2). `sends` rows that ended and released `room_bindings` rows are pruned with the existing daily retention. "

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Design D9, verbatim (agent initiation): "Agent initiation in an unbound flagged room: the api accepts the send (D4 (b), advisory); the bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active `agent` binding (session id and slug of the send, its send id) when the room is still unbound, still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never makes a second binding. If that send then ends with none of its outbound rows sent (`failed`, or `refused` at send time, D7), the settle transaction releases the binding it created (`send_failed`, my call: a binding message that never reached the user binds nothing). A send of a session into the room it is bound to binds nothing new."

Design D9, verbatim (conflicts): "an agent of session S trying to start a chat in a room bound to another session (or reserved by another session's first run in progress) is refused 409 `room_bound`, synchronously at the api, and at the sender's claim as `refused` with reason `room_bound` when the binding appeared after the api accepted the send; a session already bound to a room trying a second, unbound flagged room is refused 409 `session_bound` (claim: `refused`, `session_bound`). Neither stores an outbound row or changes any binding."

Design D7, verbatim (retention): "`sends` rows that ended and released `room_bindings` rows are pruned with the existing daily retention."

Design D8, verbatim: "Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id": E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676; removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation", "event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is the one PUT; `send_text` becomes a call of it."

Design D4, verbatim (the checks): "(a) R is policy-allowed for agent sends, checked when the api accepts the request, when the bot claims the send, and again right before each of its outbound rows is sent to the homeserver". "(a) defined [...] R is policy-allowed for agent sends when a room or alias rule allows it, or when the inbound policy would accept a message from at least one current non-bot member of R; any member matching a deny rule denies. [...] One function, `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` [...] serves the api checks, the listing, the bot's claim and the send-time check (task mxc-agent-room-policy)."

Design D5, verbatim (chunking): "`text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`."

Interrogate verdict Act on 5, verbatim: "Tracker test spy (A high): mxc-bot-sends-delivery switches Tracker._send_pending to send_event but tests/test_tracker.py (SpyMatrix has only send_text/typing) is not in its files while ac10 demands it unchanged. Add the file and let the spy gain send_event; ac10 becomes "existing assertions unchanged"."

Interrogate verdict Act on 10, verbatim: "Policy re-check at send time (C medium): agent outbound rows already pending are delivered after a policy flip to deny when the homeserver was down. Re-check (a) when sending agent rows; refuse them (sends -> refused, reason policy) otherwise."

Scope (agents-matrix-connector): new bot module `sender.py` (claim, policy re-check through `agent_room_decision`, the binding re-check and the initiation binding through `db/bindings.py`, outbound rows, settle and the release of a failed initiation), its place in `bot.py:_work_loop` (worker, sender, tracker), `db/runs.py` (`OutboundRow` and `add_outbound` carry `send_id`, `event_type`, `relates_to` and the `agent`/`reaction` kinds with `mxa-` txn ids), any queries in `db/sends.py`, `tracker.py` (`_send_pending` sends each row with its event type and content through `send_event` and re-checks (a) before each agent row; `_prune_daily` prunes ended sends and released bindings), `tests/test_sender.py`, `tests/test_tracker.py` (`SpyMatrix` gains `send_event`; its existing assertions unchanged). `MatrixClient.send_event` comes from mxc-matrix-send-event and `agent_room_decision` from mxc-agent-room-policy. The existing reply and notice path is unchanged.

#### Acceptance conditions

- ac1: a queued message send into the room bound to its session becomes sending with outbound rows mxa-<id>-1..n of kind agent, the reply relation only on the first chunk and no fallback body, and the homeserver receives them in order [evidence: test:tests/test_sender.py::test_message_send_chunks_and_reply_relation]
- ac2: a queued reaction becomes one outbound row mxa-<id>-r of event type m.reaction with an m.annotation relation and the key, and the homeserver receives that content [evidence: test:tests/test_sender.py::test_reaction_send]
- ac3: at claim, a send whose room fails (a) through agent_room_decision (a member now matches a deny rule, or the room's allow rule was removed) is refused with the policy reason and gets no outbound row, while a room allowed only through a current member's facebook rule is delivered [evidence: test:tests/test_sender.py::test_policy_recheck_refuses]
- ac4: at claim, a send to an unbound flagged room from a session bound to no room binds that room to the send's session (origin agent, the send's id and slug) in the claim transaction and is delivered [evidence: test:tests/test_sender.py::test_claim_binds_unbound_flagged_room]
- ac5: at claim, a send whose room is now bound to or reserved by another session is refused room_bound, one whose session is now bound to another room session_bound, and one to an unbound room no longer flagged room_not_authorised; two queued sends of two sessions to one unbound flagged room bind it to the first claimed and refuse the other room_bound; none of the refused gets an outbound row or changes a binding [evidence: test:tests/test_sender.py::test_claim_refuses_binding_conflicts]
- ac6: a send that bound its room and ends failed or refused with none of its outbound rows sent releases that binding with reason send_failed in the settle transaction; one with a sent chunk keeps it, and a failed send into an already bound room releases nothing [evidence: test:tests/test_sender.py::test_failed_initiation_releases_binding]
- ac7: a send whose outbound rows are still pending when (a) turns to deny (the homeserver was down, then a deny rule was added) sends nothing further: its pending rows are failed with the policy reason and the send becomes refused with it, while reply and notice rows of runs are sent as before [evidence: test:tests/test_tracker.py::test_agent_rows_rechecked_before_send]
- ac8: a sending send becomes sent with the first row's event id once all its rows are sent, and failed with the first failed row's reason when one failed [evidence: test:tests/test_sender.py::test_settle_sent_and_failed]
- ac9: sends to a room whose chat run is still in progress are delivered before that run ends [evidence: test:tests/test_sender.py::test_sends_go_out_during_running_chat_run]
- ac10: a restart between the homeserver send and the sent mark resends the same txn id and the room gets each event once [evidence: test:tests/test_sender.py::test_restart_exactly_once]
- ac11: the bot work loop runs the worker, the sender and the tracker in that order each interval, and a sender failure other than a lost token does not stop the loop [evidence: test:tests/test_sender.py::test_bot_loop_runs_sender_between_worker_and_tracker]
- ac12: the daily prune also deletes ended sends and released bindings older than the retention [evidence: test:tests/test_sender.py::test_daily_prune_includes_sends]
- ac13: the tracker sends reply and notice rows through send_event with the m.room.message content send_text sent, the test SpyMatrix records send_event calls, and the existing tracker test assertions are unchanged [evidence: command:uv run pytest tests/test_tracker.py]
- ac14: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_sender.py tests/test_tracker.py && mise run lint]

#### Files

- `src/agents_matrix_connector/sender.py`
- `src/agents_matrix_connector/bot.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/bindings.py`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_sender.py`
- `tests/test_tracker.py`

#### Interfaces

- Uses `matrix.py:MatrixClient.send_event(room_id, event_type, txn_id, content) -> str` (mxc-matrix-send-event) and `api/rooms.py:agent_room_decision(room, rule_list, settings) -> policy.Decision` (mxc-agent-room-policy).
- `sender.py` (new): `class Sender(pool, settings, *, now=utcnow)` (the matrix client is not a Sender dependency; review fix 2026-10-28) with `async tick()`: claim queued sends; per send, in its claim transaction, re-check (a) through `agent_room_decision`, then (b) through `db/bindings.py` (`active_for_room`, `active_for_session`, the room flag, and `bind_for_send` for an unbound flagged room), refusing `room_bound`, `session_bound` or `room_not_authorised`; insert outbound rows; settle sending sends whose rows all ended, releasing (`send_failed`) a binding the send created when none of its rows was sent.
- `tracker.py:Tracker._prune_daily` also calls `sends.prune` and `bindings.prune_released` with the existing retention.
- `db/runs.py:add_outbound(conn, *, room_id, run_id=None, send_id=None, kind, chunks, event_type="m.room.message", relates_to=None)`; txn ids `mxc-<run>-<n>`, `mxc-<run>-notice` (unchanged), `mxa-<send>-<n>`, `mxa-<send>-r`. `OutboundRow` gains `send_id`, `event_type`, `relates_to`.
- `tracker.py:Tracker._send_pending` builds each row's content from `event_type`, `body` and `relates_to` and calls `send_event`; for a row with a `send_id` it first re-checks (a) for the row's room (rules and the room loaded once per pass) and, when denied, fails the send's pending rows, moves the send `sending -> refused` with the policy reason and, when none of its rows was sent, releases a binding the send created (`send_failed`), in one transaction.
- `tests/test_tracker.py:SpyMatrix` gains `send_event`, recording `(room_id, event_type, txn_id, content)`.

#### Expected outcome

Every accepted agent send reaches the room as a message (chunked, optionally a quoted reply) or a reaction, exactly once, at once, even while a chat run is in progress, and its status reports how it ended; an initiation binds its room to its session at claim, a send that lost a binding race is refused before anything is sent, and an initiation that never reached the user leaves the room unbound.

#### Steps

- Red: write `tests/test_sender.py`, add `test_agent_rows_rechecked_before_send` and the `SpyMatrix.send_event` spy to `tests/test_tracker.py`; run `uv run pytest tests/test_sender.py tests/test_tracker.py`: the new tests fail.
- Green: `db/runs.py`, `db/sends.py`, `db/bindings.py` (only if a query is missing), `sender.py`, `tracker.py`, `bot.py`; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Reuse `MatrixClient._request` and its error taxonomy, `chunks.split`, the deterministic txn-id scheme and `Tracker._send_pending`'s ordering (an unavailable homeserver stops the pass; a lost token propagates) (discovery "reuse").
- The fake homeserver's `_send` (`fake_homeserver.py`) already accepts any event type and records content: assert relations on what it recorded.
- Typing stays keyed by run id; agent sends neither start nor stop typing.
- Every (a) check (claim and send time) calls `api/rooms.py:agent_room_decision` with `rules.list_rules` and the settings, the same function as the api; never `policy.evaluate` on the room subject alone (interrogate Act 2).
- The bot is the only mover of `sends` and the only writer of `outbound` and `room_bindings` (D7, D9); every status move goes through `queue.transition`. A unique-index conflict in `bind_for_send` is mapped to a refusal inside a savepoint, so the claim transaction of the other sends in the batch survives.
- `tests/test_sender.py` and `tests/test_tracker.py` are DB-backed (CI). Keep the content builder (event type, body, relation) a pure function with a non-DB test in `tests/test_sender.py` so the local run has signal.
- `tests/test_tracker.py`: the spy gains `send_event`; no existing assertion is edited (interrogate Act 5).

- 2026-10-27 amended: interrogate.md Acts 2, 5, 10: member-aware (a) at claim and send time, tests/test_tracker.py added with a send_event spy, send_event split out to mxc-matrix-send-event

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding at claim, claim-time refusals, release of a failed initiation, prune

- 2026-10-28 done: fix1 dropped unused matrix param; CI 40744168950 green

- 2026-10-28 actuals: no agent records

### S24: orch plugins pin 0.2.0

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint`
- Verified head: af167e81460d0fa45e16099cef440eea61bed4ce

#### Requirement

README Goal, verbatim: "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."

Design D13, verbatim: "The orchestrator then pins v0.2.0 and adds `CHAT_TOOLS` to every session's allow list (`k8s/on_start.py:orchestrator_allow`); the routes decide." (This task: the pin; orch-chat-tools-allow: the allow list.)

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.2.0` on origin (task plugins-release-0-3-0).

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.2.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.2.0#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.2.0` and the `## Images` plugins release tag.
- `tests/test_settings.py::test_defaults` is no longer accurate (named): on main it pins `any_mcp_plugins_ref == "v0.1.0"`; it asserts `v0.2.0`.
- No agents-helmfile change (helmfile-chat-values).

#### Acceptance conditions

- ac1: the settings default is v0.2.0 (updated) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.2.0 default and no longer names v0.1.0 for the plugins [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.2.0` |' README.md && ! grep -qF 'plugins release tag (`v0.1.0`)' README.md]
- ac4: the pinned orchestrator plugin carries the chat tools [evidence: command:grep -rq "chat_send" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

#### Interfaces

- `Settings.any_mcp_plugins_ref` default `v0.2.0` (`ORCH_ANY_MCP_PLUGINS_REF`); dev dependency `any-mcp-tatara-orchestrator` at `v0.2.0`.

#### Expected outcome

Agent pods rendered by this orchestrator install the plugins release that offers the chat tools.

#### Steps

- Confirm tag `v0.2.0` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.2.0`); stop and report if absent.
- Red: change `test_defaults` to v0.2.0; run `uv run --frozen pytest tests/test_settings.py tests/test_images.py`: fails.
- Green: settings default, pyproject pin, `uv lock`, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties dev dependency, uv.lock and the default to one tag.
- Since the swap this epic precedes slash-commands: it builds on main (plugins pin v0.1.0), not on slash-commands' pin task.
- The README check of ac3 matches README line 120 ("plugins release tag (`v0.1.0`)"); read the README first and adapt the grep only in wording if the sentence differs, keeping the intent (no v0.1.0 plugins pin left).
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); the deploy is chat-live-smoke.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S25: chat smoke script

- Status: done
- Files: `scripts/chat-smoke.sh`, `mise.toml`, `tests/test_chat_smoke_script.py`, `README.md`, `tests/test_mise_tasks.py`
- Verify: `uv run pytest tests/test_chat_smoke_script.py tests/test_mise_tasks.py && mise run lint`
- Verified head: 0804582c1488b5b936ee1969aa62bfd61ac923e9

#### Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D17, verbatim: "`scripts/chat-smoke.sh` (mise task `chat-smoke`), never part of `scripts/smoke.sh`, because it posts real messages from the owner's Facebook account. Under the 1:1 binding (D9) only the owner DM's bound session may post there, so the script first reads the owner DM's `binding` through the connector UI API (port-forward to the api container) and picks its caller (gate question Q11, recommended; my call pending the answer): when the DM is bound, the leader pod of the bound session (that pod's own `ORCH_AGENT_*` env, never printed; no message to or change of that session, nothing created or deleted); when it is unbound, a throwaway alone session whose S1 initiates and binds the DM, deleted at the end, after which the script waits for the binding's release (its own deadline). From the chosen pod it calls the orchestrator agent routes: lists rooms (the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` must be listed), S1 sends a message with no inbound in the run, S2 replies to S1's `s<n>`, S3 reacts with a thumbs-up to S1's `s<n>`, S4 reacts with a second, different emoji to the same target; it polls each send's status to `sent` or `failed` with its own deadline per wait, prints the caller (bound session or throwaway), the binding before and after, the ids, statuses and reasons, owns its port-forwards (trap cleanup) and deletes the throwaway session when it made one."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Open question Q11 (pending; the plan follows the recommended answer), verbatim: "Under the 1:1 rule a throwaway smoke session is refused room_bound in the owner DM whenever the DM is already bound to its chat session (for example the mx-5 hive leader). Should chat-smoke run S1-S4 from the leader pod of the session the owner DM is bound to (only that pod's own agent credentials; no message to or change of that session, nothing created or deleted), and create a throwaway session that initiates there and is deleted afterwards (releasing the binding) only when the owner DM is unbound?" recommended "yes".

Architecture, verbatim: "S1 a send with no inbound message for >24h shows up in Messenger; S2 a reply shows as a quoted reply; S3 a thumbs-up reaction shows; S4 a second, different reaction replaces the first or is rejected (and how the connector sees the failure)."

Open question Q8 (approved by the user 2026-10-27), verbatim: "S1 runs at smoke time even if the owner DM had an inbound message in the last 24 h; the smoke records the hours since the last inbound, and the over-24h case is confirmed at the first natural opportunity and noted in agents-helmfile MEMORY.md without holding the epic?" answer "yes".

Retro proposals, verbatim: "for smoke-script tasks the reviewer checks every timeout or deadline against the AC and the MEMORY claim" and "smoke script owns its port-forward (trap cleanup, kill stale on the port first) and orchestrator runs no manual port-forwards during smoke."

Scope (agents-helmfile): new `scripts/chat-smoke.sh` (env `RELEASE`, `NAMESPACE`, `CHAT_SMOKE_ROOM` default `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`, `CHAT_SMOKE_PRESET` or the default preset, `CHAT_SMOKE_TIMEOUT_S` per wait, `MATRIX_RELEASE`, `SMOKE_LOCAL_PORT`, `SMOKE_MATRIX_API_LOCAL_PORT`); it also reads, through a port-forward to the connector api container, the room's `binding` (to pick its caller, D17) and newest inbound message time, and prints the hours since it (S1 precondition, Q8). New mise task `chat-smoke`; README names the task and says it posts to the owner DM; `tests/test_chat_smoke_script.py` with kubectl and curl fakes.

#### Acceptance conditions

- ac1: against fakes the script lists the rooms, runs S1, S2 (reply_to S1's id), S3 (thumbs-up to S1's id) and S4 (a different emoji to S1's id) in that order, prints each id, status and reason, and exits 0 when S1-S3 end sent [evidence: test:tests/test_chat_smoke_script.py::test_s1_to_s4_happy_path]
- ac2: when the owner DM's binding names a session, the script runs S1-S4 from that session's leader pod with that pod's own agent env, creates and deletes no session, sends no message to that session, and prints the caller and the binding before and after [evidence: test:tests/test_chat_smoke_script.py::test_bound_dm_uses_bound_session]
- ac3: when the owner DM is unbound, the script creates a throwaway session whose S1 initiates there, deletes it at the end and waits, with its own deadline, until the DM's binding is released, printing the binding before, during and after; a binding still held at that deadline exits 1 naming the step [evidence: test:tests/test_chat_smoke_script.py::test_unbound_dm_uses_throwaway_and_waits_release]
- ac4: when the owner DM is not listed for the chosen caller the script exits 1 naming the room and sends nothing [evidence: test:tests/test_chat_smoke_script.py::test_room_not_listed_stops_before_sending]
- ac5: every status wait has its own CHAT_SMOKE_TIMEOUT_S deadline, so a slow S1 does not shorten S3's wait, and a timeout exits 1 naming the step [evidence: test:tests/test_chat_smoke_script.py::test_each_wait_has_its_own_deadline]
- ac6: an S4 that ends failed or is refused is printed with its status and reason and does not fail the script, while a failed S1, S2 or S3 exits 1 [evidence: test:tests/test_chat_smoke_script.py::test_s4_failure_is_reported_not_fatal]
- ac7: the script prints the hours since the room's newest inbound message before S1 [evidence: test:tests/test_chat_smoke_script.py::test_prints_hours_since_last_inbound]
- ac8: no token or ORCH_AGENT_* value is printed, a stale port-forward on its port is killed first, and the trap deletes the throwaway session (only one the script created) and kills its port-forwards on success, failure and interrupt [evidence: test:tests/test_chat_smoke_script.py::test_cleanup_and_no_secrets]
- ac9: the fakes replay response bodies with the shapes of the connector's committed openapi-agent.json and openapi.json (the room binding) and the orchestrator README chat section [evidence: judgement:reviewer compares the fake bodies with openapi-agent.json and openapi.json on agents-matrix-connector main]
- ac10: the mise task chat-smoke runs the script and README names it [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- ac11: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_chat_smoke_script.py tests/test_mise_tasks.py && mise run lint]

#### Files

- `scripts/chat-smoke.sh`
- `mise.toml`
- `tests/test_chat_smoke_script.py`
- `README.md`
- `tests/test_mise_tasks.py`

#### Interfaces

- `mise run chat-smoke` = `bash scripts/chat-smoke.sh`.
- Output lines: `caller: bound <slug>` or `caller: throwaway <slug>`, `binding before: <slug or none>`, `hours since last inbound: <n>`, `S1 s<n> sent`, `S2 s<n> sent`, `S3 s<n> sent`, `S4 s<n> <status> <reason>`, `binding after: <slug or none>`.
- Reads `binding` from `GET /matrix/api/v1/rooms/{room_id}` of the connector UI API (mxc-room-initiate-flag) through the api container port-forward.

#### Expected outcome

One command proves send without inbound, quoted reply and reactions against the live deployment, leaving no session or port-forward behind.

#### Steps

- Red: write `tests/test_chat_smoke_script.py` following `tests/test_smoke_script.py` (PATH-injected kubectl and curl fakes); run `uv run pytest tests/test_chat_smoke_script.py`: fails (no script).
- Green: write the script and the mise task, README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Reuse `scripts/smoke.sh`'s patterns: session creation through the orchestrator API port-forward, waiting for a Ready pod, running curl inside the pod with its own `ORCH_AGENT_*` env (never printed), trap cleanup.
- Bound case (Q11, recommended answer; the plan follows it until Q11 is answered): the caller is the bound session's leader pod. How to find that pod for a hive session is a fact to probe at build time (the orchestrator API's session view and the pod labels `agents.szymonrichert.pl/session=<slug>` used by `scripts/smoke.sh`); if neither names the leader pod, return it as a question, never guess. The script only runs curl in that pod; it never posts a session message, never scales, restarts or deletes that session.
- The calls go through the orchestrator agent routes from inside the session pod (agent identity is the pod IP), never directly to the connector agent port, so the smoke proves the whole path including the relay.
- Each wait gets its own deadline variable computed when that wait starts (retro: a shared deadline failed a smoke spuriously).
- Never add these steps to `scripts/smoke.sh`: that smoke must never send a Matrix message.

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): caller picked from the owner DM binding (Q11)

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S26: mxc api blank text

- Status: done
- Files: `src/agents_matrix_connector/api/agent.py`, `tests/test_api_agent.py`, `MEMORY.md`
- Verify: `uv run pytest tests/test_api_agent.py && mise run lint`
- Verified head: ed9c0f71164f5efe4fe56c01d9f967982f7d8224

#### Requirement

Discovered by mxc-bot-sends-delivery (2026-10-28): the `/chat/v1` message route accepts a text that is only whitespace; the sender then fails that send as `empty_text`, so the agent gets 202 for a message that can never be delivered.

Design D5, verbatim: "`text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`."

Rule (my call, recorded in the connector MEMORY.md): a text with no non-whitespace character counts as empty and is refused at the api with 422 `invalid_text` (the same code and status as an empty text), nothing queued. The sender keeps its `empty_text` failure as a defence for rows queued before this change.

#### Acceptance conditions

- ac1: a message whose text is only whitespace is refused with 422 invalid_text and no sends row is written [evidence: test:tests/test_api_agent.py::test_whitespace_only_text_refused]
- ac2: MEMORY.md records the whitespace rule [evidence: command:grep -qi "whitespace" MEMORY.md]
- ac3: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_agent.py && mise run lint]

#### Files

- `src/agents_matrix_connector/api/agent.py`
- `tests/test_api_agent.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done: CI 40750406829 green

- 2026-10-28 actuals: no agent records

### S27: mxc room session binding

- Status: done
- Files: `src/agents_matrix_connector/worker.py`, `src/agents_matrix_connector/db/runs.py`, `src/agents_matrix_connector/db/bindings.py`, `MEMORY.md`, `README.md`, `tests/test_worker.py`, `tests/test_runs_repo.py`
- Verify: `uv run pytest tests/test_runs_repo.py tests/test_worker.py && mise run lint`
- Verified head: 9c031d0d9dfd5c3d52a8023a382a4354d9586e55

#### Requirement

README Goal, verbatim: "A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session."

User decision (final gate, 2026-10-27, relayed by the mx-5 leader), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". It replaces Q2's last-speaker routing (rejected); this task replaces the retired task mxc-route-last-speaker.

Design D9, verbatim:

> User decision (final gate, 2026-10-27, relayed by the mx-5 leader), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". It replaces the last-speaker routing (the architecture's fork 3 pick, rejected with Q2): each chat room is bound to at most one session at a time and that session to exactly that one room; a user message in a bound room always goes to its bound session. There is no last-speaker routing and no room shared by several sessions.

> How a room gets bound: - Inbound chat in an unbound room: the worker's claim transaction of a `first` run reserves the   room (an active `inbound` binding with the run id and no session yet), so no agent can initiate   there while the session is being created; when the run stores its session id   (`_RoomRunStore.set_session`), the same transaction fills the binding's session id and slug   (idempotent for a retried dispatch). A first run that finishes without a session (for example   `preset_not_found` or a refused dispatch) releases its reservation in its finish transaction   (`run_failed`). - Agent initiation in an unbound flagged room: the api accepts the send (D4 (b), advisory); the   bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active   `agent` binding (session id and slug of the send, its send id) when the room is still unbound,   still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes   decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never   makes a second binding. If that send then ends with none of its outbound rows sent (`failed`, or   `refused` at send time, D7), the settle transaction releases the binding it created   (`send_failed`, my call: a binding message that never reached the user binds nothing). - A send of a session into the room it is bound to binds nothing new.

> Routing a user message (`Worker._room`): the room's active binding decides, before any preset check (interrogate Act 1, B5, Q9): - bound to a session that `agents_common.runs.running_session` reports running (it exists and its   desired state is active, not that it is mid-turn): the batch becomes a `follow` run into it,   whatever its slug (an `mx-` chat session, a hive leader, a webhook or schedule session), and the   tracker posts its final answer as today. A busy session (for example a hive leader in a long   turn) gets the batch queued behind its current turn; the tracker follows that message for at   most `MATRIX_RUN_TIMEOUT_SECONDS` (default 1800 s, 30 min), and meanwhile the room's later   messages stay `new`, because a room with a run in progress is not ready (`inbound.rooms_ready`),   as for every run today. - bound to a session reported gone or deleting (`running_session` returns None): the binding is   released (`session_gone`) and the room is handled as unbound in the same tick. - a refused session check (an `OrchestratorError` other than not found) keeps the binding and   leaves the rows `new`, logged at most once a minute (my call: a hard binding never moves on an   ambiguous answer); an unavailable orchestrator retries next tick as today. - reserved by a first run in progress: nothing to do (the room is not ready anyway). - unbound: only now does the preset matter: the room's effective preset (room setting, else   default) starts a new `mx-` session under the new-session cap as today, which binds the room;   with no preset the rows are ignored `no_preset` as today and the room stays unbound. A delivery that finds the bound session gone (`Worker._session_gone`) releases the binding in the transaction that fails the run `session_gone`, so the next tick starts a new session as today.

> On session delete: the connector learns it from the orchestrator (`running_session` returns None: not found, or desired state `deleting`) and releases the binding (`session_gone`): at once when it routes the room's next batch, and otherwise within about a minute through a binding sweep in `Worker.tick` (at most once per 60 s, my call: one `GET /api/v1/sessions/{id}` per active binding with a session; an unavailable orchestrator ends that sweep, a refused check keeps the binding). After the release the room is unbound: the next user message starts a new `mx-` session (preset needed), and an agent may initiate there if the room is flagged. Nothing else releases a binding: turning `agents_may_initiate` off or adding a deny rule does not unbind (a deny rule still stops every agent send through D4 (a) and every inbound message) (Q10).

> `runs.preset_id` of a follow run (interrogate Act 1): the bound session's `preset_id` from the `running_session` lookup (`GET /api/v1/sessions/{id}`) the worker already makes; when it is null, the room's effective preset; when that is null too, NULL. Migration 0002 drops NOT NULL on `runs.preset_id` and adds CHECK `kind <> 'first' OR preset_id IS NOT NULL` (my call: an explicit "no preset" rather than a sentinel uuid; a first run still always has one, and no NOT NULL violation is possible). No extra orchestrator call; agents-common is unchanged (a follow run's `RunRef.preset_id` is never read by `deliver`).

> A follow run into a session that has no other run in this room (the run itself excluded), for example the first user answer into a session bound by its agent send, renders the prompt with the PREAMBLE (as a first prompt), because that session never saw the untrusted-input framing (my call). This holds on the first delivery and on every retry through `Worker._resume`, which today renders `first=False` for every follow run (interrogate Act 7).

> MEMORY amendment (connector MEMORY.md, dated): 2026-10-25 "One agent session per room" becomes "one session per room and one room per session (hard 1:1 binding in room_bindings), released only when the session is deleted".

Open question Q9 (approved by the user 2026-10-27, adapted to the 1:1 rule), verbatim: "When a room is bound to a running session (for example one that started the chat there through agents_may_initiate), your answer routes to it even if the room has no preset; a preset is only needed to start a new chat session in an unbound room" answer "yes".

Open question Q10 (approved by the user 2026-10-27, adapted to the 1:1 rule), verbatim: "A room stays bound to its one session until that session is deleted (the connector releases the binding at the room's next message or within about a minute); turning agents_may_initiate off or adding a deny rule does not unbind it, though a deny rule still stops every agent send and inbound message" answer "yes".

Interrogate verdict, verbatim: "1. Preset contradiction (B,C high): D9/mxc-route-last-speaker keep `no_preset` before routing while B5/Q9 promise routing to a running last speaker without a preset. Build B5: routing to a running last speaker happens before the preset check; a preset is needed only to start a new mx- session; follow runs need a non-null runs.preset_id: use the target session's preset (GET /api/v1/sessions/{id}); if that is null too, define the value explicitly (no NOT NULL violation possible). ACs pin both paths." (adapted: the bound session takes the place of the last speaker) "7. Preamble lost on resume (B medium): Worker._resume renders first=False; a follow run into a session new to the room must keep the PREAMBLE on the retry path too, excluding the run itself from "no earlier run in this room". Add Worker._resume to the task and an AC."

Scope (agents-matrix-connector): `worker.py` (`Worker._room` routes by the room's active binding before the preset check; the first-run claim reserves the room; `_RoomRunStore.set_session` fills the binding and `_RoomRunStore.finish` releases a reservation without a session; `Worker._session_gone` releases the binding; the 60 s binding sweep in `Worker.tick`; the follow-run preset rule; the PREAMBLE rule in `Worker._deliver`, so `Worker._resume` keeps it), `db/runs.py` (`latest_session` removed; `RunRow.preset_id` and `create_run` accept no preset for a follow run; a query for "this session has another run in this room"), `db/bindings.py` (any query the worker needs beyond mxc-sends-schema's), `MEMORY.md` (the dated amendment, with the why), README (how a room is bound, that the user's messages always go to the bound session, the busy-session hold, and that only deleting the session releases the binding). The `room_bindings` table and `runs.preset_id` nullability are migration 0002 (mxc-sends-schema); the agent-initiated binding is the sender's (mxc-bot-sends-delivery). `tests/test_runs_repo.py::test_create_run_and_latest_session` is no longer accurate (named): it pins `latest_session`, which the binding replaces and this task removes; it becomes `test_create_run`, keeping every run-creation check and dropping only the `latest_session` assertions.

#### Acceptance conditions

- ac1: a first run in an unbound room reserves the room's binding in its claim transaction (origin inbound, the run id, no session), and storing the run's session id fills the binding's session id and slug, a retried dispatch with the same id changing nothing [evidence: test:tests/test_worker.py::test_first_run_binds_room]
- ac2: a first run that ends without a session (preset_not_found, a refused dispatch) releases its reservation with reason run_failed, and the room's next batch starts a new first run [evidence: test:tests/test_worker.py::test_failed_first_run_releases_reservation]
- ac3: a room bound to a running session that is not an mx- session (bound by an agent send) gets the next batch as a follow run into that session, before any preset check: also with no room preset and no default preset [evidence: test:tests/test_worker.py::test_bound_session_gets_batch_without_preset]
- ac4: a user message in a bound room never goes to any other session: with another session holding runs in that room and with a newer run of another session elsewhere, the batch goes to the bound session [evidence: test:tests/test_worker.py::test_batch_goes_only_to_bound_session]
- ac5: a bound session reported gone or deleting releases the binding with reason session_gone, and in the same tick the room starts a new mx- session (which binds it) when it has a preset, or ignores the rows no_preset and stays unbound when it has none [evidence: test:tests/test_worker.py::test_gone_bound_session_released]
- ac6: a delivery that finds the bound session gone fails the run session_gone and releases the binding in that transaction, and the next tick starts a new session [evidence: test:tests/test_worker.py::test_session_gone_releases_binding]
- ac7: a refused session check (an OrchestratorError other than not found) keeps the binding and leaves the rows new, and an unavailable orchestrator retries next tick, both without a new session [evidence: test:tests/test_worker.py::test_refused_check_keeps_binding]
- ac8: the binding sweep runs at most once per 60 s, releases with reason session_gone every active binding whose session is gone or deleting, keeps running ones and reservations, and ends early without releasing anything when the orchestrator is unavailable [evidence: test:tests/test_worker.py::test_binding_sweep_releases_deleted_sessions]
- ac9: a follow run records the bound session's preset_id, the room's effective preset when the session has none, and no preset (NULL) when neither has one, without an error [evidence: test:tests/test_worker.py::test_follow_run_preset_from_session]
- ac10: a follow run into a session with no other run in the room renders the PREAMBLE, and a follow run into a session with an earlier run in the room does not [evidence: test:tests/test_worker.py::test_preamble_for_session_new_to_room]
- ac11: a follow run into a session new to the room whose first delivery failed (orchestrator unavailable) is retried by Worker._resume with the PREAMBLE, the run itself not counting as an earlier run; a resumed follow run into a session with an earlier run in the room renders no PREAMBLE [evidence: test:tests/test_worker.py::test_resume_keeps_preamble_for_session_new_to_room]
- ac12: run creation keeps its checks (slug mx-<id>, no session or message, integer id, other kinds refused) and latest_session no longer exists (updated) [evidence: test:tests/test_runs_repo.py::test_create_run]
- ac13: the existing worker behaviour (batching, reuse bypassing the cap, session gone fallback, new-session cap, no preset, restart idempotence, typing, receipts) is unchanged [evidence: command:uv run pytest tests/test_worker.py]
- ac14: connector MEMORY.md records the amendment "one session per room and one room per session", dated, with the why [evidence: command:grep -qF "one session per room and one room per session" MEMORY.md]
- ac15: README describes the 1:1 binding: how a room is bound (an inbound chat starting a session, an agent initiating in an unbound flagged room), that the user's messages always go to the bound session, that a busy session holds the room's later messages until its reply or the run timeout, and that only deleting the session releases the binding [evidence: command:grep -qi "one room per session" README.md && grep -qi "run timeout" README.md && grep -qi "session is deleted" README.md]
- ac16: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_runs_repo.py tests/test_worker.py && mise run lint]

#### Files

- `src/agents_matrix_connector/worker.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/bindings.py`
- `MEMORY.md`
- `README.md`
- `tests/test_worker.py`
- `tests/test_runs_repo.py`

#### Interfaces

- Uses `db/bindings.py` (mxc-sends-schema): `reserve_for_run`, `fill_session`, `release`, `active_for_room`, `active_with_session`; any extra worker query goes there too (readers or bot-worker writers only).
- `worker.py:Worker._room(room_id)`: reads the room's active binding first; a session binding checks `agent_runs.running_session` and, running, claims a `follow` run with `preset_id` from that `Session.preset_id`, else the room's effective preset, else None; `None` from the check releases (`session_gone`) and falls through to the unbound path; an `OrchestratorError` other than not found keeps the binding and the rows; a reservation does nothing; unbound: `_preset` decides between a `first` run (whose claim transaction calls `reserve_for_run`) and `no_preset`.
- `worker.py:_RoomRunStore.set_session` fills the run's binding in the same transaction as the runs update; `_RoomRunStore.finish` releases (`run_failed`) the reservation of a run that ends with no session; `Worker._session_gone` releases (`session_gone`) the binding of the gone session in the transaction that fails the run.
- `worker.py:Worker.tick` runs the binding sweep at most once per 60 s (clock from `now`), before the room pass: `running_session` per `active_with_session` row; None releases `session_gone`; `OrchestratorUnavailable` ends the sweep; `OrchestratorError` keeps that binding.
- `db/runs.py`: `latest_session` removed; `RunRow.preset_id: uuid.UUID | None`; `create_run(conn, *, room_id, preset_id: str | None, kind)`; `has_other_run(conn, session_id, room_id, exclude_run_id) -> bool` (name left to the builder).
- `worker.py:Worker._deliver` renders `first=True` when the session has no other run in the room, so `Worker._resume` (which calls `_deliver` for follow runs) keeps the PREAMBLE; `RunRef.preset_id` of a follow run without a preset is `""` (never read by `deliver`).
- Release reasons (constants in `worker.py`): `session_gone` (reuse `tracker.SESSION_GONE`), `run_failed`.

#### Expected outcome

Every chat room talks to exactly one session: the user's messages in a bound room always reach its bound session (an `mx-` chat session or a session that started the chat with agents_may_initiate), with or without a preset; a room is bound when an inbound chat starts its session; deleting the session frees the room within about a minute, after which the next message starts a new chat session.

#### Steps

- Red: rename `test_create_run_and_latest_session` to `test_create_run` without the `latest_session` assertions, add the eleven worker tests (ac1 to ac11); run `uv run pytest tests/test_runs_repo.py tests/test_worker.py`: the new tests fail (no binding routing, `latest_session` still present is caught by `test_create_run`).
- Green: `db/runs.py`, `db/bindings.py` if a query is missing, `worker.py`, README, MEMORY; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Retires and replaces mxc-route-last-speaker (user decision 2026-10-27): no candidate list, no last-speaker ordering, no walk over several sessions. A user message never goes to any session but the bound one.
- The binding check runs before the preset check (interrogate Act 1, Q9 adapted): a bound running session takes the batch without a preset; the no_preset ignore and the new-session cap apply only to an unbound room, unchanged there.
- `running_session` already returns `agents_common.orchestrator.Session`, which carries `preset_id` (nullable); no new orchestrator call. It returns None both for not found and for desired `deleting`, the only two ways a session is deleted.
- A refused check keeps the binding (my call in D9: a hard binding never moves on an ambiguous answer); pin test `test_refused_check_keeps_binding`.
- The worker, the sender (mxc-bot-sends-delivery) and the tracker run sequentially in the one bot process; the partial unique indexes still decide any conflict: a `reserve_for_run` that loses (the room got an agent binding between the read and the claim) rolls the claim back and the room is retried next tick as bound.
- `test_session_gone_falls_back` stays unchanged and must keep passing; the binding assertions of that path live in the new `test_session_gone_releases_binding`.
- MEMORY.md entry format: `- One session per room and one room per session (2026-10-27, epic matrix-connector-agent-initi): hard 1:1 binding in room_bindings, released only when the session is deleted; why: the user's final-gate decision ...` amending the 2026-10-25 line, newest first.
- DB-backed tests (CI); keep the routing decision (binding state and check result to action) a pure function with a non-DB test in `tests/test_worker.py` so the local run has signal.

- 2026-10-28 done: CI 40746644847 green

- 2026-10-28 actuals: no agent records

### S28: mxc skip duplicate final

- Status: done
- Files: `src/agents_matrix_connector/tracker.py`, `src/agents_matrix_connector/db/sends.py`, `README.md`, `tests/test_tracker.py`, `tests/test_readme_api.py`
- Verify: `uv run pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint`
- Verified head: f9d489922cfa4ac63b49747906c4e83be4ea6ba0

#### Requirement

README Non-goal, verbatim: "No automatic forwarding of every final reply of every turn to the chat (agents use the send tool)."

Design D10, verbatim:

> When a chat-started run's turn completes, the tracker compares its `final_text`, stripped, with the
> stripped `text` of every `message` send of the same session created at or after the run's
> `started_at`. Only a send that reached the user counts (interrogate Act 3, the lead's call):
>
> - a matching send that is `sent`: the run closes `handled` with reason `already_sent` and no outbound row is stored;
> - else a matching send still `queued` or `sending`: the run stays in progress and the check repeats each tick until that send settles, bounded by the run timeout (`MATRIX_RUN_TIMEOUT_SECONDS` from the run's `started_at`); when the timeout passes first, the final answer is posted (my call: a late duplicate beats a lost answer);
> - a matching send that ended `failed` or `refused` does not count, so the final answer is posted.
>
> Anything else posts as today.

Design anti-goal, verbatim: "Double output: the same text posted twice because the agent sent it and its final answer repeated it."

Scope (agents-matrix-connector): `tracker.py` (the match in the completed-turn branch, a new reason constant `ALREADY_SENT = "already_sent"`), the query in `db/sends.py`, README (the reason). `tests/test_readme_api.py::test_readme_lists_every_reason` gains `tracker.ALREADY_SENT` in its reason set (extended, nothing removed).

Interrogate verdict, verbatim: "3. Failed send suppresses the final answer (A,B,C medium): D10 matching must count only sends that reached the user. My call: match only `sent` sends; a matching send still `queued`/`sending` when the final answer is ready delays the close until it settles (bounded by the run timeout), and if it ends `failed` the final answer is posted. AC for failed and for queued-then-failed."

#### Acceptance conditions

- ac1: a completed chat run whose final text equals a sent message send of the same session made during the run is handled with reason already_sent and stores no outbound row [evidence: test:tests/test_tracker.py::test_final_text_already_sent_is_not_posted]
- ac2: a different text, a send made before the run started, a reaction and another session's send all leave the reply posted as today [evidence: test:tests/test_tracker.py::test_final_text_posted_unless_already_sent]
- ac3: a matching send that ended failed, and one that ended refused, do not count: the final answer is posted [evidence: test:tests/test_tracker.py::test_final_text_posted_when_matching_send_failed]
- ac4: while a matching send is queued or sending the completed run stays in progress; when that send then fails the final answer is posted, and when it is then sent the run closes already_sent with no outbound row [evidence: test:tests/test_tracker.py::test_pending_matching_send_delays_close]
- ac5: a matching send still pending when the run timeout passes does not hold the run longer: the final answer is posted [evidence: test:tests/test_tracker.py::test_pending_match_bounded_by_run_timeout]
- ac6: README names the already_sent reason and the rule that only a delivered send suppresses the final answer [evidence: test:tests/test_readme_api.py::test_readme_lists_every_reason]
- ac7: the existing tracker behaviour is unchanged [evidence: test:tests/test_tracker.py::test_completed_turn_replies]
- ac8: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_matrix_connector/tracker.py`
- `src/agents_matrix_connector/db/sends.py`
- `README.md`
- `tests/test_tracker.py`
- `tests/test_readme_api.py`

#### Interfaces

- `tracker.py:ALREADY_SENT = "already_sent"`.
- `db/sends.py:message_sends_since(conn, session_id, since) -> list[tuple[str, str]]` (name left to the builder): `(text, status)` of the session's message sends created at or after `since`.
- `tracker.py:Tracker._outcome`: a completed turn with a `sent` match closes `already_sent`; with only a `queued`/`sending` match returns None (still running) until the run timeout, then posts; otherwise posts.

#### Expected outcome

An agent that sends its answer with `orchestrator_chat_send` during a chat-started turn and ends the turn with the same text does not post it twice.

#### Steps

- Red: add the two tracker tests and `ALREADY_SENT` to the README reason test; run `uv run pytest tests/test_tracker.py tests/test_readme_api.py`: they fail.
- Green: tracker, query, README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Compare `str.strip()` of both sides only; no fuzzy matching (D10).
- While the close waits on a pending match, the run stays in progress, so the room's next batch waits too (as for any running run); typing stays on as for a running turn.
- The inbound rows of the run settle `handled` with the same reason, as for `empty_reply`.
- DB-backed tracker tests (CI); `test_readme_api.py` runs locally.

- 2026-10-27 amended: interrogate.md Act 3: only sent sends suppress the final answer; pending matches delay the close within the run timeout

- 2026-10-28 done: CI 40747755877 green

- 2026-10-28 actuals: no agent records

### S29: orch chat contract

- Status: done
- Files: `tests/fakes/fake_chat.py`, `tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`, `tests/test_chat_contract.py`
- Verify: `uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint`
- Verified head: 9d5419c096c9fd1004bbcee84241d1f4d762451f

#### Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D16, verbatim: "Contract: the connector commits its agent listener OpenAPI document (`openapi-agent.json`, pinned like `openapi.json`); the orchestrator vendors it with a source line (`tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`), its fake chat upstream validates against it, and a test asserts every relay route maps to a path and method of the vendored document (my call)."

Retro proposal (generic-any-mcp-with-git-and, cross-session-messaging-and), verbatim: "any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it."

Scope (agents-orchestrator, tests only): vendor `openapi-agent.json` from agents-matrix-connector `main` after mxc-agent-routes merged, as `tests/fakes/chat_openapi.json`, with `tests/fakes/chat_openapi.source` holding `agents-matrix-connector <full sha>`; new `tests/fakes/fake_chat.py` (an ASGI fake of the `/chat/v1` upstream that validates each request body against the vendored request schemas, answers with documented shapes, records calls, and can be told to refuse); new `tests/test_chat_contract.py`.

#### Acceptance conditions

- ac1: tests/fakes/chat_openapi.json is byte-identical to openapi-agent.json at the agents-matrix-connector commit named in tests/fakes/chat_openapi.source, which is on that repo's main [evidence: judgement:reviewer runs git show <sha>:openapi-agent.json in agents-matrix-connector and compares it with the vendored file]
- ac2: every orchestrator chat route maps to a path and method of the vendored document [evidence: test:tests/test_chat_contract.py::test_relay_routes_exist_upstream]
- ac3: every success and error answer of the fake validates against the vendored response schemas [evidence: test:tests/test_chat_contract.py::test_fake_chat_matches_vendored_schema]
- ac4: the bodies the relay forwards for rooms, send, reply, react and status validate against the vendored request schemas [evidence: test:tests/test_chat_contract.py::test_relay_requests_match_vendored_schema]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint]

#### Files

- `tests/fakes/fake_chat.py`
- `tests/fakes/chat_openapi.json`
- `tests/fakes/chat_openapi.source`
- `tests/test_chat_contract.py`

#### Interfaces

- `tests/fakes/fake_chat.py`: `FakeChat(token: str)` with `.app` (ASGI), `.calls` (method, path, headers, body), `.refuse(route, status, code)`; validates against `tests/fakes/chat_openapi.json`.
- `tests/fakes/chat_openapi.source`: one line `agents-matrix-connector <40-hex sha>`.

#### Expected outcome

The orchestrator's view of the chat upstream cannot drift from the connector's: the fake is checked against the connector's own committed document, and the relay's requests against the same.

#### Steps

- Vendor the document: `git -C <agents-matrix-connector checkout> show origin/main:openapi-agent.json > tests/fakes/chat_openapi.json`, write the source line with that commit.
- Red: write `tests/test_chat_contract.py`; run `uv run --frozen pytest tests/test_chat_contract.py`: fails (no fake).
- Green: write `tests/fakes/fake_chat.py`; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- `jsonschema` and `openapi-schema-validator` are already in `uv.lock` (transitive); use one of them if it is importable in the dev environment, else resolve the document's `$ref`s by hand in the fake. A new direct dependency would touch `pyproject.toml` and `uv.lock`, which this task may not: return it as a `discovered` entry.
- ac2 and ac4 run without a database (override `require_agent` as in `tests/test_agent_chat.py`).
- orch-chat-tools-allow reuses `FakeChat` for the plugin parity test.

- 2026-10-28 done: vendored doc from connector branch 0380120; re-check on connector main after its merge commit

- 2026-10-28 actuals: no agent records

### S30: mxc e2e agent sends

- Status: done
- Files: `tests/e2e/conftest.py`, `tests/e2e/test_e2e_agent.py`
- Verify: `uv run pytest tests/e2e/test_e2e_agent.py && mise run lint`
- Verified head: 40810bd99d90a3628dfbb1f3ee7ff6786aac447e

#### Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can send several messages in a row without a user reply in between (follow-ups), including while a chat-started turn is still running."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."
- "A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session."

Design D16, verbatim (e2e): "E2E: the connector stack test (real api and bot processes, fake homeserver, fake orchestrator) covers send without inbound, follow-ups during a running chat run, reply and reaction relations, refusals, the 1:1 binding (an initiation binds the room, the user's answer reaches the bound session, `room_bound` and `session_bound` refusals, the release on session delete), and a 16000-character text of 4-byte characters accepted and delivered in chunks (interrogate Act 6)."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Scope (agents-matrix-connector): the e2e stack (`tests/e2e/conftest.py`) also starts the api's agent listener with a test token hash and exposes a client for `/chat/v1`; new `tests/e2e/test_e2e_agent.py`.

#### Acceptance conditions

- ac1: a send to a flagged allowed unbound room with no inbound message reaches the fake homeserver and its status reads sent [evidence: test:tests/e2e/test_e2e_agent.py::test_initiate_without_inbound]
- ac2: two follow-up sends of the room's bound session made while its chat-started run is still in progress reach the homeserver before that run's final answer [evidence: test:tests/e2e/test_e2e_agent.py::test_follow_ups_during_running_run]
- ac3: a reply to an m<n> carries m.in_reply_to with that inbound event id and a reaction carries m.annotation with the key, as recorded by the fake homeserver [evidence: test:tests/e2e/test_e2e_agent.py::test_reply_and_reaction_relations]
- ac4: a denied room, an unflagged unbound room and a bad reference are refused at once and nothing reaches the homeserver [evidence: test:tests/e2e/test_e2e_agent.py::test_refusals]
- ac5: a non-mx session's delivered send to an unbound flagged room binds the room to it, and the user's next message there is delivered to that session as a follow run [evidence: test:tests/e2e/test_e2e_agent.py::test_initiation_binds_and_answer_reaches_session]
- ac6: in a bound room another session's send answers 409 room_bound, and the bound session's send to a second unbound flagged room answers 409 session_bound; nothing of either reaches the homeserver and the binding is unchanged [evidence: test:tests/e2e/test_e2e_agent.py::test_binding_refusals]
- ac7: after the bound session is deleted in the fake orchestrator, the binding is released and the user's next message starts a new mx- session that then holds the room [evidence: test:tests/e2e/test_e2e_agent.py::test_release_on_session_delete]
- ac8: a chat-started turn whose final answer equals what the session already sent is not posted twice [evidence: test:tests/e2e/test_e2e_agent.py::test_no_double_output]
- ac9: a message of 16000 4-byte characters is accepted by the agent listener and reaches the fake homeserver in MATRIX_REPLY_CHUNK_CHARS chunks whose bodies join to that text, and its status reads sent [evidence: test:tests/e2e/test_e2e_agent.py::test_max_text_delivered]
- ac10: the existing e2e cases still pass [evidence: command:uv run pytest tests/e2e/test_e2e_api.py]
- ac11: the targeted tests and lint pass [evidence: command:uv run pytest tests/e2e/test_e2e_agent.py && mise run lint]

#### Files

- `tests/e2e/conftest.py`
- `tests/e2e/test_e2e_agent.py`

#### Interfaces

- `tests/e2e/conftest.py:Stack` gains the agent listener base URL and a helper that calls `/chat/v1/*` with the test bearer, `X-Orch-Session` and `X-Orch-Slug`.

#### Expected outcome

One end-to-end suite proves G1, G2, G3 and G6 (the 1:1 binding: bind on initiation, answers to the bound session, room_bound and session_bound, release on session delete) across the real api and bot processes.

#### Steps

- Red: write `tests/e2e/test_e2e_agent.py` against the extended stack; run `uv run pytest tests/e2e/test_e2e_agent.py`: the cases fail before the stack serves the agent listener.
- Green: extend the stack fixture; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- The stack needs Docker (Postgres); this pod has none, so GitHub CI runs it; quote the CI run's summary.
- Use `agents_common.fake_orchestrator.FakeOrchestrator` as the existing e2e cases do; a non-mx session is a session the fake reports running whose slug does not start with `mx-`; deleting a session is removing it from the fake (or setting its desired state to deleting), after which the next user message or the 60 s binding sweep releases the binding (shorten the wait through the stack's clock or by sending the next message, never by sleeping 60 s).
- Build the test token at runtime (`secrets.token_hex(32)`) and pass its sha256 in the stack env.

- 2026-10-27 amended: interrogate.md Act 6: 16000 4-byte characters delivered end to end

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding, refusals and release end to end

- 2026-10-28 done: CI 40751882452 green (345 passed)

- 2026-10-28 actuals: no agent records

### S31: orch chat tools allow

- Status: done
- Files: `src/agents_orchestrator/k8s/on_start.py`, `tests/test_on_start.py`, `tests/e2e/test_e2e_kind.py`, `tests/test_agent_chat.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_on_start.py tests/test_agent_chat.py && mise run lint`
- Verified head: 1be7f315f8ba40435d7ab661f416493440730ab7

#### Requirement

README Goal, verbatim: "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."

Design D13, verbatim: "The orchestrator then pins v0.2.0 and adds `CHAT_TOOLS` to every session's allow list (`k8s/on_start.py:orchestrator_allow`); the routes decide. (probe) The allow-list change must land with the pin, not with the routes: `tests/test_on_start.py::test_allowed_tools_exist_in_plugin` requires every allowed tool to exist in the pinned plugin. `claude.main_agent_only_tools` already covers `mcp__any-mcp__orchestrator_*` (`k8s/render.py:159`), so subagents cannot call them."

Design D16, verbatim: "The orchestrator's tools-parity test drives the released v0.2.0 plugin against the real routes and the fake upstream."

Retro proposal (cross-session-messaging-and), verbatim: "agents-orchestrator kind e2e tests: allow-list assertions hard-code tool names; derive them from the shared allow-list constant so a list change cannot break e2e only."

Scope (agents-orchestrator): `k8s/on_start.py` (`CHAT_TOOLS = ["chat_rooms", "chat_send", "chat_react", "chat_status"]` appended for every session, alone and hive), README (the Agent API chat section says the tools are in every allow list, leader only), `tests/test_agent_chat.py` (`test_chat_tools_parity`). Named tests no longer accurate: `tests/test_on_start.py::test_alone_session_tools_entry` and `tests/test_on_start.py::test_hive_session_tools` pin the allow lists without the chat tools; they are updated to include them. `tests/e2e/test_e2e_kind.py:assert_alone_session_tools` pins a literal list; it is changed to compare with `on_start.orchestrator_allow(SessionSpec(replicas=1))` (retro proposal).

Design D5, verbatim (orchestrator caps): "The orchestrator caps the forwarded request body at 256 KiB (413 `payload_too_large`) and the upstream call at 10 s. The cap covers the worst case of a valid maximal request (interrogate Act 6; my call on the figure): 16000 characters of 4 bytes each are 64000 bytes raw (the plugin's httpx encodes JSON as raw UTF-8), and up to 192000 bytes when a client escapes every character as a JSON surrogate pair (12 bytes), plus a room id of up to 255 characters, `reply_to` and the JSON keys; 256 KiB (262144 bytes) covers all of it, where the verdict's example of 80 KiB would refuse the escaped form."

Interrogate verdict, verbatim: "6. Size caps (A,C medium): 16000 characters can exceed the orchestrator's 32 KiB body cap. Make the relay cap cover the worst case (4 bytes per character plus JSON overhead, e.g. 80 KiB) with an AC sending 16000 4-byte characters end to end." (this task: the end-to-end leg through the released plugin, the real relay route and the fake upstream).

#### Acceptance conditions

- ac1: an alone session's allow list is the session, init-scripts and chat tools (updated) [evidence: test:tests/test_on_start.py::test_alone_session_tools_entry]
- ac2: a hive session's allow list ends with the chat tools (updated) [evidence: test:tests/test_on_start.py::test_hive_session_tools]
- ac3: every allowed tool, the chat tools included, exists in the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac4: the released plugin drives chat_rooms, chat_send, chat_react and chat_status against the real agent routes and the fake chat upstream, and the results equal the direct route answers [evidence: test:tests/test_agent_chat.py::test_chat_tools_parity]
- ac5: orchestrator_chat_send through the released plugin with a text of 16000 4-byte characters is relayed and the fake upstream receives that exact text [evidence: test:tests/test_agent_chat.py::test_chat_send_max_text_through_plugin]
- ac6: the kind e2e allow-list assertion is derived from on_start instead of a literal list [evidence: command:grep -q "orchestrator_allow" tests/e2e/test_e2e_kind.py && ! grep -q '"init_scripts_edit",$' tests/e2e/test_e2e_kind.py]
- ac7: the README says the chat tools are in every session's allow list [evidence: command:grep -q "orchestrator_chat_send" README.md]
- ac8: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_on_start.py tests/test_agent_chat.py && mise run lint]

#### Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `tests/e2e/test_e2e_kind.py`
- `tests/test_agent_chat.py`
- `README.md`

#### Interfaces

- `k8s/on_start.py:CHAT_TOOLS`; `orchestrator_allow(spec)` returns `[*SESSION_TOOLS, *INIT_SCRIPTS_TOOLS, *CHAT_TOOLS]` for alone sessions and the hive list followed by `CHAT_TOOLS`.

#### Expected outcome

Every new session's agents see the four chat tools; only the leader's calls succeed, and the released plugin is proven against the real routes.

#### Steps

- Red: update the two on-start tests, add `test_chat_tools_parity`, change the e2e helper; run `uv run --frozen pytest tests/test_on_start.py tests/test_agent_chat.py`: they fail.
- Green: `CHAT_TOOLS`, README; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- `test_chat_tools_parity` follows `tests/test_agent_session_messaging.py::test_session_tools_parity` (PluginHarness with an ASGI transport and the caller's pod IP) and uses `tests/fakes/fake_chat.py:FakeChat` as the upstream. It is DB-backed (CI).
- The kind e2e runs only in CI (kind); the local check is ac5.
- Changing the allow list changes the rendered on-start config hash: existing sessions roll on deploy (chat-live-smoke).

- 2026-10-27 amended: interrogate.md Act 6: 16000 4-byte characters end to end through the released plugin

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done: CI test/lint/chart green run 40742034508; e2e pending at review

- 2026-10-28 actuals: no agent records

### S32: helmfile chat values

- Status: done
- Files: `values/agents-matrix-connector/common.yaml`, `values/agents-orchestrator/common.yaml`, `helmfile.yaml.gotmpl`, `tests/test_matrix_connector_release.py`, `tests/test_orchestrator_release.py`
- Verify: `uv run pytest tests/test_matrix_connector_release.py tests/test_orchestrator_release.py && mise run lint`
- Verified head: ab481511369e1480041c6ed329cbad1f965e02fd

#### Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D14, verbatim (values): "Values: connector image tag and chart version, agent port; orchestrator image tag and chart version, `chat.url: http://agents-matrix-connector-api-agents:8001`, `ORCH_ANY_MCP_PLUGINS_REF: v0.2.0`; agents-web tag with the toggle."

Design D18, verbatim: "(3) Apply the connector first (migration 0002 runs in its init container; the agent listener comes up), then the orchestrator with its chat secret and the v0.2.0 plugins ref (until then the routes answer 503 `chat_unconfigured`; the ref rolls agent pods), then agents-web. (4) The orchestrator session runs every apply with `--selector` in that order; no AC runs an apply. Gate question Q6 settles how this deploy relates to the one deploy epic approved for the four earlier epics."

Open question Q6 (pending gate), verbatim: "This epic's agents-helmfile values and live smoke run only after the one deploy approved for the four earlier epics (file-download, markdown, file-editor, slash-commands) has applied, so this epic's applies move only the connector, the orchestrator (chat config, plugins v0.2.0) and agents-web; if that deploy epic does not exist when this epic reaches helmfile-chat-values, the orchestrator creates and runs it first?" recommended "yes".

Retro tech debt (file-download-in-file-browse), verbatim: "Deploy coupling: orchestrator `FileEntry.target_type` is required, so the orchestrator image must deploy with wrapper >= 4581f3b; the later deploy epic must pin them together."

Scope (agents-helmfile): `values/agents-matrix-connector/common.yaml` (image tag = the connector `main` sha7 that carries every connector task of this epic, CI-published; `agentApi.port` 8001 if not the chart default), `helmfile.yaml.gotmpl` (connector and orchestrator chart versions `0.1.0-main.<sha7>`), `values/agents-orchestrator/common.yaml` (image tag = the orchestrator `main` sha7 that carries every orchestrator task of this epic; `chat.url`; `ORCH_ANY_MCP_PLUGINS_REF: v0.2.0`; the agent image stays what the earlier deploy pinned). Named tests no longer accurate: `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` pins the plugins ref of the earlier deploy; it asserts `v0.2.0`. No apply here: the orchestrator session applies in chat-live-smoke.

#### Acceptance conditions

- ac1: the connector image tag and chart version name the same connector main sha7, and the release still needs its database [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- ac2: the orchestrator image tag and chart version name the same orchestrator main sha7 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac3: the orchestrator values set chat.url to http://agents-matrix-connector-api-agents:8001 and no plaintext chat token [evidence: test:tests/test_orchestrator_release.py::test_chat_upstream_wired]
- ac4: new sessions install the orchestrator plugin at v0.2.0 (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac5: the pinned connector sha7 contains mxc-e2e-agent-sends and the pinned orchestrator sha7 contains orch-chat-tools-allow and orch-chart-chat, both on their repos' main with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha and the CI run of that sha]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_matrix_connector_release.py tests/test_orchestrator_release.py && mise run lint]

#### Files

- `values/agents-matrix-connector/common.yaml`
- `values/agents-orchestrator/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_matrix_connector_release.py`
- `tests/test_orchestrator_release.py`

#### Interfaces

- `values/agents-orchestrator/common.yaml`: `chat.url`, `env.ORCH_ANY_MCP_PLUGINS_REF: v0.2.0`, `image.tag`.
- `values/agents-matrix-connector/common.yaml`: `image.tag`.
- `helmfile.yaml.gotmpl`: chart `version` of both releases.

#### Expected outcome

agents-helmfile describes the deployed state this epic needs; one apply per release (connector, then orchestrator) brings it live.

#### Steps

- Confirm Q6's precondition: the earlier four epics' deploy is applied (the orchestrator image and agent image pins already moved past b3a2975 and claude-code-wrapper 0.3.0); stop and report if not.
- Red: add `test_chat_upstream_wired`, update `test_any_mcp_configured_for_new_sessions` and the pin expectations; run `uv run pytest tests/test_matrix_connector_release.py tests/test_orchestrator_release.py`: they fail.
- Green: values and chart versions; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Tests that run `helmfile build` or `helm pull oci://harbor...` fail without network in this pod (discovery sec 5); quote them as environmental and name which ones.
- The image tags must exist in Harbor (CI images job of each merge); chat-live-smoke checks them before applying.
- agents-helmfile has no CI workflow: the reviewer's local verify is the evidence.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done

- 2026-10-28 actuals: no agent records

### S33: helmfile orch chat pin

- Status: done
- Files: `values/agents-orchestrator/common.yaml`, `helmfile.yaml.gotmpl`, `tests/test_orchestrator_release.py`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_smoke_script.py && mise run lint`
- Verified head: 6998c2bcd1c3e9cc2551195fe3b58fbd1395b997

#### Requirement

User rule (2026-10-28, mx-34 msg 190), verbatim in memory deploy-small-often: deploy small and often; each reviewed, independently runnable task or small group merges to its component main and deploys at once (check-pins, apply, smoke); backend before web.

The orchestrator half of this epic is merged: agents-orchestrator PR #30, merge commit 37edd586a8ba754769419bec9b01e573c1704709 (orch-chat-relay, orch-chart-chat, orch-plugins-pin-0-3-0, orch-chat-contract, orch-chat-tools-allow). Without `chat.url` and the chat token the relay routes answer 503 `chat_unconfigured` (design B7), so it is safe to deploy before the connector.

Scope (agents-helmfile), no apply here (the orchestrator session applies, never a subagent):
- `values/agents-orchestrator/common.yaml`: `image.tag` 37edd58 and `env.ORCH_ANY_MCP_PLUGINS_REF: v0.2.0` (design D13: the orchestrator pins plugins v0.2.0; the ref rolls agent pods, which the deploy-safe OnDelete replacer does idle-only).
- `helmfile.yaml.gotmpl`: agents-orchestrator chart version `0.1.0-main.37edd58` (CI-published from main).
- `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` is no longer accurate (named): it pins `v0.1.0`; it asserts `v0.2.0`.
- No `chat.url`, no chat secret: those stay with helmfile-chat-secrets and helmfile-chat-values.
- MEMORY.md: a dated entry for the early orchestrator deploy and why.

#### Acceptance conditions

- ac1: the orchestrator values pin image 37edd58 and the chart version 0.1.0-main.37edd58 [evidence: command:grep -q "tag: 37edd58" values/agents-orchestrator/common.yaml && grep -q "0.1.0-main.37edd58" helmfile.yaml.gotmpl]
- ac2: new sessions install the orchestrator plugin at v0.2.0 (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: every pin has a green published build [evidence: command:mise run check-pins]
- ac4: MEMORY.md records the early orchestrator deploy [evidence: command:grep -q "37edd58" MEMORY.md]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_smoke_script.py && mise run lint]

#### Files

- `values/agents-orchestrator/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_orchestrator_release.py`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done: check-pins ok 9 pins; apply by supervisor after merge

- 2026-10-28 actuals: no agent records

### S34: helmfile web toggle pin

- Status: done
- Files: `values/agents-web/common.yaml`, `helmfile.yaml.gotmpl`, `tests/test_web_release.py`
- Verify: `uv run pytest tests/test_web_release.py && mise run lint`
- Verified head: c1825b744ea639c297fe605331b668a1f5d15290

#### Requirement

Design D14, verbatim (values): "agents-web tag with the toggle."

Design D15, verbatim: "The room drawer gets an "Agents may start chats" switch bound to `agents_may_initiate`, saved with the preset and trigger in the one PUT (gate question Q4)."

Design D18, verbatim: "then the orchestrator with its chat secret and the v0.2.0 plugins ref [...], then agents-web."

Scope (agents-helmfile): `values/agents-web/common.yaml` image tag and `helmfile.yaml.gotmpl` agents-web chart version `0.1.0-main.<sha7>`, both the agents-web `main` sha7 that carries web-room-initiate-toggle (CI-published). No apply here.

#### Acceptance conditions

- ac1: the agents-web image tag and chart version name the same agents-web main sha7 [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac2: the pinned agents-web sha7 contains web-room-initiate-toggle on main with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of the task's verified_head against the pinned sha and the CI run of that sha]
- ac3: the web release still lists the matrix backend and needs the connector [evidence: test:tests/test_web_release.py::test_matrix_backend_configured]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_web_release.py && mise run lint]

#### Files

- `values/agents-web/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_web_release.py`

#### Interfaces

- `values/agents-web/common.yaml`: `image.tag`; `helmfile.yaml.gotmpl`: agents-web chart `version`.

#### Expected outcome

agents-helmfile pins the agents-web build with the "Agents may start chats" switch.

#### Steps

- Red: point the pin expectations at the new sha7 (the pin test compares tag and chart version; change the values only after confirming the sha7 exists in Harbor); run `uv run pytest tests/test_web_release.py`.
- Green: values and chart version; run the task's verify: passes. Quote the summary line with counts.

#### Notes

- Dependency-bump TDD exception (a pin change with no behaviour change here); the pin test is the guard.
- `test_web_release_chart` runs `helmfile build` and needs network; environmental in this pod.
- The apply is in chat-live-smoke, after the orchestrator.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done

### S35: chat live smoke

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run lint && grep -q chat-smoke MEMORY.md`
- Verified head: fd1a382

#### Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D17, verbatim: "The orchestrator session runs it after the applies and after setting `agents_may_initiate` on the owner DM; the user confirms in Messenger what S1-S4 look like (gate question Q7)."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". Design D17, verbatim (the caller): "Under the 1:1 binding (D9) only the owner DM's bound session may post there, so the script first reads the owner DM's `binding` through the connector UI API (port-forward to the api container) and picks its caller (gate question Q11, recommended; my call pending the answer)". Open question Q11 is pending; the plan follows its recommended answer "yes".

Design D18, verbatim: "(3) Apply the connector first (migration 0002 runs in its init container, creating `room_bindings` with its backfill; the agent listener comes up), then the orchestrator with its chat secret and the v0.2.0 plugins ref (until then the routes answer 503 `chat_unconfigured`; the ref rolls agent pods), then agents-web. (4) The orchestrator session runs every apply with `--selector` in that order; no AC runs an apply. Standing rule (user, 2026-10-27): deploy whenever possible; live applies need no approval."

Open question Q1 (approved by the user 2026-10-27, "All yes"), verbatim: "Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)?" answer "yes".

Open question Q7 (approved by the user 2026-10-27), verbatim: "You confirm in Messenger what S1-S4 look like (one line each: shown, quoted reply shown, thumbs-up shown, second reaction replaced or rejected), while the orchestrator records the connector-side ids, statuses and reasons?" answer "yes".

User decision (2026-10-27), verbatim: "if the post-deploy smoke shows mautrix-meta does not carry quoted replies/reactions to Messenger, reply/react are dropped and send stays (user-approved)".

Design D17, verbatim (the drop): "If S2 or S3 shows that the deployed mautrix-meta does not carry quoted replies or reactions to Messenger, reply and react are dropped and send stays (user decision 2026-10-27): the orchestrator records it in agents-helmfile MEMORY.md and adds the removal as tasks of this epic (`ticket.py new-task`), without asking again."

Scope (agents-helmfile, orchestrator session; no subagent applies): check the new connector, orchestrator and agents-web image tags exist in Harbor; `mise run diff -- --selector name=<release>` reviewed, then `mise run apply -- --selector name=agents-matrix-connector`, then `name=agents-orchestrator`, then `name=agents-web` (workbench MEMORY 2026-10-25 standing approval for apply-smoke tasks); `mise run smoke` (the regular smoke, posts nothing); set `agents_may_initiate` on the owner DM through a port-forward to the connector api container (PUT `/matrix/api/v1/rooms/!iLWrAwaTMYnINJsyNv:szymonrichert.pl/settings`) and read its `binding` (GET `/matrix/api/v1/rooms/!iLWrAwaTMYnINJsyNv:szymonrichert.pl`) before and after the smoke; `mise run chat-smoke`; ask the user for the Messenger confirmation (Q7); record the results in agents-helmfile `MEMORY.md` (dated: pins, S1-S4 ids, statuses, reasons, hours since the last inbound, the user's confirmation, what S4 did).

#### Acceptance conditions

- ac1: (orchestrator session) the three new image tags exist in Harbor before any apply [evidence: judgement:orchestrator records the registry check of each tag in the task Notes]
- ac2: after the three applies helmfile reports no pending change [evidence: command:mise run diff]
- ac3: (orchestrator session) the regular smoke passes on the new deployment [evidence: judgement:orchestrator quotes the final line of mise run smoke with exit 0 in the task Notes]
- ac4: (orchestrator session) the owner DM reads agents_may_initiate true and no other room has it [evidence: judgement:orchestrator quotes GET /matrix/api/v1/rooms filtered to agents_may_initiate true]
- ac5: (orchestrator session) the owner DM's binding is quoted before and after mise run chat-smoke: when it was bound, it is bound to the same session afterwards; when it was unbound, it is released after the throwaway session's deletion [evidence: judgement:orchestrator quotes the binding field of GET /matrix/api/v1/rooms/{owner DM} before and after in the task Notes]
- ac6: (orchestrator session) mise run chat-smoke exits 0 with S1, S2 and S3 sent and S4's status and reason printed [evidence: judgement:orchestrator quotes the S1-S4 lines in the task Notes]
- ac7: (user) Messenger shows S1, S2 as a quoted reply, S3 as a thumbs-up, and S4 replacing the first reaction or not shown; when S2 or S3 does not show, the orchestrator records that reply/react are dropped and send stays (user decision 2026-10-27) and the removal tasks exist in this epic, with no stop to ask [evidence: judgement:the user's one-line confirmation per step, quoted in the task Notes, and for a failed S2 or S3 the drop line and the new task ids]
- ac8: agents-helmfile MEMORY.md records the live results, dated, including the caller (bound session or throwaway), the binding before and after, and whether reply/react were kept or dropped [evidence: command:grep -q "chat-smoke" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

- None new; uses `mise run diff`, `mise run apply`, `mise run smoke`, `mise run chat-smoke`, the connector UI API through a port-forward.

#### Expected outcome

The chat tools work live: an agent posted, replied and reacted in the owner DM without an inbound message, and the user saw it in Messenger.

#### Steps

- Preconditions: helmfile-chat-secrets ac6 (hash matches) green; Q6 precondition holds; Q11 and Q12 answered (design.md Open questions; a "no" amends chat-smoke-script or mxc-sends-schema first); tags exist (ac1).
- Diff and apply per release in D18's order; after each apply wait for the rollout; then `mise run diff` (ac2).
- `mise run smoke` (ac3); set the flag (ac4); quote the owner DM's binding, `mise run chat-smoke`, quote the binding again (ac5, ac6); ask the user (ac7); write MEMORY.md (ac8) and commit it.

#### Notes

- Live and irreversible operations listed in design.md: the applies (the plugins ref rolls every running agent pod, including the mx-5 hive), migration 0002 (with the room_bindings backfill), the flag grant, the Messenger sends. Standing rule (user, 2026-10-27): deploy whenever possible; live applies need no approval.
- After migration 0002 the owner DM is expected to be bound to the session of its newest run (backfill); if that session was already deleted the first binding sweep releases it within about a minute: quote the binding only after that minute.
- Never put an apply in AC evidence (workbench MEMORY 2026-10-25); `mise run diff` exits 0 only when nothing is pending.
- If S2 or S3 shows wrongly in Messenger, reply/react are dropped and send stays (user decision 2026-10-27): record it in MEMORY.md and add the removal (connector reply_to and reactions routes, orchestrator reactions route and `reply_to`, plugin chat_react and `reply_to`, docs) as new tasks of this epic with `ticket.py new-task`; do not stop to ask.
- Minutes run 3-4x over seeds for live tasks in recent epics (retro); plan for several smoke runs.

- 2026-10-27 amended: user decision 2026-10-27: reply/react dropped and send kept if S2 or S3 fails, no stop to ask; Q1 approved

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding quoted before and after; Q7 approved

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-29 done: ac1-ac6 evidence: .scratchpad/matrix/run-notes.md 'chat-live-smoke evidence' (Harbor tags, diff rc=0, smoke OK, only owner DM agents_may_initiate, binding mx-34 before/after, chat-smoke rc=0 S1-S4 sent). ac7: user via mx-34 msg 325 'Lovely 😊' / 'all recommended, go': reply/react kept, send kept, no removal tasks; S4 unverified. ac8: agents-helmfile PR #47 fd1a382 merged 52b6893; reviewer extra-facts finding dismissed (all sourced from run-notes and msg 325). pointsActual 1 is the reviewer's score of the ac8 doc step only.

- 2026-10-29 actuals: no agent records

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
