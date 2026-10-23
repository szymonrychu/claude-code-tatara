# cluster presets design

## Summary

The agent-orchestrator gains named cluster presets: stored, sparse ClusterSpec templates with create, copy, edit and delete through `/api/v1/presets` and a Presets settings page reached from the hamburger menu built by web-ui-cluster-tabs-with-fil. A migration seeds a `Default` preset (`replicas: 1`). Scheduling a cluster takes a preset (and an optional slug, generated from the preset name when absent); the api re-validates the preset against current settings, fills the write-time defaults and stores the result as the cluster's own spec, so a preset edit or delete never touches a running cluster. Live cluster edit is retired: `PATCH /api/v1/clusters/{cluster_id}`, its schema, repository function, client call and the form's edit mode are removed and pinned by retirement tests. `POST /api/v1/clusters` keeps a raw `spec` body for headless callers. The epic ends with the agents-helmfile pin; apply and smoke are run by the user.

## Intent and why

The user wants scheduling to be one choice instead of a long form, repeatable setups kept by name, and no live session edit (user request 2026-10-23, README Description). Live edit rolls every agent pod today because the pod template carries a hash of the rendered config (`k8s/render.py:189`, `:254`), ending running turns; snapshot-at-create removes that failure mode while presets keep the convenience.

## Goals

- `GET|POST /api/v1/presets`, `GET|PUT|DELETE /api/v1/presets/{preset_id}` and `POST /api/v1/presets/{preset_id}/copy` exist, are documented in README and OpenAPI, and validate every save against current settings.
- A `Default` preset with `{"replicas": 1}` exists after migration; it can be edited and copied, never renamed or deleted (409 `preset_default`); deleting the last preset is 409 `last_preset`.
- `POST /api/v1/clusters` accepts `{"preset_id", "slug"?}` or `{"slug", "spec"}`, exactly one of `spec` and `preset_id`; the preset path stores a filled snapshot plus `preset_id` and `preset_name`.
- Editing or deleting a preset never changes a cluster's `spec` or `generation`; a delete sets the cluster's `preset_id` to null and keeps `preset_name`.
- The New cluster dialog shows a preset select (default preselected) and an optional slug, nothing else; the PresetForm (from ClusterForm) edits presets with /meta defaults shown for unset fields and saves only what the user set.
- PATCH is gone from the API (405, retirement test), and `patchCluster`, `PatchCluster`, `update_spec`, `ClusterDeleting`, the `stored` parameter of `validate_spec` and `ClusterForm.tsx` are gone from the code.
- The hamburger menu's Settings section lists Presets, which opens a full main-area page with a Back button.
- Every capability has an API-only test, and the kind e2e drives presets end to end through `/api/v1`.
- agents-helmfile pins the merged orchestrator chart and image.

## Non-goals

- No preset versioning or history beyond each cluster's snapshot; no per-user presets; no import or export (Q11); no settings category other than Presets.
- No change to reconcile, dispatch or discard of a created cluster.
- No change to `scripts/smoke.sh`: it keeps creating its cluster with a raw spec (Q2).
- No re-plan of web-ui-cluster-tabs-with-fil parts (top bar, SessionsMenu, retire ribbon, workspace proxy, its deploy pin); this epic builds on them after that epic merges.

## Anti-goals

- A preset edit or delete that bumps a running cluster's generation or restarts its pods.
- Freezing /meta defaults into presets, so a later `ORCH_DEFAULT_*` change no longer reaches untouched fields.
- A red main in any repo between tasks: the frontend stops calling PATCH before the backend removes it.
- Breaking headless callers beyond the documented exception (PATCH removal, and a create body with neither `spec` nor `preset_id`).

## Constraints

