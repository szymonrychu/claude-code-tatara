---
title: web webhook menu entry
status: todo
repo: agents-web
value: the Webhooks page appears in the menu between Clusters and Presets whenever the webhook backend is configured
files: [src/backends/registry.ts, src/backends/registry.test.ts, src/webhooks/menu.ts]
verify: "npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint"
depends_on: [web-webhook-mappings]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web webhook menu entry

## Requirement

Register the Webhooks menu entry (design D11; request: "webUI entry between clusters and presets"; contracts `agents-web-backend-registry`, `agents-web-backends-config`). Paths are in code/agents-web.

- `src/webhooks/menu.ts`: `webhooksMenu: MenuEntry = {id: 'webhooks', label: 'Webhooks', order: 20, backend: 'webhooks', render: (onBack) => <WebhooksPage onBack={onBack} />}`.
- `src/backends/registry.ts`: `BACKEND_MENUS.webhooks = [webhooksMenu]`.
- `src/backends/registry.test.ts`: with a config listing `orchestrator` and `webhooks` the entries are ordered Clusters (if registered), Webhooks, Presets; with `webhooks` absent there is no Webhooks entry; Webhooks sits directly above Presets when no Clusters entry exists.
- `src/App.test.tsx` stays green.

## Acceptance conditions

- AC1: Webhooks is listed between Clusters and Presets when configured and absent otherwise [evidence: command:npx vitest run src/backends/registry.test.ts]
- AC2: the app tests pass [evidence: command:npx vitest run src/App.test.tsx]
- AC3: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/webhooks/menu.ts`

## Interfaces

- Uses `agents-web-backend-registry` (order slot 20) and `agents-web-backends-config` (backend id `webhooks`, basePath `/webhooks/api/v1`).

## Expected outcome

With the webhooks backend configured, the menu shows Clusters, Webhooks, Presets.

## Steps

- Red: registry test cases; run: fail. Green: register; run the verify command.

## Notes

- configuration-improvements adds Clusters at slot 10; the order is correct with or without it.
