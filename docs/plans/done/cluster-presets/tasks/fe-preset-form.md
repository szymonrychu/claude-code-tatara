---
title: fe preset form
status: done
repo: agent-orchestrator
value: "presets are edited in the familiar cluster form, which no longer edits running clusters"
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/presets/PresetForm.tsx, frontend/src/clusters/ClusterForm.test.tsx, frontend/src/presets/PresetForm.test.tsx, frontend/src/clusters/clusterSpecForm.ts, frontend/src/clusters/DiscardClusterDialog.test.tsx, frontend/src/api/client.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-new-cluster-dialog]
model: ""
review: ""
verified_head: 9fb81a85a04f4768958d33369b46120fdeaa0b70
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 12
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# fe preset form

## Requirement

Turn the cluster form into the preset editor and remove the cluster edit path (design D2, D5, D6; user Q4, Q5, Q7, Q8), test-first.

- `git mv frontend/src/clusters/ClusterForm.tsx frontend/src/presets/PresetForm.tsx` and rewrite it as `PresetForm({open, preset?, copyOf?, onClose, onSaved})` (part `fe-preset-form`): new (neither prop), edit (`preset`) and copy (`copyOf`, name prefilled `<source name> copy` with the source part cut to fit 40 characters and right-trimmed, saved as a new preset). A "Name" field replaces Slug, checked client-side with the Q8 rules (1 to 40 characters of letters, digits, spaces, dots, dashes, underscores; leading or trailing spaces give an inline error and are never trimmed); the default preset's name is read-only in edit. PVC size is editable and optional in every mode. Save: new and copy call `createPreset`, edit calls `updatePreset`; a 409 or 422 shows in an outlined Alert.
- Sparse saving (Q7) in `frontend/src/clusters/clusterSpecForm.ts`: `FormValues.name` replaces `slug`; a form state built from /meta and a stored preset spec shows the stored value for every stored key and the /meta default (`blankValues(meta)`) for every other field, and records which fields are set (stored keys, plus every field the user changes); clearing a field always means unset: the key is omitted from the stored spec, never stored as null, and numbers like replicas or max_attempts fall back to defaults at schedule; the Model and Effort selects show a stored value that is not in the /meta lists as an extra option labelled `<value> (not available)`; `toPresetSpec(values, setKeys)` returns only the set fields as ClusterSpec keys. `validate(values, meta)` loses its `mode` parameter (name rules instead of slug; PVC size not required). `MAX_SLUG` stays exported (NewClusterDialog uses it). Remove what only the cluster create and edit modes used.
- Retire the cluster edit path: `patchCluster` and the `PatchCluster` alias leave `frontend/src/api/client.ts`; no `mode` prop or `'edit'` path remains.
- Tests: `git mv frontend/src/clusters/ClusterForm.test.tsx frontend/src/presets/PresetForm.test.tsx`, rewritten for the preset editor; its `DiscardClusterDialog` tests (re-read from `ClusterForm.test.tsx` as merged by web-ui-cluster-tabs-with-fil; the Ribbon-created cases are already gone there) move unchanged to a new `frontend/src/clusters/DiscardClusterDialog.test.tsx`. The retirement test runs `git ls-files src/clusters/ClusterForm.tsx src/clusters/ClusterForm.test.tsx` with `node:child_process` from the frontend dir and expects empty output, and reads `src/api/client.ts` to assert it contains neither `patchCluster` nor `PatchCluster`.

## Acceptance conditions

- AC1: a new preset shows every /meta default and saving untouched sends only the name and an empty spec; a changed field is sent [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t new_preset_prefills_defaults_saves_only_set_fields]
- AC2: editing shows stored values and defaults for the rest, keeps stored keys and PUTs through updatePreset [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t edit_round_trips_stored_fields]
- AC3: copy prefills from the source with the name "<source> copy" (source part cut to fit 40 characters and right-trimmed) and creates a new preset [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t copy_prefills_from_source]
- AC4: the default preset's name is read-only, name rules are validated (a leading or trailing space gives an inline error), PVC size is editable [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t name_rules_default_name_and_pvc]
- AC5: a server 409 or 422 is shown in an Alert [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t shows_server_errors]
- AC6: ClusterForm.tsx and ClusterForm.test.tsx are gone from git ls-files and client.ts has no patchCluster or PatchCluster [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t cluster_edit_path_retired]
- AC7: the discard dialog tests pass from their new file [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/DiscardClusterDialog.test.tsx]
- AC8: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]
- AC9: a stored model or effort outside the /meta lists shows as an extra option "<value> (not available)" and round-trips unchanged [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t edit_shows_unavailable_stored_value]
- AC10: clearing a field omits its key from the saved spec and never sends null [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t clearing_a_field_unsets_it]

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`
- `frontend/src/presets/PresetForm.test.tsx`
- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/clusters/DiscardClusterDialog.test.tsx`
- `frontend/src/api/client.ts`

## Interfaces

- `PresetForm({open, preset?: PresetView, copyOf?: PresetView, onClose, onSaved: (preset: PresetView) => void})` in `frontend/src/presets/PresetForm.tsx` (part `fe-preset-form`, consumed by fe-presets-page).
- `clusterSpecForm.ts`: `FormValues.name`, `blankValues(meta)`, the preset form-state builder, `toPresetSpec(values, setKeys)`, `validate(values, meta)`, `MAX_SLUG`.
- `api/client.ts` without `patchCluster` and `PatchCluster`.

## Expected outcome

The form that used to create and edit clusters now creates, edits and copies presets, saving only what the user set, and nothing in the frontend can edit a running cluster.

## Steps

- `git mv` the form and its test, write the preset tests and the retirement test (titles as in the AC refs), move the discard tests to `DiscardClusterDialog.test.tsx`; run `mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx`: fails.
- Rewrite `PresetForm.tsx` and `clusterSpecForm.ts`, drop `patchCluster` and `PatchCluster` from `client.ts`; run the verify command: passes.

## Notes

- Deletion of the edit path is pinned by `cluster_edit_path_retired` (deletion pinned by a retirement test).
- Keep the Model and Effort selects, env rows, any-mcp JSON and resource fields from cluster-form-defaults-and-ga; only the slug, mode and PATCH parts change.
- Clearing a field always means unset (ruling 5): the key is omitted, never stored as null; this replaces the earlier nullable-key choice.
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".
- Builder check ruling 4 (2026-10-23): names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".
- Builder check ruling 5 (2026-10-23): clearing a field always means unset: the key is omitted from the stored spec, never stored as null; numbers like replicas or max_attempts cleared fall back to defaults at schedule.
- Builder check ruling 8 (2026-10-23): re-read ClusterForm.test.tsx as merged by web-ui-cluster-tabs-with-fil and move the discard-dialog tests; the Ribbon-created cases are already gone there.

- 2026-10-23 amended: builder check rulings 2, 4, 5, 8: not-available option, name spaces, clear means unset, discard tests from merged file (AC3, AC4 rewritten, AC9, AC10 added)
