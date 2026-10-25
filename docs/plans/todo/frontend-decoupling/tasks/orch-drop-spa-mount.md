---
title: orch drop spa mount
status: todo
repo: agent-orchestrator
value: the orchestrator api is API-only
files: [src/agent_orchestrator/api/spa.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/settings.py, tests/test_spa.py, tests/test_settings.py, Dockerfile, README.md]
verify: "uv run pytest -q tests/test_spa.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: []
uses: []
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

# orch drop spa mount

## Requirement

The orchestrator api stops serving the UI (design D9; amends prior D1 and D12). Paths are in code/agent-orchestrator. Deletion pinned by retirement tests.

- Delete `src/agent_orchestrator/api/spa.py`; `api/app.py:create_app` no longer mounts anything at `/` (drop the `SpaStaticFiles` import and the `static_dir` branch).
- `settings.py:Settings.static_dir` removed; an `ORCH_STATIC_DIR` left in an environment is ignored (settings already use `extra="ignore"`).
- `Dockerfile`: drop `ORCH_STATIC_DIR=/app/static` from the `ENV` line (the node stage goes in task orch-drop-frontend-build).
- `tests/test_spa.py` becomes the retirement test: `git ls-files src/agent_orchestrator/api/spa.py` is empty; `GET /`, `GET /index.html` and `GET /clusters/x` on the api answer 404 with the JSON error body `error.code == "not_found"`; `PATCH /api/v1/clusters/{id}` still answers 405 from the API itself.
- `tests/test_settings.py`: the `static_dir` default assertion is replaced by one proving the field is gone and `ORCH_STATIC_DIR` is ignored.
- `README.md`: remove the `ORCH_STATIC_DIR` row; `orch api` serves `/api/v1` and `/healthz`, `/readyz` only; the components table no longer says the api serves the SPA.

## Acceptance conditions

- AC1: spa.py is no longer tracked [evidence: test:tests/test_spa.py::test_spa_module_untracked]
- AC2: GET / and client-route paths on the api answer the JSON 404 [evidence: test:tests/test_spa.py::test_root_is_json_404]
- AC3: PATCH on a cluster still answers 405 from the API [evidence: test:tests/test_spa.py::test_patch_cluster_still_405]
- AC4: static_dir is gone and ORCH_STATIC_DIR is ignored [evidence: test:tests/test_settings.py::test_static_dir_retired]
- AC5: no ORCH_STATIC_DIR in the image or README, no SPA claim in the README [evidence: command:! grep -n ORCH_STATIC_DIR Dockerfile README.md && ! grep -nE 'serves the SPA|/api/v1., the UI' README.md]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `src/agent_orchestrator/api/spa.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/settings.py`
- `tests/test_spa.py`
- `tests/test_settings.py`
- `Dockerfile`
- `README.md`

## Interfaces

- Removes `api/spa.py:SpaStaticFiles` and `Settings.static_dir` (contract `agent-orchestrator-settings-env`: `ORCH_STATIC_DIR` leaves the documented env). The `/api/v1` surface is unchanged.

## Expected outcome

The api is API-only: `/` is a JSON 404 and the image no longer sets `ORCH_STATIC_DIR`.

## Steps

- Red: rewrite `tests/test_spa.py` and the settings test; `uv run pytest -q tests/test_spa.py tests/test_settings.py` fails (spa.py tracked, `/` still mounted when a static dir is set).
- Green: delete the module and the mount, remove the field, the Dockerfile env and the README row.
- `uv run pytest -q tests/test_spa.py tests/test_settings.py && mise run lint`: pass. Name "deletion pinned by a retirement test" in tests.note.

## Notes

- Retirement tests assert on `git ls-files`, never on the filesystem.
- The live orchestrator keeps serving the UI until deploy-pin-orch-no-spa; the web cutover happens first (design D8).