- Python only except the TypeScript frontend; single writer per table: `presets` is written only by the api (README `### Single-writer interpretation`), and the `clusters.preset_id` `ON DELETE SET NULL` cascade is an api write too.
- Test-first; retirement tests assert on `git ls-files <path>` for removed files and on module attributes or signatures for removed symbols.
- Orchestrator `tests/test_readme_api.py` requires a README `### \`METHOD /api/v1...\`` heading per route and `openapi.json` plus `frontend/src/api/schema.d.ts` regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`, then `npm --prefix frontend run gen:api`); `test_frontend_schema_matches_openapi` needs `frontend/node_modules`, so verifies run `npm --prefix frontend ci` first.
- `frontend/src/layout/designRules.ts`: no colour literals, no decorative Unicode, no `title=` on buttons, fontWeight 400 or 500.
- Verify commands in this container: orchestrator `uv run pytest -q -p no:cacheprovider <files>` (testcontainers, dockerd running) plus `uv run ruff check . && uv run ruff format --check .`; frontend `mise x node@24.20.0 -- npm --prefix frontend ci`, then `test -- <files>`, `run lint`, `run build`, `run check:api`; the kind e2e is verified by collection (`-m e2e --collect-only`) and runs in the PR CI `e2e` job; agents-helmfile tests that build the helmfile pull charts over the network and fail here, so the pin verify deselects them.
- Order: this epic runs after web-ui-cluster-tabs-with-fil is merged (README blockers) and edits its `App.tsx`, `App.test.tsx`, `layout/TopBar.tsx` and `layout/TopBar.test.tsx`.

## Decisions

### D1: Data model and seed
Migration `0002_presets.sql` adds `presets` (`id` uuid, `name` text 1 to 40 chars, `spec` jsonb, `is_default` boolean, `created_at`, `updated_at`) with a unique index on `lower(name)` and a partial unique index allowing one default, seeds `Default` with the fixed id `00000000-0000-0000-0000-000000000001` and `{"replicas": 1}` through `INSERT ... ON CONFLICT DO NOTHING`, and adds `clusters.preset_id` (`REFERENCES presets ON DELETE SET NULL`) and `clusters.preset_name`. Every statement is idempotent (`IF NOT EXISTS`), so re-applying never fails and never overwrites an edited default. Alternatives: seeding in the api at startup (rejected: a second writer path and a race between api replicas); a versioned preset table (rejected: Non-goals). Names are unique case-insensitively and the seed name is `Default` (my call). Serves approvals B, D.

### D2: A preset stores only what was set
`POST` and `PUT` take `{"name", "spec"}` where `spec` is a ClusterSpec; the api stores `spec.model_dump(mode="json", exclude_unset=True)`, so only the keys the caller sent are kept, and `PresetView.spec` returns exactly the stored object (a subset of ClusterSpec keys, typed `dict[str, Any]` in OpenAPI). Save-time validation runs the public `check_spec` (validate, then write-time fill) and discards the filled result; the fill runs again at schedule. Alternative: storing the filled spec (rejected: freezes defaults, Q7). The `dict` response type is my call. Serves approval A.

### D3: Preset routes and errors
`GET /presets` (default first, then by name, case-insensitive), `POST /presets` (201), `GET /presets/{id}`, `PUT /presets/{id}` (full replace of name and spec), `DELETE /presets/{id}` (204), `POST /presets/{id}/copy` (201, optional body `{"name"}`; without it the name is `<source> copy`, then `<source> copy 2`, `copy 3` and so on, the source part cut so the name stays within 40 characters; the stored spec is copied verbatim and the copy is never default). Errors: 404 `not_found`, 409 `conflict` (name taken), 409 `preset_default` (rename or delete of the default), 409 `last_preset`, 422 `invalid_request`. The UI Copy action opens the editor prefilled from the source and creates on save, so Cancel leaves nothing behind; the copy route serves headless callers (my call). Serves approvals A, B.

### D4: Create from a preset and the snapshot
`CreateCluster` becomes `{"slug"?, "spec"?, "preset_id"?}` with `extra="forbid"`: exactly one of `spec` and `preset_id` (422 otherwise); with `spec` the slug stays required (my call). With `preset_id`, inside the existing creation transaction after the advisory lock, the api reads the preset `FOR SHARE` (404 `not_found` when missing), runs `check_spec` on it against current settings (a 422 message starts `preset '<name>': `), and inserts the filled spec as the cluster's own spec with `preset_id` and `preset_name`. Without a slug it uses `generated_slug(preset.name)`, retried with a fresh suffix up to 5 times on a slug clash (my call); an explicit slug clash stays 409 `conflict`. `ClusterView` gains `preset_id` and `preset_name`. Serves approvals C, D.

### D5: PATCH retirement and dead code
Removed: `api/clusters.py:patch_cluster`, `schemas.PatchCluster`, `db/clusters.py:update_spec` and `ClusterDeleting` (its only user), the `stored` parameter of `spec.validate_spec` and of `check_spec`, the PATCH tests, the README `### PATCH` section; `cluster_deleting` stays (messages and checks still answer it). `PATCH /api/v1/clusters/{id}` then answers 405 because GET and DELETE share the path. Frontend: `patchCluster`, the `PatchCluster` alias, `mode: 'edit'` and `ClusterForm.tsx` go. The frontend retirement lands before the backend one so `npm run build` stays green when `schema.d.ts` loses `PatchCluster`. Serves approval E.

