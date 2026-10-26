---
title: live reply proof
status: todo
repo: agents-helmfile
value: "proves G1 live: an allowed Messenger message gets the agent's reply"
files: [MEMORY.md]
verify: mise run diff
depends_on: [apply-smoke-matrix]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 668998
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# live reply proof

## Requirement

Live proof of goal G1 (scope audit 2026-10-26): "a Messenger message to the connected Facebook account in an allowed chat gets the agent's reply in the same chat". Read-only; no file changes.

Precondition: the connector's default preset is set (user chose 'Default', 00000000-0000-0000-0000-000000000001, set 2026-10-26) and the user has sent one new Messenger message in the allowed owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` after that. Otherwise end `blocked`, whoCanClear "user: send one Messenger message in the owner DM".

- Through the smoke's 127.0.0.1 port-forward to the api (port 8000): `GET /matrix/api/v1/rooms/{room_id}/messages` shows the new inbound message dispatched (not ignored) with a session, and an outbound reply; `GET /matrix/api/v1/rooms/{room_id}` shows the session.
- Read-only bot log tail shows the dispatch and the reply send, with no token in the output.
- Quote the evidence (statuses, session id, event ids; no message bodies) in /Users/szymonri/Documents/claude-code-tatara/.scratchpad/agents-matrix-connector/g1-proof.md.
- Never send a Matrix message, never change rules or settings, never apply.

## Acceptance conditions

- AC1: a new inbound message in the allowed owner DM was dispatched to a session and the agent's reply was posted back in the same room [evidence: judgement:the /rooms/{id}/messages and /rooms/{id} output quoted in g1-proof.md]
- AC2: the bot log shows the dispatch and reply without the token [evidence: judgement:the sanitized log excerpt in g1-proof.md]

## Files

- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
