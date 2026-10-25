---
title: mxc scaffold and cli
status: todo
repo: agents-matrix-connector
value: the connector has a Python project with agents-common on session names and a console script to grow
files: [pyproject.toml, uv.lock, .mise.toml, src/agents_matrix_connector/__init__.py, src/agents_matrix_connector/cli.py, tests/conftest.py, tests/test_cli.py, README.md]
verify: "uv lock --check && uv run --frozen pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc scaffold and cli

## Requirement

Turn the component-add scaffold of `code/agents-matrix-connector` (orchestrator step O1) into the Python project of the connector (design D1, D15). Paths are in code/agents-matrix-connector.

- `pyproject.toml`: project `agents-matrix-connector`, `requires-python >=3.12`, version `0.1.0`; dependencies `agents-common @ git+https://github.com/szymonrychu/agents-common@<tag>` where `<tag>` is the newest agents-common tag whose `agents_common.orchestrator.OrchestratorClient` has `create_session` (released by epic orchestrator-rename-sessions; find it with `git ls-remote --tags https://github.com/szymonrychu/agents-common`), `fastapi`, `uvicorn[standard]`, `httpx`; dev group `agents-common[testing] @ git+...@<same tag>`, `ruff`, `pytest`, `pytest-asyncio` (the agents-webhook `pyproject.toml` layout: `[tool.pytest.ini_options] pythonpath = ["src", "tests"]`, `asyncio_mode = "auto"`, the same ruff settings); console script `agents-matrix-connector = "agents_matrix_connector.cli:main"`.
- `uv.lock` from `uv lock`.
- `.mise.toml` (the scaffold's mise config): tasks `install`, `test`, `lint`, `fmt`, `test:chart`, `lint:chart` as agents-webhook's `mise.toml`, chart path `chart/agents-matrix-connector`.
- `src/agents_matrix_connector/__init__.py`: `__version__` read from the installed package metadata.
- `src/agents_matrix_connector/cli.py`: `main(argv=None) -> int` with argparse: `--version` prints `agents-matrix-connector <version>` and exits 0; `--help` exits 0; a `SUBCOMMANDS: dict[str, str]` table (empty in this task; task mxc-service-entrypoints registers `migrate`, `api` and `bot`); an unknown subcommand exits 2 with the usage on stderr; exit code constant `EXIT_BAD_SETTINGS = 78`.
- `tests/conftest.py` registers the `agents_common.testing` pytest plugin (`pytest_plugins = ["agents_common.testing"]`), as agents-webhook does.
- `README.md`: keep the scaffold's `## What this is`; add `## Development` naming `mise run test` and `mise run lint`, and that DB tests need Docker (testcontainers).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: `agents-matrix-connector --version` prints the package version and exits 0 [evidence: test:tests/test_cli.py::test_version]
- AC2: an unknown subcommand exits 2 and prints the usage to stderr [evidence: test:tests/test_cli.py::test_unknown_subcommand_exits_2]
- AC3: agents-common is pinned to a tag whose client has session names [evidence: command:grep -q 'agents-common @ git+https://github.com/szymonrychu/agents-common@v' pyproject.toml && uv run --frozen python -c "from agents_common.orchestrator import OrchestratorClient; assert hasattr(OrchestratorClient, 'create_session')"]
- AC4: the lock is current, the agents-common pytest plugin is registered and lint passes [evidence: command:uv lock --check && grep -q 'agents_common.testing' tests/conftest.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `.mise.toml`
- `src/agents_matrix_connector/__init__.py`
- `src/agents_matrix_connector/cli.py`
- `tests/conftest.py`
- `tests/test_cli.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
