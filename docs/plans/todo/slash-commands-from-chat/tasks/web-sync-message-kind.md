---
title: web sync message kind
status: todo
repo: agents-web
value: "agents-web's vendored orchestrator API matches the orchestrator that classifies slash messages"
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "npm run check:api && npx tsc -b && npm run lint"
depends_on: [orch-message-kind, orch-render-client-commands]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web sync message kind

## Requirement

Design D12, verbatim (the API part): "A command the orchestrator could not deliver shows in QueueStrip as failed with the wrapper code (D10)." Design D1, verbatim: "The stored text stays raw; `MessageView` gains `kind`." Constraint, verbatim: "Orchestrator route/schema changes regenerate `openapi.json` [...]; agents-web vendors it with `npm run sync:api -- orchestrator`."

Scope (agents-web): run `npm run sync:api -- orchestrator` against the agents-orchestrator commit carrying orch-message-kind and orch-render-client-commands; commit `openapi/orchestrator.json`, `openapi/orchestrator.source` and the generated `src/api/schema.d.ts` (never hand-edited). No UI change: QueueStrip already shows a failed message's `error`.

## Acceptance conditions

- ac1: the vendored spec and the generated types agree [evidence: command:npm run check:api]
- ac2: MessageView in the generated types has kind and wrapper_command_id [evidence: command:grep -q "wrapper_command_id" src/api/schema.d.ts]
- ac3: the source pin names the orchestrator commit with the message kind [evidence: command:grep -q "agents-orchestrator" openapi/orchestrator.source]
- ac4: the app type-checks and lint passes [evidence: command:npx tsc -b && npm run lint]

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
