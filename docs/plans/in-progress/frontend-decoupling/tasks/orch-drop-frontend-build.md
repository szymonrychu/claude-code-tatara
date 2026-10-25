---
title: orch drop frontend build
status: done
repo: agent-orchestrator
value: "the orchestrator repo, image and CI carry no UI or node"
files: [frontend, Dockerfile, .github/workflows/ci.yaml, tests/test_readme_api.py, tests/test_frontend_retired.py, .gitignore, README.md, MEMORY.md]
verify: "uv run pytest -q tests/test_frontend_retired.py tests/test_readme_api.py tests/test_images.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-drop-spa-mount]
model: ""
review: ""
verified_head: 2dec27b
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 14
actual_tokens: 523879
actual_roles: "impl 12, review 1"
actual_role_tokens: "impl 387549, review 136330"
---

# orch drop frontend build

## Requirement

Remove the UI source and its build from agent-orchestrator; it lives in agents-web now (design D9, D11). Paths are in code/agent-orchestrator. Deletion pinned by retirement tests.

Precondition, checked first: read `<ao-sha>` from agents-web `MEMORY.md` (`curl -fsSL https://raw.githubusercontent.com/szymonrychu/agents-web/main/MEMORY.md`, the `agent-orchestrator <sha40>` import line). `git diff --quiet <ao-sha> HEAD -- frontend` must pass: no frontend change landed after the import. Otherwise end `blocked` with the `git log --oneline <ao-sha>..HEAD -- frontend` list, whoCanClear "orchestrator: port these commits to agents-web, then rerun".

- `git rm -r frontend`.
- `Dockerfile`: no node stage and no `COPY --from=frontend`; nothing under `/app/static`.
- `.github/workflows/ci.yaml`: delete the `frontend` job; the `test` job loses `actions/setup-node` and `npm ci`. Every other job unchanged.
- `tests/test_readme_api.py`: delete `test_frontend_schema_matches_openapi` (the agents-web `check:api` against its vendored copy replaces it); the README and `openapi.json` drift tests stay.
- `tests/test_frontend_retired.py`: `git ls-files frontend` is empty; the Dockerfile has no `FROM node` and no `/app/static`; the workflow has no `npm`, `setup-node` or `frontend` job.
- `.gitignore`: drop `frontend/dist/`.
- `README.md`: the opening line describes a headless `/api/v1` whose web UI is the agents-web component (link https://github.com/szymonrychu/agents-web); `## Development` has no npm step; the openapi regeneration note says "then `npm run sync:api -- orchestrator` in agents-web".
- `MEMORY.md`: a dated 2026-10-25 entry amending D1 and D12: the UI moved to agents-web at `<ao-sha>` and the api is API-only; why: services talk only through HTTP, and other services need UI entries without living in the orchestrator.
- The kind e2e (API-only) keeps passing; it builds the image without a node stage now.

## Acceptance conditions

- AC1: frontend/ is no longer tracked [evidence: test:tests/test_frontend_retired.py::test_frontend_untracked]
- AC2: the image has no node stage and no static dir [evidence: test:tests/test_frontend_retired.py::test_dockerfile_has_no_frontend_stage]
- AC3: CI runs no npm and has no frontend job [evidence: test:tests/test_frontend_retired.py::test_ci_has_no_npm]
- AC4: the schema drift test is retired and the README and openapi drift tests pass [evidence: command:uv run pytest -q tests/test_readme_api.py && ! grep -n test_frontend_schema_matches_openapi tests/test_readme_api.py]
- AC5: the image builds and runs [evidence: command:docker build -t agent-orchestrator:no-ui . && docker run --rm agent-orchestrator:no-ui --help]
- AC6: the API-only kind e2e passes [evidence: command:mise run test:e2e]
- AC7: README and MEMORY point at agents-web [evidence: command:grep -q agents-web README.md && grep -q agents-web MEMORY.md && ! grep -n 'npm ' README.md | grep -v 'sync:api -- orchestrator']
- AC8: no frontend change landed after the import [evidence: judgement:the task notes quote the empty git diff --stat <ao-sha> HEAD -- frontend]

## Files

- `frontend`
- `Dockerfile`
- `.github/workflows/ci.yaml`
- `tests/test_readme_api.py`
- `tests/test_frontend_retired.py`
- `.gitignore`
- `README.md`
- `MEMORY.md`

## Interfaces

- Owns `orch-no-ui` (contract `orch-ui-retired`): agent-orchestrator has no `frontend/`; UI work targets agents-web; an orchestrator route change is followed by `npm run sync:api -- orchestrator` in agents-web. Contract `agent-orchestrator-image` keeps its name and tag scheme.

## Expected outcome

agent-orchestrator is a Python-only repo: pytest needs no node, the image is smaller, CI has no npm, and the kind e2e is green.

## Steps

- Check the precondition; quote the diff in the notes.
- Red: `tests/test_frontend_retired.py`; `uv run pytest -q tests/test_frontend_retired.py` fails (frontend tracked, node stage present).
- Green: `git rm -r frontend`, edit Dockerfile, ci.yaml, test_readme_api.py, .gitignore, README.md, MEMORY.md.
- `uv run pytest -q tests/test_frontend_retired.py tests/test_readme_api.py tests/test_images.py && mise run lint`: pass. Then the docker build and `mise run test:e2e`. Name "deletion pinned by a retirement test" in tests.note.

## Notes

- Local testcontainers Postgres may fail to start on this machine (discovery brief section 1); the targeted tests here need no database. If `mise run test:e2e` fails for a local Docker reason, quote the output and the CI `e2e` job result of the pushed branch.
- `.github/` in the diff makes the review tier full.

- 2026-10-25 amended: AC7 contradicted the requirement's README note 'npm run sync:api -- orchestrator in agents-web'; the grep now allows that one note

- 2026-10-25 done
