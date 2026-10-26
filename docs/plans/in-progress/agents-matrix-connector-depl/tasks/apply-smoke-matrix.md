---
title: apply smoke matrix
status: done
repo: agents-helmfile
value: the connector and the Chats page are live and proven by the smoke
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [helmfile-matrix-secrets, helmfile-matrix-releases, helmfile-web-chats-entry, smoke-matrix-check]
model: sonnet
review: ""
verified_head: 8bce546bf6fe3f4e1e9f196cb56676d967c31b9c
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: 1
actual_minutes: 26
actual_tokens: 985030
actual_roles: "impl 19, review 6"
actual_role_tokens: "impl 919075, review 65955"
---

# apply smoke matrix

## Requirement

Apply to the live `agents` namespace and prove it (design D13; live-deploy rule: the orchestrator runs live applies itself, never a subagent). Paths are in code/agents-helmfile.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: new releases `agents-matrix-connector-db` and `agents-matrix-connector`; the agents-orchestrator token-hash addition; agents-web version, image tag and the matrix backend. Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator (main session, never a subagent): `mise run apply` in code/agents-helmfile (lint, test and the kube-context guard run first; never bypass the guard); a failing apply is not retried blindly: read the helm error and report its tail.
- After the apply, implementer: `mise run diff` again (no drift) and `mise run smoke` (exit 0, including the connector checks); read-only `kubectl -n agents logs deploy/agents-matrix-connector-bot --tail=50` shows the first sync and no token in the output; `MEMORY.md`: a dated line: applied agents-matrix-connector `0.1.0-main.<sha7>` with its CNPG database as `@hermes:szymonrichert.pl` (Hermes at 0 replicas), agents-web `0.1.0-main.<sha7>` with Chats; default deny; smoke green (quote its last log line).
- After the smoke, implementer: create the one allow rule the user asked for (2026-10-25, verbatim: 'Whitelist only 1 channel for now- the one where Hermess sends "Hermess is shutting down..." messages (Szymon Richert to Szymon Richert)'; that is Hermes' home channel, the owner DM portal `!iLWrAwaTMYnINJsyNv:szymonrichert.pl`): `POST /matrix/api/v1/rules` with `{"list": "allow", "kind": "room", "value": "!iLWrAwaTMYnINJsyNv:szymonrichert.pl", "note": "owner DM, Hermes home channel"}` through the port-forward the smoke uses (bypassing the SSO sidecar); then `GET /matrix/api/v1/rules` lists exactly that allow rule and no deny rule, and `GET /matrix/api/v1/rooms/{room_id}` for it shows the decision allowed (a 404 because the room is not yet discovered stops the task `blocked` with the `/rooms` listing, whoCanClear "orchestrator"). The default policy stays deny.
- Last, once the allow rule is in place and the smoke is green: send the user one Messenger message, a short joke chosen then, into `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` as the bot (user request 2026-10-25, verbatim: 'Once it's deployed, ping me with a message (a joke, don't tell me now).'). Send it through the bot's own Matrix client in the bot pod (for example a one-off `kubectl exec` running the connector's MatrixClient with the mounted token file), never printing the token; quote the returned event id in the task notes. This is the only Matrix message the deploy sends.
- No other file changes.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the connector checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q "agents-matrix-connector" MEMORY.md && grep -q "smoke" MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes and the bot log shows a sync without the token [evidence: judgement:the diff output and the log tail quoted in the task notes]
- AC5: the only access rule is the allow rule for `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` and that room's decision is allowed [evidence: judgement:the GET /rules and GET /rooms/{room_id} output quoted in the task notes]
- AC6: the joke message was sent once to the allowed room and its event id is recorded [evidence: judgement:the event id quoted in the task notes]

## Files

- `MEMORY.md`

## Interfaces

- The live releases; nothing new.

## Expected outcome

The connector runs in namespace `agents`, logged in and syncing; the Chats page is live; the smoke is green. A first Messenger chat then shows up in Chats as default-deny until the user allows it.

## Steps

- `mise run diff` (expected changes only), "ready for apply"; orchestrator applies; `mise run diff` (no drift); `mise run smoke` (exit 0); MEMORY line.

## Notes

- Same shape as agents-webhook-microservice task apply-smoke-webhook. Deploy tasks never use apply as AC evidence.

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed

- 2026-10-25 amended: user 2026-10-25: once deployed, ping the user with a joke message

- 2026-10-26 done
