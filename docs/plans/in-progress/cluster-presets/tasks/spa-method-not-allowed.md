---
title: spa method not allowed
status: todo
repo: agent-orchestrator
value: "the retired PATCH answers 405 in the real image, as the API contract says"
files: [src/agent_orchestrator/api/spa.py, tests/test_spa.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_spa.py tests/test_api_clusters.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [presets-review-fixes]
owns: []
uses: []
model: sonnet
estimate: 5
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

# spa method not allowed

## Requirement

CI e2e (kind, real image) failure on PR szymonrychu/agent-orchestrator#5: tests/e2e/test_e2e_kind.py::test_patch_cluster_retired gets 404 {"error":{"code":"not_found","message":"not found"}} instead of 405. Cause: the image sets ORCH_STATIC_DIR, so api/app.py mounts SpaStaticFiles at "/"; Starlette prefers the mount's full match over the /api/v1/clusters/{id} route's partial (method) match, and SpaStaticFiles.get_response (api/spa.py) answers every `api/` path with 404 before any method check. The unit tests never mount the SPA, so they see FastAPI's 405.

Fix in src/agent_orchestrator/api/spa.py: a request whose method is not GET or HEAD is answered 405 Method Not Allowed (with an Allow: GET, HEAD header, as plain StaticFiles does) before the `api/` 404 branch; GET/HEAD to an unknown `api/` path still answers 404. Add unit tests that build the app with a static_dir (a temp dir with an index.html) and assert: PATCH /api/v1/clusters/<uuid> answers 405; GET /api/v1/unknown answers 404; GET / still serves index.html.

## Acceptance conditions

- AC1: with the SPA mounted, PATCH /api/v1/clusters/{id} answers 405 [evidence: test:tests/test_spa.py::test_patch_cluster_405_with_spa_mounted]
- AC2: with the SPA mounted, GET of an unknown api path still answers 404 and GET / serves index.html [evidence: test:tests/test_spa.py::test_unknown_api_get_404_and_index_served]

## Files

- `src/agent_orchestrator/api/spa.py`
- `tests/test_spa.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The kind e2e test_patch_cluster_retired passes in CI: PATCH on a cluster answers 405 with the SPA mounted.

## Steps

- Write the AC tests in tests/test_spa.py and run the verify command: AC1 fails with 404.
- Answer non-GET/HEAD with 405 in SpaStaticFiles before the api/ 404 branch.
- Run the verify command: all pass.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
