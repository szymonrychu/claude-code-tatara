---
title: web webhook endpoints
status: in-progress
repo: agents-web
value: "webhook URLs are created, shown with their credentials once, rotated and deleted from the UI"
files: [src/webhooks/EndpointsList.tsx, src/webhooks/CreateEndpointDialog.tsx, src/webhooks/CredentialsDialog.tsx, src/webhooks/WebhooksPage.tsx, src/webhooks/Endpoints.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/Endpoints.test.tsx src/webhooks/WebhooksPage.test.tsx && npm run lint"
depends_on: [web-webhook-events-page]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 15
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web webhook endpoints

## Requirement

Webhook endpoints in the UI (design D7, D11, D18; re-plan 2026-10-25: the entry between Clusters and Presets manages webhook endpoints: create with type, preset, optional suffix and optional credentials, show the full URL and the credentials once, rotate, delete). Paths are in code/agents-web.

- `CreateEndpointDialog({open, onClose, onCreated})`: type select (GitHub PR, GitHub issue, GitLab MR, GitLab issue, Grafana alert), `PresetSelect` (required), an optional suffix field ("random when empty"; client-side check of `^[A-Za-z0-9._~-]{1,128}$`), an optional "Set credentials" switch revealing username and password fields (password at least the backend's minimum from `getMeta()`), an optional prompt template textarea with the placeholder list (`$event`, `$type`, `$source`, `$kind`, `$action`, `$repo`, `$number`, `$url`, `$title`); submit calls `createEndpoint`; 409 `suffix_taken` and 422 show `FormError` on the field; success calls `onCreated(created)`.
- `CredentialsDialog({endpoint, onClose})`: shows the full URL, the username and the password with copy buttons, the line "The password is shown only now. Rotate the credentials to get a new one.", and per type a short hint where they go (GitHub/GitLab: `https://<user>:<password>@<host>/webhook/<suffix>` as the URL; Grafana: the webhook contact point's basic auth fields); closing it drops the password from state.
- `EndpointsList({refreshKey, onChanged})`: rows with the full URL (copy button), type, preset name resolved from the presets list, username, created and rotated times; "Rotate credentials" (confirm, then `rotateEndpoint`, then `CredentialsDialog`); "Delete" (confirm naming the URL, then `deleteEndpoint`); an empty state "No endpoints yet" with a create button.
- `WebhooksPage.tsx`: an "Endpoints" section with a "New endpoint" button above the events section; creating, rotating and deleting refresh the list; the events endpoint filter lists the endpoints.
- `src/webhooks/Endpoints.test.tsx`: create with defaults shows the returned URL and password once; create with suffix and credentials sends them; preset required; suffix pattern and 409 errors shown; the password is not rendered after the dialog closes or in the list; rotate asks, calls the API and shows the new credentials; delete asks and calls the API; list renders preset names and copy buttons.

## Acceptance conditions

- AC1: an endpoint is created with type, preset and optional suffix and credentials, and the full URL and credentials are shown once [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t create]
- AC2: endpoints are listed with URL, type, preset name and username, never the password [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t list]
- AC3: rotate and delete ask for confirmation and call the API [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t "rotate|delete"]
- AC4: backend validation errors are shown in the dialog [evidence: command:npx vitest run src/webhooks/Endpoints.test.tsx -t error]
- AC5: the page tests still pass and lint passes [evidence: command:npx vitest run src/webhooks/WebhooksPage.test.tsx && npx tsc -b && npm run lint]

## Files

- `src/webhooks/EndpointsList.tsx`
- `src/webhooks/CreateEndpointDialog.tsx`
- `src/webhooks/CredentialsDialog.tsx`
- `src/webhooks/WebhooksPage.tsx`
- `src/webhooks/Endpoints.test.tsx`

## Interfaces

- Consumes `web-webhook-client` and `trigger-ui-page-pattern` (`PresetSelect`, `FormError`).

## Expected outcome

The Webhooks page lists endpoints and creates, rotates and deletes them, showing the URL and credentials once.

## Steps

- Red: `src/webhooks/Endpoints.test.tsx`; run `npx vitest run src/webhooks/Endpoints.test.tsx`: fail.
- Green: the three components and the page section; run the verify command.

## Notes

- Reuse `PresetSelect` and `FormError` from `src/triggers`.
- Never keep the password in component state after the credentials dialog closes, and never in the list.

- 2026-10-25 in-progress: re-plan 2026-10-25: added; not started

User requirement (2026-10-25), verbatim: "webhook configuration consists of jinja2 template for initial prompt. Jinja2 must include JSON parsing filter. it must be possible to provide an example JSON to check how Jinja templae compiles."
Orchestrator ruling for this task: the endpoint create dialog has a multiline Jinja2 template editor plus an "Example JSON" editor and a Preview button calling `POST /webhooks/api/v1/templates/preview`, showing the rendered prompt or the error; a per-type sample payload can prefill the example. Tests.
