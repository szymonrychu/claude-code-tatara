---
title: web preset plugin sources
status: todo
repo: agents-web
value: "users paste plugin source links into the preset form, one row per source"
files: [openapi/orchestrator.json, openapi/orchestrator.source, src/api/schema.d.ts, src/sessions/sessionSpecForm.ts, src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx]
verify: "npx vitest run src/presets/PresetForm.test.tsx && npm run build && mise run lint"
depends_on: [web-plugin-source-parser, orch-any-mcp-sources-spec]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web preset plugin sources

## Requirement

User request, verbatim: "In webUI add ability to provide links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox where it can be pasted- multiple plugins can be provided)." Goal G5 (epic README), verbatim: "The agents-web preset form edits the plugin sources: a "+" button adds a one-line text box per source, several sources allowed." Orchestrator design call, verbatim: "agents-web: preset form "any-mcp plugins" section: a "+" button adds a one-line text box per source, each removable, validated against the notation with an inline error, stored as spec.any_mcp_sources." Design D10, verbatim: "a "+" icon button (precedent `src/chat/ScaleControl.tsx`, `@mui/icons-material/Add`) adds a one-line text box, each row removable, an inline error per row, stored as `spec.any_mcp_sources` only when non-empty."

Scope (agents-web, base: the merged state of epic cross-session-messaging-and):
- Sync the orchestrator API: `npm run sync:api -- orchestrator` (with `--from <the epic's agents-orchestrator tree>` when the default `../agents-orchestrator` is not it) after task orch-any-mcp-sources-spec is committed there; this rewrites `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` (generated, never hand-edited).
- `src/sessions/sessionSpecForm.ts`: `FormValues.anyMcpSources: string[]` (blank `[]`), per-row errors in `FormErrors` like `initScripts`, `stateFromPreset` loads `any_mcp_sources`, `validate` uses `pluginSourceError` per row, `toPresetSpec` writes the trimmed rows only when there is at least one.
- `src/presets/PresetForm.tsx`: an "any-mcp plugins" section after the any-mcp config field: one single-line `TextField` per row with an inline error and a remove `IconButton`, and a "+" `IconButton` (`@mui/icons-material/Add`, aria-label "Add any-mcp plugin") that appends an empty row; add the key to the `text()` exclusion type.
- `src/presets/PresetForm.test.tsx`: the tests in the acceptance conditions.
- No text uses the word "cluster" (`src/nomenclature.test.ts`).

## Acceptance conditions

- ac1: the section starts with no rows and saving an untouched preset sends no any_mcp_sources [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins sparse by default']
- ac2: each click on the + button adds a one-line text box, and several pasted sources save as any_mcp_sources in row order, trimmed [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins add rows and save']
- ac3: a row's remove button removes that row, and removing every row saves no any_mcp_sources [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins remove rows']
- ac4: an invalid row shows its inline error and blocks saving, and a preset with sources loads one row per source [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins validate and load']
- ac5: the vendored orchestrator schema has any_mcp_sources and the generated types match it [evidence: command:grep -q '"any_mcp_sources"' openapi/orchestrator.json && npm run check:api]
- ac6: the type check and build pass [evidence: command:npm run build]
- ac7: the whole web suite, including the nomenclature guard, passes [evidence: command:npm test]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