### D6: Frontend forms
`NewClusterDialog` (new): a preset `Select` with the default preselected, an optional Slug field (checked client-side only against `MAX_SLUG`; the server 422 is shown otherwise), Create posts `{preset_id, slug?}`; errors in an outlined Alert. `PresetForm` (git mv of `ClusterForm.tsx`): new, edit and copy modes, a Name field instead of Slug, PVC size editable and optional; fields not stored in the preset show the /meta default (`blankValues(meta)`) and are saved only once the user changes them (set-field tracking in `clusterSpecForm.ts`, `toPresetSpec(values, setKeys)`). The default preset's name is read-only. `clusterSpecForm.ts` stays at its path (my call). Serves approvals A, C.

### D7: Presets page and menu entry
`PresetsPage` is a full main-area view (Q10) opened from the `settingsCategories` entry `{id: 'presets', label: 'Presets'}` passed through `TopBar` to `SessionsMenu` (cross-epic contract `orch-settings-menu`). App holds a `view` state (`cluster` or `presets`), no router (my call); Back or choosing a session returns to the cluster view. The page lists presets with the default marked, New preset, and per-row Edit, Copy and Delete (no Delete on the default; Delete confirms through `ConfirmDialog`). Serves approval F.

### D8: API-only end-to-end proof
`tests/e2e/test_e2e_kind.py` schedules its shared 2-replica cluster from a preset created through the API (explicit `SLUG`, so the kubectl label lookups stay), then proves on the live cluster: a preset PUT leaves the cluster's spec and generation unchanged, a preset DELETE nulls `preset_id` and keeps `preset_name`, copy works, the default preset schedules with a generated slug (that extra cluster is discarded at once), and PATCH answers 405. The ASGI tests per route are the in-process API-only proof. Serves approval G.

