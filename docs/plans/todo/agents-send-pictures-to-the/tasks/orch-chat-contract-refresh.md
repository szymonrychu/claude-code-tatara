---
title: orch chat contract refresh
status: todo
repo: agents-orchestrator
value: "the orchestrator's chat upstream fake matches the connector that serves pictures"
files: [tests/fakes/chat_openapi.json, tests/fakes/chat_openapi.source, tests/fakes/fake_chat.py, tests/test_chat_contract.py]
verify: "uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint"
depends_on: [mxc-images-route]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chat contract refresh

## Requirement

Design D9, verbatim: "Refresh the vendored contract `tests/fakes/chat_openapi.*` from connector main (already stale) with the new route."

Delta fix-as-ac, verbatim: "Refresh tests/fakes/chat_openapi.json from connector main (already stale)."

Design D2, verbatim: "Then POST JSON `{data: base64, path, caption?, room?, reply_to?}` to `{ORCH_CHAT_URL}/chat/v1/images`; status and body pass through unchanged (D2 of the merged epic)."

Scope (agents-orchestrator, tests only):
- `tests/fakes/chat_openapi.json`: byte for byte the connector's `openapi-agent.json` at the commit `tests/fakes/chat_openapi.source` names; that commit carries `POST /chat/v1/images` (mxc-images-route): connector `main` once the connector PR merged, else the connector epic-branch commit, kept reachable by a merge commit (my call, the matrix epic's precedent: web `openapi/matrix.source` pinned 23f0424).
- `tests/fakes/chat_openapi.source`: `agents-matrix-connector <full sha>`.
- `tests/fakes/fake_chat.py`: `FakeChat` answers `POST /chat/v1/images` per the vendored schema (202 `{id, status, path}`, the documented refusals through `refuse`) and records the call.
- `tests/test_chat_contract.py`: a test for the new fake route; the existing contract tests keep passing against the refreshed document. The relay still serves four routes in this task (orch-chat-images-route adds the fifth).

## Acceptance conditions

- ac1: the source line names the full sha of a connector commit that serves POST /chat/v1/images, and the vendored document equals that commit's openapi-agent.json byte for byte [evidence: command:sha=$(awk '{print $2}' tests/fakes/chat_openapi.source) && git -C ../agents-matrix-connector cat-file -e "$sha" && git -C ../agents-matrix-connector show "$sha:openapi-agent.json" | cmp -s - tests/fakes/chat_openapi.json && grep -q '"/chat/v1/images"' tests/fakes/chat_openapi.json]
- ac2: FakeChat answers POST /chat/v1/images with a 202 body valid under the vendored schema, refuses on request with a documented status, and records the call [evidence: test:tests/test_chat_contract.py::test_fake_chat_images_route]
- ac3: the existing contract tests pass against the refreshed document [evidence: test:tests/test_chat_contract.py::test_fake_chat_matches_vendored_schema]
- ac4: the contract and chat tests and lint pass (no database) [evidence: command:uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint]

## Files

- `tests/fakes/chat_openapi.json`
- `tests/fakes/chat_openapi.source`
- `tests/fakes/fake_chat.py`
- `tests/test_chat_contract.py`

## Interfaces

- `tests/fakes/fake_chat.FakeChat`: route `("POST", "/chat/v1/images")`, answers `{id: "s<n>", status: "queued", path}`; `refuse("/images", status, code)` as for the other routes.

## Expected outcome

The orchestrator's contract fake of the chat upstream matches the connector that serves pictures, so the relay tests of orch-chat-images-route test against the real contract (design D16 of the matrix epic).

## Steps

- Read `tests/fakes/fake_chat.py`, `tests/test_chat_contract.py` and the connector's `openapi-agent.json` at the commit carrying mxc-images-route.
- Red: `test_fake_chat_images_route`; run `uv run --frozen pytest tests/test_chat_contract.py`: fails (no route in the document or fake).
- Green: copy the document, update the source line, teach FakeChat the route; run the task's verify: passes. Quote the summary line.

## Notes

- The vendored document has been stale since 0380120 (connector openapi-agent.json gained 400 responses); the refresh may surface such differences in `test_fake_chat_matches_vendored_schema` and the fake's refusals: fix the fake, never the document.
- In the integration worktree layout the connector tree is the sibling `../agents-matrix-connector`; fetch the pinned commit there first.
- (my call, builder-check Q1) The connector tasks merge to connector `main` first; this task starts after that and pins the connector `main` sha, so the epic-branch fallback in Scope is not used.
