---
title: file proxy routes
status: in-progress
repo: agent-orchestrator
value: headless clients and the UI can browse and read a cluster workdir through /api/v1
files: [src/agent_orchestrator/api/workspace.py, src/agent_orchestrator/api/schemas.py, tests/test_api_files.py, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-proxy-seam, wrapper-file-api]
owns: [orch-files-api]
uses: [workspace-proxy-module, wrapper-files-api]
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

# file proxy routes

## Requirement

Proxy the wrapper file API through the orchestrator api (design D1, D4; user Q8, Q9), test-first.

Routes in `src/agent_orchestrator/api/workspace.py` (prefix `/api/v1`), with response models in `api/schemas.py`:

- `GET /api/v1/clusters/{cluster_id}/files?path=&offset=&agent_id=` -> 200 `FileListing` `{cluster_id, agent_id, root, path, entries: [{name, type, size, mtime}], next_offset}`: forwards to `GET /v1/sessions/{session_id}/files` on the agent chosen by `resolve_agent` (first ready agent, or `agent_id`).
- `GET /api/v1/clusters/{cluster_id}/files/content?path=&agent_id=` -> 200 `FileContent` `{cluster_id, agent_id, path, size, mtime, mime, kind, content}` from `GET /v1/sessions/{session_id}/files/content`.
- Wrapper errors pass through with status and code (`invalid_path` 400, `not_found` 404, `not_a_directory` 400, `not_a_file` 400); the proxy errors of D4 apply. `invalid_path`, `not_a_directory`, `not_a_file` are added to the README API error code list.

FakeWrapper (`tests/fakes/fake_wrapper.py`) gains both routes over a per-session temp workdir with the wrapper's field names, paging, kinds and error codes, and `tests/test_fake_wrapper_contract.py` gains file cases run against both the fake and the real image (`-m integration`), so the fake stays honest.

README: a `### \`GET /api/v1/clusters/{cluster_id}/files\`` and a `### \`GET /api/v1/clusters/{cluster_id}/files/content\`` section (parameters, response, errors). Regenerate `openapi.json` and `frontend/src/api/schema.d.ts`.

## Acceptance conditions

- AC1: listing through the api returns the wrapper listing of the first ready agent with cluster_id and agent_id added, paging intact [evidence: test:tests/test_api_files.py::test_list_proxied_from_first_ready_agent]
- AC2: agent_id selects that agent and an agent of another cluster is not_found [evidence: test:tests/test_api_files.py::test_agent_id_selects_and_scopes]
- AC3: content is proxied with text, binary and too_large kinds [evidence: test:tests/test_api_files.py::test_content_proxied]
- AC4: wrapper invalid_path and not_found pass through and an unreachable wrapper is 502 wrapper_unreachable [evidence: test:tests/test_api_files.py::test_errors_pass_through]
- AC5: no ready agent answers 409 agent_not_ready [evidence: test:tests/test_api_files.py::test_no_ready_agent]
- AC6: README, openapi.json and schema.d.ts match the app [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_readme_api.py]
- AC7: the fake's file routes have contract cases collected under the integration marker [evidence: command:uv run pytest -q -p no:cacheprovider -m integration --collect-only tests/test_fake_wrapper_contract.py]
- AC8: targeted suites, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && uv run ruff check . && uv run ruff format --check .]
- AC9: a wrapper not_found for path empty (missing workdir root) passes through as 404 not_found [evidence: test:tests/test_api_files.py::test_missing_root_not_found_passes_through]

## Files

- `src/agent_orchestrator/api/workspace.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_files.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`
- `README.md`
- `openapi.json`
- `frontend/src/api/schema.d.ts`

## Interfaces

- `GET /api/v1/clusters/{cluster_id}/files`, `GET /api/v1/clusters/{cluster_id}/files/content`; `schemas.FileEntry`, `FileListing`, `FileContent` (owns part `orch-files-api`, consumed by fe-filesystem-panel and kind-e2e-workspace).
- Uses `workspace-proxy-module` and the wrapper contract `wrapper-files-api` (wrapper README, task wrapper-file-api).

## Expected outcome

A headless client can browse and read a cluster's workdir through `/api/v1` alone; the UI types exist in `schema.d.ts`.

## Steps

- Extend FakeWrapper with the two routes and write `tests/test_api_files.py` (`client_for` pattern with `httpx.ASGITransport`, DB factories, a FakeWrapper per agent); run `uv run pytest -q -p no:cacheprovider tests/test_api_files.py`: fails (404).
- Add the routes and schemas; rerun: passes.
- README sections; `uv run python -m agent_orchestrator.api.openapi > openapi.json`; `mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend run gen:api`; run the verify command: passes.
- Add the contract cases to `tests/test_fake_wrapper_contract.py`; the integration run needs the new wrapper image and happens after wrapper-sha-pin (CI); here confirm collection only.

## Notes

- `tests/test_readme_api.py::test_frontend_schema_matches_openapi` needs `frontend/node_modules`; the verify runs `npm ci` first.
- `schema.d.ts` is generated; never hand-edit it.
- The wrapper field names are the contract (wrapper README `GET /v1/sessions/{id}/files`); copy them, do not rename.
- Builder check ruling 11: A missing workdir root (not_found for path "") renders as an empty tree with the line "workdir not created yet", not as an error.

- 2026-10-23 amended: builder check rulings 11 add acceptance conditions AC9-AC9
