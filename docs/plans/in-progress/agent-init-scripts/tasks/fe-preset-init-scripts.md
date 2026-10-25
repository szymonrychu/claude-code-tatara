---
title: fe preset init scripts
status: in-progress
repo: agent-orchestrator
value: init scripts can be written and edited in the preset form
files: [frontend/src/clusters/clusterSpecForm.ts, frontend/src/presets/PresetForm.tsx, frontend/src/presets/PresetForm.test.tsx]
verify: "cd frontend && npx vitest run src/presets/PresetForm.test.tsx && npm run lint"
depends_on: [init-scripts-spec-field]
owns: []
uses: [orch-cluster-spec-init-scripts]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-init-scripts-fe-preset-init-scripts/agent-orchestrator
branch: agent-init-scripts-fe-preset-init-scripts
verified_head: ""
run: ""
provides: []
---

# fe preset init scripts

## Requirement

Init scripts as preset form fields in the UI (user decisions C1, X2; design D5). Paths are in code/agent-orchestrator/frontend. The generated `src/api/schema.d.ts` already carries `init_scripts` (task init-scripts-spec-field).

- `src/clusters/clusterSpecForm.ts`: form value `initScripts: string[]`, set key `initScripts` (added to `SetKey`); loading a stored spec fills it and marks it set when `init_scripts` is present; validation mirrors the server (at most 20 entries, each non-empty after trim and at most 16384 characters; the error names the script number); the built spec carries `init_scripts` only when the key is set (sparse, like the other fields); clearing every row of a set key sends `[]`.
- `src/presets/PresetForm.tsx`: an "Init scripts" group after the any-mcp config, modelled on the env rows: one multiline monospace TextField per script labelled `Init script <n>`, a remove button `Remove init script <n>`, an `Add init script` button, and helper text "Runs once when a cluster starts, in the shared workdir; agents can read and edit it; edits apply to the next cluster." Theme tokens only, no colour literals (designRules).
- `src/presets/PresetForm.test.tsx`: add, edit, remove, load existing, validation messages, sparse submit body.

Interfaces: `clusterSpecForm.ts` `SetKey` `initScripts`, form value `initScripts`.

Steps: write the PresetForm tests first, see them fail, implement; then `npm run build` and `npm run check:api`.

## Acceptance conditions

- AC1: the preset form adds, edits and removes init script rows and submits them as init_scripts [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "init scripts"]
- AC2: an existing preset's init_scripts load into the rows and a preset without them submits no init_scripts key [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "init scripts sparse"]
- AC3: an empty or oversize script and a 21st script show a validation message naming the script and block Save [evidence: command:cd frontend && npx vitest run src/presets/PresetForm.test.tsx -t "init scripts validation"]
- AC4: lint, typecheck build, design rules and API drift check pass [evidence: command:cd frontend && npm run lint && npm run build && npx vitest run src/layout/designRules.test.ts && npm run check:api]

## Files

- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/presets/PresetForm.test.tsx`

## Interfaces

- `frontend/src/clusters/clusterSpecForm.ts` `SetKey` `initScripts`, form value `initScripts: string[]`, its validation (reused by fe-cluster-init-dialog).

## Expected outcome

The preset form edits init scripts as rows and submits them sparse.

## Steps

- Red: add the PresetForm tests; `cd frontend && npx vitest run src/presets/PresetForm.test.tsx` fails.
- Green: form value, validation, rows; run the verify command, then `npm run build` and `npm run check:api`.

## Notes

- Export the validation helper so the cluster dialog reuses it.
