---
title: fe preset form
status: todo
repo: agent-orchestrator
value: "presets are edited in the familiar cluster form, which no longer edits running clusters"
files: [frontend/src/clusters/ClusterForm.tsx, frontend/src/presets/PresetForm.tsx, frontend/src/clusters/ClusterForm.test.tsx, frontend/src/presets/PresetForm.test.tsx, frontend/src/clusters/clusterSpecForm.ts, frontend/src/clusters/DiscardClusterDialog.test.tsx, frontend/src/api/client.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: [fe-new-cluster-dialog]
owns: [fe-preset-form]
uses: [fe-preset-client, orch-presets-api]
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

# fe preset form

## Requirement

Turn the cluster form into the preset editor and remove the cluster edit path (design D2, D5, D6; user Q4, Q5, Q7, Q8), test-first.

- `git mv frontend/src/clusters/ClusterForm.tsx frontend/src/presets/PresetForm.tsx` and rewrite it as `PresetForm({open, preset?, copyOf?, onClose, onSaved})` (part `fe-preset-form`): new (neither prop), edit (`preset`) and copy (`copyOf`, name prefilled `<source name> copy`, saved as a new preset). A "Name" field replaces Slug, checked client-side with the Q8 rules (1 to 40 characters of letters, digits, spaces, dots, dashes, underscores); the default preset's name is read-only in edit. PVC size is editable and optional in every mode. Save: new and copy call `createPreset`, edit calls `updatePreset`; a 409 or 422 shows in an outlined Alert.
- Sparse saving (Q7) in `frontend/src/clusters/clusterSpecForm.ts`: `FormValues.name` replaces `slug`; a form state built from /meta and a stored preset spec shows the stored value for every stored key and the /meta default (`blankValues(meta)`) for every other field, and records which fields are set (stored keys, plus every field the user changes); `toPresetSpec(values, setKeys)` returns only the set fields as ClusterSpec keys. `validate(values, meta)` loses its `mode` parameter (name rules instead of slug; PVC size not required). `MAX_SLUG` stays exported (NewClusterDialog uses it). Remove what only the cluster create and edit modes used.
- Retire the cluster edit path: `patchCluster` and the `PatchCluster` alias leave `frontend/src/api/client.ts`; no `mode` prop or `'edit'` path remains.
- Tests: `git mv frontend/src/clusters/ClusterForm.test.tsx frontend/src/presets/PresetForm.test.tsx`, rewritten for the preset editor; its `DiscardClusterDialog` tests move unchanged to a new `frontend/src/clusters/DiscardClusterDialog.test.tsx`. The retirement test runs `git ls-files src/clusters/ClusterForm.tsx src/clusters/ClusterForm.test.tsx` with `node:child_process` from the frontend dir and expects empty output, and reads `src/api/client.ts` to assert it contains neither `patchCluster` nor `PatchCluster`.

## Acceptance conditions

- AC1: a new preset shows every /meta default and saving untouched sends only the name and an empty spec; a changed field is sent [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t new_preset_prefills_defaults_saves_only_set_fields]
- AC2: editing shows stored values and defaults for the rest, keeps stored keys and PUTs through updatePreset [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t edit_round_trips_stored_fields]
- AC3: copy prefills from the source with the name "<source> copy" and creates a new preset [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t copy_prefills_from_source]
- AC4: the default preset's name is read-only, name rules are validated, PVC size is editable [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t name_rules_default_name_and_pvc]
- AC5: a server 409 or 422 is shown in an Alert [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t shows_server_errors]
- AC6: ClusterForm.tsx and ClusterForm.test.tsx are gone from git ls-files and client.ts has no patchCluster or PatchCluster [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/presets/PresetForm.test.tsx -t cluster_edit_path_retired]
- AC7: the discard dialog tests pass from their new file [evidence: command:cd frontend && mise x node@24.20.0 -- npx vitest run src/clusters/DiscardClusterDialog.test.tsx]
- AC8: tests, design rules, lint and build pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx src/clusters/DiscardClusterDialog.test.tsx src/layout/designRules.test.ts && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build]

## Files

- `frontend/src/clusters/ClusterForm.tsx`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/clusters/ClusterForm.test.tsx`
- `frontend/src/presets/PresetForm.test.tsx`
- `frontend/src/clusters/clusterSpecForm.ts`
- `frontend/src/clusters/DiscardClusterDialog.test.tsx`
- `frontend/src/api/client.ts`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
