---
title: web webhook events page
status: done
repo: agents-web
value: "the user sees recent webhook events with their status and reason, refreshed live"
files: [src/webhooks/WebhooksPage.tsx, src/webhooks/EventsTable.tsx, src/webhooks/WebhooksPage.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/WebhooksPage.test.tsx && npm run lint"
depends_on: [web-trigger-ui-kit, web-webhook-api-client]
model: ""
review: ""
verified_head: 969c76b
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: 1
actual_minutes: 3
actual_tokens: 369006
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 288636, review 80370"
---

# web webhook events page

## Requirement

The Webhooks page with recent events (design D11; request: "recent events (along with their status: new/in-progress/handled/ignored)"; re-plan 2026-10-25: events belong to an endpoint, no map action). Paths are in code/agents-web.

- `WebhooksPage({onBack})`: title "Webhooks", a back control; task web-webhook-endpoints adds the endpoints section above the events; a status filter (all, new, in-progress, handled, ignored, failed) and an endpoint filter; the events table.
- `EventsTable({events})`: columns received time (relative, full on hover), endpoint (suffix and type), kind, repo#number (link to `url`), title, `RunStatusChip` with reason, cluster slug; rows that went to a running agent show "update of #id", duplicates "duplicate of #id".
- Data via `usePoll(() => listEvents({status, endpointId}), 5000)`; "Load older" uses `beforeId`; `FormError` on failure; an empty state "No events yet" pointing at the endpoints section.
- `src/webhooks/WebhooksPage.test.tsx`: rows render with endpoint, status chips and reasons; update and duplicate links; the filters change the query; polling refreshes; load older; empty and error states.

## Acceptance conditions

- AC1: recent events show endpoint, kind, repo and number, title, status chip with reason and cluster [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx -t rows]
- AC2: the status and endpoint filters, polling and load older work [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx -t filter]
- AC3: empty and error states render [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx -t state]
- AC4: types and lint pass [evidence: command:npx tsc -b && npm run lint]

## Files

- `src/webhooks/WebhooksPage.tsx`
- `src/webhooks/EventsTable.tsx`
- `src/webhooks/WebhooksPage.test.tsx`

## Interfaces

- `src/webhooks/WebhooksPage.tsx` `WebhooksPage({onBack})`, `src/webhooks/EventsTable.tsx` `EventsTable({events})`; consumes `web-webhook-client` and `trigger-ui-page-pattern`.

## Expected outcome

The user sees the live event list with statuses.

## Steps

- Red: tests; run: fail. Green: components; run the verify command.

## Notes

- Reuse `RunStatusChip`, `usePoll`, `FormError` from `src/triggers`.

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

- 2026-10-25 done
