---
title: spa serving and dockerfile
status: todo
repo: agent-orchestrator
value: "Ships the web UI inside the orchestrator image and makes CI prove the frontend builds, lints, tests and matches the API types."
files: [src/agent_orchestrator/api/spa.py, src/agent_orchestrator/api/app.py, Dockerfile, .dockerignore, .github/workflows/ci.yaml, tests/test_spa.py]
verify: "uv run pytest tests/test_spa.py -q && mise run lint"
depends_on: [api-events-and-streams, fe-api-client-and-stream]
owns: []
uses: [api-app]
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

# spa serving and dockerfile

## Requirement

Serving the SPA and the orchestrator image (D12, D17).

`api/spa.py`:
- `SpaStaticFiles` serves `index.html` with `Cache-Control: no-cache`, and hashed `assets/*` with `Cache-Control: public, max-age=31536000, immutable`.
- Any non-file path outside `/api/` falls back to index.html, so client routes work.
- An unknown `/api/...` path stays a JSON 404 in the error shape.
- `create_app` mounts it last, only when `settings.static_dir` is set and exists.

The multi-stage `Dockerfile`:
- stage 1 is `node:24-bookworm-slim`, running `npm ci` and `npm run build` in frontend/
- stage 2 is `python:3.12-slim-bookworm`, with `uv sync --frozen --no-dev` into /app/.venv, `frontend/dist` copied to /app/static, and `ORCH_STATIC_DIR=/app/static`
- user 1000, `ENTRYPOINT ["orch"]`

`.dockerignore` excludes .venv, node_modules, .git and tests.

`.github/workflows/ci.yaml` gains a `frontend` job on ubuntu-latest that runs in frontend/: `npm ci`, `npm run lint`, `npm test`, `npm run build`, `npm run check:api`. The last fails when `src/api/schema.d.ts` is stale against `openapi.json`.

## Acceptance conditions

- AC1: index.html is served with no-cache and assets as immutable [evidence: test:tests/test_spa.py::test_index_no_cache_assets_immutable]
- AC2: client routes fall back to index.html [evidence: test:tests/test_spa.py::test_client_route_fallback]
- AC3: unknown /api paths stay JSON 404s [evidence: test:tests/test_spa.py::test_unknown_api_path_is_json_404]
- AC4: without a static dir nothing is mounted [evidence: test:tests/test_spa.py::test_no_static_dir_no_mount]
- AC5: the image builds and serves the SPA [evidence: command:docker build -t agent-orchestrator:test . && docker run --rm agent-orchestrator:test --version]
- AC6: CI runs the frontend lint, test, build and API drift check [evidence: command:grep -q 'npm run check:api' .github/workflows/ci.yaml && grep -q 'npm run build' .github/workflows/ci.yaml && grep -q 'npm run lint' .github/workflows/ci.yaml]

## Files

- `src/agent_orchestrator/api/spa.py`
- `src/agent_orchestrator/api/app.py`
- `Dockerfile`
- `.dockerignore`
- `.github/workflows/ci.yaml`
- `tests/test_spa.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
