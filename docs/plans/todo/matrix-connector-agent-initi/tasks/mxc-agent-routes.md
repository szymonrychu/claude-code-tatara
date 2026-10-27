---
title: mxc agent routes
status: todo
repo: agents-matrix-connector
value: "agents can list their rooms, send, reply, react and read delivery status, refused at once when the room is not theirs"
files: [src/agents_matrix_connector/api/agent.py, src/agents_matrix_connector/db/sends.py, src/agents_matrix_connector/api/openapi.py, openapi-agent.json, README.md, tests/test_api_agent.py, tests/test_readme_api.py]
verify: "uv run pytest tests/test_api_agent.py tests/test_readme_api.py tests/test_agent_gate.py && mise run lint"
depends_on: [mxc-sends-schema, mxc-room-initiate-flag, mxc-agent-listener]
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

# mxc agent routes

## Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji."
- "An agent can list the rooms it may post to and read the delivery status of what it sent."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

README Non-goal, verbatim: "No posting to arbitrary allowed rooms; no raw Matrix event ids from agents."

Design D2, verbatim (the connector side): "the connector's agent listener serves it under `/chat/v1` [...] Every upstream call carries `Authorization: Bearer <ORCH_CHAT_TOKEN>`, `X-Orch-Session: <session uuid>` and `X-Orch-Slug: <slug>`, and never the agent token. Responses: rooms 200 `{"rooms": [{room_id, name, kind, bound, agents_may_initiate}]}`; messages and reactions 202 `{id: "s<n>", status: "queued"}`; status 200 `{id, kind, status, reason, room_id, created_at, sent_at}`. Errors use the shared `{"error": {"code", "message"}}` shape."

Design D4, verbatim: "Session S may post to room R only if both hold (architecture fork 2, pick): (a) `policy.evaluate(room subject R)` is allow, checked when the api accepts the request and again when the bot delivers it; (b) R is bound to S, or `room_settings.agents_may_initiate` is true for R. [...] Room choice for a send: `room` given, that room; `room` omitted and `reply_to` given, the room of the referenced message (my call); both omitted, S's bound room when there is exactly one, else 422 `room_required`. A reaction's room is always its target's room. An unknown room and a room failing (a) answer the same 403 `room_not_allowed` (my call: no probing of room existence); a room passing (a) but failing (b) answers 403 `room_not_authorised`. `GET /chat/v1/rooms` lists exactly the rooms passing (a) and (b) for S, bound rooms first, then by name, then room id (my call: tiebreak pinned by a test). One predicate function serves the route checks and the listing."

Design D5, verbatim: "`text`: 1 to 16000 characters (same bound as `session_send`) [...] `key`: 1 to 16 code points, no whitespace, no control characters and no ASCII characters; else 422 `invalid_key`. [...] Request bodies reject unknown fields (422 `invalid_request`). Check order on the connector, a refusal queues nothing: token (401 `unauthorized`), body validation (422 `invalid_request`, `invalid_key`), reference resolution (422 `bad_reference`), room choice (422 `room_required`), (a) 403 `room_not_allowed`, (b) 403 `room_not_authorised`, rate 429 `rate_limited`."

Design D6, verbatim: "It answers 422 `bad_reference` for an unknown id, an id of another room than the given `room`, an `s<n>` not yet `sent`, and an `s<n>` of another session; replying to a reaction or reacting to a reaction is 422 `bad_reference` too (my call). Raw Matrix event ids are never accepted. `GET /chat/v1/messages/{id}` answers 404 `not_found` for an id that is not one of the caller session's sends."

Design D16, verbatim (contract document): "the connector commits its agent listener OpenAPI document (`openapi-agent.json`, pinned like `openapi.json`)".

Scope (agents-matrix-connector): the four `/chat/v1` routes in `api/agent.py` (`GET /chat/v1/rooms`, `POST /chat/v1/messages` body `{text, room?, reply_to?}`, `POST /chat/v1/reactions` body `{to, key}`, `GET /chat/v1/messages/{id}`), the session from `X-Orch-Session` (a uuid; missing or malformed is 401 `unauthorized`) and `X-Orch-Slug`; any helper queries in `db/sends.py`; `api/openapi.py` exports both documents; committed `openapi-agent.json`; README `## Agent API` section with one `### \`METHOD /chat/v1/...\`` heading per route, every error code and the send statuses and reasons.

## Acceptance conditions

