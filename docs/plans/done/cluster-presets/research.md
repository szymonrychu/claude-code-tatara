# Research: cluster presets

Researched 2026-10-23 against agent-orchestrator 3004ed3 (the submodule pin) and the in-progress epic cluster-form-defaults-and-ga. Paths are relative to `code/agent-orchestrator/`.

## 1. How a cluster is created and edited today

- `POST /api/v1/clusters` takes `{"slug", "spec"}` (`api/schemas.py:14-18`, `CreateCluster`, spec defaults to `ClusterSpec()`), validates slug and spec (`api/clusters.py:116-138`), serialises creation under an advisory lock to enforce `max_clusters`, and stores the spec as `clusters.spec` jsonb (`db/migrations/0001_init.sql:1-10`).
- `PATCH /api/v1/clusters/{id}` takes `{"spec"}` (`schemas.py:21-24`), replaces the whole spec and bumps `generation` (`api/clusters.py:154-169`, `db/clusters.py:105-118`); README `### PATCH /api/v1/clusters/{cluster_id}`. The original design listed editing as goal G3 and the route in D11 (`docs/plans/done/agent-orchestrator/design.md:19`, `:199`).
- The reconciler re-renders on every pass (`reconciler/loop.py:203-236`); the pod template carries a hash of the rendered ccw config (`k8s/render.py:189`, `254`), so any spec change that alters the config rolls every agent pod, ending running turns. That is the practical cost of live edit.
- Callers of PATCH in the tree: only the UI (`frontend/src/api/client.ts:75-76`, `clusters/ClusterForm.tsx:73`) and tests (`tests/test_api_clusters.py:88`, `:346`, `tests/test_clusters_repo.py:58`, `:72`, `tests/test_readme_api.py`). `bench/runner.py:115` and `agents-helmfile/scripts/smoke.sh:46` only POST and DELETE. tatara and magic-trainer are named consumers of the API (README first paragraph) and were not checked.

## 2. The form and /meta defaults

- `GET /api/v1/meta` (`api/clusters.py:83-105`) returns defaults (model, effort, replicas, auto_compact_pct, pvc_size, storage_class, max_attempts), the image allowlist, models and caps. cluster-form-defaults-and-ga extends it with efforts and resource defaults, makes Model and Effort selects, prefills every field from /meta (`blankValues(meta)`), and moves resource defaults to write time in POST and PATCH (its tasks `meta-form-defaults.md`, `form-dropdowns-and-gauge-tic.md`, `defaults-at-write-time-and-l.md`).
- `frontend/src/clusters/clusterSpecForm.ts` holds the form state (`FormValues`), `blankValues(meta)` for create, `valuesFromSpec(slug, spec)` for edit, validation and the spec mapping. `ClusterForm.tsx:22-49` switches on `mode: 'create' | 'edit'`; edit disables slug and PVC size (`ClusterForm.tsx:90`, `:104`).
- Reuse for presets: `valuesFromSpec` already turns a stored spec into form values, so editing a preset is the current edit mode pointed at a preset; `blankValues(meta)` is the new-preset form; copy is `valuesFromSpec` of the source with a new name. The slug field becomes a name field; PVC size becomes editable again because a preset has no PVC yet.
- Defaults policy: storing only what the user set keeps /meta as the single source of defaults; the write-time fill at schedule then applies the current `ORCH_DEFAULT_*` values. Storing the shown defaults inside the preset would freeze them.

## 3. Presets: data model and API shape

- Single-writer rule (AGENTS.md; agent-orchestrator MEMORY.md D2): `presets` is written only by the api, like `clusters`.
- Snapshot at create: the cluster row keeps its own full spec (as today); `preset_id` and `preset_name` are provenance only. Prior art: EC2 launch templates are immutable and versioned: "Launch templates are immutable; after you create a launch template, you can't modify it. Instead, you can create a new version", and an instance launched without a version uses the default version (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/manage-launch-template-versions.html). Kubernetes controllers work the other way: a Deployment or StatefulSet template change rolls the pods, which is exactly the restart live edit causes here. Snapshot-at-create keeps the EC2 property (a template change never touches running instances) without carrying versions.
- Validation at schedule as well as at save, because `validate_spec` (`spec.py`) depends on settings (image allowlist, caps, and after the in-progress epic, models and efforts).
- Default preset: seeded by a migration (`INSERT ... ON CONFLICT DO NOTHING`, so a re-run never overwrites a user edit), `is_default` true, `replicas: 1`.

## 4. Hamburger menu

- The top bar does not exist yet: today's shell is a left aside on tablet and desktop and a dense app bar with a "Menu" button and a temporary Drawer on phone (`frontend/src/layout/Shell.tsx:15-77`). web-ui-cluster-tabs-with-fil replaces it with a top tab bar and, per its Q14, builds the hamburger `IconButton` plus a MUI `Drawer` listing the sessions from the top and a settings section pinned at the bottom.
- This epic adds the first settings category, Presets, which opens the presets page in the main area.
- MUI's temporary Drawer is the stock navigation drawer pattern (https://mui.com/material-ui/react-drawer/); no new dependency.

## 5. Order between the epics

1. cluster-form-defaults-and-ga (in progress): /meta and form defaults, PATCH validation.
2. web-ui-cluster-tabs-with-fil: top bar, tabs, hamburger menu, Edit action dropped from the UI.
3. cluster-presets (this epic): presets, schedule by preset, PATCH retired, Presets in the menu.
4. hive-mode-leadership-handove: its `hive` switch becomes a preset field.
