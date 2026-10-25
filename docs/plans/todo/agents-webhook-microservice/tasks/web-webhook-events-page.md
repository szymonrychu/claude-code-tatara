---
title: web webhook events page
status: todo
repo: agents-web
value: "the user sees recent webhook events with their status and reason, refreshed live"
files: [src/webhooks/WebhooksPage.tsx, src/webhooks/EventsTable.tsx, src/webhooks/WebhooksPage.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/WebhooksPage.test.tsx && npm run lint"
depends_on: [web-trigger-ui-kit, web-webhook-api-client]
owns: []
uses: [trigger-ui-page-pattern, web-webhook-client]
model: ""
estimate: 5
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

# web webhook events page

## Requirement

The Webhooks page with recent events (design D11; request: "recent events (along with their status: new/in-progress/handled/ignored)"). Paths are in code/agents-web.

- `WebhooksPage({onBack})`: title "Webhooks", a back control, a status filter (all, new, in-progress, handled, ignored, failed), the events table; task web-webhook-mappings adds the mappings section below the table.
- `EventsTable({events, onMap})`: columns received time (relative, full on hover), source, kind, repo#number (link to `url`), title, `RunStatusChip` with reason, cluster slug; rows that are updates or duplicates show "update of #id" / "duplicate of #id"; a "Map to preset" action per row calls `onMap(event)`.
- Data via `usePoll(() => listEvents({status}), 5000)`; "Load older" uses `beforeId`; `FormError` on failure; an empty state "No events yet" with the three ingest URLs from `getMeta()`.
- `src/webhooks/WebhooksPage.test.tsx`: rows render with status chips and reasons; the filter changes the query; polling refreshes; load older; empty state shows the ingest paths; error state; the map action fires with the row's event.

## Acceptance conditions

- AC1: recent events show source, kind, repo and number, title, status chip with reason and cluster [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx -t rows]
- AC2: the status filter, polling and load older work [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx -t filter]
- AC3: empty and error states render [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx -t state]
- AC4: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `src/webhooks/WebhooksPage.tsx`
- `src/webhooks/EventsTable.tsx`
- `src/webhooks/WebhooksPage.test.tsx`

## Interfaces

- `WebhooksPage({onBack})` rendered by the menu entry (task web-webhook-menu-entry).

## Expected outcome

The user sees the live event list with statuses.

## Steps

- Red: tests; run: fail. Green: components; run the verify command.

## Notes

- Reuse `RunStatusChip`, `usePoll`, `FormError` from `src/triggers`.
