# Webhook event filters design

## Summary

Every agents-webhook endpoint gets its own allow and deny rules over the normalized fields of its type: author, actor, repository, labels (Grafana alert labels as `key=value`), title, body and comment text, kind, action, and for PR/MR the source and target branch. Rules match by `equals` or by `regex`; regex runs on RE2 (linear time) with hard bounds, so a user pattern cannot stall the public ingest. A delivery that fails a filter is still accepted (202) and stored `ignored` with reason `filter_denied: <field>` or `filter_not_allowed: <field>`; it never starts an agent. Filters are set at endpoint creation, edited later through a new `PUT /webhooks/api/v1/endpoints/{id}/filters`, and in the agents-web Webhooks UI, whose example-JSON preview also reports whether the example passes. The global `WEBHOOK_ALLOWED_AUTHORS` is retired in favour of per-endpoint author rules; `WEBHOOK_BOT_LOGINS` stays as the global self-loop guard.

## Intent and why

User request 2026-10-25, verbatim: "small epic- for each of supported webhooks add whiltelisting/blacklisting ability- e.g. grafana webhooks should blacklist if a label X consist of value Y, or issue/mr webhook will be received but internall ignorred if author is not one of the usernames from the list (or repos)- in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events." Follow-up, verbatim: "other fields: title regex, branch name, etc".

Today an endpoint reacts to every handled event of its type; the only knobs are two global env lists that apply to every endpoint alike. One hook per repo or org sends far more than the operator wants an agent for (staging alerts, PRs into release branches, issues from strangers), and each such event costs a cluster.

## Goals

- G1: every endpoint type has per-endpoint allow and deny rules over the fields of D3, including author, repository, labels (Grafana `key=value`), title regex and PR/MR source and target branch.
- G2: a delivery that fails a filter answers 202 and is stored `ignored` with reason `filter_denied: <field>` or `filter_not_allowed: <field>`; it is never dispatched.
- G3: filters are set on create and replaced later through the endpoints API; the agents-web Webhooks UI edits them on create and on an existing endpoint, and its example-JSON preview shows whether the example passes.
- G4: regex rules run on RE2 with the bounds of D4; a pattern RE2 refuses, or any rule outside the bounds, is rejected on save with 422 naming the rule.
- G5: `WEBHOOK_ALLOWED_AUTHORS` and the reason `author_not_allowed` are gone; `WEBHOOK_BOT_LOGINS` and `self_event` stay.
- G6: the live namespace runs the new agents-webhook and agents-web builds and the smoke, extended with a filter check, is green.

## Non-goals

