---
title: web backend menu
status: done
repo: agents-web
value: "later services add UI entries by registering them, shown only when configured"
files: [src/backends/registry.ts, src/backends/registry.test.ts, src/App.tsx, src/App.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-runtime-config]
model: ""
review: ""
verified_head: 61c1def
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 5
actual_tokens: 595294
actual_roles: "impl 3, review 3"
actual_role_tokens: "impl 467564, review 127730"
---

# web backend menu

## Requirement

Settings-menu entries come from a backend registry and appear only for configured backends (design D3). Paths are in code/agents-web.

- `src/backends/registry.ts`: `MenuEntry {id, label, order, backend, render(onBack): ReactNode}`; `BACKEND_MENUS: Record<string, MenuEntry[]>` keyed by backend id; `menuEntries(config: RuntimeConfig): MenuEntry[]` returns the entries of the configured backends sorted by `order`, then `label`; a configured id with no registered entries is skipped with one `console.warn` naming it.
- The orchestrator registers every settings entry the UI has at move time (Presets, `order` 40, and any entry agent-init-scripts or cluster-scaling added). Reserved order slots, documented in the file header: 10 Clusters (configuration-improvements), 20 Webhooks (agents-webhook-microservice), 30 Schedules (agents-schedule-microservice), 40 Presets.
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

- Owns `backend-registry` (contract `agents-web-backend-registry`): `src/backends/registry.ts:BACKEND_MENUS`, `menuEntries`, `MenuEntry`, the order slots. Uses `backends-config` from web-runtime-config.
- Replaces the role of contract `orch-settings-menu` (`SessionsMenu` `settingsCategories` `{id, label, onOpen}` is unchanged).

## Expected outcome

A later service adds its UI by registering entries under its backend id; the chart's `config.json` decides whether they appear.

## Steps

- Red: `src/backends/registry.test.ts` and the new `App.test.tsx` cases; `npx vitest run src/backends/registry.test.ts src/App.test.tsx` fails.
- Green: implement the registry, move the Presets entry into it, build `settingsCategories` from it in `App.tsx`.
- `npx tsc -b && npm run lint`: pass.

## Notes

- No router is introduced; the existing `view` state now holds `'cluster'` or an entry id.

- 2026-10-25 done
