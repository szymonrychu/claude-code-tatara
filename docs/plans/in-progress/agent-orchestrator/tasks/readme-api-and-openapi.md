---
title: readme api and openapi
status: done
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-readme-api-and-openapi/agent-orchestrator
branch: agent-orchestrator-readme-api-and-openapi
verified_head: 87131ab81f8148581b962afcca93d4386b0095c5
run: agent-orchestrator
provides: [openapi-v1]
acs_for_audit: []
process_gaps: []
---

# readme api and openapi

## Requirement

API documentation and its enforcement (D2, D11).

README.md sections:
- `## API`: every route with method, path, request body, response and error codes, plus a `### Events` table of the SSE event names of both streams, and the versioning rule (additive only within v1).
- `## Architecture`: the process table of D1; the writer-per-table table with the single-writer interpretation of no shared state; the NOTIFY channels and their payloads; the polling fallbacks.
- `## Data model`.
- The `## API` section documents the 403 `forbidden` source-allowlist error (`ORCH_ALLOWED_CIDRS`, direct peer only, health routes exempt), the 409 `cluster_limit` error and the `meta` caps (D22).

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
- AC6: README API documents the forbidden and cluster_limit errors and ORCH_ALLOWED_CIDRS [evidence: test:tests/test_readme_api.py::test_readme_documents_allowlist_and_limits]

## Files

- `README.md`
- `MEMORY.md`
- `ROADMAP.md`
- `openapi.json`
- `src/agent_orchestrator/api/openapi.py`
- `tests/test_readme_api.py`

## Interfaces

- `agent_orchestrator.api.openapi:export() -> str`; `openapi.json` (contract `openapi-v1`, consumed by the frontend type generator)

## Expected outcome

README is the spec, kept in parity with the code, and `openapi.json` is the source of the UI's types.

## Steps

- Write tests/test_readme_api.py with the five named tests; run it; expect failures.
- Write openapi.py, export openapi.json, and write the README sections, MEMORY.md and ROADMAP.md.
- Rerun `uv run pytest tests/test_readme_api.py -q`; expect `5 passed`; run `mise run lint`.

## Ruling

- 2026-10-23 accepted: gate-repeat on a parking-wording false positive: ROADMAP.md:5 describes the bench experiment the epic delivers (bench-cli task), it defers nothing; verified true.

- 2026-10-23 accepted: parking false positive at ROADMAP.md:5; verified true.

## Notes

Modelled on claude-code-wrapper's tests/test_readme_api.py. Any later route change must regenerate openapi.json; spa-serving-and-dockerfile adds the CI drift step for the frontend types.