- Filters over raw payload JSON paths, Grafana annotations, per-alert Grafana labels (only the group's `commonLabels`), or fields not in D3.
- Boolean expressions or OR-groups across rules (D2 fixes the combination rule).
- Re-evaluating events already queued when an endpoint's filters change.
- Editing any other endpoint field (type, preset, template stay create-only, prior design D7).
- Filter hit counters or metrics.
- Changing the built-in ignore rules (`self_event`, `action_ignored`, `resolved`, drafts, title-only edits).

## Anti-goals

- A user regex that can make ingest CPU-bound (ReDoS) on the public, unauthenticated-reachable path.
- A filtered delivery answered with a 4xx or 5xx, so the forge retries or disables the hook.
- A filter failure that leaks the rule set, the payload or credentials into logs.
- A second, divergent copy of the field catalogue in the UI (the UI reads it from `GET /meta`).
- Scope creep into a generic rules engine or a query language.

## Constraints

- Python only in agents-webhook, TypeScript in agents-web; services talk only over HTTP; `endpoints` keeps one writer (the api).
- No backward compatibility shims (house rule): the retired env var and reason are removed, not aliased.
- Test-first per task; targeted verify per task; small tasks, model per task (sonnet unless a task adds a module or touches more than five files).
- The DB-backed agents-webhook tests (`tests/test_endpoints_repo.py`, `tests/test_ingest_http.py`, `tests/test_api.py`, `tests/e2e/`) start Postgres through testcontainers, so their verify needs a running Docker daemon.
- The orchestrator (main session) runs `mise run apply` in agents-helmfile; apply never appears in AC evidence.
- The ingest auth order is unchanged (429, 401, 413, ping, 400, normalize, classify, record): filters run after classify and before record, never before authentication.

## Decisions

### D1: Filters live on the endpoint

Each endpoint carries `filters = {"allow": [Rule], "deny": [Rule]}` in a new `endpoints.filters jsonb NOT NULL DEFAULT '{"allow": [], "deny": []}'` column (migration `0004_endpoint_filters.sql`), written only by the api (create and the new filters route), read by ingest through `endpoints.authenticate`, which already loads the endpoint row. Empty lists mean today's behaviour. Alternatives: a separate `endpoint_filters` table with one row per rule (rejected: no query ever needs a single rule, and a second table needs its own writer rule); global filters in env (rejected: user decision "per webhook endpoint"). User decision 1.

### D2: Rule model and semantics

`Rule = {"field": <D3 field>, "match": "equals" | "regex" (default "equals"), "values": [str, ...]}`. Within a rule, values are OR: the rule matches when the event's field matches any value. Deny: the first deny rule (in list order) that matches ignores the event with reason `filter_denied: <field>`. Allow: when deny passed, the first allow rule that does not match ignores the event with `filter_not_allowed: <field>`; so allow rules AND together (author in list AND repo in list, gate Q3). An event field that is absent (None, for example `comment` on a non-comment event, `source_branch` on a GitHub `issue_comment`) never matches: it fails an allow rule and never trips a deny rule (fail closed for allowlists, my call). List fields (forge `labels`) match when any element matches. `equals` compares case-insensitively for `author`, `actor`, `repo` and forge `labels` (GitHub and GitLab treat logins, repo paths and label names case-insensitively) and case-sensitively for everything else (my call). `regex` is an unanchored RE2 search over the field text; users anchor with `^...$` and use `(?i)` for case-insensitivity (my call: one semantic for every field). Grafana `labels` values are `key=value` (split on the first `=`, key non-empty): `equals` compares the label's value exactly, `regex` searches the label's value with the part after `=`; a key the alert group does not carry never matches. Deny is checked before allow. User decisions 2, 4. Alternatives: deny-wins-over-allow per field (same effect, more code); anchored regex like Alertmanager matchers (rejected: a title regex is naturally a search; one rule is easier to explain).

### D3: Field catalogue per type

`filters.FIELDS` is the single source; `GET /meta` serves it as `filter_fields`, the README `## Filters` section documents it, and validation refuses a field that does not apply to the endpoint's type.

| Field | Normalized source | github-issue | github-pr | gitlab-issue | gitlab-mr | grafana-alert |
|---|---|---|---|---|---|---|
| `author` | `NormalizedEvent.author` (item author; the commenter on comment events; GitLab: the hook user) | yes | yes | yes | yes | no (alerts have no author) |
| `actor` | `actor` (the sender of the event) | yes | yes | yes | yes | no |
| `repo` | `repo` (`owner/name`, GitLab `path_with_namespace`) | yes | yes | yes | yes | no (alerts have no repo) |
| `labels` | `labels` (forge label names; Grafana `commonLabels` as `key=value`) | yes | yes | yes | yes | yes |
| `title` | `title` (Grafana: `alertname` or the notification title) | yes | yes | yes | yes | yes |
| `body` | `body` (issue/PR/MR description; Grafana: summary and description annotations) | yes | yes | yes | yes | yes |
| `comment` | `comment_body` (comment events only) | yes | yes | yes | yes | no |
| `kind` | `kind` (`issue`, `mr`, `comment`) | yes | yes | yes | yes | no (always `alert`) |
| `action` | `action` (`opened`, `reopened`, `edited`, `synchronize`, `ready_for_review`, `created`, ...) | yes | yes | yes | yes | no (non-firing is already `resolved`) |
| `source_branch` | new `source_branch` (GitHub `pull_request.head.ref`, GitLab `object_attributes.source_branch` or `merge_request.source_branch` on notes) | no (issues have no branch) | yes | no | yes | no |
| `target_branch` | new `target_branch` (GitHub `pull_request.base.ref`, GitLab `target_branch`) | no | yes | no | yes | no |

Not offered for any type: `number`, `url`, `draft` and `changed` (the built-in rules already decide drafts and title-only edits), `delivery_id`, `dedup_key`, `priority`, the raw payload. GitHub `issue_comment` on a PR carries no branch, so `source_branch`/`target_branch` are absent there (D2: fails an allow rule). `NormalizedEvent` gains `source_branch: str | None = None` and `target_branch: str | None = None`; they are not stored as event columns (the payload already holds them; my call: no event-table migration). User decision 4.

### D4: Regex engine and bounds

Regex rules compile with RE2 through the `google-re2` package (module `re2`; PyPI wheels for cp312 on manylinux_2_28 x86_64 and aarch64, which the `python:3.12-slim-bookworm` image satisfies, and on macOS). RE2 matches in time linear in the input and refuses backreferences and lookaround at compile time, so no pattern can backtrack catastrophically. Bounds, checked on save (422 naming `filters.<allow|deny>[i]...`): at most 20 rules per list, 1 to 50 values per rule, each value 1 to 256 characters; matching reads at most the first 65536 characters of a text field (the prompt's own 64 KiB cap); compiled rule sets are cached per endpoint filter JSON. Alternatives: stdlib `re` (rejected: exponential backtracking, no timeout); the `regex` package with `timeout=` (rejected: still burns CPU up to the timeout on every delivery and adds a failure mode); glob patterns only (rejected: the user asked for a title regex). Constraint "regex safety".

### D5: Evaluation point and outcome

Ingest runs `normalize`, then `classify` (built-in rules first: `self_event`, `action_ignored`, `resolved`), and only when classify returns None, `filters.evaluate(event, endpoint.filters)`; its reason goes to `events.record(..., ignore_reason=...)`, so the delivery answers 202 `{id, status: "ignored", reason}` and never reaches the queue (gate Q2: built-in reasons win, so a filter reason only shows on an event that would otherwise run). Filters are decided at ingest only; an event already `new` when filters change runs as queued (my call). Dedup is unaffected: an ignored delivery never replaces a `new` row. User decision 3.

### D6: API surface

- `POST /webhooks/api/v1/endpoints` accepts optional `filters` (validated against the type; 422 `invalid_request` naming the rule).
- New `PUT /webhooks/api/v1/endpoints/{id}/filters` with body `Filters` replaces the endpoint's filters and returns `EndpointView`; 404 `not_found`, 422 `invalid_request`. Only filters become editable (prior D7 kept endpoints otherwise immutable; recreating would change the URL and credentials, my call).
- `EndpointView.filters` is always present.
- `GET /meta` gains `filter_fields: {<type>: [<field>, ...]}`.
- `POST /templates/preview` takes `template` optional and `filters` optional (at least one, else 422); the response is `{prompt: str | null, filters: {passed: bool, reason: str | null} | null}`. Nothing is stored.
README `## API` and the committed `openapi.json` follow (drift tests). User decision 5.

### D7: Global env lists

`WEBHOOK_ALLOWED_AUTHORS` and the reason `author_not_allowed` are retired: a per-endpoint `allow` rule on `author` does the same per endpoint, and the live value is empty, so nothing changes in production. `WEBHOOK_BOT_LOGINS` stays as the global guard against the agent's own comments re-triggering it (one bot identity for every endpoint; making it per endpoint would let one forgotten rule start a loop). Gate Q1. Alternatives: keep both (rejected: two ways to say the same thing, house rule against compatibility layers); retire both (rejected: loop safety would depend on per-endpoint discipline).

### D8: Webhooks UI

agents-web gets `FiltersEditor` (allow and deny sections, each rule a field select from `meta.filter_fields[type]`, a match select, values one per line, a `key=value` hint for Grafana labels; changing the type drops rules whose field no longer applies). The create dialog embeds it, sends `filters`, and its Preview runs when a template or a rule is set, showing the rendered prompt (template only) and "Passes the filters" or "Ignored: <reason>". Each endpoint row gets a "Filters (n)" action opening `FiltersDialog`: the editor prefilled from `EndpointView.filters`, an example JSON with a Check button (preview with filters only), Save through the PUT, the 422 message through `FormError`. The UI never validates regex itself (JavaScript regex is not RE2); the backend answer is authoritative. User decision 5.

### D9: Deploy

agents-helmfile pins the agents-webhook and agents-web main builds that contain this epic, drops `WEBHOOK_ALLOWED_AUTHORS` from `values/agents-webhook/common.yaml`, and extends the smoke: the temporary endpoint is created with a deny rule, the create answer and a PUT round-trip the filters, and `POST /templates/preview` with a matching example reports `passed: false, reason: "filter_denied: title"`. The smoke never ingests a delivery that would pass the built-in rules, so a broken filter cannot start a cluster (my call). The orchestrator runs `mise run apply`; the apply task proves no drift and a green smoke.

### D10: Headless parity

Every capability is reachable without the UI: README `## API` and `## Filters`, the committed `openapi.json`, and API-only e2e cases (real Postgres, the three processes, the fake orchestrator) for a deny, an allow miss, a pass, the PUT replacing the outcome, and the preview.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | ran (own LSP and grep sweep of agents-webhook cc0f706 and agents-web 18f5132) | filters after `classify` in `ingest/app.py:_deliver`; validation errors as `ValueError` naming the field, mapped to 422 like `db/endpoints.py:_check_suffix`; README drift tests (`tests/test_readme_config.py`, `tests/test_readme_api.py`) cover the new reasons, section and route | storing branch columns on events (the payload holds them) |
| research-code-external | ran (prior art: Alertmanager matchers `=`/`=~` on RE2, GitHub/GitLab webhook settings with no server-side filters) | RE2 for user regex, as Alertmanager and Grafana do (prometheus/alertmanager `pkg/labels/matcher.go`) | Alertmanager's fully anchored regex (D2: unanchored search) |
| research-docs | ran (google-re2 on PyPI, version 1.1.20251105, cp312 wheels for manylinux_2_28 x86_64/aarch64 and macOS, https://pypi.org/project/google-re2/) | `google-re2` as the engine | `regex` with `timeout=` (https://pypi.org/project/regex/) |
| research-papers | skipped: no algorithmic core beyond choosing a linear-time regex engine | none | none |
| retro history | ran (`ticket.py retro --history`) | for every task that deletes or cleans up, the reviewer asks what runs if the producing step fails or a variable is empty (test-temp-dirs-outside-the-c, recurring): applied to smoke-webhook-filters (the endpoint-delete trap) and retire-allowed-authors | none |

## Research inputs

- `classify` runs before record in `ingest/app.py:_deliver`; filters slot in after it - code/agents-webhook `src/agents_webhook/ingest/app.py` - ingest-applies-filters.
- `endpoints.authenticate` builds `Endpoint(*row[:-1])` positionally from `_COLUMNS`; a new column must keep `password_hash` last - `src/agents_webhook/db/endpoints.py:authenticate` - endpoint-filters-storage.
- No route edits an endpoint today (prior D7) - `src/agents_webhook/api/routes.py` - api-endpoint-filters.
- The preview needs a template today and the UI disables Preview without one - `api/schemas.py:PreviewIn`, agents-web `src/webhooks/CreateEndpointDialog.tsx` - api-endpoint-filters, web-create-endpoint-filters.
- `NormalizedEvent` has no branch fields - `src/agents_webhook/normalize.py:NormalizedEvent` - normalize-branch-fields.
- `WEBHOOK_ALLOWED_AUTHORS` is read only by `classify`; live value empty - `normalize.py:classify`, agents-helmfile `values/agents-webhook/common.yaml` - retire-allowed-authors, deploy-pin-webhook-filters.
- e2e sets `WEBHOOK_ALLOWED_AUTHORS=alice,bob` and asserts `author_not_allowed` - `tests/e2e/conftest.py`, `tests/e2e/test_e2e_api.py::test_ignore_reasons_are_listed` - e2e-endpoint-filters.
- agents-web vendors the API with `npm run sync:api -- webhooks --from <checkout>`; it refuses an uncommitted `openapi.json` - `scripts/sync-api.mjs` - web-vendor-filters-api.
- The smoke's temporary endpoint and closed-issue delivery are the only side effects; keep it so - agents-helmfile `scripts/smoke.sh` step 8 - smoke-webhook-filters.
- Retro proposal (test-temp-dirs-outside-the-c, recurring): ask "what runs if the producing command fails or the variable is empty" for any cleanup path - smoke-webhook-filters.

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `webhook-normalized-event` (adds `source_branch`, `target_branch`) | normalize-branch-fields | filter-rules-engine | `code/agents-webhook/src/agents_webhook/normalize.py` |
| `webhook-filters` (`FIELDS`, `validate`, `evaluate`, reasons) | filter-rules-engine | endpoint-filters-storage, ingest-applies-filters, api-endpoint-filters | `code/agents-webhook/src/agents_webhook/filters.py` |
| `webhook-endpoints` (adds `filters`, `set_filters`) | endpoint-filters-storage | ingest-applies-filters, api-endpoint-filters | `code/agents-webhook/src/agents_webhook/db/endpoints.py` |
| `webhook-api` (filters on create and view, PUT filters, preview, meta) | api-endpoint-filters | web-vendor-filters-api, smoke-webhook-filters, e2e-endpoint-filters | `code/agents-webhook/README.md` |
| `webhook-settings-env` (drops `WEBHOOK_ALLOWED_AUTHORS`) | retire-allowed-authors | deploy-pin-webhook-filters | `code/agents-webhook/src/agents_webhook/settings.py` |
| `web-webhook-client` (Filters types, `setEndpointFilters`) | web-vendor-filters-api | web-filters-editor, web-create-endpoint-filters, web-edit-endpoint-filters | `code/agents-web/src/webhooks/api.ts` |

Cross-epic: none changed. agents-schedule-microservice consumes the agents-common parts and `trigger-ui-page-pattern`, which this epic does not touch. `webhook-api` (registry consumers agents-web, agents-helmfile) is extended additively plus one new route, and both consumers are in this epic. The current `ticket.py` has no `contract` subcommand, so nothing was added to `docs/plans/contracts.json`.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Filters live on the endpoint | endpoint-filters-storage, ingest-applies-filters |
| D2 Rule model and semantics | filter-rules-engine |
| D3 Field catalogue per type | normalize-branch-fields, filter-rules-engine, ingest-applies-filters |
| D4 Regex engine and bounds | filter-rules-engine |
| D5 Evaluation point and outcome | ingest-applies-filters, e2e-endpoint-filters |
| D6 API surface | api-endpoint-filters, web-vendor-filters-api |
| D7 Global env lists | e2e-endpoint-filters, retire-allowed-authors, deploy-pin-webhook-filters |
| D8 Webhooks UI | web-filters-editor, web-create-endpoint-filters, web-edit-endpoint-filters |
| D9 Deploy | deploy-pin-webhook-filters, smoke-webhook-filters, apply-smoke-webhook-filters |
| D10 Headless parity | ingest-applies-filters, api-endpoint-filters, e2e-endpoint-filters |

## Review focus

- filter-rules-engine: no path compiles a user pattern with stdlib `re`; the ReDoS test uses a classic catastrophic pattern on a long input and bounds wall time; every bound is enforced on validate; absent fields fail allow and never trip deny; case rules exactly as D2.
- ingest-applies-filters: filters run after authentication and classify, before record; a filtered delivery is 202 ignored; logs carry the reason only, never the rules or payload text.
- api-endpoint-filters: 422 messages name the rule path; the PUT replaces atomically and returns the view; the preview stores nothing.
- endpoint-filters-storage: `authenticate` still compares and verifies in constant shape (the identical-401 property) with the new column.
- web-*: no client-side regex validation; type change drops inapplicable rules; the PUT error shows in the dialog.

## Left to the builder

- Internal layout of `filters.py` (dataclasses, cache shape) as long as `FIELDS`, `validate`, `evaluate`, `DENIED`, `NOT_ALLOWED` and the bounds constants are module-level names.
- UI layout and wording inside the dialogs, within MUI and the existing trigger UI kit.
- Whether the compiled-rule cache is an `lru_cache` or a dict keyed by the canonical JSON, bounded.

## Assumptions and unknown facts

- `google-re2` 1.1.20251105 installs under uv on macOS (dev) and in the image; confirmed by the filter-rules-engine verify (`uv sync`, tests) and the image build in CI.
- GitHub `pull_request`, `pull_request_review` and `pull_request_review_comment` payloads carry `pull_request.head.ref` and `base.ref`; GitLab MR hooks carry `object_attributes.source_branch`/`target_branch` and Note hooks `merge_request.source_branch`/`target_branch` (provider docs; pinned by tests/payloads.py fixtures in normalize-branch-fields).
- Grafana label rules match `commonLabels`, the labels shared by every alert in the notification (per-alert labels are a non-goal).

## Open questions
- Q1: Retire WEBHOOK_ALLOWED_AUTHORS (and reason author_not_allowed) in favour of per-endpoint author allow rules, but keep WEBHOOK_BOT_LOGINS as the global self-loop guard? [recommended: yes]
- Q2: Run the built-in ignore rules (self_event, action_ignored, resolved) before the endpoint filters, so a filter reason only appears on events that would otherwise start an agent? [recommended: yes]

## Irreversible operations in scope

- Migration `0004_endpoint_filters.sql` adds a column to the live agents-webhook database on apply (additive, forward-only; existing rows get empty filters). Covered by the gate and the apply task; the orchestrator runs `mise run apply`.
- Removing `WEBHOOK_ALLOWED_AUTHORS` from the live values: its live value is empty, so no behaviour changes.
