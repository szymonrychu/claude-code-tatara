---
title: web webhook menu entry
status: todo
repo: agents-web
value: the Webhooks page is reachable from the menu between Clusters and Presets
files: [src/backends/registry.ts, src/backends/registry.test.ts, src/webhooks/menu.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-webhook-endpoints]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 703360
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web webhook menu entry

## Requirement

Register the Webhooks menu entry (design D11; request: "webUI entry between clusters and presets"; contracts `agents-web-backend-registry`, `agents-web-backends-config`). Paths are in code/agents-web.

- `src/webhooks/menu.tsx` (JSX, so `.tsx`): `webhooksMenu: MenuEntry = {id: 'webhooks', label: 'Webhooks', order: 20, backend: 'webhooks', render: (onBack) => <WebhooksPage onBack={onBack} />}`.
- `src/backends/registry.ts`: `BACKEND_MENUS.webhooks = [webhooksMenu]`.
- `src/backends/registry.test.ts`: with a config listing `orchestrator` and `webhooks` the entries are ordered Clusters, Webhooks, Presets (Clusters is registered by configuration-improvements, done); with `webhooks` absent there is no Webhooks entry.
- `src/App.test.tsx` stays green.

## Acceptance conditions

- AC1: Webhooks is listed between Clusters and Presets when configured and absent otherwise [evidence: command:npx vitest run src/backends/registry.test.ts]
- AC2: the app tests pass [evidence: command:npx vitest run src/App.test.tsx]
- AC3: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/webhooks/menu.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
