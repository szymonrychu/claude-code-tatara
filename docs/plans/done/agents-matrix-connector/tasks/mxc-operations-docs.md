---
title: mxc operations docs
status: done
repo: agents-matrix-connector
value: "the operator can create the bot account, connect Facebook and allow a first chat from the README"
files: [README.md, MEMORY.md, AGENTS.md]
verify: "grep -q '^## Operations' README.md && grep -q '^## Security' README.md && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-openapi-and-readme, mxc-service-entrypoints]
model: sonnet
review: ""
verified_head: 645f6d5e23a4bb82358b42ac4d154cc5c5caeed8
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: 1
actual_minutes: 3
actual_tokens: 694036
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 380288, review 313748"
---

# mxc operations docs

## Requirement

Operator documentation and recorded decisions (design D2, D3, D4, D6, revision R1). Paths are in code/agents-matrix-connector.

- `README.md` `## Operations`: the bot identity taken over from Hermes (design R1): Matrix user `@hermes:szymonrichert.pl`, device `hermes-agent`, already logged in to mautrix-meta through `@facebookbot:szymonrichert.pl` with Hermes' Facebook account `61594633049360` (self ghost `@facebook_61594633049360:szymonrichert.pl` in `MATRIX_SELF_IDENTITIES`); the access token comes from Secret `hermes-agent-matrix` (key `MATRIX_ACCESS_TOKEN`, namespace `ai`) into the agents-helmfile SOPS file; Hermes is scaled to 0 in the infrastructure helmfile and must stay at 0 while the connector runs (two clients on one account would both answer); how to hand the identity back (scale the connector to 0, then revert the Hermes scale-down); token rotation (log the device out, log in again as `@hermes`, update Secret `hermes-agent-matrix`, re-run the agents-helmfile bootstrap), what default deny means for a new chat and how to allow it from the Chats page or the API.
- `README.md` `## Security`: default deny, deny wins, display names never grant, bodies of denied rooms are not stored, the untrusted-input prompt preamble, no E2EE (encrypted rooms ignored), the token only as a file in the bot pod.
- `MEMORY.md`: dated 2026-10-25 entries for: bot user with access token instead of an appservice (why), reusing Hermes' Matrix user and Facebook account with Hermes scaled to 0 (why: user decision 2026-10-25, the one allowed chat is Hermes' owner DM and home channel `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`, which exists only for that Facebook login), no E2EE (Hermes runs E2EE off), identifier-only rules with default deny (why not the webhook RE2 engine), one session per room reused while running.
- `AGENTS.md`: the component's commands (`mise run test`, `mise run lint`, Docker for DB tests) and its highest-risk surface (untrusted Messenger input reaching agents; the Matrix access token).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: README has Operations and Security sections naming the bot user, the bridge login and default deny [evidence: command:grep -q '^## Operations' README.md && grep -q '^## Security' README.md && grep -q '@hermes:szymonrichert.pl' README.md && grep -q '@facebookbot:szymonrichert.pl' README.md && grep -qi 'default deny' README.md]
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

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-25 done
