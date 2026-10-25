---
title: web filters editor
status: in-progress
repo: agents-web
value: one editor for allow and deny rules over the fields the backend says apply to the type
files: [src/webhooks/FiltersEditor.tsx, src/webhooks/FiltersEditor.test.tsx]
verify: "npm ci --no-audit --no-fund && npx vitest run src/webhooks/FiltersEditor.test.tsx && npx tsc -b && npm run lint"
depends_on: [web-vendor-filters-api]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web filters editor

## Requirement

Build the filters editor component of the Webhooks UI (design D8). User request 2026-10-25, verbatim: "in general whitelist/blacklist capability for webhooks allowing for greater granularity in how to react to webhook events." User decision: "Configurable in the endpoints API and the agents-web Webhooks UI". Paths are in code/agents-web.

New `src/webhooks/FiltersEditor.tsx`, `FiltersEditor({type, fields, value, onChange})`:

- `fields` is `meta.filter_fields[type]` (the backend's catalogue; the component holds no field list of its own); `value` and `onChange` carry a `Filters` value.
- Two sections, "Allow (every rule must match)" and "Deny (any matching rule ignores the event)", each listing its rules and an "Add allow rule" / "Add deny rule" button. A rule row has a Field select over `fields`, a Match select (`equals`, `regex`), a Values text area (one value per line; blank lines dropped), and a remove button.
- For `grafana-alert` with field `labels`, the values helper text says `key=value, one per line` (`key=regex` with match regex); for match `regex` the helper says the backend uses RE2 (no lookaround or backreferences).
- When `type` changes, rules whose field is not in the new `fields` are dropped and `onChange` reports the result.
- The component never validates a regex itself; validation errors come from the backend.

## Acceptance conditions

- AC1: adding an allow rule and a deny rule, choosing field and match and typing values reports a Filters value with one value per non-blank line [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "edits allow and deny rules"]
- AC2: the field select offers exactly the given fields [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "offers only the type's fields"]
- AC3: removing a rule reports the remaining rules [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "removes a rule"]
- AC4: a type change drops rules whose field no longer applies [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "drops rules that do not apply to the new type"]
- AC5: Grafana label rules show the key=value hint and regex rules the RE2 hint [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx -t "shows the label and regex hints"]
- AC6: the component builds no RegExp [evidence: command:! grep -n -e 'new RegExp' -e 'RegExp(' src/webhooks/FiltersEditor.tsx]
- AC7: the editor tests, type check and lint pass [evidence: command:npx vitest run src/webhooks/FiltersEditor.test.tsx && npx tsc -b && npm run lint]

## Files

- `src/webhooks/FiltersEditor.tsx`
- `src/webhooks/FiltersEditor.test.tsx`

## Interfaces

- New `src/webhooks/FiltersEditor.tsx`: `export function FiltersEditor(props: {type: string; fields: string[]; value: Filters; onChange: (next: Filters) => void}): JSX.Element` and `export const EMPTY_FILTERS: Filters` (`{allow: [], deny: []}`). Consumed by web-create-endpoint-filters and web-edit-endpoint-filters.
- Uses `Filters`, `FilterRule` from `src/webhooks/api.ts` (web-vendor-filters-api).

## Expected outcome

A controlled MUI component that edits allow and deny rules for one endpoint type and reports a valid-shaped `Filters` value.

## Steps

- Red: write `src/webhooks/FiltersEditor.test.tsx` with the five named tests (Testing Library + user-event, as `Endpoints.test.tsx`). Run `npx vitest run src/webhooks/FiltersEditor.test.tsx`: fails on the missing module.
- Green: write the component. Run the verify: all pass.

## Notes

- Keep values as one string per line in local state so typing a newline does not lose the cursor; report the split list through `onChange`.
- The drop-on-type-change can be an effect keyed on `type` and `fields`, or done by the parent; the test renders the editor, rerenders with a new `type`/`fields`, and expects `onChange` with the dropped rules.
- Follow the MUI imports style of `CreateEndpointDialog.tsx` (per-component default imports).
