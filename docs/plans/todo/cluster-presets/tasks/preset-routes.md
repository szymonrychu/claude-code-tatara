---
title: preset routes
status: todo
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
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# preset routes

## Requirement

Expose presets through `/api/v1` (design D2, D3; user Q5, Q7, Q8; headless parity), test-first in a new `tests/test_api_presets.py` (ASGI client against the real test database, like `tests/test_api_clusters.py:http`).

- `api/clusters.py`: `_check_spec` becomes the public `check_spec(spec, settings, stored=None)` (part `check-spec-public`; same behaviour, callers updated; retire-cluster-patch-route later drops `stored`).
- `api/schemas.py`: `PresetIn {name: str, spec: ClusterSpec = ClusterSpec()}` and `CopyPreset {name: str | None = None}`, both `extra="forbid"`; `PresetView {id, name, is_default, spec: dict[str, Any], created_at, updated_at}`.
- New `api/presets.py` router (`APIRouter(prefix="/api/v1")`), registered in `api/app.py:create_app` beside the clusters router:
  - `GET /presets`: list of `PresetView`, default first, then by name.
  - `POST /presets`: 201. Name checked with `validate_preset_name` (422 `invalid_request`); spec checked with `check_spec` against current settings (422 `invalid_request`), the filled result discarded; stored spec is `body.spec.model_dump(mode="json", exclude_unset=True)`, so only the keys the caller sent are kept; name taken is 409 `conflict`.
  - `GET /presets/{preset_id}`: 200, 404 `not_found`.
  - `PUT /presets/{preset_id}`: full replace of name and spec with the same rules; renaming the default is 409 `preset_default`; 404.
  - `DELETE /presets/{preset_id}`: 204; the default is 409 `preset_default`; the only preset is 409 `last_preset`; 404. Clusters made from it keep their spec; their `preset_id` becomes null by the foreign key.
  - `POST /presets/{preset_id}/copy`: optional body `CopyPreset`; 201 with a new non-default preset holding the source's stored spec verbatim; the name is `body.name` or `<source name> copy`, then `<source name> copy 2`, `copy 3` and so on until free, the source part cut so the name stays within 40 characters; an explicit name that is taken is 409 `conflict`; 404 for an unknown source.
- README `## API`: one `### \`METHOD /api/v1/presets...\`` section per route with body, response and errors; the error codes list gains `preset_default` (409) and `last_preset` (409).
- `openapi.json` regenerated (`uv run python -m agent_orchestrator.api.openapi > openapi.json`) and `frontend/src/api/schema.d.ts` (`mise x node@24.20.0 -- npm --prefix frontend run gen:api`).

## Acceptance conditions

- AC1: GET /presets returns the seeded Default first with spec {"replicas": 1} [evidence: test:tests/test_api_presets.py::test_list_has_seeded_default]
- AC2: POST stores and returns only the spec keys the caller sent, nested resources included [evidence: test:tests/test_api_presets.py::test_create_stores_only_set_fields]
- AC3: invalid names are 422 and a taken name (any case) is 409 conflict [evidence: test:tests/test_api_presets.py::test_name_rules_and_unique_409]
- AC4: a spec against current settings (model outside ORCH_MODELS, replicas above the cap, image outside the allowlist) is 422 on POST and PUT [evidence: test:tests/test_api_presets.py::test_save_validates_spec_against_settings]
- AC5: PUT replaces name and spec; the default can be edited but renaming it is 409 preset_default; unknown id is 404 [evidence: test:tests/test_api_presets.py::test_put_replaces_and_default_not_renamed]
- AC6: DELETE is 204, the default is 409 preset_default, the last preset is 409 last_preset, unknown id is 404 [evidence: test:tests/test_api_presets.py::test_delete_guards]
- AC7: copy without a name gives "<name> copy" then "<name> copy 2" within 40 characters, copies the stored spec verbatim, is never default, and a taken explicit name is 409 [evidence: test:tests/test_api_presets.py::test_copy_default_name_and_verbatim_spec]
- AC8: check_spec is public and the clusters routes use it [evidence: symbol:src/agent_orchestrator/api/clusters.py::check_spec]
- AC9: README, openapi.json and schema.d.ts match the app [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC10: targeted tests, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_presets.py tests/test_api_clusters.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
