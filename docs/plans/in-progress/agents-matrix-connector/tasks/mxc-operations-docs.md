---
title: mxc operations docs
status: in-progress
repo: agents-matrix-connector
value: "the operator can create the bot account, connect Facebook and allow a first chat from the README"
files: [README.md, MEMORY.md, AGENTS.md]
verify: "grep -q '^## Operations' README.md && grep -q '^## Security' README.md && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-openapi-and-readme, mxc-service-entrypoints]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc operations docs

## Requirement

Operator documentation and recorded decisions (design D2, D3, D4, D6; the user-run steps U1-U4). Paths are in code/agents-matrix-connector.

- `README.md` `## Operations`: the four user-run steps of design.md (create `@agents:szymonrichert.pl`, log in once with `device_id` `agents-matrix-connector` and keep only the access token, log the account in to mautrix-meta through `@facebookbot:szymonrichert.pl` with the dedicated Facebook account, grant bridge permission if refused), how to find the bot's own ghost id for `MATRIX_SELF_IDENTITIES`, token rotation (log the device out, log in again, re-run the agents-helmfile bootstrap), what default deny means for a new chat and how to allow it from the Chats page or the API.
- `README.md` `## Security`: default deny, deny wins, display names never grant, bodies of denied rooms are not stored, the untrusted-input prompt preamble, no E2EE (encrypted rooms ignored), the token only as a file in the bot pod.
- `MEMORY.md`: dated 2026-10-25 entries for: bot user with access token instead of an appservice (why), a dedicated Facebook account (why), no E2EE (Hermes runs E2EE off), identifier-only rules with default deny (why not the webhook RE2 engine), one session per room reused while running.
- `AGENTS.md`: the component's commands (`mise run test`, `mise run lint`, Docker for DB tests) and its highest-risk surface (untrusted Messenger input reaching agents; the Matrix access token).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: README has Operations and Security sections naming the bot user, the bridge login and default deny [evidence: command:grep -q '^## Operations' README.md && grep -q '^## Security' README.md && grep -q '@agents:szymonrichert.pl' README.md && grep -q '@facebookbot:szymonrichert.pl' README.md && grep -qi 'default deny' README.md]
- AC2: MEMORY records the dated design decisions [evidence: command:grep -q '2026-10-25' MEMORY.md && grep -qi 'appservice' MEMORY.md && grep -qi 'E2EE' MEMORY.md]
- AC3: AGENTS.md names the commands and the highest-risk surface [evidence: command:grep -q 'mise run test' AGENTS.md && grep -qi 'access token' AGENTS.md]

## Files

- `README.md`
- `MEMORY.md`
- `AGENTS.md`

## Interfaces

- README `## Operations` is what the orchestrator hands the user for U1-U4.

## Expected outcome

An operator can create the bot account, connect Facebook and allow a first chat from the README alone.

## Steps

- Doc-only task (TDD exception: a doc edit). Write the sections; run the verify.

## Notes

- Never put a real token, password or cookie in docs; use placeholders.
