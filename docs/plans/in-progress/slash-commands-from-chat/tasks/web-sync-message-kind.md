---
title: web sync message kind
status: done
repo: agents-web
value: "agents-web's vendored orchestrator API matches the orchestrator that classifies slash messages"
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts]
verify: "npm run check:api && npx tsc -b && npm run lint"
depends_on: [orch-message-kind, orch-render-client-commands]
model: sonnet
review: ""
verified_head: e533228523871c9b393e48a177f892989b9b64f6
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: 1
actual_minutes: 11
actual_tokens: 269242
actual_roles: "impl 7, review 4"
actual_role_tokens: "impl 151364, review 117878"
---

# web sync message kind

## Requirement

Design D12, verbatim (the API part): "A command the orchestrator could not deliver shows in QueueStrip as failed with the wrapper code (D10)." Design D1, verbatim: "The stored text stays raw (agents-common adopts an existing message by `marker in m.text`, `runs.py:_post_once`); `MessageView` gains `kind`." Constraint, verbatim: "Orchestrator route/schema changes regenerate `openapi.json` [...]; agents-web vendors it with `npm run sync:api -- orchestrator`."

Interrogate item 13 (interrogate.md), verbatim: "AC evidence that already passes today (A): orch-dispatch-commands ac10 grep matches MEMORY.md:41; web-sync-message-kind ac3 grep matches the current source pin. Replace with assertions specific to the new state."

Scope (agents-web): run `npm run sync:api -- orchestrator` against the agents-orchestrator commit carrying orch-message-kind and orch-render-client-commands; commit `openapi/orchestrator.json`, `openapi/orchestrator.source` and the generated `src/api/schema.d.ts` (never hand-edited). No UI change: QueueStrip already shows a failed message's `error`.

## Acceptance conditions

- ac1: the vendored spec and the generated types agree [evidence: command:npm run check:api]
- ac2: MessageView in the vendored spec and the generated types has kind and wrapper_command_id [evidence: command:grep -q "wrapper_command_id" openapi/orchestrator.json && grep -q "wrapper_command_id" src/api/schema.d.ts]
- ac3: the source pin names an agents-orchestrator commit whose openapi.json carries the message kind (the current pin does not) [evidence: command:git -C ../agents-orchestrator show "$(awk '{print $2}' openapi/orchestrator.source):openapi.json" | grep -q "wrapper_command_id"]
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

- 2026-10-27 amended: interrogate item 13 (ac3 evidence replaced: the pinned orchestrator commit's openapi.json must carry wrapper_command_id)

- 2026-10-29 done
