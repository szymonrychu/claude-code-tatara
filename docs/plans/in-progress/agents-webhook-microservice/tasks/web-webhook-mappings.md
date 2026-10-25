---
title: web webhook mappings
status: in-progress
repo: agents-web
value: "the user maps an event to a preset so matching events start a cluster, and removes a mapping"
files: [src/webhooks/MappingsList.tsx, src/webhooks/MapEventDialog.tsx, src/webhooks/WebhooksPage.tsx, src/webhooks/Mappings.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/Mappings.test.tsx src/webhooks/WebhooksPage.test.tsx && npm run lint"
depends_on: [web-webhook-events-page]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web webhook mappings

## Requirement

Event-to-preset mappings in the UI (design D7, D11; request: "allows to map event to preset ... allows to remove such mapping"). Paths are in code/agents-web.

- `MapEventDialog({event, open, onClose, onCreated})`: prefilled from the event: source, kind, repo (with an "any repo" switch), for Grafana the event's labels as removable chips (the subset to match); `PresetSelect` (required); an optional prompt template textarea with the placeholder list (`$event`, `$source`, `$kind`, `$action`, `$repo`, `$number`, `$url`, `$title`); submit calls `createMapping`; a 422 shows `FormError` with the field; success calls `onCreated` and closes. A note says the mapping applies to future events.
- `MappingsList({refreshKey})`: lists mappings (source, kind, repo or "any", labels, preset name resolved from the presets list, template set or default, created); a delete button opens a confirm dialog and calls `deleteMapping`.
- `WebhooksPage.tsx`: the map action opens the dialog; the mappings section renders `MappingsList`; creating or deleting refreshes the list.
- `src/webhooks/Mappings.test.tsx`: dialog prefill for a GitHub MR and a Grafana alert (labels); any-repo switch; preset required; 422 error shown; create calls the API with the right body; list renders preset names; delete asks and calls the API.

## Acceptance conditions

- AC1: mapping from an event prefills source, kind, repo or labels and creates the mapping with the chosen preset [evidence: command:npx vitest run src/webhooks/Mappings.test.tsx -t create]
- AC2: mappings are listed with preset names and removed after a confirm [evidence: command:npx vitest run src/webhooks/Mappings.test.tsx -t delete]
- AC3: backend validation errors are shown in the dialog [evidence: command:npx vitest run src/webhooks/Mappings.test.tsx -t error]
- AC4: the page tests still pass and lint passes [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx && npx tsc -b && npm run lint]

## Files

- `src/webhooks/MappingsList.tsx`
- `src/webhooks/MapEventDialog.tsx`
- `src/webhooks/WebhooksPage.tsx`
- `src/webhooks/Mappings.test.tsx`

## Interfaces

- `MapEventDialog`, `MappingsList` inside `WebhooksPage`.

## Expected outcome

The full request is usable from the UI: see events, map one to a preset, remove a mapping.

## Steps

- Red: tests; run: fail. Green: components; run the verify command.

## Notes

- Reuse `PresetSelect` and `FormError` from `src/triggers`.
