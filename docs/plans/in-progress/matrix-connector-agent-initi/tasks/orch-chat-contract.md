---
title: orch chat contract
status: in-progress
repo: agents-orchestrator
value: "the orchestrator's idea of the chat upstream cannot drift from what the connector really serves"
files: [tests/fakes/fake_chat.py, tests/fakes/chat_openapi.json, tests/fakes/chat_openapi.source, tests/test_chat_contract.py]
verify: "uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint"
depends_on: [orch-chat-relay, mxc-agent-routes]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chat contract

## Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D16, verbatim: "Contract: the connector commits its agent listener OpenAPI document (`openapi-agent.json`, pinned like `openapi.json`); the orchestrator vendors it with a source line (`tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`), its fake chat upstream validates against it, and a test asserts every relay route maps to a path and method of the vendored document (my call)."

Retro proposal (generic-any-mcp-with-git-and, cross-session-messaging-and), verbatim: "any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it."

Scope (agents-orchestrator, tests only): vendor `openapi-agent.json` from agents-matrix-connector `main` after mxc-agent-routes merged, as `tests/fakes/chat_openapi.json`, with `tests/fakes/chat_openapi.source` holding `agents-matrix-connector <full sha>`; new `tests/fakes/fake_chat.py` (an ASGI fake of the `/chat/v1` upstream that validates each request body against the vendored request schemas, answers with documented shapes, records calls, and can be told to refuse); new `tests/test_chat_contract.py`.

## Acceptance conditions

- ac1: tests/fakes/chat_openapi.json is byte-identical to openapi-agent.json at the agents-matrix-connector commit named in tests/fakes/chat_openapi.source, which is on that repo's main [evidence: judgement:reviewer runs git show <sha>:openapi-agent.json in agents-matrix-connector and compares it with the vendored file]
- ac2: every orchestrator chat route maps to a path and method of the vendored document [evidence: test:tests/test_chat_contract.py::test_relay_routes_exist_upstream]
- ac3: every success and error answer of the fake validates against the vendored response schemas [evidence: test:tests/test_chat_contract.py::test_fake_chat_matches_vendored_schema]
- ac4: the bodies the relay forwards for rooms, send, reply, react and status validate against the vendored request schemas [evidence: test:tests/test_chat_contract.py::test_relay_requests_match_vendored_schema]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint]

## Files

- `tests/fakes/fake_chat.py`
- `tests/fakes/chat_openapi.json`
- `tests/fakes/chat_openapi.source`
- `tests/test_chat_contract.py`

## Interfaces

- `tests/fakes/fake_chat.py`: `FakeChat(token: str)` with `.app` (ASGI), `.calls` (method, path, headers, body), `.refuse(route, status, code)`; validates against `tests/fakes/chat_openapi.json`.
- `tests/fakes/chat_openapi.source`: one line `agents-matrix-connector <40-hex sha>`.

## Expected outcome

The orchestrator's view of the chat upstream cannot drift from the connector's: the fake is checked against the connector's own committed document, and the relay's requests against the same.

## Steps

- Vendor the document: `git -C <agents-matrix-connector checkout> show origin/main:openapi-agent.json > tests/fakes/chat_openapi.json`, write the source line with that commit.
- Red: write `tests/test_chat_contract.py`; run `uv run --frozen pytest tests/test_chat_contract.py`: fails (no fake).
- Green: write `tests/fakes/fake_chat.py`; run the task's verify: passes. Quote the summary line with counts.

## Notes

- `jsonschema` and `openapi-schema-validator` are already in `uv.lock` (transitive); use one of them if it is importable in the dev environment, else resolve the document's `$ref`s by hand in the fake. A new direct dependency would touch `pyproject.toml` and `uv.lock`, which this task may not: return it as a `discovered` entry.
- ac2 and ac4 run without a database (override `require_agent` as in `tests/test_agent_chat.py`).
- orch-chat-tools-allow reuses `FakeChat` for the plugin parity test.
