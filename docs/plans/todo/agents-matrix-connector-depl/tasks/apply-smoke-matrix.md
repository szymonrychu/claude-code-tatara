---
title: apply smoke matrix
status: todo
repo: agents-helmfile
value: the connector and the Chats page are live and proven by the smoke
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [helmfile-matrix-secrets, helmfile-matrix-releases, helmfile-web-chats-entry, smoke-matrix-check]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# apply smoke matrix

## Requirement

Apply to the live `agents` namespace and prove it (design D13; live-deploy rule: the orchestrator runs live applies itself, never a subagent). Paths are in code/agents-helmfile.

- Implementer, before the apply: `mise run diff`; keep its output in the task notes. Expected: new releases `agents-matrix-connector-db` and `agents-matrix-connector`; the agents-orchestrator token-hash addition; agents-web version, image tag and the matrix backend. Anything else stops the task `blocked` with the diff, whoCanClear "user". Then end the implementer round with "ready for apply".
- Orchestrator (main session, never a subagent): `mise run apply` in code/agents-helmfile (lint, test and the kube-context guard run first; never bypass the guard); a failing apply is not retried blindly: read the helm error and report its tail.
- After the apply, implementer: `mise run diff` again (no drift) and `mise run smoke` (exit 0, including the connector checks); read-only `kubectl -n agents logs deploy/agents-matrix-connector-bot --tail=50` shows the first sync and no token in the output; `MEMORY.md`: a dated line: applied agents-matrix-connector `0.1.0-main.<sha7>` with its CNPG database as `@agents:szymonrichert.pl`, agents-web `0.1.0-main.<sha7>` with Chats; default deny; smoke green (quote its last log line).
- No other file changes.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile after the apply [evidence: command:mise run diff]
- AC2: the smoke passes, including the connector checks [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied versions and the smoke result [evidence: command:grep -q "agents-matrix-connector" MEMORY.md && grep -q "smoke" MEMORY.md]
- AC4: the pre-apply diff showed only the expected changes and the bot log shows a sync without the token [evidence: judgement:the diff output and the log tail quoted in the task notes]

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
