---
title: cluster presets
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-23
owner: Claude
rung: 1
---

# cluster presets

## What and why

What: Named ClusterSpec presets (create, copy, edit, delete) with a seeded 1-pod default; scheduling a cluster takes only a preset; live cluster edit is removed; Presets is the first settings category in the hamburger menu
How: A presets table written only by the api, CRUD routes, POST /clusters accepting a preset id and snapshotting its spec at create, the ClusterForm reused as the preset editor, PATCH /clusters retired with retirement tests
Why: Scheduling becomes one choice instead of a long form, repeatable setups are kept, and running clusters never restart under a live spec edit

User request (2026-10-23), verbatim:

"Live session edit is not needed. Third epic- instead of during scheduling editing, allow to prepare presets, so during scheduling only preset is required. Provide default preset (1 pod). Presets should be copiable, editable, removable, creatable. Hamburger menu on the top left side show all sessions tabs (from top) and all settings from bottom (atm "presets" is the only real setting category showing there)"

Coordinator scope (2026-10-23): a preset is a stored, named ClusterSpec template with create, copy, edit and delete; a seeded default preset has 1 pod; scheduling a cluster takes a preset and nothing else; the ClusterForm becomes the preset editor; live cluster edit (PATCH of a running cluster's spec and the UI edit mode) is removed; a running cluster keeps the spec snapshotted at create when its preset is edited or deleted.

"Session" is an orchestrator cluster, as in web-ui-cluster-tabs-with-fil. Research findings with citations are in research.md next to this README.

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: Presets: named, stored ClusterSpec templates with create, copy, edit and delete through /api/v1 and the UI.
- 1.2: A seeded default preset with 1 pod (replicas 1) always exists.
- 1.3: Scheduling a cluster from the UI takes a preset and nothing else (the slug is generated, overridable); the cluster stores a snapshot of the preset's spec taken at create, plus which preset it came from.
- 1.4: Editing or deleting a preset never changes a running cluster.
- 1.5: The ClusterForm becomes the preset editor, prefilled from /meta defaults for a new preset and from the source preset for a copy.
- 1.6: Live cluster edit is removed: PATCH /api/v1/clusters/{id}, its schema, repository function, client call and the form's edit mode go, pinned by retirement tests.
- 1.7: The hamburger menu built by web-ui-cluster-tabs-with-fil gets its first settings category, Presets, at the bottom.
- 1.8: Deployed: image and chart bumped in agents-helmfile, applied, smoke OK.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No preset versioning or history beyond the snapshot each cluster keeps.
- No per-user presets (the UI has no users).
- No settings categories other than Presets.
- No change to how a created cluster is reconciled, dispatched or discarded.

## Design

Migrated from the epic format; the design sections without a plan.md heading are under Migrated notes.

## Decisions

### D1: Data model and seed
Migration `0002_presets.sql` adds `presets` (`id` uuid, `name` text 1 to 40 chars, `spec` jsonb, `is_default` boolean, `created_at`, `updated_at`) with a unique index on `lower(name)` and a partial unique index allowing one default, seeds `Default` with the fixed id `00000000-0000-0000-0000-000000000001` and `{"replicas": 1}` through `INSERT ... ON CONFLICT DO NOTHING`, and adds `clusters.preset_id` (`REFERENCES presets ON DELETE SET NULL`) and `clusters.preset_name`. Every statement is idempotent (`IF NOT EXISTS`), so re-applying never fails and never overwrites an edited default. Alternatives: seeding in the api at startup (rejected: a second writer path and a race between api replicas); a versioned preset table (rejected: Non-goals). Names are unique case-insensitively and the seed name is `Default` (my call). Serves approvals B, D.

### D2: A preset stores only what was set
`POST` and `PUT` take `{"name", "spec"}` where `spec` is a ClusterSpec; the api stores `spec.model_dump(mode="json", exclude_unset=True)`, so only the keys the caller sent are kept, and `PresetView.spec` returns exactly the stored object (a subset of ClusterSpec keys, typed `dict[str, Any]` in OpenAPI). Save-time validation runs the public `check_spec` (validate, then write-time fill) and discards the filled result; the fill runs again at schedule. PUT passes the stored preset spec as `stored`, so a stored model, effort or image no longer in the settings lists is accepted only when unchanged (changing to an unknown value is 422); POST and scheduling validate fully. Alternative: storing the filled spec (rejected: freezes defaults, Q7). The `dict` response type is my call. Serves approval A.

### D3: Preset routes and errors
`GET /presets` (default first, then by name, case-insensitive), `POST /presets` (201), `GET /presets/{id}`, `PUT /presets/{id}` (full replace of name and spec), `DELETE /presets/{id}` (204), `POST /presets/{id}/copy` (201, optional body `{"name"}`; without it the name is `<source> copy`, then `<source> copy 2`, `copy 3` and so on, the source part cut to fit 40 characters and right-trimmed before ` copy`; names with leading or trailing spaces are rejected with 422 and the API never trims; the stored spec is copied verbatim and the copy is never default). Errors: 404 `not_found`, 409 `conflict` (name taken), 409 `preset_default` (rename or delete of the default), 409 `last_preset`, 422 `invalid_request`. The UI Copy action opens the editor prefilled from the source and creates on save, so Cancel leaves nothing behind; the copy route serves headless callers (my call). Serves approvals A, B.

### D4: Create from a preset and the snapshot
`CreateCluster` becomes `{"slug"?, "spec"?, "preset_id"?}` with `extra="forbid"`: exactly one of `spec` and `preset_id` (422 otherwise); with `spec` the slug stays required (my call). With `preset_id`, inside the existing creation transaction after the advisory lock, the api reads the preset `FOR SHARE` (404 `not_found` when missing), runs `check_spec` on it against current settings, with no `stored` (a 422 message starts `preset '<name>': `), fills `replicas` from `settings.default_replicas` when the preset leaves it unset (preset path only; the raw-spec path is unchanged), and inserts the filled spec as the cluster's own spec with `preset_id` and `preset_name`. Without a slug it uses `generated_slug(preset.name)`, retried with a fresh suffix up to 5 times on a slug clash, and the 5th clash answers 409 `conflict`, never 500 (my call); an explicit slug clash stays 409 `conflict`. `ClusterView` gains `preset_id` and `preset_name`. Serves approvals C, D.

### D5: PATCH retirement and dead code
Removed: `api/clusters.py:patch_cluster`, `schemas.PatchCluster`, `db/clusters.py:update_spec` and `ClusterDeleting` (its only user), the PATCH tests, the README `### PATCH` section; `cluster_deleting` stays (messages and checks still answer it); the `stored` parameter of `spec.validate_spec` and `check_spec` stays too, because the preset PUT uses it (ruling 2). `PATCH /api/v1/clusters/{id}` then answers 405 because GET and DELETE share the path. Frontend: `patchCluster`, the `PatchCluster` alias, `mode: 'edit'` and `ClusterForm.tsx` go. The frontend retirement lands before the backend one so `npm run build` stays green when `schema.d.ts` loses `PatchCluster`. Serves approval E.

### D6: Frontend forms
`NewClusterDialog` (new): a preset `Select` with the default preselected, an optional Slug field (checked client-side only against `MAX_SLUG`; the server 422 is shown otherwise), Create posts `{preset_id, slug?}`; errors in an outlined Alert. `PresetForm` (git mv of `ClusterForm.tsx`): new, edit and copy modes, a Name field instead of Slug, PVC size editable and optional; fields not stored in the preset show the /meta default (`blankValues(meta)`) and are saved only once the user changes them (set-field tracking in `clusterSpecForm.ts`, `toPresetSpec(values, setKeys)`). The default preset's name is read-only. `clusterSpecForm.ts` stays at its path (my call). Serves approvals A, C.

### D7: Presets page and menu entry
`PresetsPage` is a full main-area view (Q10) opened from the `settingsCategories` entry `{id: 'presets', label: 'Presets'}` passed through `TopBar` to `SessionsMenu` (cross-epic contract `orch-settings-menu`). App holds a `view` state (`cluster` or `presets`), no router (my call); Back or choosing a session returns to the cluster view. The page lists presets with the default marked, New preset, and per-row Edit, Copy and Delete (no Delete on the default; Delete confirms through `ConfirmDialog`). Serves approval F.

### D8: API-only end-to-end proof
`tests/e2e/test_e2e_kind.py` schedules its shared 2-replica cluster from a preset created through the API (explicit `SLUG`, so the kubectl label lookups stay), then proves on the live cluster: a preset PUT leaves the cluster's spec and generation unchanged, a preset DELETE nulls `preset_id` and keeps `preset_name`, copy works, the default preset schedules with a generated slug (that extra cluster is discarded at once), and PATCH answers 405. The ASGI tests per route are the in-process API-only proof. Serves approval G.

### D9: Deploy pin
agents-helmfile pins the agent-orchestrator chart `0.1.0-main.<sha7>` and image `<sha7>` of this epic's merge, like `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`; the sha is supplied with `ticket.py amend` after the merge, until then the task reports `blocked`; the task is excluded from the build run and runs after the orchestrator PR merges (ruling 10). The pin test reads `helmfile.yaml.gotmpl` as text so it runs without the chart pull. `helmfile apply` and `mise run smoke` are run by the user. Serves approval H.

### D10: Headless parity
Headless parity: every UI capability of this epic is backed by a documented public API (OpenAPI, README) that a client without the UI can drive end to end, and each feature gets an API-only e2e test (2026-10-23) (user decision)

### D11: Q1 optional generated slug
Q1: the slug is optional; it defaults to <preset name DNS-1123 form>-<4 random lowercase letters> within SLUG_MAX 40, avoiding the reserved orchestrator* prefix, and is overridable in the New cluster dialog (2026-10-23) (user decision)

### D12: Q2 raw spec kept, exactly one of spec or preset_id
Q2: POST /api/v1/clusters keeps accepting a raw spec for headless callers; exactly one of spec or preset_id (2026-10-23) (user decision)

### D13: Q3 snapshot at create
Q3: a cluster keeps the spec snapshotted at create; preset edits and deletes do not touch it (2026-10-23) (user decision)

### D14: Q4 PATCH retired from the API
Q4: PATCH /api/v1/clusters/{id} is retired from the API, not only hidden in the UI, with a 405 retirement test (2026-10-23) (user decision)

### D15: Q5 default preset guards
Q5: the default preset can be edited and copied, not renamed or deleted (409); the API refuses to delete the last preset (2026-10-23) (user decision)

### D16: Q6 seeded default content
Q6: the seeded default preset holds replicas 1 and every other field empty (2026-10-23) (user decision)

### D17: Q7 sparse preset storage
Q7: a preset stores only what the user set; the editor shows /meta defaults as prefilled values (2026-10-23) (user decision)

### D18: Q8 preset name rules
Q8: preset names are unique, 1 to 40 characters of letters, digits, spaces, dots, dashes and underscores (2026-10-23) (user decision)

### D19: Q9 tab shows preset_name only
Q9: the UI does not show that a cluster's preset changed after create; the tab shows only preset_name (2026-10-23) (user decision)

### D20: Q10 full main-area Presets view
Q10: the Presets page is a full main-area view with a Back button (2026-10-23) (user decision)

### D21: Q11 no import or export
Q11: no preset import or export in this epic (2026-10-23) (user decision)

### D22: N2 additive-only exception and dead code
N2: the README additive-only rule for /api/v1 gets a documented exception for the PATCH retirement in README and the component MEMORY.md with date and why; now-dead code (update_spec, ClusterDeleting) is removed (the stored parameter of validate_spec stays, builder check ruling 2) and tests/test_migrations is updated for 0002 and the table set (2026-10-23) (user decision)

## Open questions

- Q1: Does "only preset is required" mean the slug is optional too? [answer: yes, the slug is optional: it defaults to <preset name DNS-1123 form>-<4 random lowercase letters>, within SLUG_MAX 40 and avoiding the reserved orchestrator* prefix, and can be overridden in the New cluster dialog (user, 2026-10-23)]
- Q2: Does `POST /api/v1/clusters` keep accepting a raw `spec` for headless callers (bench, smoke, tatara, magic-trainer)? [answer: yes, POST /api/v1/clusters keeps accepting a raw spec; exactly one of spec or preset_id (user, 2026-10-23)]
- Q3: What happens to running clusters when their preset is edited or deleted? [answer: yes, a cluster keeps the spec snapshotted at create; preset edits and deletes do not touch it, preset_id becomes null on delete and preset_name is kept (user, 2026-10-23)]
- Q4: Is live cluster edit removed from the API as well as the UI? [answer: yes, PATCH /api/v1/clusters/{id} is retired from the API with a 405 retirement test (user, 2026-10-23)]
- Q5: Can the default preset be deleted or renamed? [answer: the default preset can be edited and copied, not renamed or deleted (409); the API refuses to delete the last preset (user, 2026-10-23)]
- Q6: What does the seeded default preset contain? [answer: replicas 1 and every other field empty (user, 2026-10-23)]
- Q7: Should a preset store the defaults it was shown, or only what the user changed? [answer: a preset stores only what the user set; the editor shows /meta defaults as prefilled values (user, 2026-10-23)]
- Q8: Does a preset name have rules? [answer: names unique, 1 to 40 characters, letters, digits, spaces, dots, dashes and underscores (user, 2026-10-23)]
- Q9: Should the UI show that a cluster's preset changed after it was created? [answer: no; the tab shows only preset_name and the snapshot is the truth (user, 2026-10-23)]
- Q10: Is the Presets page a full main-area view or a dialog? [answer: a full main-area view with a Back button (user, 2026-10-23)]
- Q11: Should presets be exportable or importable as JSON or YAML? [answer: no import or export in this epic (user, 2026-10-23)]
- Q12: Does the README rule that /api/v1 is additive only get a documented exception for the PATCH retirement, with the now-dead code removed? [answer: yes, documented exception in README and MEMORY.md with date and why; dead code (ClusterDeleting; the stored parameter of validate_spec stays, builder check ruling 2) removed and tests/test_migrations updated (user, 2026-10-23)]

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal | ran (discovery/reuse.md of web-ui-cluster-tabs-with-fil, lane 4) | public `_check_spec`, `arm_slug` sanitising into `spec.py`, `blankValues`/`valuesFromSpec` reuse, idempotent seed (reuse.md Plan inputs) | a second slug sanitiser |
| research-code-external | ran (research.md section 3) | snapshot at create keeps the EC2 launch template property that a template change never touches running instances (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/manage-launch-template-versions.html) | versioned presets (Kubernetes controller style roll on template change is exactly the restart to avoid) |
| research-docs | ran (research.md section 4) | MUI temporary Drawer for navigation (https://mui.com/material-ui/react-drawer/), no new dependency | none |
| research-papers | skipped: CRUD and UI work with no algorithmic core | none | none |

### Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery/reuse.md reuse | validate_spec, fill_resource_defaults, validate_slug - O/spec.py | preset-routes, create-cluster-from-preset |
| discovery/reuse.md reuse | run_migrations - O/db/migrate.py | presets-table-and-repo |
| discovery/reuse.md reuse | clusterSpecForm helpers - F/clusters/clusterSpecForm.ts:blankValues | fe-preset-form |
| discovery/reuse.md reuse | ConfirmDialog - F/layout/ConfirmDialog.tsx | fe-presets-page |
| discovery/reuse.md reuse | useClusters, sortedAgents - F/ribbon/useClusters.ts | fe-new-cluster-dialog |
| discovery/reuse.md reuse | PtyProcess, Ring, BASE_ENV, safe_write_files, LimitsConfig, require_auth, tokens_for, pod_url, WrapperClient, SourceAllowlist, Settings CsvList, openStream, ChatView, FakeWrapper | rejected: web-ui-cluster-tabs-with-fil parts, not used by presets |
| discovery/reuse.md do-not-build | WebSocket timeouts, chart wiring for ORCH_* settings, separate PTY, token scheme, WebSocket allowlist | rejected: web-ui-cluster-tabs-with-fil items; presets add no setting |
| discovery/reuse.md fix-as-ac | `_check_spec` private | preset-routes |
| discovery/reuse.md fix-as-ac | PATCH retirement leftovers | retire-cluster-patch-route, retire-spec-update-repo, fe-preset-form |
| discovery/reuse.md fix-as-ac | default preset seed idempotent | presets-table-and-repo |
| discovery/reuse.md fix-as-ac | require_auth typed to Request, ASGITransport cannot test WebSocket, websockets undeclared | rejected: web-ui-cluster-tabs-with-fil items |
| discovery/reuse.md ideas | adopted: arm_slug sanitising for preset-name slugs | slug-from-name |
| discovery/reuse.md ideas | SSE heartbeat cadence, inotify, storage.ts | rejected: web-ui-cluster-tabs-with-fil items |
| discovery/orchestrator-backend.md | B: `0002_presets.sql`, `db/presets.py`, `Cluster` preset fields, exactly one of spec or preset_id, slug generator within 40 avoiding `orchestrator*` | presets-table-and-repo, create-cluster-from-preset, slug-from-name |
| discovery/orchestrator-backend.md | B: delete patch_cluster, PatchCluster, update_spec, ClusterDeleting; 405 test; README versioning sentence; test_migrations versions and TABLES | retire-cluster-patch-route, retire-spec-update-repo, presets-table-and-repo |
| discovery/orchestrator-backend.md | regen openapi.json then `npm run gen:api` | preset-routes, create-cluster-from-preset, retire-cluster-patch-route |
| discovery/frontend.md | ClusterForm edit tests, patchCluster, PatchCluster alias, mode retired | fe-preset-form |
| discovery/frontend.md | verify `npm run lint && npm test && npm run build && npm run check:api` with node 24 | fe-new-cluster-dialog, fe-preset-form, fe-presets-page |
| research.md 1 | PATCH callers: UI and tests only; bench and smoke only POST and DELETE | retire-cluster-patch-route |
| research.md 2 | `valuesFromSpec` edits a preset, `blankValues(meta)` is the new-preset form, PVC editable again | fe-preset-form |
| research.md 3 | validation at save and again at schedule | preset-routes, create-cluster-from-preset |
| research.md 4 | Presets as the first settings category in the drawer | fe-presets-page |

## Irreversible operations

- Migration `0002_presets.sql` on the live database when the user applies the release: additive only (new table, two nullable columns, one seed row); no data is deleted. Covered by approval H and the idempotency test in presets-table-and-repo.
- Removal of `PATCH /api/v1/clusters/{cluster_id}` from the public API: a breaking change for any external caller, covered by approval E and the README exception.

## Migrated notes

### README.md: Related epics and order

Order: cluster-form-defaults-and-ga (in progress; it reworks the same form, /meta defaults and PATCH validation), then web-ui-cluster-tabs-with-fil (builds the top bar, the cluster tabs and the hamburger menu with sessions from the top and a settings section at the bottom, and already drops the Edit action from the UI), then this epic (adds Presets as the first settings category, makes New cluster take a preset, retires PATCH), then hive-mode-leadership-handove (its `hive` switch becomes one more preset field).

### README.md: Scope

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

### README.md: How (sketch, decided in design)

- Snapshot at create: the cluster row's `spec` is a copy, so editing or deleting a preset never bumps a cluster's `generation`, never re-renders its ConfigMap and never restarts its pods (the pod template carries a config hash annotation, `k8s/render.py:189`, `254`, so any spec change rolls the StatefulSet today).
- Validation twice: at preset save and again at schedule, because settings (models, efforts, image allowlist, caps) can change between the two.
- Defaults: /meta stays the source of defaults. A preset stores only what the user set (empty fields stay empty), the editor shows the /meta defaults as prefilled values, and the write-time fill from cluster-form-defaults-and-ga runs at schedule, so a later change of an `ORCH_DEFAULT_*` setting reaches new clusters made from untouched presets.
- Default preset: seeded once, can be edited and copied, cannot be deleted (409); the API refuses to delete the last preset.

### README.md: Decisions (user, 2026-10-23)

- Headless parity (user, 2026-10-23): everything in this epic must also work in headless mode. Every UI capability is backed by a documented public API (OpenAPI, README) that a client without the UI can drive end to end, and each feature gets an API-only e2e test.
- Q2: yes, POST keeps accepting a raw spec for headless callers; exactly one of spec or preset_id.
- Q3: yes, a cluster keeps the spec snapshotted at create; preset edits and deletes do not touch it.
- Q4: yes, PATCH /api/v1/clusters/{id} is retired from the API, not only hidden in the UI.

### README.md: Open questions

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

### README.md: Risks

- Removing PATCH breaks any headless caller that edits clusters; no in-tree caller uses it (`bench/runner.py` and `agents-helmfile/scripts/smoke.sh` only POST and DELETE), but tatara and magic-trainer are named API consumers in the orchestrator README and were not checked.
- The in-progress epic cluster-form-defaults-and-ga adds PATCH-specific validation (re-saving out-of-list models) that this epic deletes; landing order matters, hence the blocker chain.
- The original orchestrator design goal G3 ("Creating, editing and discarding a cluster") is reversed for editing; README and design references need updating.
- A preset valid at save can be invalid at schedule (a model removed from ORCH_MODELS, an image dropped from the allowlist); the New cluster dialog must show the 422 reason and point to the preset.
- Seeding the default preset in a migration must be idempotent and must not overwrite a user-edited default on re-run.

### README.md: Rough task list

1. migration: `presets` table with the seeded default, `clusters.preset_id` and `clusters.preset_name`.
2. presets repository and CRUD plus copy routes, validation at save, default and last-preset guards.
3. `POST /api/v1/clusters` with `preset_id`: re-validate, write-time fill, snapshot, generated slug, provenance columns; keep or drop raw `spec` per Q2.
4. retire PATCH: route, schema, repository function, tests, README section; retirement test for 405; OpenAPI and schema.d.ts regen.
5. frontend: PresetForm from ClusterForm (name field, prefill from /meta, copy), removal of the cluster edit path and `patchCluster`.
6. frontend: Presets settings page and its entry in the hamburger menu's settings section.
7. frontend: New cluster dialog with the preset select and optional slug.
8. e2e (kind): schedule from the default preset, edit the preset, the running cluster is unchanged.
9. agents-helmfile: bump, apply, smoke.

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-24)

Whole-diff review (sonnet): no blockers or majors; 3 minor findings fixed in presets-review-fixes (upgrade-path migration test, PresetForm early edits, README writers table).
Scope audit (sonnet): every approved item A-G landed, kind e2e collected (17), no gaps.
Security review: skipped, no authz, secrets, ingress or privilege surface in the diff; migration is additive and idempotent.
Full suite on integration head: lint clean, 524 passed (+ test_frontend_schema_matches_openapi passes once node_modules exist), frontend 183 passed, build and check:api clean.
CI on agent-orchestrator#5 caught a real product bug (PATCH answered 404 instead of 405 behind the SPA mount in the real image); fixed test-first in spa-method-not-allowed, full suite 528 passed, PR CI all green incl. kind e2e. Merged: agent-orchestrator#5 (9ab0d60); agents-helmfile#7 pin open.

### design.md: Summary

The agent-orchestrator gains named cluster presets: stored, sparse ClusterSpec templates with create, copy, edit and delete through `/api/v1/presets` and a Presets settings page reached from the hamburger menu built by web-ui-cluster-tabs-with-fil. A migration seeds a `Default` preset (`replicas: 1`). Scheduling a cluster takes a preset (and an optional slug, generated from the preset name when absent); the api re-validates the preset against current settings, fills the write-time defaults and stores the result as the cluster's own spec, so a preset edit or delete never touches a running cluster. Live cluster edit is retired: `PATCH /api/v1/clusters/{cluster_id}`, its schema, repository function, client call and the form's edit mode are removed and pinned by retirement tests. `POST /api/v1/clusters` keeps a raw `spec` body for headless callers. The epic ends with the agents-helmfile pin; apply and smoke are run by the user.

### design.md: Intent and why

The user wants scheduling to be one choice instead of a long form, repeatable setups kept by name, and no live session edit (user request 2026-10-23, README Description). Live edit rolls every agent pod today because the pod template carries a hash of the rendered config (`k8s/render.py:189`, `:254`), ending running turns; snapshot-at-create removes that failure mode while presets keep the convenience.

### design.md: Goals

- `GET|POST /api/v1/presets`, `GET|PUT|DELETE /api/v1/presets/{preset_id}` and `POST /api/v1/presets/{preset_id}/copy` exist, are documented in README and OpenAPI, and validate every save against current settings.
- A `Default` preset with `{"replicas": 1}` exists after migration; it can be edited and copied, never renamed or deleted (409 `preset_default`); deleting the last preset is 409 `last_preset`.
- `POST /api/v1/clusters` accepts `{"preset_id", "slug"?}` or `{"slug", "spec"}`, exactly one of `spec` and `preset_id`; the preset path stores a filled snapshot plus `preset_id` and `preset_name`.
- Editing or deleting a preset never changes a cluster's `spec` or `generation`; a delete sets the cluster's `preset_id` to null and keeps `preset_name`.
- The New cluster dialog shows a preset select (default preselected) and an optional slug, nothing else; the PresetForm (from ClusterForm) edits presets with /meta defaults shown for unset fields and saves only what the user set.
- PATCH is gone from the API (405, retirement test), and `patchCluster`, `PatchCluster`, `update_spec`, `ClusterDeleting` and `ClusterForm.tsx` are gone from the code (the `stored` parameter of `validate_spec` and `check_spec` stays for the preset PUT, ruling 2).
- The hamburger menu's Settings section lists Presets, which opens a full main-area page with a Back button.
- Every capability has an API-only test, and the kind e2e drives presets end to end through `/api/v1`.
- agents-helmfile pins the merged orchestrator chart and image.

### design.md: Non-goals

- No preset versioning or history beyond each cluster's snapshot; no per-user presets; no import or export (Q11); no settings category other than Presets.
- No change to reconcile, dispatch or discard of a created cluster.
- No change to `scripts/smoke.sh`: it keeps creating its cluster with a raw spec (Q2).
- No re-plan of web-ui-cluster-tabs-with-fil parts (top bar, SessionsMenu, retire ribbon, workspace proxy, its deploy pin); this epic builds on them after that epic merges.

### design.md: Anti-goals

- A preset edit or delete that bumps a running cluster's generation or restarts its pods.
- Freezing /meta defaults into presets, so a later `ORCH_DEFAULT_*` change no longer reaches untouched fields.
- A red main in any repo between tasks: the frontend stops calling PATCH before the backend removes it.
- Breaking headless callers beyond the documented exception (PATCH removal, and a create body with neither `spec` nor `preset_id`).

### design.md: Constraints

- Python only except the TypeScript frontend; single writer per table: `presets` is written only by the api (README `### Single-writer interpretation`), and the `clusters.preset_id` `ON DELETE SET NULL` cascade is an api write too.
- Test-first; retirement tests assert on `git ls-files <path>` for removed files and on module attributes or signatures for removed symbols.
- Orchestrator `tests/test_readme_api.py` requires a README `### \`METHOD /api/v1...\`` heading per route and `openapi.json` plus `frontend/src/api/schema.d.ts` regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`, then `npm --prefix frontend run gen:api`); `test_frontend_schema_matches_openapi` needs `frontend/node_modules`, so verifies run `npm --prefix frontend ci` first.
- `frontend/src/layout/designRules.ts`: no colour literals, no decorative Unicode, no `title=` on buttons, fontWeight 400 or 500.
- Verify commands in this container: orchestrator `uv run pytest -q -p no:cacheprovider <files>` (testcontainers, dockerd running) plus `uv run ruff check . && uv run ruff format --check .`; frontend `mise x node@24.20.0 -- npm --prefix frontend ci`, then `test -- <files>`, `run lint`, `run build`, `run check:api`; the kind e2e is verified by collection (`-m e2e --collect-only`) and runs in the PR CI `e2e` job; agents-helmfile tests that build the helmfile pull charts over the network and fail here, so the pin verify deselects them.
- Order: this epic runs after web-ui-cluster-tabs-with-fil is merged (README blockers) and edits its `App.tsx`, `App.test.tsx`, `layout/TopBar.tsx` and `layout/TopBar.test.tsx`.

### design.md: Decision coverage

| Decision | Tasks |
|---|---|
| D1 Data model and seed | presets-table-and-repo |
| D2 A preset stores only what was set | preset-routes, fe-preset-form |
| D3 Preset routes and errors | preset-routes |
| D4 Create from a preset and the snapshot | slug-from-name, create-cluster-from-preset |
| D5 PATCH retirement and dead code | retire-cluster-patch-route, retire-spec-update-repo, fe-preset-form |
| D6 Frontend forms | fe-new-cluster-dialog, fe-preset-form |
| D7 Presets page and menu entry | fe-presets-page |
| D8 API-only end-to-end proof | kind-e2e-presets |
| D9 Deploy pin | deploy-pin-presets |
| D10 Headless parity | preset-routes, create-cluster-from-preset, kind-e2e-presets |
| D11 Q1 optional generated slug | slug-from-name, create-cluster-from-preset, fe-new-cluster-dialog |
| D12 Q2 raw spec kept, exactly one of spec or preset_id | create-cluster-from-preset |
| D13 Q3 snapshot at create | create-cluster-from-preset, kind-e2e-presets |
| D14 Q4 PATCH retired from the API | retire-cluster-patch-route, fe-preset-form |
| D15 Q5 default preset guards | presets-table-and-repo, preset-routes, fe-presets-page |
| D16 Q6 seeded default content | presets-table-and-repo |
| D17 Q7 sparse preset storage | preset-routes, fe-preset-form |
| D18 Q8 preset name rules | presets-table-and-repo, preset-routes, fe-preset-form |
| D19 Q9 tab shows preset_name only | fe-new-cluster-dialog |
| D20 Q10 full main-area Presets view | fe-presets-page |
| D21 Q11 no import or export | preset-routes |
| D22 N2 additive-only exception and dead code | retire-cluster-patch-route, retire-spec-update-repo, presets-table-and-repo |

### design.md: Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `slugify-helper` | slug-from-name | create-cluster-from-preset | `code/agent-orchestrator/src/agent_orchestrator/spec.py` |
| `presets-repo` | presets-table-and-repo | preset-routes, create-cluster-from-preset | `code/agent-orchestrator/src/agent_orchestrator/db/presets.py` |
| `check-spec-public` | preset-routes | create-cluster-from-preset, retire-cluster-patch-route | `code/agent-orchestrator/src/agent_orchestrator/api/clusters.py` |
| `orch-presets-api` | preset-routes | fe-new-cluster-dialog, fe-preset-form, fe-presets-page, kind-e2e-presets | `code/agent-orchestrator/README.md` |
| `orch-cluster-create-api` | create-cluster-from-preset | fe-new-cluster-dialog, kind-e2e-presets | `code/agent-orchestrator/README.md` |
| `fe-preset-client` | fe-new-cluster-dialog | fe-preset-form, fe-presets-page | `code/agent-orchestrator/frontend/src/api/client.ts` |
| `fe-preset-form` | fe-preset-form | fe-presets-page | `code/agent-orchestrator/frontend/src/presets/PresetForm.tsx` |

Cross-epic contracts in `docs/plans/contracts.json`: this epic consumes `orch-settings-menu` (owner web-ui-cluster-tabs-with-fil, `SessionsMenu` `settingsCategories`) in fe-presets-page, and owns `orch-presets-api` and `orch-cluster-create-api` (consumer agents-helmfile: `scripts/smoke.sh` keeps the raw spec body).

### design.md: Review focus

- Snapshot integrity: no code path writes `clusters.spec` or `generation` from a preset change; the create transaction reads the preset `FOR SHARE` under the advisory lock.
- Sparse storage: `exclude_unset` survives the round trip (nested `resources` included), and the UI saves only set fields.
- Migration idempotency and the one-default index; `test_migrations` versions, tables and the concurrent-migrate count.
- Retirement completeness: no `update_spec`, `ClusterDeleting`, `PatchCluster`, `patchCluster` or `mode="edit"` left anywhere, the README versioning exception is explicit, PATCH answers 405.
- The frontend build stays green at every merge point (client.ts loses `PatchCluster` before `schema.d.ts` does).

### design.md: Left to the builder

- Internal helper names inside `db/presets.py` and `api/presets.py` beyond the interfaces named in the tasks.
- How the PresetForm marks a field as set (a `Set` of keys or per-field flags), as long as unchanged defaults are not saved and stored fields round-trip.
- The visual layout of the Presets page within the design rules.

#### Builder check rulings (my call)

1. (create-cluster-from-preset) on the preset path only, the schedule-time fill sets replicas from settings.default_replicas when the preset leaves replicas unset (alongside the existing write-time fills). The raw-spec POST path is unchanged. The seeded Default stores replicas 1 explicitly, so it schedules 1.
2. (preset-routes, fe-preset-form, retire-spec-update-repo) PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".
3. (create-cluster-from-preset) after the 5th generated-slug clash the API answers 409 conflict (the existing conflict code), never 500.
4. (presets-table-and-repo, preset-routes, fe-preset-form) names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".
5. (fe-preset-form) clearing a field always means unset: the key is omitted from the stored spec, never stored as null; numbers like replicas or max_attempts cleared fall back to defaults at schedule.
6. (kind-e2e-presets) tests delete every cluster they create in teardown; the builder checks e2e/values-kind.yaml and raises ORCH_MAX_CLUSTERS there only if needed; the generated-slug cluster is 1 replica.
7. (kind-e2e-presets) never edit the Default in e2e; edit and delete a copy. test_default_preset_listed asserts the Default exists, is_default, and its spec replicas is 1.
8. (fe-preset-form) re-read ClusterForm.test.tsx as merged by web-ui-cluster-tabs-with-fil and move the discard-dialog tests; the Ribbon-created cases are already gone there.
9. (fe-new-cluster-dialog) createCluster takes a body typed as the regenerated CreateCluster (exactly one of spec or preset_id at runtime); ClusterForm create mode keeps compiling; every task leaves `npm run build` and `npm run check:api` green.
10. (deploy-pin-presets) excluded from the build run; it runs after the orchestrator PR merges, its sha filled with ticket.py amend, same as web-ui's deploy-pin.

### design.md: Assumptions and unknowns

- tatara and magic-trainer, named API consumers in the orchestrator README, may call PATCH or POST a slug-only body; they are outside this workspace and the README exception documents the break (confirmed by the user's Q4 and Q2 answers).
- `gen_random_uuid()` is not needed: the seed uses a fixed id and the api supplies ids, so no extension is assumed.
- web-ui-cluster-tabs-with-fil merges first with `TopBar({..., settingsCategories})`, `SessionsMenu` and App hosting the New cluster and Discard dialogs as its tasks fe-top-bar and fe-retire-ribbon state; the builder reads the merged files before editing.

### design.md: Epic review rulings (2026-10-24)

- Acted on (task presets-review-fixes): migration upgrade-path test on a database with clusters; PresetForm keeps edits made before /meta loads; README writers table notes the preset delete cascade on clusters.preset_id.
- Declined: getPreset/copyPreset used only by tests (the fe-preset-client contract lists them); no "copy 2" naming on collision (the 409 is shown, as designed).

### approvals.json

- A: Presets are named, stored ClusterSpec templates that can be created, copied, edited and deleted through /api/v1 and the UI; a preset stores only what the user set and the editor (the former ClusterForm) shows /meta defaults for the rest. [decisions: D2, D3, D6, D17, D18, D21] [tasks: fe-new-cluster-dialog, fe-preset-form, fe-presets-page, preset-routes, presets-table-and-repo] [status: approved]
- B: A seeded default preset with 1 pod always exists; it can be edited and copied but not renamed or deleted, and the API refuses to delete the last preset. [decisions: D1, D3, D15, D16] [tasks: fe-presets-page, preset-routes, presets-table-and-repo] [status: approved]
- C: Scheduling a cluster takes a preset and an optional slug (generated from the preset name when absent); POST /api/v1/clusters keeps a raw spec for headless callers, exactly one of spec or preset_id. [decisions: D4, D6, D11, D12] [tasks: create-cluster-from-preset, fe-new-cluster-dialog, slug-from-name] [status: approved]
- D: A cluster keeps the spec snapshotted at create, plus which preset it came from; editing or deleting a preset never changes a running cluster. [decisions: D1, D4, D13, D19] [tasks: create-cluster-from-preset, fe-new-cluster-dialog, kind-e2e-presets, presets-table-and-repo] [status: approved]
- E: Live cluster edit is removed: PATCH /api/v1/clusters/{id} is retired (405 retirement test), with its schema, repository function, the stored parameter of validate_spec, the client call and the form's edit mode, and a documented exception to the additive-only rule. [decisions: D5, D14, D22] [tasks: fe-preset-form, presets-table-and-repo, retire-cluster-patch-route, retire-spec-update-repo] [status: approved]
- F: Presets is the first settings category at the bottom of the hamburger menu and opens a full main-area page with a Back button. [decisions: D7, D20] [tasks: fe-presets-page] [status: approved]
- G: Headless parity: every UI capability of this epic is backed by a documented public API (README, OpenAPI) and an API-only end-to-end test. [decisions: D8, D10] [tasks: create-cluster-from-preset, kind-e2e-presets, preset-routes] [status: approved]
- H: Deployed: the agent-orchestrator chart and image are pinned in agents-helmfile; helmfile apply and smoke are run by the user. [decisions: D9] [tasks: deploy-pin-presets] [status: approved]
