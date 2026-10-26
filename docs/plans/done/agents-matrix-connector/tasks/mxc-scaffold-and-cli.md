---
title: mxc scaffold and cli
status: done
repo: agents-matrix-connector
value: the connector has a Python project with agents-common on session names and a console script to grow
files: [pyproject.toml, uv.lock, .mise.toml, src/agents_matrix_connector/__init__.py, src/agents_matrix_connector/cli.py, tests/conftest.py, tests/test_cli.py, README.md]
verify: "uv lock --check && uv run --frozen pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: 936fea8e5e92d4fe0f11898164bd4d5d5f45940b
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: 2
actual_minutes: 2
actual_tokens: 436547
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 320124, review 116423"
---

# mxc scaffold and cli

## Requirement

Turn the component-add scaffold of `code/agents-matrix-connector` (orchestrator step O1) into the Python project of the connector (design D1, D15). Paths are in code/agents-matrix-connector.

- `pyproject.toml`: project `agents-matrix-connector`, `requires-python >=3.12`, version `0.1.0`; dependencies `agents-common @ git+https://github.com/szymonrychu/agents-common@<tag>` where `<tag>` is `v0.3.0` (the release with session names, tagged at 6dd79c8 on 2026-10-25; task mxc-common-session-names then only confirms the pin and the session names), `fastapi`, `uvicorn[standard]`, `httpx`; dev group `agents-common[testing] @ git+...@<same tag>`, `ruff`, `pytest`, `pytest-asyncio` (the agents-webhook `pyproject.toml` layout: `[tool.pytest.ini_options] pythonpath = ["src", "tests"]`, `asyncio_mode = "auto"`, the same ruff settings); console script `agents-matrix-connector = "agents_matrix_connector.cli:main"`.
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
- AC3: agents-common is pinned to tag v0.3.0 [evidence: command:grep -q 'agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0' pyproject.toml && uv run --frozen python -c "import agents_common"]
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

- `src/agents_matrix_connector/cli.py`: `main(argv: Sequence[str] | None = None) -> int`, `SUBCOMMANDS`, `EXIT_BAD_SETTINGS`. Extended by mxc-service-entrypoints.
- `pyproject.toml` console script `agents-matrix-connector` (contract `agents-matrix-connector-image` entrypoint).

## Expected outcome

`uv run agents-matrix-connector --version` prints `agents-matrix-connector 0.1.0`; `uv run pytest tests/test_cli.py` passes; the project installs agents-common with session names.

## Steps

- Red: write `tests/test_cli.py` (`test_version`, `test_unknown_subcommand_exits_2`, calling `main([...])` and capturing output). `uv run pytest tests/test_cli.py -q` fails: no package.
- Green: write `pyproject.toml`, `uv lock`, the package and `cli.py`, `tests/conftest.py`, the mise tasks and README section. Run the verify: tests pass, lint clean.

## Notes

- Mirror `code/agents-webhook/pyproject.toml` and `mise.toml`; do not copy its modules.
- If no agents-common tag with `create_session` exists yet, end `blocked`, whoCanClear "orchestrator: orchestrator-rename-sessions must release agents-common with session names" (this epic is blocked by that epic, design D15).
- Design D16: model choice per task is recorded in design.md.

- 2026-10-25 amended: gate item 16 (user 'Go' 2026-10-25): start the connector before orchestrator-rename-sessions; pin agents-common v0.2.0 now, bump in mxc-common-session-names

- 2026-10-25 amended: agents-common v0.3.0 is tagged (6dd79c8); pin it directly (main orchestrator, 2026-10-25)

- 2026-10-25 done
