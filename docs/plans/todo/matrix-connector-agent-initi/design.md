# matrix connector agent-initiated and follow-up messages design

## Summary

A session leader reaches the user's Matrix (Messenger) chat at any time through four new
any-mcp tools, `orchestrator_chat_rooms`, `orchestrator_chat_send`, `orchestrator_chat_react` and
`orchestrator_chat_status`. The orchestrator checks the caller (agent token, pod IP, leader) and
forwards the call synchronously to a new token-protected agent listener on the connector api. The
connector checks the room (policy-allowed, and bound to the session or flagged
`agents_may_initiate`), queues a `sends` row and answers `s<n>`; the bot delivers it through
`outbound`, with quoted replies and reactions resolved from short `m<n>`/`s<n>` references, never raw
event ids. A chat room and a session are bound one to one (user decision at the final gate,
D9): the user's chat messages always go to the room's one bound session, an agent starts a chat
only in an unbound flagged room (which binds it to that agent's session), and the binding is
released only when the session is deleted. any-mcp-tatara-plugins v0.3.0 ships the tools; agents-helmfile wires one new secret, the
values and a live smoke (S1-S4) in the owner DM. Architecture decision adopted from
`.scratchpad/design/matrix-outbound-arch.md` (every "(pick)" is the design); deviations forced by
probed facts are marked "(probe)".

## Intent and why

User request (2026-10-27, relayed by the mx-5 leader), verbatim: "Bug: agents talking to the user
over the Matrix connector (bridged to Facebook Messenger) can only answer the turn that came from a
chat message. [...] Replies to turns started any other way (e.g. a <session-message> from another
session's leader, background task completions, member agents reporting) show only in the web UI and
never reach the chat. [...] The agent has no Matrix MCP tool, only plain-text replies." Requirements:
"1. Must: an agent can initiate a chat with the user over the connector (no prior inbound message
needed). 2. Must: an agent can send follow-ups (multiple messages without a user reply in between).
3. Ideally: an agent can reply to a specific message (threaded/quoted reply) and react to messages
with emoji (reactions may be enough for acknowledgements)."

Why it fails today (discovery brief sec 1): the tracker follows only the one orchestrator message the
connector posted (`tracker.py:Tracker._outcome`, `db/runs.py:latest_session`), and stops when that
run finishes; turns started any other way have no connector message, and agents have no tool.

## Goals

The README Goals, verbatim:

- G1: An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn.
- G2: An agent can send several messages in a row without a user reply in between (follow-ups), including while a chat-started turn is still running.
- G3: An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji.
- G4: An agent can list the rooms it may post to and read the delivery status of what it sent.
- G5: Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator.
- G6: A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session.
- G7: Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction.

## Non-goals

The README Non-goals, verbatim:

- No automatic forwarding of every final reply of every turn to the chat (agents use the send tool).
- No posting to arbitrary allowed rooms; no raw Matrix event ids from agents.
- No member-agent (non-leader) chat tools; members report through their leader.
- No other chat channels (Slack, Telegram); one upstream only.
- No change to the inbound allow/deny policy model.

Also (my call): no inbound Messenger reactions or reply relations as prompt context (discovery
"ideas": noted, not doing now); no agents-common change or tag; no orchestrator migration; no
NetworkPolicies.

## Anti-goals

- The agent token, the orchestrator master key or the Matrix access token reaching the connector
  agent listener, a log line, an error body or the prompt.
- A room the policy denies receiving any agent message, or a send accepted at the api and delivered
  after the policy turned to deny.
- Weakening default deny or the identifier-only rules (connector AGENTS.md: "do not weaken them").
- A second writer on any connector table, or a queue row changed outside a status-guarded update.
- A room bound to two sessions, or a session bound to two rooms, at any moment (D9); a user
  message in a bound room reaching any session but the bound one.
- Double output: the same text posted twice because the agent sent it and its final answer repeated
  it.
- An existing chat-started reply path regressing (the tracker's final-answer posting stays).
- A live deploy, `mise run apply` or a Matrix send in any acceptance condition's evidence
  (workbench MEMORY 2026-10-25).

## Constraints

- Services talk only through HTTP or a queue; each table has exactly one writer; queue tables change
  rows only through status-guarded updates (`agents_common.db.queue.transition`).
- Ordering after slash-commands-from-chat: its `plugins-release-0-2-0` tag and
  `orch-plugins-pin-0-2-0` merge first (this epic edits the same orchestrator `settings.py`,
  `pyproject.toml`, `uv.lock`, `tests/test_settings.py`, and releases plugins v0.3.0 on top of
  v0.2.0). README blocker `slash-commands-from-chat` holds the whole epic.
- `web-room-initiate-toggle` lands after markdown-rendering-in-chat and file-editor-with-tabs-and-hi
  (shared agents-web files). Ticket `depends_on` cannot name another epic's task, and `ticket.py
  new-task` refuses files shared with an in-progress epic that is not a blocker (file-editor shares
  the orchestrator `openapi.json`, `pyproject.toml`, `uv.lock` and `tests/e2e/test_e2e_kind.py`), so
  both epics are README blockers too (my call); both precede slash-commands in the approved order, so
  the extra blockers delay nothing.
- No `mise run apply` or other live deploy in AC evidence; `mise run diff` or a judgement AC
  instead; the orchestrator session runs applies and tag pushes (workbench MEMORY 2026-10-25).
  Standing rule (user, 2026-10-27): deploy whenever possible; live applies need no approval.
- No Docker in agent pods: DB-backed tests (testcontainers) and chart tests needing `helm` run in
  GitHub CI; tasks keep non-DB unit tests for their logic so the local verify has signal
  (retro proposal, see Research inputs).
- Model per task: opus when the task adds a product source module or touches more than five files,
  else sonnet; a new test file or test fake alone does not count as a module (my call).
- No em dashes, smart quotes or decorative Unicode anywhere.

## Decisions

### D1: orchestrator-relayed tools, synchronous forward to the connector

The agent calls `orchestrator_chat_*` tools of the existing orchestrator plugin; the orchestrator's
agent API checks the caller and forwards the call over HTTP to the connector's agent listener; the
connector checks the room and queues a `sends` row, which the bot delivers through `outbound`
(architecture fork 1, option A, pick).

Alternatives: B outbox table in the orchestrator pulled by the connector (refusals arrive late as a
status, agents cannot list rooms, needs orchestrator migration 0009 behind slash-commands' 0008 and an
agents-common client and tag); C the connector verifies agent tokens through an orchestrator route
(the agent token reaches a second service; pod-IP binding depends on the connector seeing the real
source IP, unknown); D a connector-issued credential per session (no way to inject it; a token in the
prompt shows in the transcript); E no tool, forward every leader final reply (no initiation, no
reply/react, posts coordination turns from the owner's Facebook account).

Why: the orchestrator alone can prove "session S's leader is calling" and the connector alone knows
the rooms; A keeps each fact where it lives, nothing new learns the agent token, refusals stay
synchronous like `session_send` (`api/agent.py:session_send`), and no orchestrator table is needed.

### D2: the chat upstream contract is `/chat/v1` (my call)

The orchestrator stays free of Matrix concepts: it calls a generic chat upstream at
`ORCH_CHAT_URL` and the connector's agent listener serves it under `/chat/v1`:

| Orchestrator agent route (agent port 8001) | Upstream call |
|---|---|
| `GET /agent/v1/chat/rooms` | `GET {ORCH_CHAT_URL}/chat/v1/rooms` |
| `POST /agent/v1/chat/messages` body `{text, room?, reply_to?}` | `POST {ORCH_CHAT_URL}/chat/v1/messages` |
| `POST /agent/v1/chat/reactions` body `{to, key}` | `POST {ORCH_CHAT_URL}/chat/v1/reactions` |
| `GET /agent/v1/chat/messages/{id}` | `GET {ORCH_CHAT_URL}/chat/v1/messages/{id}` |

Every upstream call carries `Authorization: Bearer <ORCH_CHAT_TOKEN>`, `X-Orch-Session: <session
uuid>` and `X-Orch-Slug: <slug>`, and never the agent token. Responses: rooms 200 `{"rooms": [{room_id,
name, kind, bound, agents_may_initiate}]}`; messages and reactions 202 `{id: "s<n>", status:
"queued"}` (a duplicate, D5: the existing send's id and current status); status 200 `{id, kind, status, reason, room_id, created_at, sent_at}`. Errors use the
shared `{"error": {"code", "message"}}` shape; the binding refusals of D4 (b) are 409 `room_bound`
and 409 `session_bound`. The orchestrator passes the upstream status and JSON
body through unchanged, and answers 503 `chat_unavailable` on a connection error, timeout or a
non-JSON upstream answer. There is one upstream: no multi-channel registry (YAGNI).

Alternatives: forward to `/matrix/agent/v1` (puts "matrix" in the orchestrator's contract); have the
orchestrator re-validate bodies (two validators that can drift).

### D3: the connector agent listener is a second port of the api process (probe)

`agents-matrix-connector api` binds a second listener, `MATRIX_AGENT_PORT` (default 8001), serving
only `/chat/v1/*`, `/healthz` and `/readyz`, behind a bearer gate: the sha256 hex of the presented
token must equal `MATRIX_AGENT_TOKEN_SHA256` (constant-time compare, mirroring the orchestrator's
`api/service_auth.py:ServiceGate`). With `MATRIX_AGENT_TOKEN_SHA256` empty the listener is not bound
(my call). The token never reaches a log line or an error body. The chart adds a container port
`agents` 8001 on the api pod only and a Service `<fullname>-api-agents`; the bot still has no Service.

(probe) The architecture says the listener "runs under the existing SourceAllowlist trust model,
with the token as the credential". The deployed `MATRIX_API_ALLOWED_CIDRS` is `127.0.0.1/32`
(helmfile values; only the oauth2-proxy sidecar reaches the UI app), so the orchestrator pod would be
refused. The agent listener therefore skips the source allowlist and authenticates by token alone,
exactly like the orchestrator's agent and service ports (`api/allowlist.py:SourceAllowlist`, "the
agent and service ports authenticate on their own and are skipped"). The UI app and its allowlist are
unchanged.

Alternatives: a separate `agent` subcommand and Deployment (more chart, same trust); serve it from the
bot (puts an HTTP surface next to the Matrix token; breaks "nothing reaches the bot").

### D4: room authorisation and room choice

Session S may post to room R only if both hold (architecture fork 2, pick):
(a) R is policy-allowed for agent sends, checked when the api accepts the request, when the bot
claims the send, and again right before each of its outbound rows is sent to the homeserver;
(b) R is bound to S (D9), or R is unbound, `room_settings.agents_may_initiate` is true for R and S
is bound to no room (an initiation: the bot's claim of the send binds R to S, D9). The api checks
(b) when it accepts the request; the bot's claim re-checks it and is the authoritative binding step
(the database's unique indexes decide a race, D9).

(a) defined (interrogate Act 2, the lead's call): agents send with no sender, so the room subject
alone (`policy.evaluate(_room_subject(R))`) would default-deny a room allowed only by `facebook:` or
`user:` rules and would ignore deny rules on its members. R is policy-allowed for agent sends when a
room or alias rule allows it, or when the inbound policy would accept a message from at least one
current non-bot member of R; any member matching a deny rule denies. In order: an infrastructure or
encrypted room is refused exactly as for inbound (`room_infrastructure`, `room_encrypted`); a room or
alias deny rule denies (`denied: <kind>`); a deny rule (user, facebook or display_name) matching any
current non-bot member denies (`denied: <kind>`); a room or alias allow rule allows; one current
non-bot member for whom `policy.evaluate` with that member as sender allows makes R allowed; else
`not_allowed`. A current non-bot member is a `room_members` row with membership `join` whose user id
is not `MATRIX_USER_ID` and not in `MATRIX_SELF_IDENTITIES` or `MATRIX_BRIDGE_BOTS` (my call: the
exclusion discovery already applies). One function, `api/rooms.py:agent_room_decision(room,
rule_list, settings) -> policy.Decision` over the pure `policy.evaluate_agent_room(room_subject,
member_subjects, rules, default_policy)`, serves the api checks, the listing, the bot's claim and the
send-time check (task mxc-agent-room-policy). The inbound policy model is unchanged (README
Non-goal); this is how its rules read for a sender-less agent message.

Bound means an active `room_bindings` row pairing R and S (D9); nothing else binds (no `runs` or
`sends` row is read as a binding, and the api writes no binding). A room reserved by another
session's first run in progress (an active binding without a session yet, D9) counts as bound to
another session. `room_settings.agents_may_initiate boolean NOT NULL DEFAULT false` is new; its writer stays the api.
`PUT /matrix/api/v1/rooms/{room_id}/settings` takes an optional `agents_may_initiate`; omitted keeps
the stored value (my call: the flag is an authorisation grant, so a save of the preset or trigger
from an older UI never silently grants or revokes it); `RoomView` and `RoomDetail` return it.

Room choice for a send: `room` given, that room; `room` omitted and `reply_to` given, the room of the
referenced message (my call); both omitted, S's bound room, and when S is bound to no room 422
`room_required`. A reaction's room is always its target's room. A room taken from `reply_to` or
from a reaction's target goes through (a) and (b) exactly like a given room: a reply or reaction
whose referenced message's room fails (a) answers 403 `room_not_allowed` and one failing (b) its
(b) refusal below, including an `m<n>` of an ignored inbound row in a denied room (interrogate
Act 4). An unknown room and a room failing
(a) answer the same 403 `room_not_allowed` (my call: no probing of room existence). A room passing
(a) but failing (b) answers, in this order (my call on the codes): 409 `room_bound` when R is bound
to another session (or reserved by another session's first run), 403 `room_not_authorised` when R
is unbound and not flagged, 409 `session_bound` when R is unbound and flagged but S is already bound
to another room (D9 conflicts). `GET /chat/v1/rooms` lists exactly the rooms passing (a) and (b)
for S: S's bound room when it passes (a), else, while S is bound to no room, every unbound flagged
room passing (a); `bound` is true only for S's own room; the bound room first, then by name, then
room id (my call: tiebreak pinned by a test). One predicate function serves the route checks and
the listing.

Rejected: any allowed room (lets a webhook session post into any allowed group chat as the owner's
Facebook account); a single configured home room (a helm value the user cannot change from the UI);
a room shared by several sessions with the answer routed to the last speaker (the earlier pick,
rejected by the user at the final gate, D9).

### D5: limits and validation (my call except the rate)

- Rate: at most `MATRIX_AGENT_RATE_PER_MINUTE` (default 20, gate question Q5) sends (messages and
  reactions together) per session in the last 60 s, counted on `sends` rows of any status; above
  it 429 `rate_limited`, nothing queued.
- `text`: 1 to 16000 characters (same bound as `session_send`); split into chunks of
  `MATRIX_REPLY_CHUNK_CHARS` with `chunks.split`.
- `key`: 1 to 16 code points, no whitespace, no control characters and no ASCII characters; else
  422 `invalid_key`. Whether Messenger accepts arbitrary emoji is unknown; S4 shows it.
- Request bodies reject unknown fields (422 `invalid_request`).
- Duplicate (interrogate Act 9, the lead's call): an agent that retries after a 503
  `chat_unavailable` timeout must not post twice. A request identical to a send of the same
  session, room and kind, with the same `text` (message) or `key` (reaction) and the same
  `reply_to` (the `m<n>`/`s<n>` given, or none; a reaction's `to`), compared exactly, with status
  `queued`, `sending` or `sent` and created within the last 60 s, answers 202 with that send's id and
  its current status (`{id: "s<n>", status: "queued" | "sending" | "sent"}`) and stores no new row
  (my call: `sending` is in flight like `queued`; a duplicate is not counted by the rate limit; a
  `failed` or `refused` send is not a duplicate, so a retry after a failure queues anew).
- Check order on the connector, a refusal queues nothing: token (401 `unauthorized`), body
  validation (422 `invalid_request`, `invalid_key`), reference resolution (422 `bad_reference`),
  room choice (422 `room_required`), (a) 403 `room_not_allowed`, (b) 409 `room_bound`, 403
  `room_not_authorised`, 409 `session_bound` (D4), duplicate (202, the existing send), rate 429
  `rate_limited`. The (b) check at the api, like the duplicate lookup and the rate count, is not
  atomic with the insert; the bot's claim re-checks (b) and refuses a send that lost a race
  (`refused` with reason `room_bound`, `session_bound` or `room_not_authorised`, D9).
- The orchestrator caps the forwarded request body at 256 KiB (413 `payload_too_large`) and the
  upstream call at 10 s. The cap covers the worst case of a valid maximal request (interrogate Act
  6; my call on the figure): 16000 characters of 4 bytes each are 64000 bytes raw (the plugin's httpx
  encodes JSON as raw UTF-8), and up to 192000 bytes when a client escapes every character as a
  JSON surrogate pair (12 bytes), plus a room id of up to 255 characters, `reply_to` and the JSON
  keys; 256 KiB (262144 bytes) covers all of it, where the verdict's example of 80 KiB would refuse
  the escaped form.

### D6: message references `m<n>` and `s<n>`

The prompt shows `id="m<inbound.id>"` on each `<message>`; a send answers `s<sends.id>`. Tools accept
only `m<n>` or `s<n>` (architecture fork 4). The connector resolves `m<n>` to the inbound row's
`event_id` and `s<n>` to the send's delivered `event_id` (first chunk of a message, the reaction
event of a reaction). It answers 422 `bad_reference` for an unknown id, an id of another room than
the given `room`, an `s<n>` not yet `sent`, and an `s<n>` of another session; replying to a reaction
or reacting to a reaction is 422 `bad_reference` too (my call). Raw Matrix event ids are never
accepted. `GET /chat/v1/messages/{id}` answers 404 `not_found` for an id that is not one of the
caller session's sends.

### D7: the `sends` queue and the `outbound` changes (migration 0002)

`sends` (new queue, COMMENT `queue: inserted by api, transitions by bot worker`): `id bigserial`,
`session_id uuid NOT NULL`, `slug text NULL`, `kind` CHECK `message|reaction`, `room_id text NOT
NULL`, `text text NULL`, `key text NULL`, `reply_to text NULL` (the `m<n>`/`s<n>` the agent gave),
`ref_event_id text NULL`, `event_id text NULL`, `status` CHECK `queued|sending|sent|failed|refused`,
`reason text NULL`, `created_at`, `claimed_at`, `sent_at`; indexes for queued rows, per session and
time (rate), and per room and status. `outbound` keeps the bot worker as its
only writer and gains `send_id bigint NULL`, `event_type text NOT NULL DEFAULT 'm.room.message'`,
`relates_to jsonb NULL`; its kind CHECK gains `agent` and `reaction`. `runs` gets an index on
`(session_id, room_id)` for the "other run of this session in this room" check (D9 PREAMBLE), and
`runs.preset_id` drops NOT NULL with a new CHECK `kind <> 'first' OR preset_id IS NOT NULL` (D9).
`room_settings` gains `agents_may_initiate`. The same migration creates `room_bindings` with its
two partial unique indexes and the backfill (D9).

Flow: the api inserts `sends(queued)`; a new bot step (`sender.py`, run in the bot work loop between
`Worker.tick` and `Tracker.tick`) claims queued rows `queued -> sending`, re-checks (a) (denied:
`refused` with the policy reason, no outbound row) and (b) (D4; a room bound to another session,
a session bound elsewhere or an unflagged unbound room: `refused` with reason `room_bound`,
`session_bound` or `room_not_authorised`, no outbound row), binds an unbound flagged room to the
send's session in the same transaction when (b) holds through the flag (D9), and inserts the
outbound rows in the same transaction with transaction ids `mxa-<send id>-<n>` (message chunks) or `mxa-<send id>-r`
(reaction); `Tracker._send_pending` sends every pending row with its own event type and content;
before it sends a row of a send (kind `agent` or `reaction`) it re-checks (a) for that row's room,
and when (a) now fails it marks every still-pending outbound row of that send `failed` with the
policy reason and moves the send `sending -> refused` with the same reason, in one transaction, and
sends nothing of it (interrogate Act 10: rows already pending while the homeserver was down are not
delivered after the policy turned to deny; my call: chunks already sent stay sent); once every
outbound row of a `sending` send has ended, the bot marks it `sent` (all sent, `event_id` of the
first row) or `failed` (the first failed row's reason); a send that ends `failed` or `refused`
with none of its outbound rows sent releases, in that transaction, the binding it created
(`send_failed`, D9). Sends never wait on `inbound.rooms_ready`, so follow-ups go out while a chat
run is in progress (G2). `sends` rows that ended and released `room_bindings` rows are pruned with
the existing daily retention.

### D8: reply and reaction content

Reply: `m.room.message` `{msgtype: m.text, body, "m.relates_to": {"m.in_reply_to": {"event_id":
E}}}` on the first chunk only, with no fallback body (fallbacks are best effort since MSC3676;
removal proposed in MSC2781). Reaction: `m.reaction` `{"m.relates_to": {"rel_type": "m.annotation",
"event_id": E, "key": <emoji>}}`. `MatrixClient.send_event(room_id, event_type, txn_id, content)` is
the one PUT; `send_text` becomes a call of it.

### D9: hard 1:1 binding between a chat room and a session (user decision)

User decision (final gate, 2026-10-27, relayed by the mx-5 leader), verbatim: "1. hard 1:1
relationship between chat and session / Wrap other code changes around it, besides that: Go". It
replaces the last-speaker routing (the architecture's fork 3 pick, rejected with Q2): each chat
room is bound to at most one session at a time and that session to exactly that one room; a user
message in a bound room always goes to its bound session. There is no last-speaker routing and no
room shared by several sessions.

Storage: the uniqueness lives in the connector's own database. Migration 0002 creates
`room_bindings` (COMMENT `writer: bot worker`): `id bigserial`, `room_id text NOT NULL`,
`session_id uuid NULL`, `slug text NULL`, `origin` CHECK `inbound|agent`, `run_id bigint NULL` (the
first run that bound it), `send_id bigint NULL` (the send that bound it), `created_at`,
`released_at timestamptz NULL`, `release_reason text NULL`. A binding is active while `released_at`
is NULL. A partial unique index on `room_id WHERE released_at IS NULL` and one on `session_id WHERE
released_at IS NULL AND session_id IS NOT NULL` make two active bindings of one room, or of one
session, impossible; CHECKs: an `inbound` binding has a `run_id`, an `agent` binding a `session_id`
and a `send_id`. The bot worker (its worker and sender steps, one bot process) is the only writer;
the api only reads it. A release is a guarded UPDATE (`released_at IS NULL`, plus the expected
session); released rows stay as history and are pruned with the daily retention (my call).
`runs.latest_session` is removed: the binding replaces it.

Backfill (my call, gate question Q12): 0002 inserts one active `inbound` binding per room from its
newest run that has a session (its session id, slug and run id), or a reservation for a room whose
newest run is an in-progress first run without a session yet, so existing chats keep their session.
A session that is the newest of several rooms (not expected: the worker creates one `mx-` session
per room) binds only the room of its newest run. A backfilled binding of a session already deleted
is released by the first binding sweep (below).

How a room gets bound:
- Inbound chat in an unbound room: the worker's claim transaction of a `first` run reserves the
  room (an active `inbound` binding with the run id and no session yet), so no agent can initiate
  there while the session is being created; when the run stores its session id
  (`_RoomRunStore.set_session`), the same transaction fills the binding's session id and slug
  (idempotent for a retried dispatch). A first run that finishes without a session (for example
  `preset_not_found` or a refused dispatch) releases its reservation in its finish transaction
  (`run_failed`).
- Agent initiation in an unbound flagged room: the api accepts the send (D4 (b), advisory); the
  bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active
  `agent` binding (session id and slug of the send, its send id) when the room is still unbound,
  still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes
  decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never
  makes a second binding. If that send then ends with none of its outbound rows sent (`failed`, or
  `refused` at send time, D7), the settle transaction releases the binding it created
  (`send_failed`, my call: a binding message that never reached the user binds nothing).
- A send of a session into the room it is bound to binds nothing new.

Routing a user message (`Worker._room`): the room's active binding decides, before any preset
check (interrogate Act 1, B5, Q9):
- bound to a session that `agents_common.runs.running_session` reports running (it exists and its
  desired state is active, not that it is mid-turn): the batch becomes a `follow` run into it,
  whatever its slug (an `mx-` chat session, a hive leader, a webhook or schedule session), and the
  tracker posts its final answer as today. A busy session (for example a hive leader in a long
  turn) gets the batch queued behind its current turn; the tracker follows that message for at
  most `MATRIX_RUN_TIMEOUT_SECONDS` (default 1800 s, 30 min), and meanwhile the room's later
  messages stay `new`, because a room with a run in progress is not ready (`inbound.rooms_ready`),
  as for every run today.
- bound to a session reported gone or deleting (`running_session` returns None): the binding is
  released (`session_gone`) and the room is handled as unbound in the same tick.
- a refused session check (an `OrchestratorError` other than not found) keeps the binding and
  leaves the rows `new`, logged at most once a minute (my call: a hard binding never moves on an
  ambiguous answer); an unavailable orchestrator retries next tick as today.
- reserved by a first run in progress: nothing to do (the room is not ready anyway).
- unbound: only now does the preset matter: the room's effective preset (room setting, else
  default) starts a new `mx-` session under the new-session cap as today, which binds the room;
  with no preset the rows are ignored `no_preset` as today and the room stays unbound.
A delivery that finds the bound session gone (`Worker._session_gone`) releases the binding in the
transaction that fails the run `session_gone`, so the next tick starts a new session as today.

On session delete: the connector learns it from the orchestrator (`running_session` returns None:
not found, or desired state `deleting`) and releases the binding (`session_gone`): at once when it
routes the room's next batch, and otherwise within about a minute through a binding sweep in
`Worker.tick` (at most once per 60 s, my call: one `GET /api/v1/sessions/{id}` per active binding
with a session; an unavailable orchestrator ends that sweep, a refused check keeps the binding).
After the release the room is unbound: the next user message starts a new `mx-` session (preset
needed), and an agent may initiate there if the room is flagged. Nothing else releases a binding:
turning `agents_may_initiate` off or adding a deny rule does not unbind (a deny rule still stops
every agent send through D4 (a) and every inbound message) (Q10).

Conflicts (D4 (b), D5): an agent of session S trying to start a chat in a room bound to another
session (or reserved by another session's first run in progress) is refused 409 `room_bound`,
synchronously at the api, and at the sender's claim as `refused` with reason `room_bound` when the
binding appeared after the api accepted the send; a session already bound to a room trying a
second, unbound flagged room is refused 409 `session_bound` (claim: `refused`, `session_bound`).
Neither stores an outbound row or changes any binding. The room listing shows a bound session only
its own room and an unbound session only unbound flagged rooms, so an agent that follows the
listing meets neither refusal.

`runs.preset_id` of a follow run (interrogate Act 1): the bound session's `preset_id` from the
`running_session` lookup (`GET /api/v1/sessions/{id}`) the worker already makes; when it is null,
the room's effective preset; when that is null too, NULL. Migration 0002 drops NOT NULL on
`runs.preset_id` and adds CHECK `kind <> 'first' OR preset_id IS NOT NULL` (my call: an explicit
"no preset" rather than a sentinel uuid; a first run still always has one, and no NOT NULL
violation is possible). No extra orchestrator call; agents-common is unchanged (a follow run's
`RunRef.preset_id` is never read by `deliver`).

A follow run into a session that has no other run in this room (the run itself excluded), for
example the first user answer into a session bound by its agent send, renders the prompt with the
PREAMBLE (as a first prompt), because that session never saw the untrusted-input framing (my
call). This holds on the first delivery and on every retry through `Worker._resume`, which today
renders `first=False` for every follow run (interrogate Act 7).

The room's binding is visible to the user (my call: the live smoke and the operator need it):
`RoomView` and `RoomDetail` of the UI API gain `binding: {session_id, slug, origin, since} | null`
(the active binding; a reservation shows `session_id` null), next to the unchanged `session` (the
latest run). Showing it in agents-web: noted, not doing now.

MEMORY amendment (connector MEMORY.md, dated): 2026-10-25 "One agent session per room" becomes
"one session per room and one room per session (hard 1:1 binding in room_bindings), released only
when the session is deleted".

### D10: no double output (my call on the match rule)

When a chat-started run's turn completes, the tracker compares its `final_text`, stripped, with the
stripped `text` of every `message` send of the same session created at or after the run's
`started_at`. Only a send that reached the user counts (interrogate Act 3, the lead's call):

- a matching send that is `sent`: the run closes `handled` with reason `already_sent` and no
  outbound row is stored;
- else a matching send still `queued` or `sending`: the run stays in progress and the check
  repeats each tick until that send settles, bounded by the run timeout (`MATRIX_RUN_TIMEOUT_SECONDS`
  from the run's `started_at`); when the timeout passes first, the final answer is posted (my call:
  a late duplicate beats a lost answer);
- a matching send that ended `failed` or `refused` does not count, so the final answer is posted.

Anything else posts as today.

### D11: prompt changes

`prompt.render` adds `room_id="..."` to `<chat>` and `id="m<inbound.id>"` to each `<message>`
(escaped like every attribute). PREAMBLE gains: final answers are posted only for chat-started
turns; use `orchestrator_chat_send` to reach the user at any other time, `reply_to` and
`orchestrator_chat_react` take the `m<n>` ids shown here.

### D12: the orchestrator relay

`api/chat.py` (new router, agent port only): every route runs `require_agent`, then `_leads` (403
`not_leader`), then requires chat configured (503 `chat_unconfigured`), then forwards (D2). Settings
`ORCH_CHAT_URL` (http or https URL) and `ORCH_CHAT_TOKEN` (secret, never in repr or logs): both set
or both empty, else a settings error naming both (my call). Nothing is stored. The chart takes
`chat.url`, `chat.token` or `chat.existingSecret`/`chat.existingSecretKey`, renders `ORCH_CHAT_URL`
in the settings ConfigMap and `ORCH_CHAT_TOKEN` from a Secret, on the api container only (my call).

### D13: plugin tools, release v0.3.0, allow list with the pin

The orchestrator plugin gains `chat_rooms`, `chat_send`, `chat_react`, `chat_status` (HttpBinding
tools, existing `on_error` mapping); descriptions say the final answer reaches the chat only for
chat-started turns, sends are asynchronous and return `s<n>`, `reply_to`/`to` take `m<n>`/`s<n>`,
leader only, status via `orchestrator_chat_status`, and the 1:1 binding (D9): a session talks in at most one chat room, its bound room, and starts a chat only in an unbound flagged room while it is bound to none (`room_bound`, `session_bound` otherwise). any-mcp-tatara-plugins releases v0.3.0 (the
orchestrator session pushes the tag after merge). The orchestrator then pins v0.3.0 and adds
`CHAT_TOOLS` to every session's allow list (`k8s/on_start.py:orchestrator_allow`); the routes decide.

(probe) The allow-list change must land with the pin, not with the routes:
`tests/test_on_start.py::test_allowed_tools_exist_in_plugin` requires every allowed tool to exist in
the pinned plugin. `claude.main_agent_only_tools` already covers `mcp__any-mcp__orchestrator_*`
(`k8s/render.py:159`), so subagents cannot call them.

### D14: secrets and helmfile values (probe)

One new token. `scripts/bootstrap-secrets.sh` gains `bootstrap_chat_token`: both files or neither,
never rotates, never prints. (probe) The architecture says the sha256 goes to
`values/agents-matrix-connector/default.secrets.yaml`; that file exists and the script never touches
an existing target, so the token goes to two new files instead:
`values/agents-orchestrator/chat-token.secrets.yaml` (`{chat: {token}}`) and
`values/agents-matrix-connector/agent-token.secrets.yaml` (`{agentApi: {tokenSha256}}`), both listed
on their releases in `helmfile.yaml.gotmpl`. Values: connector image tag and chart version, agent
port; orchestrator image tag and chart version, `chat.url:
http://agents-matrix-connector-api-agents:8001`, `ORCH_ANY_MCP_PLUGINS_REF: v0.3.0`; agents-web tag
with the toggle.

### D15: agents-web toggle

The room drawer gets an "Agents may start chats" switch bound to `agents_may_initiate`, saved with
the preset and trigger in the one PUT (gate question Q4). The vendored `openapi/matrix.json` and
generated `src/api/matrix-schema.d.ts` follow the connector's committed `openapi.json`.

### D16: tests: unit, contract, e2e

Unit tests per task. Contract: the connector commits its agent listener OpenAPI document
(`openapi-agent.json`, pinned like `openapi.json`); the orchestrator vendors it with a source line
(`tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`), its fake chat upstream
validates against it, and a test asserts every relay route maps to a path and method of the
vendored document (my call). The orchestrator's tools-parity test drives the released v0.3.0 plugin
against the real routes and the fake upstream. E2E: the connector stack test (real api and bot
processes, fake homeserver, fake orchestrator) covers send without inbound, follow-ups during a
running chat run, reply and reaction relations, refusals, the 1:1 binding (an initiation binds the
room, the user's answer reaches the bound session, `room_bound` and `session_bound` refusals, the
release on session delete), and a 16000-character text of 4-byte characters accepted and delivered
in chunks (interrogate Act 6). On the orchestrator side the tools-parity test also sends that text
through the released plugin, the relay and the fake upstream, and the relay test sends it raw and
fully escaped.

### D17: live smoke S1-S4 in the owner DM, in its own script

`scripts/chat-smoke.sh` (mise task `chat-smoke`), never part of `scripts/smoke.sh`, because it posts
real messages from the owner's Facebook account. Under the 1:1 binding (D9) only the owner DM's
bound session may post there, so the script first reads the owner DM's `binding` through the
connector UI API (port-forward to the api container) and picks its caller (gate question Q11,
recommended; my call pending the answer): when the DM is bound, the leader pod of the bound session
(that pod's own `ORCH_AGENT_*` env, never printed; no message to or change of that session, nothing
created or deleted); when it is unbound, a throwaway alone session whose S1 initiates and binds the
DM, deleted at the end, after which the script waits for the binding's release (its own deadline).
From the chosen pod it calls the orchestrator agent routes: lists rooms (the owner DM
`!iLWrAwaTMYnINJsyNv:szymonrichert.pl` must be listed), S1 sends a message with no inbound in the
run, S2 replies to S1's `s<n>`, S3 reacts with a thumbs-up to S1's `s<n>`, S4 reacts with a second,
different emoji to the same target; it polls each send's status to `sent` or `failed` with its own
deadline per wait, prints the caller (bound session or throwaway), the binding before and after,
the ids, statuses and reasons, owns its port-forwards (trap cleanup) and deletes the throwaway
session when it made one. The orchestrator session runs it after the applies and after setting
`agents_may_initiate` on the owner DM; the user confirms in Messenger what S1-S4 look like (gate
question Q7). If S2 or S3 shows that the deployed mautrix-meta does not carry quoted replies or
reactions to Messenger, reply and react are dropped and send stays (user decision 2026-10-27): the
orchestrator records it in agents-helmfile MEMORY.md and adds the removal as tasks of this epic
(`ticket.py new-task`), without asking again. Architecture S1-S4: "S1 a send with no inbound message for >24h
shows up in Messenger; S2 a reply shows as a quoted reply; S3 a thumbs-up reaction shows; S4 a
second, different reaction replaces the first or is rejected (and how the connector sees the
failure)."

### D18: deploy order

(1) slash-commands' plugins v0.2.0 tag and orchestrator pin merge first (README blocker). (2) No
orchestrator migration. (3) Apply the connector first (migration 0002 runs in its init container,
creating `room_bindings` with its backfill; the agent listener comes up), then the orchestrator with
its chat secret and the v0.3.0 plugins ref (until then the routes answer 503 `chat_unconfigured`;
the ref rolls agent pods), then agents-web. (4) The orchestrator session runs every apply with
`--selector` in that order; no AC runs an apply. Standing rule (user, 2026-10-27): deploy whenever
possible; live applies need no approval. Gate question Q6 (approved) settles how this deploy
relates to the one deploy epic approved for the four earlier epics.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | ran (discovery brief `.scratchpad/discovery/matrix-outbound.md`) | reuse `MatrixClient._request`, `chunks.split`, deterministic txn ids, `Tracker._send_pending`, `queue.transition`, `policy.evaluate` room subject, `require_agent`/`_leads`/`session_send` refusal order, plugin `HttpBinding` shape, fake homeserver generic `_send` (brief "Plan inputs: reuse") | Matrix E2EE, an appservice, display-name allow rules, agents holding the Matrix token or master key, NetworkPolicies (brief "do-not-build") |
| architect (opus) | ran (`.scratchpad/design/matrix-outbound-arch.md`) | forks 1, 2, 4, 5 and 6 picks (D1-D18); fork 3 (last speaker) replaced by the user's 1:1 binding (D9) | outbox (B), connector token verify (C), connector credential (D), auto-forward (E) |
| research-docs | ran inside the architect pass | `m.in_reply_to` on first chunk, no fallback (MSC3676, https://git.sudo.is/matrix/matrix-doc/src/branch/main/proposals/3676-transitioning-away-from-reply-fallbacks.md; MSC2781); `m.annotation` reactions; mautrix-meta ROADMAP marks Matrix to Messenger replies and reactions done (https://raw.githubusercontent.com/mautrix/meta/main/ROADMAP.md) | reply fallback bodies |
| research-code-external | skipped: the analogues are in-repo (orchestrator agent and service ports, `session_send`) | none | none |
| research-papers | skipped: no algorithmic core | none | none |

## Research inputs

Plan inputs of the discovery brief and architecture, and the retro proposals of the last five done
epics that bear on this epic (recurring workflow ones first).

- Retro, recurring (file-download-in-file-browse, leader-auto-handover): no Docker in agent pods makes DB tests CI-only. Acted on: every DB-backed task keeps non-DB unit tests for its logic and names CI as the DB gate in Notes: mxc-sends-schema, mxc-agent-routes, mxc-bot-sends-delivery, mxc-room-session-binding, mxc-skip-duplicate-final, mxc-e2e-agent-sends, orch-chat-relay, orch-chat-tools-allow.
- Retro, recurring (leader-auto-handover, generic-any-mcp-with-git-and, cross-session-messaging-and): live apply, smoke and release tasks run 3-4x over the minutes seed. Acted on: higher points for chat-live-smoke (8) and chat-smoke-script (5), so calibration seeds them higher; minutes are never set by hand.
- Retro, recurring (generic-any-mcp-with-git-and, cross-session-messaging-and): defects missed because fakes encode a wrong assumption; ACs that shell out cite a captured real output sample. Acted on: orch-chat-contract (fake upstream validated against the connector's committed agent OpenAPI); chat-smoke-script (its fakes replay responses captured from the connector agent routes' committed OpenAPI examples and the orchestrator README shapes).
- Retro, recurring (leader-auto-handover, cross-session-messaging-and): smoke-script deadlines checked per wait against the AC; the duplicate-predicate sweep runs before the last code task merges. Acted on: chat-smoke-script (one deadline per wait, pinned by a test); mxc-agent-routes (one authorisation predicate for routes and listing, AC).
- Retro, recurring (cross-session-messaging-and, matrix-read-receipts): a smoke owns its port-forward (trap cleanup, kill a stale one first). Acted on: chat-smoke-script.
- Retro, recurring (cross-session-messaging-and): hand-backs quote the verify summary line with counts; task verify commands do not use bare `-q`. Acted on: every task's verify omits `-q`.
- Retro, recurring (paste-env-contents-into-the, matrix-read-receipts): each merge-semantics or tiebreak ruling in Notes names a pin test. Acted on: mxc-room-initiate-flag (omitted flag keeps value), mxc-agent-routes (room list order), mxc-sends-schema (backfill: a session newest in several rooms binds only its newest run's room), mxc-room-session-binding (a refused session check keeps the binding).
- Retro, recurring (leader-auto-handover, file-download-in-file-browse): session gitconfig lacks identity or credential helper; epic-run preflight checks `git config user.email`. No task: epic-run preflight (orchestrator).
- Retro, recurring (leader-auto-handover, paste-env-contents-into-the): `ticket.py new-task` leaves template sections. No task: the planner filled every task's Interfaces, Expected outcome, Steps and Notes in this plan.
- Retro, code (cross-session-messaging-and): kind e2e allow-list assertions hard-code tool names; derive them from the shared constant. Acted on: orch-chat-tools-allow.
- Retro, code (generic-any-mcp-with-git-and): a fake credential literal tripped GitGuardian. Acted on: mxc-agent-listener, orch-chat-relay, helmfile-chat-secrets build fake tokens at runtime.
- Retro, tech debt (file-download-in-file-browse): orchestrator `FileEntry.target_type` needs wrapper >= 4581f3b; the later deploy must pin them together. Acted on: gate question Q6 and helmfile-chat-values (the orchestrator image this epic deploys includes it).
- Retro, tech debt (leader-auto-handover): agents-helmfile has no CI workflows; helmfile PRs rest on the reviewer's local verify. Noted, not doing now: a helmfile CI workflow; helmfile tasks quote their local verify.
- Retro, tech debt (generic-any-mcp-with-git-and): smoke depends on Harbor holding every deployed tag. Acted on: chat-live-smoke checks the three new image tags exist before applying (judgement AC).
- Discovery fix-as-ac: replies to turns not started by a chat message must reach the mapped room; follow-ups without an intervening user message; denied or unknown rooms refused; only the leader may send. Acted on: mxc-agent-routes, mxc-bot-sends-delivery, orch-chat-relay, mxc-e2e-agent-sends.
- Discovery reuse: `MatrixClient._request` and error taxonomy, `chunks.split`, txn-id dedup, `Tracker._send_pending`. Acted on: mxc-bot-sends-delivery.
- Discovery reuse: `policy.evaluate` room subject (`api/rooms.py:_room_subject`). Acted on: mxc-agent-routes, mxc-bot-sends-delivery.
- Discovery reuse: orchestrator `require_agent`, `_leads`, `session_send` refusal pattern. Acted on: orch-chat-relay.
- Discovery reuse: plugin `HttpBinding` tool shape and `on_error`. Acted on: plugin-chat-tools.
- Discovery reuse: fake homeserver generic `_send` records content. Acted on: mxc-bot-sends-delivery, mxc-e2e-agent-sends.
- Discovery do-not-build: E2EE, appservice, display-name allow rules, Matrix token or master key for agents, NetworkPolicies. Acted on: none built (Non-goals).
- Discovery idea: inbound Messenger reactions and replies as prompt context. Noted, not doing now.
- Architecture risk: double output. Acted on: mxc-skip-duplicate-final, mxc-prompt-message-refs (PREAMBLE), plugin-chat-tools (description).
- Architecture unknown: deployed mautrix-meta behaviour for replies and reactions. Acted on: chat-live-smoke (S1-S4; user decision 2026-10-27: reply/react dropped and send kept if S2 or S3 fails).
- Interrogate verdict (`interrogate.md`, 2026-10-27), Act on 1 preset contradiction. Acted on, adapted to the 1:1 binding: mxc-room-session-binding (the bound session takes the batch before any preset check), mxc-sends-schema (D9).
- Interrogate Act 2 policy for sender-less agent sends. Acted on: mxc-agent-room-policy, mxc-agent-routes, mxc-bot-sends-delivery (D4).
- Interrogate Act 3 failed send suppresses the final answer. Acted on: mxc-skip-duplicate-final (D10).
- Interrogate Act 4 reaction and reply room authorisation. Acted on: mxc-agent-routes (D4).
- Interrogate Act 5 tracker test spy. Acted on: mxc-bot-sends-delivery (tests/test_tracker.py in its files; MatrixClient.send_event split out to mxc-matrix-send-event to stay within 8 files).
- Interrogate Act 6 size caps. Acted on: orch-chat-relay, orch-chat-tools-allow, mxc-agent-routes, mxc-e2e-agent-sends (D5, D16).
- Interrogate Act 7 PREAMBLE lost on resume. Acted on: mxc-room-session-binding (D9).
- Interrogate Act 8 last-speaker ordering. Superseded: the user rejected last-speaker routing at the final gate (Q2); the 1:1 binding (D9) leaves no ordering to define. No task.
- Interrogate Act 9 duplicate send on timeout retry. Acted on: mxc-agent-routes (D5).
- Interrogate Act 10 policy re-check at send time. Acted on: mxc-bot-sends-delivery (D4, D7).
- Interrogate Consider (binding never expires; busy hive leader; "while it runs"). Acted on: D9 and Q10 (a binding is released when its session is deleted), D9 (a busy bound session holds the room's later messages until its reply or the run timeout; "running" means desired state active): mxc-room-session-binding.
- Interrogate Noted (error codes reveal m<n> existence; token-only agent port; reaction rows in the UI feed). Noted, not doing now.
- User decision (final gate, 2026-10-27), "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". Acted on: D9 and every task that touches the binding: mxc-sends-schema (room_bindings, unique indexes, backfill), mxc-room-session-binding (routing, reservation, release on session delete, sweep), mxc-bot-sends-delivery (binding at claim, claim-time refusals, release of a failed initiation), mxc-agent-routes (409 room_bound and session_bound, listing), mxc-room-initiate-flag (binding in the room view), plugin-chat-tools (descriptions and codes), mxc-e2e-agent-sends, chat-smoke-script and chat-live-smoke (Q11). Task mxc-route-last-speaker retired (its file removed; mxc-room-session-binding takes its non-routing scope: follow-run preset rule, PREAMBLE on resume, MEMORY and README).
- Retro, recurring (markdown-rendering-in-chat): an agents-web vitest test is flaky under load and the failing name was never captured. Acted on: web-room-initiate-toggle (Notes: on a first-run failure capture the failing test name and output tail before any rerun).
- Retro, workflow (markdown-rendering-in-chat): calibrate seeds by task kind. No task: calibration tooling, not this epic.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 orchestrator-relayed tools | orch-chat-relay, mxc-agent-routes, plugin-chat-tools |
| D2 chat upstream contract | orch-chat-relay, mxc-agent-routes, orch-chat-contract |
| D3 connector agent listener | mxc-agent-listener, mxc-chart-agent-port |
| D4 room authorisation and room choice | mxc-sends-schema, mxc-room-initiate-flag, mxc-agent-room-policy, mxc-agent-routes, mxc-bot-sends-delivery, plugin-chat-tools |
| D5 limits and validation | mxc-agent-listener, mxc-agent-routes, orch-chat-relay, orch-chat-tools-allow |
| D6 message references | mxc-agent-routes, mxc-sends-schema |
| D7 sends queue and outbound | mxc-sends-schema, mxc-bot-sends-delivery |
| D8 reply and reaction content | mxc-matrix-send-event, mxc-bot-sends-delivery |
| D9 hard 1:1 room-session binding | mxc-sends-schema, mxc-room-session-binding, mxc-bot-sends-delivery, mxc-agent-routes, mxc-room-initiate-flag, mxc-e2e-agent-sends |
| D10 no double output | mxc-skip-duplicate-final |
| D11 prompt changes | mxc-prompt-message-refs |
| D12 orchestrator relay | orch-chat-relay, orch-chart-chat |
| D13 plugin tools, release, allow list | plugin-chat-tools, plugins-release-0-3-0, orch-plugins-pin-0-3-0, orch-chat-tools-allow |
| D14 secrets and helmfile values | helmfile-chat-secrets, helmfile-chat-values, helmfile-web-toggle-pin |
| D15 agents-web toggle | web-room-initiate-toggle, helmfile-web-toggle-pin |
| D16 unit, contract, e2e tests | orch-chat-contract, orch-chat-tools-allow, mxc-e2e-agent-sends |
| D17 live smoke S1-S4 | mxc-room-initiate-flag, chat-smoke-script, chat-live-smoke |
| D18 deploy order | helmfile-chat-values, chat-live-smoke |

## Review focus

- Authorisation (mxc-agent-room-policy, mxc-agent-routes, mxc-bot-sends-delivery): (a) as defined
  in D4 (member-aware, deny on any member) on every route, at claim and again right before each
  agent row is sent; the same predicate for listing; a room taken from `reply_to` or a reaction
  target checked like a given room; no route accepts a raw event id; a session cannot read or
  reference another session's `s<n>`.
- Duplicate suppression (mxc-skip-duplicate-final, mxc-agent-routes): only `sent` sends suppress a
  final answer; a pending match delays the close within the run timeout; a retried identical send
  returns the existing `s<n>`.
- Secrets: the agent token never leaves the orchestrator (forwarded headers asserted); the chat token
  and its hash never logged or echoed; the agent listener has no SourceAllowlist bypass of the UI app.
- Single writer and guarded transitions: `sends` inserted only by the api, moved only by the bot,
  every move through `queue.transition`; `outbound` and `room_bindings` written only by the bot.
- Exactly-once delivery across a bot restart between send and mark (deterministic `mxa-` txn ids).
- The 1:1 binding (mxc-sends-schema, mxc-room-session-binding, mxc-bot-sends-delivery,
  mxc-agent-routes): two active bindings of one room or of one session are impossible in the
  database (partial unique indexes), not only in code; `room_bindings` written only by the bot; a
  user message in a bound room reaches only the bound session, before any preset check; a first
  run reserves the room at claim and a first run without a session releases it; only a gone or
  deleting session (route time or the 60 s sweep) and a failed initiating send release a binding,
  never a refused check, a flag change or a deny rule; `room_bound` and `session_bound` refused at
  the api and again at claim with no outbound row; the backfill keeps each existing chat's session;
  a follow run's preset_id is never a NOT NULL violation; the PREAMBLE reaches a session new to the
  room on the first delivery and on a resume.
- Smoke script: every wait has its own deadline; nothing secret printed; cleanup on every exit path;
  the caller is the owner DM's bound session when the DM is bound and a throwaway session only when
  it is unbound (Q11), and the bound session is never messaged, changed or deleted.

## Left to the builder

- Module and function names inside the connector and orchestrator, within the files each task lists.
- How the api process runs two uvicorn listeners (two `serve_asgi` tasks or one server with two
  sockets), as long as each listener serves only its own app.
- The exact PREAMBLE and tool-description wording, within D11 and D13's content.
- Index names and column order in migration 0002, within D7's columns and constraints.
- Whether the sender step settles `sending` sends in the same tick or the next.
- Function names of the binding repository (`db/bindings.py`) and how the 60 s binding sweep keeps
  its last-run time, within D9.

## Assumptions and unknown facts

- The deployed mautrix-meta bridges Matrix `m.in_reply_to` and `m.annotation` to Messenger (upstream
  ROADMAP says done; deployed version unknown). Confirmed by chat-live-smoke S2-S4; if S2 or S3 fails,
  reply/react are dropped and send stays (architecture "changes my mind"; user-approved 2026-10-27,
  no stop to ask).
- Messenger accepts arbitrary emoji keys or a fixed set: unknown; S4 and the key rule (D5) bound it.
- Messenger automation or rate limits on the owner account: unknown; the per-session rate limit bounds it.
- The oauth2-proxy admission sidecar on the connector api pod does not intercept a second container
  port, as on the orchestrator api pod (helmfile values comment, orchestrator agents port 8001).
  Confirmed by chat-live-smoke (the relay reaches the connector).
- SOPS encryption of the new secrets files needs only the public recipients in `.sops.yaml`; decryption
  for diff and apply needs the orchestrator session's key. Confirmed when helmfile-chat-secrets runs.

## Builder check settlements (2026-10-27)

The builder check (sonnet, no prior context) asked nine questions; settled here, facts probed:

- B1 (vendoring from `origin/main`): the agents-matrix-connector PR merges mid-epic, as soon as its tasks before orch-chat-contract are done and green, the same way the claude-code-wrapper PRs merged mid-epic in file-download-in-file-browse and file-editor-with-tabs-and-hi; orch-chat-contract and web-room-initiate-toggle start only after that merge and are amended with its sha (my call).
- B2 (tag v0.3.0): the orchestrator session pushes `v0.3.0` after plugins-release-0-3-0 merges with green CI and after reporting to the mx-5 leader; orch-plugins-pin-0-3-0 and orch-chat-tools-allow wait for the tag, they never start without it (my call).
- B3 (v0.2.0 state): this epic is blocked by slash-commands-from-chat, markdown-rendering-in-chat and file-editor-with-tabs-and-hi; it is claimed only after all three are merged, so those files are read in their merged state at build time (fact: README blockers).
- B4 (gate questions): Q1-Q10 were answered at the gate (final answer 2026-10-27); Q11 and Q12 came with the 1:1 rework and are answered before the tasks they touch start (chat-smoke-script, mxc-sends-schema).
- B5 (flagged room without preset): a room bound to a running session (D9; for example one an agent bound by initiating there) routes the user's answer to it without a preset; a preset is needed only to start a new mx- session in an unbound room, and without one the answer is ignored as `no_preset` exactly as today (my call; Q9 adapted to the 1:1 rule).
- B6 (answers into non-mx sessions mid-turn): yes: a room bound to a non-mx session (a hive leader, a webhook or schedule session that initiated there) sends every user message to it as a follow message queued behind its current turn, and the tracker posts that session's final answer to the chat (D9; Q2's last-speaker routing was rejected, the 1:1 binding decides).
- B7 (`ORCH_CHAT_URL`): the chart default is empty (routes answer 503 chat_unconfigured); agents-helmfile sets `http://agents-matrix-connector-api-agents:8001`, the in-namespace Service name; namespace `agents` (fact: agents-helmfile values).
- B8 (`room` argument): `room` takes a Matrix room id (`!id:server`) as listed by orchestrator_chat_rooms and as shown in the prompt's `room_id`, or is omitted; names are never accepted (my call).
- B9 (images): each repo's CI builds and pushes the Harbor image on its `main` merge (build-push job, as for claude-code-wrapper 4581f3b); chat-live-smoke's precondition is that those main builds are green (fact: CI workflows).

## Open questions

- Q1: Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)? [answer: yes (approved by the user 2026-10-27, 'All yes')]
- Q2: Your next chat message after an agent starts a chat or sends a follow-up goes to the session that last spoke in the room while it runs ('while it runs' means the session exists with desired state active, not that it is mid-turn), including a hive leader or a webhook or schedule session, as a follow message with its final answer posted to the chat; if that session is busy (for example a hive leader in a long turn), your message waits behind its current turn and the connector tracks the reply for up to 30 min (the run timeout), holding your later messages in that room meanwhile; otherwise it goes to the room's chat session? [answer: no: rejected by the user at the final gate answer 2026-10-27, relayed by the mx-5 leader: '1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go'; replaced by the hard 1:1 room-session binding (D9): your chat messages always go to the room's one bound session]
- Q3: No automatic forwarding of every final reply; agents use the send tool (my call, pending gate)? [answer: yes (approved by the user 2026-10-27, 'All yes')]
- Q4: Add an 'agents may start chats' toggle to the agents-web room settings in this epic (my call, pending gate)? [answer: yes (approved by the user 2026-10-27, 'All yes')]
- Q5: Per-session limit of 20 messages a minute (my call, pending gate)? [answer: yes (approved by the user 2026-10-27, 'All yes')]
- Q6: This epic's agents-helmfile values and live smoke run only after the one deploy approved for the four earlier epics (file-download, markdown, file-editor, slash-commands) has applied, so this epic's applies move only the connector, the orchestrator (chat config, plugins v0.3.0) and agents-web; if that deploy epic does not exist when this epic reaches helmfile-chat-values, the orchestrator creates and runs it first? [answer: yes (approved by the user, final gate answer 2026-10-27, relayed by the mx-5 leader: '1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go')]
- Q7: You confirm in Messenger what S1-S4 look like (one line each: shown, quoted reply shown, thumbs-up shown, second reaction replaced or rejected), while the orchestrator records the connector-side ids, statuses and reasons? [answer: yes (approved by the user, final gate answer 2026-10-27, relayed by the mx-5 leader: '1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go')]
- Q8: S1 runs at smoke time even if the owner DM had an inbound message in the last 24 h; the smoke records the hours since the last inbound, and the over-24h case is confirmed at the first natural opportunity and noted in agents-helmfile MEMORY.md without holding the epic? [answer: yes (approved by the user, final gate answer 2026-10-27, relayed by the mx-5 leader: '1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go')]
- Q9: When a room is bound to a running session (for example one that started the chat there through agents_may_initiate), your answer routes to it even if the room has no preset; a preset is only needed to start a new chat session in an unbound room (reworded 2026-10-27 for the 1:1 rule; was: "When the last speaker in a flagged room is a running session, your answer routes there even if the room has no preset; a preset is only needed to start a new chat session")? [answer: yes, adapted to the 1:1 rule (approved by the user, final gate answer 2026-10-27, relayed by the mx-5 leader: '1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go'; the 1:1 rule wins where it conflicts, so the room's bound session takes the place of the last speaker and the question is reworded)]
- Q10: A room stays bound to its one session until that session is deleted (the connector releases the binding at the room's next message or within about a minute); turning agents_may_initiate off or adding a deny rule does not unbind it, though a deny rule still stops every agent send and inbound message (reworded 2026-10-27 for the 1:1 rule; was: "A session stays bound to a room it posted in; turning agents_may_initiate off does not unbind it; revocation is a deny rule on the room or deleting the session")? [answer: yes, adapted to the 1:1 rule (approved by the user, final gate answer 2026-10-27, relayed by the mx-5 leader: '1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go'; the 1:1 rule wins where it conflicts, so the question is reworded: deleting the session releases the binding)]
- Q11: Under the 1:1 rule a throwaway smoke session is refused room_bound in the owner DM whenever the DM is already bound to its chat session (for example the mx-5 hive leader). Should chat-smoke run S1-S4 from the leader pod of the session the owner DM is bound to (only that pod's own agent credentials; no message to or change of that session, nothing created or deleted), and create a throwaway session that initiates there and is deleted afterwards (releasing the binding) only when the owner DM is unbound? [recommended: yes]
- Q12: Migration 0002 (approved, no down step) also creates room_bindings and backfills one active binding per room from its newest run that has a session, or reserves the room for an in-progress first run without one, so existing chats keep their session; bindings of sessions already deleted are released by the bot's first binding sweep. Approve that backfill as part of migration 0002? [recommended: yes]

## Irreversible operations in scope

Approved at the final gate (2026-10-27): the plugins tag v0.3.0, migration 0002 without a down
step, the new SOPS token and the live applies; standing rule since then: deploy whenever possible
(live applies need no approval).

- Tag `v0.3.0` pushed to any-mcp-tatara-plugins origin on the merge commit of plugins-release-0-3-0
  (orchestrator session, after green CI). Safeguard: approved at the gate; ac on the tag checked
  after the push.
- Live migration 0002 on the agents-matrix-connector database (runs in the connector init container
  on apply): additive (new tables `sends` and `room_bindings`, new columns, widened CHECK, the
  `room_bindings` backfill from existing runs), but the migrator has no down step. Safeguard:
  approved at the gate (the backfill inside it: gate question Q12); migration idempotence,
  constraint, uniqueness and backfill tests in mxc-sends-schema.
- Live applies (orchestrator session, chat-live-smoke): agents-matrix-connector, agents-orchestrator
  (the v0.3.0 plugins ref changes the rendered config hash and rolls every running agent pod,
  including the mx-5 hive), agents-web. Safeguard: approved at the gate and the standing deploy
  rule; `--selector` per release in D18's order; `mise run diff` reviewed before each apply.
- New credential: the chat token generated by `bootstrap-secrets.sh` and committed SOPS-encrypted.
  Safeguard: approved at the gate; never rotates, both files or neither.
- Grant: `agents_may_initiate` set on the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` (Q1).
  While the DM is bound to its chat session the flag lets no other session in (D9).
- Messages sent to the user's Messenger from the owner's Facebook account by the live smoke (S1-S4)
  in the owner DM; a sent Messenger message cannot be unsent by the connector. Under the 1:1 rule
  they are sent with the identity of the DM's bound session when it is bound (Q11).
