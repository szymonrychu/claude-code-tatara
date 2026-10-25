---
title: web webhook mappings
status: todo
repo: agents-web
value: "the user maps an event to a preset so matching events start a cluster, and removes a mapping"
files: [src/webhooks/MappingsList.tsx, src/webhooks/MapEventDialog.tsx, src/webhooks/WebhooksPage.tsx, src/webhooks/Mappings.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/Mappings.test.tsx src/webhooks/WebhooksPage.test.tsx && npm run lint"
depends_on: [web-webhook-events-page]
owns: []
uses: [trigger-ui-page-pattern, web-webhook-client]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
