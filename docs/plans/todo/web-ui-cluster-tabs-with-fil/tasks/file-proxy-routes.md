---
title: file proxy routes
status: todo
repo: agent-orchestrator
value: headless clients and the UI can browse and read a cluster workdir through /api/v1
files: [src/agent_orchestrator/api/workspace.py, src/agent_orchestrator/api/schemas.py, tests/test_api_files.py, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py, README.md, openapi.json, frontend/src/api/schema.d.ts]
verify: "mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise run lint"
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
- AC8: targeted suites, schema check and lint pass [evidence: command:mise x node@24.20.0 -- npm --prefix frontend ci && uv run pytest -q -p no:cacheprovider tests/test_api_files.py tests/test_readme_api.py && mise x node@24.20.0 -- npm --prefix frontend run check:api && mise run lint]

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
