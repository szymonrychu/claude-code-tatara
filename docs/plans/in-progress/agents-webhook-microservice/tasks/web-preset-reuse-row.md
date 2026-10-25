---
title: web preset reuse row
status: todo
repo: agents-web
value: agent reuse is switched on or off when creating or editing a preset in the UI
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts, src/clusters/clusterSpecForm.ts, src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/presets src/clusters && npm run check:api && npm run lint"
depends_on: [orch-preset-reuse-field]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 13
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web preset reuse row

## Requirement

The agent reuse switch in the preset form (design D17; user clarification 2026-10-25: "(agent reuse is an optional feature, it can be set during preset creation)"; contract `agents-web-openapi-vendor`). Paths are in code/agents-web.

- `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`: re-vendored with `npm run sync:api -- orchestrator` from this epic's agent-orchestrator checkout (`../agent-orchestrator`) after task orch-preset-reuse-field.
- `src/clusters/clusterSpecForm.ts`: a `reuseRunningAgent` value and `SetKey`, sparse like the other optional keys: written to `spec.reuse_running_agent` only when set, read back from a preset's spec.
- `src/presets/PresetForm.tsx`: a switch row "Reuse running agent" with help text "Webhook and schedule events for the same item go to the agent still running for it instead of starting a new one"; default off; shown in the preset form only.
- `src/presets/PresetForm.test.tsx`: the row renders off by default; turning it on saves `reuse_running_agent: true`; a preset with it set loads on; leaving it untouched keeps the spec sparse (no key).

## Acceptance conditions

- AC1: the preset form saves, loads and omits reuse_running_agent sparsely [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t reuse]
- AC2: the vendored orchestrator schema matches the generated types [evidence: command:npm run check:api]
- AC3: the existing preset and cluster form tests pass [evidence: command:npx vitest run src/presets src/clusters]
- AC4: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/clusters/clusterSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
