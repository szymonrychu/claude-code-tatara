---
title: orch package rename
status: todo
repo: agents-orchestrator
value: "the Python project is agents-orchestrator, consistent with every other agents-* component"
files: [pyproject.toml, uv.lock, src/, tests/, Dockerfile, .dockerignore, openapi.json]
verify: "uv run pytest -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch package rename

## Requirement

Rename the Python project from agent-orchestrator to agents-orchestrator (design D1, D10; user decision: agent-orchestrator becomes agents-orchestrator for consistency). Paths are in code/agents-orchestrator (the submodule after orchestrator step O2; the GitHub repo is szymonrychu/agents-orchestrator).

- `pyproject.toml`: `name = "agents-orchestrator"`, packages `src/agents_orchestrator`, console script `orch = "agents_orchestrator.cli:main"` (the `orch` name stays, D10); `uv.lock` refreshed with `uv lock`.
- `git mv src/agent_orchestrator src/agents_orchestrator`; every import, module path and string `agent_orchestrator` in src/ and tests/ becomes `agents_orchestrator`.
- The hyphenated name inside src/: `k8s/labels.py` `MANAGED_BY = "agents-orchestrator"`; `settings.py` default `claude_secret_name = "agents-orchestrator-claude"`; any other default, log line or docstring in src/ naming agent-orchestrator.
- `Dockerfile` and `.dockerignore`: package paths.
- `openapi.json`: regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json` (never hand-edited).
- `tests/test_project_name.py` (new, written first): `git ls-files src/agent_orchestrator` prints nothing (retirement); the pyproject name is agents-orchestrator; `git grep -n -E 'agent[-_]orchestrator'` over `src/`, `pyproject.toml`, `Dockerfile` and `openapi.json` finds nothing.
- Out of this task: the chart directory, CI, mise, scripts and e2e (orch-chart-ci-rename) and the docs (orch-docs-e2e-sessions). Only names change; the cluster vocabulary is later tasks' work.

## Acceptance conditions

- AC1: the old package path is gone from git [evidence: test:tests/test_project_name.py::test_old_package_retired]
- AC2: the distribution, package, managed-by label value and default Secret names say agents-orchestrator [evidence: test:tests/test_project_name.py::test_package_named_agents_orchestrator]
- AC3: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC4: the component suite and lint pass [evidence: command:uv run pytest -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/`
- `tests/`
- `Dockerfile`
- `.dockerignore`
- `openapi.json`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
