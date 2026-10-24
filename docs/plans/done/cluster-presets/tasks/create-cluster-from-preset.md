---
title: create cluster from preset
status: done
repo: agent-orchestrator
value: "scheduling a cluster takes only a preset, and later preset changes never touch it"
files: [src/agent_orchestrator/api/clusters.py, src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/db/clusters.py, tests/test_api_create_from_preset.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_create_from_preset.py tests/test_api_clusters.py tests/test_clusters_repo.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check ."
depends_on: [slug-from-name, preset-routes]
owns: [orch-cluster-create-api]
uses: [slugify-helper, presets-repo, check-spec-public]
model: ""
estimate: 6
estimate_by: formula
actual: 10
actual_roles: "impl 4, verify 4, review 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/cluster-presets-create-cluster-from-preset/agent-orchestrator
branch: cluster-presets-create-cluster-from-preset
verified_head: de2e84784c44399af9c4527956e14425db6917fd
run: cluster-presets
provides: []
acs_for_audit: []
process_gaps: []
---

# create cluster from preset

## Requirement

Let `POST /api/v1/clusters` schedule a cluster from a preset and snapshot its spec (design D4; user Q1, Q2, Q3; headless parity), test-first in a new `tests/test_api_create_from_preset.py`.

- `api/schemas.py`: `CreateCluster` becomes `{slug: str | None = None, spec: ClusterSpec | None = None, preset_id: uuid.UUID | None = None}`, `extra="forbid"` (part `orch-cluster-create-api`). Exactly one of `spec` and `preset_id`, else 422 `invalid_request` ("exactly one of spec or preset_id"); with `spec` the slug is required (422 "slug is required with spec"). `ClusterView` gains `preset_id: uuid.UUID | None` and `preset_name: str | None`.
- `db/clusters.py`: `Cluster` gains `preset_id` and `preset_name` (read by `_from_row`); `create(conn, slug, spec, preset_id=None, preset_name=None)` inserts them.
- `api/clusters.py:create_cluster`, preset path: inside the existing transaction after `pg_advisory_xact_lock(_CREATE_LOCK)` and the `max_clusters` check, read the preset with `presets.get_for_share` (404 `not_found` "preset not found"); run `check_spec(ClusterSpec.model_validate(preset.spec), settings)` against current settings, a 422 message prefixed `preset '<name>': `; the filled spec is the cluster's own spec (the snapshot). On this preset path only, when the preset leaves `replicas` unset the schedule-time fill sets it from `settings.default_replicas`, alongside the write-time fills (the raw-spec path is unchanged; the seeded Default stores replicas 1 explicitly, so it schedules 1). Slug: `body.slug` checked with `validate_slug`, or `generated_slug(preset.name)` retried with a fresh suffix up to 5 times on `ClusterExists`; an explicit slug clash stays 409 `conflict`, and after the 5th generated-slug clash the answer is 409 `conflict` too, never 500. Insert with `preset_id` and `preset_name`. `_view` fills the two new fields.
- Raw spec path unchanged apart from the exactly-one rule; its clusters have null `preset_id` and `preset_name`.
- No code path changes a cluster's `spec` or `generation` when a preset is edited or deleted.
- README `### POST /api/v1/clusters` documents both bodies, the generated slug, the snapshot, 404 for an unknown preset and the preset-named 422; `### GET /api/v1/clusters/{cluster_id}` lists `preset_id` and `preset_name`. `openapi.json` and `frontend/src/api/schema.d.ts` regenerated.

## Acceptance conditions

- AC1: POST {preset_id: Default} is 201 with a slug matching ^default-[a-z]{4}$, spec replicas 1 with resources filled from the current defaults, preset_id and preset_name set [evidence: test:tests/test_api_create_from_preset.py::test_create_from_default_preset_generates_slug]
- AC2: an explicit slug is used, a clashing explicit slug is 409 conflict, and a generated slug clash is retried [evidence: test:tests/test_api_create_from_preset.py::test_explicit_slug_and_generated_retry]
- AC3: both spec and preset_id, neither, or spec without slug are 422 invalid_request [evidence: test:tests/test_api_create_from_preset.py::test_exactly_one_of_spec_or_preset_id]
- AC4: a preset that became invalid under current settings is 422 with a message naming the preset [evidence: test:tests/test_api_create_from_preset.py::test_preset_revalidated_at_schedule]
- AC5: editing and then deleting the preset leaves the cluster spec and generation unchanged; after the delete preset_id is null and preset_name is kept [evidence: test:tests/test_api_create_from_preset.py::test_snapshot_survives_preset_edit_and_delete]
- AC6: an unknown preset_id is 404 not_found and creates nothing [evidence: test:tests/test_api_create_from_preset.py::test_unknown_preset_404]
- AC7: a preset without resources gets the resource defaults current at schedule time, so a settings change reaches the next cluster [evidence: test:tests/test_api_create_from_preset.py::test_defaults_filled_at_schedule]
- AC8: README, openapi.json and schema.d.ts match the app [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC9: targeted tests, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_create_from_preset.py tests/test_api_clusters.py tests/test_clusters_repo.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC10: a preset that leaves replicas unset schedules settings.default_replicas, the Default schedules its stored 1, and a raw spec POST without replicas is unchanged [evidence: test:tests/test_api_create_from_preset.py::test_replicas_filled_from_settings_at_schedule]
- AC11: after the 5th generated-slug clash the answer is 409 conflict, never 500 [evidence: test:tests/test_api_create_from_preset.py::test_generated_slug_exhausted_409]

## Files

- `src/agent_orchestrator/api/clusters.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/db/clusters.py`
- `tests/test_api_create_from_preset.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- `POST /api/v1/clusters` body `{"slug"?, "spec"?, "preset_id"?}` (part `orch-cluster-create-api`, defined in README.md; cross-epic contract of the same name, consumer agents-helmfile smoke).
- `ClusterView.preset_id`, `ClusterView.preset_name`; `db/clusters.Cluster.preset_id`, `.preset_name`; `db/clusters.create(conn, slug, spec, preset_id=None, preset_name=None)`.
- Uses `spec.generated_slug` (slugify-helper), `db/presets.get_for_share` (presets-repo), `check_spec` (check-spec-public).

## Expected outcome

A cluster can be scheduled with nothing but a preset id; it owns a full copy of the preset's spec as filled at that moment and remembers the preset's id and name.

## Steps

- Write `tests/test_api_create_from_preset.py` with the nine tests named in the AC refs; run `uv run pytest -q -p no:cacheprovider tests/test_api_create_from_preset.py`: fails.
- Change `CreateCluster`, `ClusterView`, `Cluster`, `create` and `create_cluster`; run the file and `tests/test_api_clusters.py tests/test_clusters_repo.py`: pass.
- Update README, regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.

## Notes

- `repo.create` opens a nested transaction (a savepoint), so a generated-slug clash can be retried inside the outer creation transaction without losing the advisory lock.
- A preset deleted between the read and the insert is impossible while it is held `FOR SHARE`.
- `tests/factories.py:insert_cluster` keeps working because the new columns are nullable.
- `orch bench`, `scripts/smoke.sh` and the kind e2e send `{"slug", "spec"}` and stay valid.
- Builder check ruling 1 (2026-10-23): on the preset path only, the schedule-time fill sets replicas from settings.default_replicas when the preset leaves replicas unset (alongside the existing write-time fills). The raw-spec POST path is unchanged. The seeded Default stores replicas 1 explicitly, so it schedules 1.
- Builder check ruling 3 (2026-10-23): after the 5th generated-slug clash the API answers 409 conflict (the existing conflict code), never 500.

- 2026-10-23 amended: builder check rulings 1, 3: preset-path replicas fill from settings.default_replicas; 409 after the 5th slug clash (AC10, AC11)
