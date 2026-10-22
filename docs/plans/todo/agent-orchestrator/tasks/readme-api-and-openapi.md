---
title: readme api and openapi
status: todo
repo: agent-orchestrator
value: "A documented, versioned contract for tatara, magic-trainer and the UI, enforced by a parity test and an OpenAPI drift check."
files: [README.md, MEMORY.md, ROADMAP.md, openapi.json, src/agent_orchestrator/api/openapi.py, tests/test_readme_api.py]
verify: "uv run pytest tests/test_readme_api.py -q && mise run lint"
depends_on: [api-events-and-streams]
owns: [openapi-v1]
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

# readme api and openapi

## Requirement

API documentation and its enforcement (D2, D11).

README.md sections:
- `## API`: every route with method, path, request body, response and error codes, plus a `### Events` table of the SSE event names of both streams, and the versioning rule (additive only within v1).
- `## Architecture`: the process table of D1; the writer-per-table table with the single-writer interpretation of no shared state; the NOTIFY channels and their payloads; the polling fallbacks.
- `## Data model`.

OpenAPI:
- `src/agent_orchestrator/api/openapi.py`: `export() -> str`, deterministic JSON with sorted keys and a trailing newline; `python -m agent_orchestrator.api.openapi` prints it.
- `openapi.json` is committed at the repo root.

MEMORY.md records the single-writer interpretation, one session per pod, and why events are stored rather than proxied. ROADMAP.md lists the bench experiment.

`tests/test_readme_api.py` asserts:
- every (method, path) of `create_app()` under /api/v1 appears in `## API`
- every route in `## API` exists in the app
- `openapi.json` equals `export()`
- every SSE event name the stream module emits appears in `### Events`

## Acceptance conditions

- AC1: every app route is documented in README API [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- AC2: README documents no route the app lacks [evidence: test:tests/test_readme_api.py::test_no_stale_route_in_readme]
- AC3: the committed openapi.json equals the export [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC4: every SSE event name is documented [evidence: test:tests/test_readme_api.py::test_sse_event_types_documented]
- AC5: README states the single-writer interpretation [evidence: doc-section:README.md#Architecture]

## Files

- `README.md`
- `MEMORY.md`
- `ROADMAP.md`
- `openapi.json`
- `src/agent_orchestrator/api/openapi.py`
- `tests/test_readme_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
