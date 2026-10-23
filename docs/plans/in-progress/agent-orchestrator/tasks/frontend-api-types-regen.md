---
title: frontend api types regen
status: todo
repo: agent-orchestrator
value: API changes always ship with matching frontend types
files: [frontend/src/api/schema.d.ts, tests/test_readme_api.py]
verify: "cd frontend && npm run check:api && cd .. && uv run pytest tests/test_readme_api.py -q -p no:cacheprovider && mise run lint"
depends_on: [fe-api-client-and-stream, readme-api-and-openapi]
owns: []
uses: []
model: ""
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

# frontend api types regen

## Requirement

CI frontend job fails at npm run check:api: frontend/src/api/schema.d.ts is stale against openapi.json (bench-cli 503cf0d added TurnView.usage to openapi.json without regenerating the types). Regenerate with npm run gen:api, commit, and make the backend drift test (tests that pin openapi.json) also fail when frontend/src/api/schema.d.ts is stale, so a future API change cannot land without regenerating the frontend types.

## Acceptance conditions

- AC1: npm run check:api passes [evidence: command:cd frontend && npm run check:api]
- AC2: a Python test fails when schema.d.ts does not match openapi.json [evidence: test:tests/test_readme_api.py::test_frontend_schema_matches_openapi]

## Files

- `frontend/src/api/schema.d.ts`
- `tests/test_readme_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

Frontend API types match openapi.json, enforced by a backend test.

What is true and observable when the task is done.

## Steps

- Red: CI check:api diff (usage field missing); write the backend drift test, see it fail.
- Run npm run gen:api; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
