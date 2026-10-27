---
title: orch chat contract
status: todo
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
