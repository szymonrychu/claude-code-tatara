---
title: preset routes
status: done
repo: agent-orchestrator
value: "presets can be created, copied, edited and deleted through the documented API"
files: [src/agent_orchestrator/api/presets.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/api/schemas.py, src/agent_orchestrator/api/clusters.py, tests/test_api_presets.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_presets.py tests/test_api_clusters.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check ."
depends_on: [presets-table-and-repo]
owns: [check-spec-public, orch-presets-api]
uses: [presets-repo]
model: ""
estimate: 6
estimate_by: formula
actual: 9
actual_roles: "impl 4, verify 3, review 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/cluster-presets-preset-routes/agent-orchestrator
branch: cluster-presets-preset-routes/agent-orchestrator
verified_head: dde2170bcce0ebb5903fb981507d343100e24880
run: cluster-presets
provides: [check-spec-public, orch-presets-api]
acs_for_audit: []
process_gaps: []
fork_point: 233ff92
---

# preset routes

## Requirement

Expose presets through `/api/v1` (design D2, D3; user Q5, Q7, Q8; headless parity), test-first in a new `tests/test_api_presets.py` (ASGI client against the real test database, like `tests/test_api_clusters.py:http`).

- `api/clusters.py`: `_check_spec` becomes the public `check_spec(spec, settings, stored=None)` (part `check-spec-public`; same behaviour, callers updated; `stored` stays for the preset PUT and is not dropped by retire-cluster-patch-route or retire-spec-update-repo).
- `api/schemas.py`: `PresetIn {name: str, spec: ClusterSpec = ClusterSpec()}` and `CopyPreset {name: str | None = None}`, both `extra="forbid"`; `PresetView {id, name, is_default, spec: dict[str, Any], created_at, updated_at}`.
- New `api/presets.py` router (`APIRouter(prefix="/api/v1")`), registered in `api/app.py:create_app` beside the clusters router:
  - `GET /presets`: list of `PresetView`, default first, then by name.
  - `POST /presets`: 201. Name checked with `validate_preset_name` (422 `invalid_request`; leading or trailing spaces are rejected and the API never trims); spec checked with `check_spec` against current settings (422 `invalid_request`), the filled result discarded; stored spec is `body.spec.model_dump(mode="json", exclude_unset=True)`, so only the keys the caller sent are kept; name taken is 409 `conflict`.
  - `GET /presets/{preset_id}`: 200, 404 `not_found`.
  - `PUT /presets/{preset_id}`: full replace of name and spec with the same rules; renaming the default is 409 `preset_default`; 404. `check_spec` gets the stored preset spec as `stored`, so a stored model, effort or image that is no longer in the settings lists is accepted only when unchanged from the stored preset; changing to an unknown value is 422.
  - `DELETE /presets/{preset_id}`: 204; the default is 409 `preset_default`; the only preset is 409 `last_preset`; 404. Clusters made from it keep their spec; their `preset_id` becomes null by the foreign key.
  - `POST /presets/{preset_id}/copy`: optional body `CopyPreset`; 201 with a new non-default preset holding the source's stored spec verbatim; the name is `body.name` or `<source name> copy`, then `<source name> copy 2`, `copy 3` and so on until free, the source part cut to fit 40 characters and right-trimmed before ` copy`; an explicit name that is taken is 409 `conflict`; 404 for an unknown source.
- README `## API`: one `### \`METHOD /api/v1/presets...\`` section per route with body, response and errors; the error codes list gains `preset_default` (409) and `last_preset` (409).
- `openapi.json` regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`) and `frontend/src/api/schema.d.ts` (`mise x node@24.20.0 -- npm --prefix frontend run gen:api`).

## Acceptance conditions

- AC1: GET /presets returns the seeded Default first with spec {"replicas": 1} [evidence: test:tests/test_api_presets.py::test_list_has_seeded_default]
- AC2: POST stores and returns only the spec keys the caller sent, nested resources included [evidence: test:tests/test_api_presets.py::test_create_stores_only_set_fields]
- AC3: invalid names (including leading or trailing spaces, never trimmed) are 422 and a taken name (any case) is 409 conflict [evidence: test:tests/test_api_presets.py::test_name_rules_and_unique_409]
- AC4: a spec against current settings (model outside ORCH_MODELS, replicas above the cap, image outside the allowlist) is 422 on POST and PUT [evidence: test:tests/test_api_presets.py::test_save_validates_spec_against_settings]
- AC5: PUT replaces name and spec; the default can be edited but renaming it is 409 preset_default; unknown id is 404 [evidence: test:tests/test_api_presets.py::test_put_replaces_and_default_not_renamed]
- AC6: DELETE is 204, the default is 409 preset_default, the last preset is 409 last_preset, unknown id is 404 [evidence: test:tests/test_api_presets.py::test_delete_guards]
- AC7: copy without a name gives "<name> copy" then "<name> copy 2" within 40 characters (source part cut and right-trimmed), copies the stored spec verbatim, is never default, and a taken explicit name is 409 [evidence: test:tests/test_api_presets.py::test_copy_default_name_and_verbatim_spec]
- AC8: check_spec is public and the clusters routes use it [evidence: symbol:src/agent_orchestrator/api/clusters.py::check_spec]
- AC9: README, openapi.json and schema.d.ts match the app [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC10: targeted tests, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_presets.py tests/test_api_clusters.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC11: PUT accepts a stored model, effort or image no longer in the settings lists when unchanged, changing it to an unknown value is 422, and POST of such a value is 422 [evidence: test:tests/test_api_presets.py::test_put_accepts_unchanged_out_of_list_value]

## Files

- `src/agent_orchestrator/api/presets.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/api/schemas.py`
- `src/agent_orchestrator/api/clusters.py`
- `tests/test_api_presets.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- Routes: `GET|POST /api/v1/presets`, `GET|PUT|DELETE /api/v1/presets/{preset_id}`, `POST /api/v1/presets/{preset_id}/copy` (part `orch-presets-api`, defined in README.md).
- `api/clusters.py:check_spec(spec, settings, stored=None) -> ClusterSpec` (part `check-spec-public`).
- `schemas.PresetIn`, `schemas.CopyPreset`, `schemas.PresetView`.
- Error codes `preset_default` (409), `last_preset` (409), plus the existing `conflict`, `not_found`, `invalid_request`.

## Expected outcome

A headless client can list, create, read, replace, copy and delete presets, with the same validation the cluster create applies, and the README and OpenAPI describe it.

## Steps

- Write `tests/test_api_presets.py` with the eight tests named in the AC refs (reuse `make_settings`, `client_for`, `assert_error` by importing them from `test_api_clusters` or a small local copy); run `uv run pytest -q -p no:cacheprovider tests/test_api_presets.py`: fails with 404s.
- Rename `_check_spec`, add schemas, `api/presets.py` and the router registration; run the test file: passes.
- Add the README sections and error codes; regenerate `openapi.json` and `schema.d.ts`; run the verify command: passes.

## Notes

- `exclude_unset=True` must be applied to the parsed request model, not to a re-validated copy, or every default reappears.
- `check_spec` is called for its validation; the filled spec it returns is not stored here.
- DELETE answers 204 with no body; keep `response_model=None` so OpenAPI stays clean.
- Builder check ruling 2 (2026-10-23): PUT of a preset accepts a stored model, effort or image that is no longer in the settings lists only when that value is unchanged from the stored preset (the legacy rule PATCH used); changing to an unknown value is 422. validate_spec keeps its `stored` parameter (and check_spec its `stored` parameter) for this; retire-spec-update-repo must not delete it, it still deletes update_spec and ClusterDeleting if unused. Scheduling always validates fully (no `stored`) and returns 422 with the reason and the preset name. The editor's Model/Effort select shows a stored out-of-list value as an extra option labelled "<value> (not available)".
- Builder check ruling 4 (2026-10-23): names with leading or trailing spaces are rejected (422 on the API, inline error in the form); the API never trims. The copy name's source part is cut to fit 40 characters and right-trimmed before " copy".

- 2026-10-23 amended: builder check rulings 2, 4: PUT keeps unchanged out-of-list values via stored; no trimming, copy name cut and right-trimmed (AC3, AC7 rewritten, AC11 added)
