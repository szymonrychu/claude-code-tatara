---
title: orch chat relay
status: todo
repo: agents-orchestrator
value: "session leaders reach the chat through the orchestrator, which proves who calls and keeps the agent token to itself"
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/api/chat.py, src/agents_orchestrator/api/app.py, README.md, openapi.json, MEMORY.md, tests/test_agent_chat.py, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint"
depends_on: []
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

# orch chat relay

## Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "An agent can list the rooms it may post to and read the delivery status of what it sent."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

README Non-goals, verbatim: "No member-agent (non-leader) chat tools; members report through their leader." and "No other chat channels (Slack, Telegram); one upstream only."

Design D2, verbatim: "The orchestrator stays free of Matrix concepts: it calls a generic chat upstream at `ORCH_CHAT_URL` and the connector's agent listener serves it under `/chat/v1` [...] Every upstream call carries `Authorization: Bearer <ORCH_CHAT_TOKEN>`, `X-Orch-Session: <session uuid>` and `X-Orch-Slug: <slug>`, and never the agent token. [...] The orchestrator passes the upstream status and JSON body through unchanged, and answers 503 `chat_unavailable` on a connection error, timeout or a non-JSON upstream answer. There is one upstream: no multi-channel registry (YAGNI)."

The D2 route table: `GET /agent/v1/chat/rooms` to `GET {ORCH_CHAT_URL}/chat/v1/rooms`; `POST /agent/v1/chat/messages` body `{text, room?, reply_to?}` to `POST {ORCH_CHAT_URL}/chat/v1/messages`; `POST /agent/v1/chat/reactions` body `{to, key}` to `POST {ORCH_CHAT_URL}/chat/v1/reactions`; `GET /agent/v1/chat/messages/{id}` to `GET {ORCH_CHAT_URL}/chat/v1/messages/{id}`.

Design D12, verbatim: "`api/chat.py` (new router, agent port only): every route runs `require_agent`, then `_leads` (403 `not_leader`), then requires chat configured (503 `chat_unconfigured`), then forwards (D2). Settings `ORCH_CHAT_URL` (http or https URL) and `ORCH_CHAT_TOKEN` (secret, never in repr or logs): both set or both empty, else a settings error naming both (my call). Nothing is stored."

Design D5, verbatim (orchestrator caps): "The orchestrator caps the forwarded request body at 32 KiB (413 `payload_too_large`) and the upstream call at 10 s."

Scope (agents-orchestrator): `settings.py` (`chat_url`, `chat_token`), new `api/chat.py`, `api/app.py` (include the router), README (Configuration rows; `## Agent API` gets a `### Chat` section with one `#### `METHOD /agent/v1/chat/...`` heading per route, the checks in order and the pass-through rule), committed `openapi.json`, `MEMORY.md` (dated entry: the chat upstream relay and why the orchestrator names it chat, not matrix). The chart, the plugin tools and the allow list are later tasks.

## Acceptance conditions

- ac1: ORCH_CHAT_URL and ORCH_CHAT_TOKEN default empty, the URL must be http or https, one set without the other is a settings error naming both, and the token never appears in repr [evidence: test:tests/test_settings.py::test_chat_settings]
- ac2: the README Configuration section names every ORCH_ variable, the two new ones included [evidence: test:tests/test_settings.py::test_env_names_documented_in_readme]
- ac3: each chat route forwards its method, path, query and body to ORCH_CHAT_URL/chat/v1 with the chat bearer, X-Orch-Session and X-Orch-Slug of the caller, and the forwarded request carries neither the agent token nor any other inbound header [evidence: test:tests/test_agent_chat.py::test_forwards_with_chat_token_never_agent_token]
- ac4: the upstream status and JSON body (202, 403 room_not_allowed, 422 bad_reference, 429 rate_limited) reach the agent unchanged [evidence: test:tests/test_agent_chat.py::test_upstream_status_and_body_pass_through]
- ac5: a connection error, a timeout and a non-JSON upstream answer give 503 chat_unavailable without echoing the upstream text [evidence: test:tests/test_agent_chat.py::test_upstream_failure_is_chat_unavailable]
- ac6: with chat unconfigured every chat route answers 503 chat_unconfigured and makes no upstream call [evidence: test:tests/test_agent_chat.py::test_unconfigured]
- ac7: a request body over 32 KiB answers 413 payload_too_large and makes no upstream call [evidence: test:tests/test_agent_chat.py::test_body_cap]
- ac8: a non-leader member gets 403 not_leader, a bad token 401 and a foreign peer IP 403, and none of them reaches the upstream [evidence: test:tests/test_agent_chat.py::test_leader_only_and_identity]
- ac9: the chat routes are served only on the agent port; the main and service ports answer 404 or 403 for them [evidence: test:tests/test_agent_chat.py::test_chat_routes_only_on_agent_port]
- ac10: the README documents every chat route and the committed openapi.json matches the app [evidence: command:uv run --frozen pytest tests/test_readme_api.py::test_every_route_documented tests/test_readme_api.py::test_openapi_json_matches_app]
- ac11: MEMORY.md records the chat upstream relay decision, dated [evidence: command:grep -qi "chat upstream" MEMORY.md]
- ac12: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_agent_chat.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/api/chat.py`
- `src/agents_orchestrator/api/app.py`
- `README.md`
- `openapi.json`
- `MEMORY.md`
- `tests/test_agent_chat.py`
- `tests/test_settings.py`

## Interfaces

- `settings.py:Settings.chat_url: str = ""`, `chat_token: str = Field(default="", repr=False)`; a validator for both-or-neither and the URL scheme.
- `api/chat.py` (new): `router = APIRouter(prefix="/agent/v1/chat", tags=["agent"])` with `GET /rooms`, `POST /messages`, `POST /reactions`, `GET /messages/{send_id}`; one `httpx.AsyncClient` (timeout 10 s) owned by the app lifespan or created per app; a `forward(method, path, body, session, slug)` helper.
- Agent-facing errors added: 403 `not_leader`, 503 `chat_unconfigured`, 503 `chat_unavailable`, 413 `payload_too_large`; everything else is the upstream's.

## Expected outcome

A session leader can call four chat routes on the orchestrator agent port; the orchestrator proves who is calling and relays to the chat upstream with its own token, storing nothing.

## Steps

- Red: write `tests/test_agent_chat.py` (non-DB cases with `require_agent` overridden and an `httpx.MockTransport` upstream; DB cases for identity and leadership like `tests/test_agent_session_messaging.py`), add `test_chat_settings`; run `uv run --frozen pytest tests/test_agent_chat.py tests/test_settings.py`: the new tests fail.
- Green: settings, router, app wiring, README, `openapi.json` (`uv run python -m agents_orchestrator.api.openapi > openapi.json`), MEMORY; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Reuse `api/agent.py:require_agent` and `_leads` (import them; do not copy). Leader check exactly as `session_send`.
- No Docker in agent pods: the DB-backed cases (ac8) run in CI; ac3-ac7 and ac9 must be non-DB so the local verify has signal (retro proposal).
- Build fake tokens at runtime in tests (retro proposal, GitGuardian).
- Never log the chat token, the agent token or the upstream body; log method, path, status only.
- `X-Orch-Slug` is the caller session's slug from the sessions repo, never from the request.