- ac1: a send to a policy-allowed room flagged agents_may_initiate, with no run and no inbound row of that session, answers 202 {id: s<n>, status: queued} and stores a queued sends row with the session, slug, room and text [evidence: test:tests/test_api_agent.py::test_send_to_flagged_room_without_inbound]
- ac2: a room bound by a runs row is accepted unflagged; with room omitted, exactly one bound room is used and zero or several answer 422 room_required; with room omitted and reply_to given the referenced message's room is used [evidence: test:tests/test_api_agent.py::test_room_choice]
- ac3: an unknown room and a policy-denied room answer 403 room_not_allowed, an allowed room neither bound nor flagged answers 403 room_not_authorised, and no refusal stores a row [evidence: test:tests/test_api_agent.py::test_room_refusals_queue_nothing]
- ac4: reply_to m<n> and s<n> store the resolved event id; an unknown id, another room's id, an unsent s<n>, another session's s<n>, a reaction target and a raw event id answer 422 bad_reference [evidence: test:tests/test_api_agent.py::test_reply_references]
- ac5: a reaction takes its target's room, stores kind reaction with the key, and a key with ASCII, whitespace, control characters or more than 16 code points answers 422 invalid_key [evidence: test:tests/test_api_agent.py::test_reactions]
- ac6: after MATRIX_AGENT_RATE_PER_MINUTE sends of one session in 60 s the next answers 429 rate_limited and stores nothing, while another session is unaffected [evidence: test:tests/test_api_agent.py::test_rate_limit]
- ac7: empty or longer than 16000 characters text and unknown body fields answer 422 invalid_request; a missing or malformed X-Orch-Session answers 401 unauthorized [evidence: test:tests/test_api_agent.py::test_validation]
- ac8: GET /chat/v1/rooms lists exactly the rooms a send would be accepted for, bound rooms first, then by name, then room id [evidence: test:tests/test_api_agent.py::test_rooms_listing_order]
- ac9: for a matrix of rooms (allowed or denied, bound or flagged or neither), the listing and the send check agree room by room, because one predicate serves both [evidence: test:tests/test_api_agent.py::test_listing_matches_send_checks]
- ac10: GET /chat/v1/messages/{id} returns the caller session's send with status, reason, room and times, and 404 not_found for another session's or an unknown id [evidence: test:tests/test_api_agent.py::test_status_own_sends_only]
- ac11: the committed openapi-agent.json matches the agent app [evidence: test:tests/test_readme_api.py::test_agent_openapi_committed_matches]
- ac12: README `## Agent API` lists every /chat/v1 route and names every error code, send status and reason [evidence: test:tests/test_readme_api.py::test_readme_lists_every_agent_route]
- ac13: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_agent.py tests/test_readme_api.py tests/test_agent_gate.py && mise run lint]

## Files

- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/api/openapi.py`
- `openapi-agent.json`
- `README.md`
- `tests/test_api_agent.py`
- `tests/test_readme_api.py`

## Interfaces

- `GET /chat/v1/rooms` -> 200 `{"rooms": [{"room_id", "name", "kind", "bound", "agents_may_initiate"}]}`.
- `POST /chat/v1/messages` body `{"text": str, "room": str | null, "reply_to": "m<n>" | "s<n>" | null}` -> 202 `{"id": "s<n>", "status": "queued"}`.
- `POST /chat/v1/reactions` body `{"to": "m<n>" | "s<n>", "key": str}` -> 202 `{"id": "s<n>", "status": "queued"}`.
- `GET /chat/v1/messages/{id}` (`id` is `s<n>`) -> 200 `{"id", "kind", "status", "reason", "room_id", "created_at", "sent_at"}`.
- Errors `{"error": {"code", "message"}}`: 401 `unauthorized`, 404 `not_found`, 422 `invalid_request`, `invalid_key`, `bad_reference`, `room_required`, 403 `room_not_allowed`, `room_not_authorised`, 429 `rate_limited`, 503 `unavailable` (database).
- One predicate, for example `api/agent.py:may_post(conn, session_id, room, rules, settings) -> Literal["ok", "room_not_allowed", "room_not_authorised"]`, used by the send and reaction routes and by the listing.
- `api/openapi.py`: `export()` (UI, unchanged) and `export_agent()`; `python -m agents_matrix_connector.api.openapi --agent > openapi-agent.json` (or an equivalent documented command).

## Expected outcome

The orchestrator can ask the connector, on the session's behalf, which rooms it may post to, queue a message, a quoted reply or a reaction there, and read back what happened, with every refusal synchronous and nothing queued on a refusal.

## Steps

- Red: write `tests/test_api_agent.py` and the two README/OpenAPI tests; run `uv run pytest tests/test_api_agent.py tests/test_readme_api.py`: the new tests fail.
- Green: routes, predicate, any repository helpers, OpenAPI export and README; regenerate both documents; run the task's verify: passes. Quote the summary line with counts.

## Notes

- The policy subject is `api/rooms.py:_room_subject`; evaluate with `rules.list_rules` and `settings.default_policy`, as the rooms route does. Import it rather than copying it.
- The room ordering rule is a tiebreak ruling: its pin test is `test_rooms_listing_order` (retro proposal). The single-predicate rule is pinned by `test_listing_matches_send_checks` (retro proposal: duplicate-predicate sweep before the last code task merges).
- The api only inserts `sends`; it never updates them (single writer, D7).
- `tests/test_api_agent.py` is DB-backed (CI); keep the key validator and the reference parser as pure functions with non-DB tests in it too.
- The rate limit is advisory like the orchestrator's session-message limits: the count and the insert are not one atomic step; document that in README.
