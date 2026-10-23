---
title: cluster presets
blockers: [web-ui-cluster-tabs-with-fil]
stage: build
owner: ""
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-23
---

# cluster presets

## Project brief

What: Named ClusterSpec presets (create, copy, edit, delete) with a seeded 1-pod default; scheduling a cluster takes only a preset; live cluster edit is removed; Presets is the first settings category in the hamburger menu
How: A presets table written only by the api, CRUD routes, POST /clusters accepting a preset id and snapshotting its spec at create, the ClusterForm reused as the preset editor, PATCH /clusters retired with retirement tests
Why: Scheduling becomes one choice instead of a long form, repeatable setups are kept, and running clusters never restart under a live spec edit

## Description

User request (2026-10-23), verbatim:

"Live session edit is not needed. Third epic- instead of during scheduling editing, allow to prepare presets, so during scheduling only preset is required. Provide default preset (1 pod). Presets should be copiable, editable, removable, creatable. Hamburger menu on the top left side show all sessions tabs (from top) and all settings from bottom (atm "presets" is the only real setting category showing there)"

Coordinator scope (2026-10-23): a preset is a stored, named ClusterSpec template with create, copy, edit and delete; a seeded default preset has 1 pod; scheduling a cluster takes a preset and nothing else; the ClusterForm becomes the preset editor; live cluster edit (PATCH of a running cluster's spec and the UI edit mode) is removed; a running cluster keeps the spec snapshotted at create when its preset is edited or deleted.

"Session" is an orchestrator cluster, as in web-ui-cluster-tabs-with-fil. Research findings with citations are in research.md next to this README.

## Goals

- Presets: named, stored ClusterSpec templates with create, copy, edit and delete through /api/v1 and the UI.
- A seeded default preset with 1 pod (replicas 1) always exists.
- Scheduling a cluster from the UI takes a preset and nothing else (the slug is generated, overridable); the cluster stores a snapshot of the preset's spec taken at create, plus which preset it came from.
- Editing or deleting a preset never changes a running cluster.
- The ClusterForm becomes the preset editor, prefilled from /meta defaults for a new preset and from the source preset for a copy.
- Live cluster edit is removed: PATCH /api/v1/clusters/{id}, its schema, repository function, client call and the form's edit mode go, pinned by retirement tests.
- The hamburger menu built by web-ui-cluster-tabs-with-fil gets its first settings category, Presets, at the bottom.
- Deployed: image and chart bumped in agents-helmfile, applied, smoke OK.

## Non-goals

- No preset versioning or history beyond the snapshot each cluster keeps.
- No per-user presets (the UI has no users).
- No settings categories other than Presets.
- No change to how a created cluster is reconciled, dispatched or discarded.

## Related epics and order

Order: cluster-form-defaults-and-ga (in progress; it reworks the same form, /meta defaults and PATCH validation), then web-ui-cluster-tabs-with-fil (builds the top bar, the cluster tabs and the hamburger menu with sessions from the top and a settings section at the bottom, and already drops the Edit action from the UI), then this epic (adds Presets as the first settings category, makes New cluster take a preset, retires PATCH), then hive-mode-leadership-handove (its `hive` switch becomes one more preset field).

## Scope

- agent-orchestrator backend:
  - migration: a `presets` table (`id`, `name` unique, `spec` jsonb, `is_default`, `created_at`, `updated_at`), written only by the api; the default preset seeded by the migration with `replicas: 1` and every other field empty, so /meta defaults apply at write time as today; `clusters` gains `preset_id` (nullable, `ON DELETE SET NULL`) and `preset_name` (text, kept after a delete) for provenance.
  - routes: `GET /api/v1/presets`, `POST /api/v1/presets`, `GET|PUT|DELETE /api/v1/presets/{id}`, `POST /api/v1/presets/{id}/copy`; every save runs `validate_spec` against current settings.
  - `POST /api/v1/clusters` accepts `{"preset_id": ..., "slug"?: ...}`: the api re-validates the preset's spec against current settings, fills write-time defaults, and stores the result as the cluster's own spec (the snapshot). Whether the raw `{"slug", "spec"}` body stays for headless callers is open question Q2.
  - retirement: `PATCH /api/v1/clusters/{id}`, `schemas.PatchCluster`, `db/clusters.update_spec`, their tests and the README section are removed; a retirement test pins `PATCH` answering 405.
  - README API sections, OpenAPI and `frontend/src/api/schema.d.ts` regenerated.
- agent-orchestrator frontend:
  - Presets settings page reached from the hamburger menu's settings section: a list with Create, Copy, Edit and Delete; the default preset is marked.
  - ClusterForm becomes PresetForm: `name` instead of `slug`, no create or edit of clusters, prefilled from /meta defaults (`blankValues(meta)`) for a new preset and from the source for a copy; `valuesFromSpec` stays for editing a preset; `pvcSize` is editable again since a preset is not a running cluster.
  - New cluster dialog: preset select (default preselected) and an optional slug; nothing else.
  - removal of `patchCluster` in `api/client.ts` and of the form's `mode: 'edit'` path, with the tests that covered them.
- agents-helmfile: bump, apply, smoke (`scripts/smoke.sh` creates a cluster with POST; it keeps working or moves to a preset, per Q2).

## How (sketch, decided in design)

- Snapshot at create: the cluster row's `spec` is a copy, so editing or deleting a preset never bumps a cluster's `generation`, never re-renders its ConfigMap and never restarts its pods (the pod template carries a config hash annotation, `k8s/render.py:189`, `254`, so any spec change rolls the StatefulSet today).
- Validation twice: at preset save and again at schedule, because settings (models, efforts, image allowlist, caps) can change between the two.
- Defaults: /meta stays the source of defaults. A preset stores only what the user set (empty fields stay empty), the editor shows the /meta defaults as prefilled values, and the write-time fill from cluster-form-defaults-and-ga runs at schedule, so a later change of an `ORCH_DEFAULT_*` setting reaches new clusters made from untouched presets.
- Default preset: seeded once, can be edited and copied, cannot be deleted (409); the API refuses to delete the last preset.

## Decisions (user, 2026-10-23)

- Q2: yes, POST keeps accepting a raw spec for headless callers; exactly one of spec or preset_id.
- Q3: yes, a cluster keeps the spec snapshotted at create; preset edits and deletes do not touch it.
- Q4: yes, PATCH /api/v1/clusters/{id} is retired from the API, not only hidden in the UI.

## Open questions

- Q1: Does "only preset is required" mean the slug is optional too? [recommended: yes, the slug defaults to `<preset name>-<4 random lowercase characters>` and can be overridden in the New cluster dialog]
- Q2: Does `POST /api/v1/clusters` keep accepting a raw `spec` for headless callers (bench, smoke, tatara, magic-trainer)? [recommended: yes, exactly one of `spec` or `preset_id`; the UI always sends a preset; `orch bench` keeps building arm specs inline]
- Q3: What happens to running clusters when their preset is edited or deleted? [recommended: nothing; the cluster keeps the spec snapshotted at create, `preset_id` is set to null on delete and `preset_name` keeps showing where it came from]
- Q4: Is live cluster edit removed from the API as well as the UI? [recommended: yes, PATCH /api/v1/clusters/{id} is retired with a 405 retirement test; changing a running cluster means discarding it and scheduling a new one]
- Q5: Can the default preset be deleted or renamed? [recommended: edited and copied yes, renamed and deleted no; the API also refuses to delete the last preset]
- Q6: What does the seeded default preset contain? [recommended: `replicas: 1` and every other field empty, so /meta defaults (model, effort, resources, PVC size, auto-compact) fill in at schedule]
- Q7: Should a preset store the defaults it was shown, or only what the user changed? [recommended: only what the user set, so later changes of ORCH_DEFAULT_* settings reach new clusters from untouched fields; the editor shows defaults as prefilled values]
- Q8: Does a preset name have rules? [recommended: unique, 1 to 40 characters, letters, digits, spaces, dots, dashes and underscores; the generated slug uses its DNS-1123 form]
- Q9: Should the UI show that a cluster's preset changed after it was created? [recommended: no, the tab shows only `preset_name`; the snapshot is the truth]
- Q10: Is the Presets page a full main-area view or a dialog? [recommended: a full main-area view in place of the active tab content, left with the hamburger menu or a Back button]
- Q11: Should presets be exportable or importable as JSON or YAML? [recommended: no, not in this epic]

## Risks

- Removing PATCH breaks any headless caller that edits clusters; no in-tree caller uses it (`bench/runner.py` and `agents-helmfile/scripts/smoke.sh` only POST and DELETE), but tatara and magic-trainer are named API consumers in the orchestrator README and were not checked.
- The in-progress epic cluster-form-defaults-and-ga adds PATCH-specific validation (re-saving out-of-list models) that this epic deletes; landing order matters, hence the blocker chain.
- The original orchestrator design goal G3 ("Creating, editing and discarding a cluster") is reversed for editing; README and design references need updating.
- A preset valid at save can be invalid at schedule (a model removed from ORCH_MODELS, an image dropped from the allowlist); the New cluster dialog must show the 422 reason and point to the preset.
- Seeding the default preset in a migration must be idempotent and must not overwrite a user-edited default on re-run.

## Rough task list

1. migration: `presets` table with the seeded default, `clusters.preset_id` and `clusters.preset_name`.
2. presets repository and CRUD plus copy routes, validation at save, default and last-preset guards.
3. `POST /api/v1/clusters` with `preset_id`: re-validate, write-time fill, snapshot, generated slug, provenance columns; keep or drop raw `spec` per Q2.
4. retire PATCH: route, schema, repository function, tests, README section; retirement test for 405; OpenAPI and schema.d.ts regen.
5. frontend: PresetForm from ClusterForm (name field, prefill from /meta, copy), removal of the cluster edit path and `patchCluster`.
6. frontend: Presets settings page and its entry in the hamburger menu's settings section.
7. frontend: New cluster dialog with the preset select and optional slug.
8. e2e (kind): schedule from the default preset, edit the preset, the running cluster is unchanged.
9. agents-helmfile: bump, apply, smoke.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
