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

- `components['schemas']['MessageView']` gains `kind: 'turn' | 'command'` and `wrapper_command_id: string | null`; `wrapper.agent_commands` becomes `string[]`.

## Expected outcome

agents-web's vendored orchestrator API matches the orchestrator of this epic.

## Steps

- Run `npm run sync:api -- orchestrator` (reads ../agents-orchestrator at the epic's integration commit); run the task's verify: passes.

## Notes

- Generated files only: the TDD exception for a generated-code sync with no behaviour change applies; `npm run check:api` is the guard.
- `src/sessions/sessionSpecForm.ts` and `PresetForm.tsx` keep compiling with `agent_commands: string[]` (noted, not doing now: free-form agent command input in PresetForm).
- The sibling epic file-download-in-file-browse re-vendors the same files (task web-sync-orchestrator-api); whichever lands second re-runs the sync (design Assumptions).
- Depends on orch-message-kind and orch-render-client-commands.
