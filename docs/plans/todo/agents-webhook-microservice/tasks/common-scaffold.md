---
title: common scaffold
status: todo
repo: agents-common
value: "the shared library repo exists with a package, tooling and CI, so the trigger services can depend on it"
files: [pyproject.toml, uv.lock, mise.toml, .github/workflows/ci.yaml, src/agents_common/__init__.py, tests/test_package.py, README.md]
verify: "uv run pytest tests/test_package.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: []
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# common scaffold

## Requirement

Turn the scaffolded `code/agents-common` into an installable Python library (design D1, D15). Paths are in code/agents-common.

Precondition, checked first: `code/agents-common` is a submodule of the superrepo with origin `https://github.com/szymonrychu/agents-common` (created by epic agents-webhook-component, task create-agents-common-repo, D15). If it is missing, end `blocked` with whoCanClear "orchestrator: run epic agents-webhook-component and `git submodule update --init code/agents-common`".

- `pyproject.toml`: project `agents-common`, version `0.1.0`, `requires-python >=3.12`, src layout package `agents_common`, dependencies `psycopg[binary,pool]>=3.2`, `pydantic-settings>=2`, `httpx>=0.27`, `starlette>=0.40`; optional extra `testing` with `pytest`, `pytest-asyncio`, `testcontainers[postgres]`; dev group with ruff and the testing extra; ruff config copied from agent-orchestrator (line length, rules). `uv lock`.
- `mise.toml`: tasks `install`, `test` (`uv run pytest`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `fmt`, matching agent-orchestrator's.
- `.github/workflows/ci.yaml`: jobs `lint` and `test` on push and pull_request, uv setup as in agent-orchestrator's `ci.yaml`; Docker available for testcontainers in `test`.
- `src/agents_common/__init__.py`: `__version__` read from package metadata.
- `tests/test_package.py`: the package imports and `__version__ == "0.1.0"`; replaces the scaffold smoke test if it duplicates it.
- `README.md`: one paragraph on what the library is, the install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0`, and the module list (filled per module by later tasks).

## Acceptance conditions

- AC1: the package installs and reports version 0.1.0 [evidence: command:uv run pytest tests/test_package.py -q]
- AC2: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC3: CI runs lint and test on push and pull_request [evidence: command:grep -q "ruff check" .github/workflows/ci.yaml && grep -q "pytest" .github/workflows/ci.yaml]
- AC4: the submodule exists with the GitHub origin [evidence: command:git remote get-url origin | grep -q "szymonrychu/agents-common"]

## Files

- `pyproject.toml`
- `uv.lock`
- `mise.toml`
- `.github/workflows/ci.yaml`
- `src/agents_common/__init__.py`
- `tests/test_package.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