### D9: Deploy pin
agents-helmfile pins the agent-orchestrator chart `0.1.0-main.<sha7>` and image `<sha7>` of this epic's merge, like `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`; the sha is supplied with `ticket.py amend` after the merge, until then the task reports `blocked`. The pin test reads `helmfile.yaml.gotmpl` as text so it runs without the chart pull. `helmfile apply` and `mise run smoke` are run by the user. Serves approval H.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal | ran (discovery/reuse.md of web-ui-cluster-tabs-with-fil, lane 4) | public `_check_spec`, `arm_slug` sanitising into `spec.py`, `blankValues`/`valuesFromSpec` reuse, idempotent seed (reuse.md Plan inputs) | a second slug sanitiser |
| research-code-external | ran (research.md section 3) | snapshot at create keeps the EC2 launch template property that a template change never touches running instances (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/manage-launch-template-versions.html) | versioned presets (Kubernetes controller style roll on template change is exactly the restart to avoid) |
| research-docs | ran (research.md section 4) | MUI temporary Drawer for navigation (https://mui.com/material-ui/react-drawer/), no new dependency | none |
| research-papers | skipped: CRUD and UI work with no algorithmic core | none | none |

## Research inputs

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
| discovery/orchestrator-backend.md | B: delete patch_cluster, PatchCluster, update_spec, ClusterDeleting, `stored`; 405 test; README versioning sentence; test_migrations versions and TABLES | retire-cluster-patch-route, retire-spec-update-repo, presets-table-and-repo |
| discovery/orchestrator-backend.md | regen openapi.json then `npm run gen:api` | preset-routes, create-cluster-from-preset, retire-cluster-patch-route |
| discovery/frontend.md | ClusterForm edit tests, patchCluster, PatchCluster alias, mode retired | fe-preset-form |
| discovery/frontend.md | verify `npm run lint && npm test && npm run build && npm run check:api` with node 24 | fe-new-cluster-dialog, fe-preset-form, fe-presets-page |
| research.md 1 | PATCH callers: UI and tests only; bench and smoke only POST and DELETE | retire-cluster-patch-route |
| research.md 2 | `valuesFromSpec` edits a preset, `blankValues(meta)` is the new-preset form, PVC editable again | fe-preset-form |
| research.md 3 | validation at save and again at schedule | preset-routes, create-cluster-from-preset |
| research.md 4 | Presets as the first settings category in the drawer | fe-presets-page |

## Decision coverage

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

## Contracts

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

## Review focus

- Snapshot integrity: no code path writes `clusters.spec` or `generation` from a preset change; the create transaction reads the preset `FOR SHARE` under the advisory lock.
- Sparse storage: `exclude_unset` survives the round trip (nested `resources` included), and the UI saves only set fields.
- Migration idempotency and the one-default index; `test_migrations` versions, tables and the concurrent-migrate count.
- Retirement completeness: no `update_spec`, `ClusterDeleting`, `stored`, `PatchCluster`, `patchCluster` or `mode="edit"` left anywhere, the README versioning exception is explicit, PATCH answers 405.
- The frontend build stays green at every merge point (client.ts loses `PatchCluster` before `schema.d.ts` does).

## Left to the builder

- Internal helper names inside `db/presets.py` and `api/presets.py` beyond the interfaces named in the tasks.
- How the PresetForm marks a field as set (a `Set` of keys or per-field flags), as long as unchanged defaults are not saved and stored fields round-trip.
- The visual layout of the Presets page within the design rules.

## Assumptions and unknowns

- tatara and magic-trainer, named API consumers in the orchestrator README, may call PATCH or POST a slug-only body; they are outside this workspace and the README exception documents the break (confirmed by the user's Q4 and Q2 answers).
- `gen_random_uuid()` is not needed: the seed uses a fixed id and the api supplies ids, so no extension is assumed.
- web-ui-cluster-tabs-with-fil merges first with `TopBar({..., settingsCategories})`, `SessionsMenu` and App hosting the New cluster and Discard dialogs as its tasks fe-top-bar and fe-retire-ribbon state; the builder reads the merged files before editing.

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
- Q11: Should presets be exportable or importable as JSON or YAML? [recommended: no, not in this epic]
- Q12: Does the README rule that /api/v1 is additive only get a documented exception for the PATCH retirement, with the now-dead code removed? [recommended: yes, README and the component MEMORY.md document the exception with date and why; ClusterDeleting, the stored parameter of validate_spec and the PATCH tests go, and tests/test_migrations is updated for 0002 and the presets table]

## Irreversible operations in scope

- Migration `0002_presets.sql` on the live database when the user applies the release: additive only (new table, two nullable columns, one seed row); no data is deleted. Covered by approval H and the idempotency test in presets-table-and-repo.
- Removal of `PATCH /api/v1/clusters/{cluster_id}` from the public API: a breaking change for any external caller, covered by approval E and the README exception.
