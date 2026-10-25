---
title: fe cluster init dialog
status: done
repo: agent-orchestrator
value: a person sees how a running cluster was initialised and can edit its scripts for the next cluster
files: [frontend/src/clusters/InitScriptsDialog.tsx, frontend/src/clusters/InitScriptsDialog.test.tsx, frontend/src/layout/TopBar.tsx, frontend/src/layout/TopBar.test.tsx, frontend/src/App.tsx, frontend/src/api/client.ts]
verify: "cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx src/layout/TopBar.test.tsx && npm run lint"
depends_on: [init-scripts-public-api, fe-preset-init-scripts]
owns: []
uses: [orch-cluster-init-scripts-api]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-init-scripts-fe-cluster-init-dialog/agent-orchestrator
branch: agent-init-scripts-fe-cluster-init-dialog
verified_head: ec7dd9a246cbbb48a196977ad22b94200661ff87
run: agent-init-scripts
provides: []
acs_for_audit: []
process_gaps: []
fork_point: a38fbb6
---

# fe cluster init dialog

## Requirement

A cluster-level "Init scripts" dialog in the UI: see how the cluster was initialised and edit the scripts for the next cluster (user decisions C2, C3, X2; design D5). Paths are in code/agent-orchestrator/frontend. Reads and writes only the public routes from task init-scripts-public-api (`GET|PUT /api/v1/clusters/{id}/init-scripts`); the generated schema already has `InitScriptsView`.

- `src/api/client.ts`: `getInitScripts(clusterId)` and `putInitScripts(clusterId, scripts)` typed from the schema, using the existing request helper and error type.
- `src/clusters/InitScriptsDialog.tsx`: opened with a ClusterView; loads the view; shows the run state (`skipped`, `running`, `succeeded`, `failed` with exit code or reason), started and finished times, the log tail in a monospace scroll box, `script_path`, and a note when `edited_since_run`; edits the scripts with the same row editor behaviour and validation as the preset form (reuse the validation from `clusterSpecForm.ts`, do not duplicate it); Save PUTs and then shows "Saved. Applies to the next cluster" plus "Preset <name> updated" when `preset_updated`; server errors show in an Alert. Theme tokens only.
- `src/layout/TopBar.tsx`: the cluster actions menu gains an `Init scripts` item before `Discard`, calling a new `onInitScripts(cluster)` prop; `src/App.tsx` holds the open-dialog state and renders the dialog like `DiscardClusterDialog`.
- Tests: `src/clusters/InitScriptsDialog.test.tsx` (each state rendered, edit and save body, preset_updated message, error Alert) and `src/layout/TopBar.test.tsx` (menu item calls the prop).

Interfaces: `client.ts::getInitScripts`, `client.ts::putInitScripts`, `TopBarProps.onInitScripts`.

Steps: write both tests first, see them fail, implement; then `npm run build`.

## Acceptance conditions

- AC1: the dialog renders skipped, running, succeeded and failed states with exit code, log tail, script path and the edited-since-run note [evidence: command:cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx -t "states"]
- AC2: saving PUTs the edited scripts and shows the next-cluster and preset-updated messages; a server error shows an Alert [evidence: command:cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx -t "save"]
- AC3: the TopBar cluster menu has Init scripts before Discard and it calls onInitScripts with the cluster [evidence: command:cd frontend && npx vitest run src/layout/TopBar.test.tsx -t "init scripts"]
- AC4: lint, typecheck build and design rules pass [evidence: command:cd frontend && npm run lint && npm run build && npx vitest run src/layout/designRules.test.ts]

## Files

- `frontend/src/clusters/InitScriptsDialog.tsx`
- `frontend/src/clusters/InitScriptsDialog.test.tsx`
- `frontend/src/layout/TopBar.tsx`
- `frontend/src/layout/TopBar.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`

## Interfaces

- `frontend/src/api/client.ts::getInitScripts`, `putInitScripts`; `TopBarProps.onInitScripts`; `InitScriptsDialog`.

## Expected outcome

The cluster menu opens an Init scripts dialog that shows the run and saves edited scripts for the next cluster.

## Steps

- Red: write `InitScriptsDialog.test.tsx` and the TopBar test; `cd frontend && npx vitest run src/clusters/InitScriptsDialog.test.tsx src/layout/TopBar.test.tsx` fails.
- Green: client functions, dialog, menu item, App wiring; run the verify command, then `npm run build`.

## Notes

- Mirror `DiscardClusterDialog` for open state in `App.tsx`.
