---
title: web sync session safety api
status: in-progress
repo: agents-web
value: the web client is typed against the API fields that describe backups and queue age
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "npm run check:api && npx tsc -b && npm run lint"
depends_on: [orch-api-session-safety]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 641999
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web sync session safety api

## Requirement

Design D8, user decision verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

Goal G7, verbatim: "The web discard dialog states what history is lost or backed up; the chat shows an agent-unavailable banner with the age of the oldest queued message."

This task is the re-sync: "Re-sync the vendored OpenAPI (npm run sync:api)."

Scope (agents-web): `npm run sync:api -- orchestrator --from <agents-orchestrator integration tree>` after task orch-api-session-safety; commit `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` as generated; no hand edits.

Notes: `npm run check:api` fails on drift in CI. In-progress epic slash-commands-from-chat also re-syncs these files (task web-sync-message-kind): regenerate from the orchestrator tree that carries both epics' changes, never merge the generated files by hand.

## Acceptance conditions

- AC1: the vendored orchestrator OpenAPI and generated types are in sync [evidence: command:npm run check:api]
- AC2: the types carry oldest_queued_at and the backup view [evidence: command:grep -q "oldest_queued_at" src/api/schema.d.ts && grep -q "last_transcripts_backup" src/api/schema.d.ts]
- AC3: the app typechecks [evidence: command:npx tsc -b]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
