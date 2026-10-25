---
title: web backend menu
status: todo
repo: agents-web
value: "later services add UI entries by registering them, shown only when configured"
files: [src/backends/registry.ts, src/backends/registry.test.ts, src/App.tsx, src/App.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-runtime-config]
owns: [backend-registry]
uses: [backends-config]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# web backend menu

## Requirement

Settings-menu entries come from a backend registry and appear only for configured backends (design D3). Paths are in code/agents-web.

- `src/backends/registry.ts`: `MenuEntry {id, label, order, backend, render(onBack): ReactNode}`; `BACKEND_MENUS: Record<string, MenuEntry[]>` keyed by backend id; `menuEntries(config: RuntimeConfig): MenuEntry[]` returns the entries of the configured backends sorted by `order`, then `label`; a configured id with no registered entries is skipped with one `console.warn` naming it.
- The orchestrator registers every settings entry the UI has at move time (Presets, `order` 30, and any entry agent-init-scripts or cluster-scaling added). Reserved order slots, documented in the file header: 10 Clusters (configuration-improvements), 20 Webhooks (agents-webhook-microservice), 30 Presets, 40 Schedules (agents-schedule-microservice).
- `src/App.tsx`: `settingsCategories` for `TopBar` are built from `menuEntries(current config)`; the main area shows the selected cluster or the selected entry's `render(() => back to cluster)`. With the default config the UI behaves as before: the Presets entry opens `PresetsPage`.
- `src/App.test.tsx`: with the default config Presets is listed and opens the presets page; a test-registered entry of a second backend is shown only when that backend is in the config.

## Acceptance conditions

- AC1: menuEntries filters by configured backends, orders by order then label and warns once for an unregistered id [evidence: command:npx vitest run src/backends/registry.test.ts]
- AC2: App lists Presets with the default config and shows a second backend's entry only when configured [evidence: command:npx vitest run src/App.test.tsx]
- AC3: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/App.tsx`
- `src/App.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
