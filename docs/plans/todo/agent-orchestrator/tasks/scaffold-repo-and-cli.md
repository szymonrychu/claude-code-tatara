---
title: scaffold repo and cli
status: todo
repo: agent-orchestrator
value: "Gives every later task a Python project that builds, lints and tests, CI that runs both, and the `orch` command the entrypoints hang on."
files: [pyproject.toml, uv.lock, mise.toml, .github/workflows/ci.yaml, src/agent_orchestrator/__init__.py, src/agent_orchestrator/cli.py, tests/test_cli.py, README.md]
verify: "uv run pytest tests/test_cli.py -q && mise run lint"
depends_on: []
owns: [orch-cli]
uses: [any-mcp-config]
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

# scaffold repo and cli

## Requirement

Create the Python project at the root of code/agent-orchestrator.

- uv project `agent-orchestrator`, Python 3.12, src layout, package `agent_orchestrator` with `__version__`, console script `orch = agent_orchestrator.cli:main`.
- pyproject declares every runtime dependency of the epic (D22: `any-mcp @ git+https://github.com/szymonrychu/any-mcp@<full sha of any-mcp origin/main at implementation time>` is one of them, so `ClusterSpec.any_mcp_config` is validated against the real any-mcp config model; container-images-ci re-pins it to the release tag): fastapi==0.160.0, uvicorn[standard], psycopg[binary,pool]==3.3.6, httpx, lightkube==1.0.1, pydantic, pydantic-settings, pyyaml. Dev group: pytest, pytest-asyncio, testcontainers[postgres], ruff, and `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<sha>` pinned to the full sha of claude-code-wrapper origin/main at implementation time (container-images-ci re-pins it to the sha of the image it builds from). No later task edits pyproject.toml or uv.lock except container-images-ci.
- pytest config: `pythonpath = ["src", "tests"]`, `asyncio_mode = "auto"`, markers `integration` (needs a real wrapper image) and `e2e` (needs kind), `addopts = "-q -m 'not integration and not e2e'"`.
- ruff config: line length 100, target py312, rules E, F, I, UP, B, SIM.
- mise.toml: tools python 3.12 and uv; tasks `lint` (`uv run ruff check . && uv run ruff format --check .`), `fmt`, `test` (`uv run pytest`), `test:integration` (`uv run pytest -m integration`), `test:e2e` (`uv run pytest -m e2e tests/e2e`).
- `.github/workflows/ci.yaml` on push to main and on pull requests, ubuntu-latest: job `lint` (mise run lint) and job `test` (mise run test; docker is available for testcontainers).
- `cli.py`: argparse front end with a command registry `register(name, func, help)`; `orch --version` prints the package version; `orch` with no command prints help and exits 2; an unknown command exits 2; a registered command is dispatched with its parsed args and its return code is the exit code.
- README.md: what the component is (one paragraph from design.md Summary) and a `## Development` section naming the mise tasks.
- `.gitignore` for .venv, __pycache__, node_modules, frontend/dist.

## Acceptance conditions

- AC1: orch --version prints the package version [evidence: test:tests/test_cli.py::test_version_prints_package_version]
- AC2: a registered command is dispatched and its return code becomes the exit code [evidence: test:tests/test_cli.py::test_registered_command_dispatches]
- AC3: no command or an unknown command exits 2 with help [evidence: test:tests/test_cli.py::test_unknown_command_exits_2]
- AC4: the console script is installed [evidence: command:uv run orch --version]
- AC5: lint passes on the new project [evidence: command:mise run lint]
- AC6: CI runs lint and the test suite on pull requests [evidence: command:grep -q 'pull_request' .github/workflows/ci.yaml && grep -q 'mise run test' .github/workflows/ci.yaml && grep -q 'mise run lint' .github/workflows/ci.yaml]
- AC7: the any-mcp config model is importable, so cluster specs can be validated against it [evidence: command:uv run python -c 'from any_mcp.config import AnyMcpConfig']

## Files

- `pyproject.toml`
- `uv.lock`
- `mise.toml`
- `.github/workflows/ci.yaml`
- `src/agent_orchestrator/__init__.py`
- `src/agent_orchestrator/cli.py`
- `tests/test_cli.py`
- `README.md`

## Interfaces

- `agent_orchestrator.cli:main(argv: list[str] | None = None) -> int`
- `agent_orchestrator.cli:register(name: str, func: Callable[[argparse.Namespace], int], help: str, configure: Callable[[argparse.ArgumentParser], None] | None = None) -> None` (contract `orch-cli`; entrypoints-and-singleton and bench-cli register their commands through it).

## Expected outcome

`uv run orch --version` prints the version, `mise run lint` and `uv run pytest tests/test_cli.py -q` pass, and CI runs lint and tests.

## Steps

- Write tests/test_cli.py with the three named tests; run `uv run pytest tests/test_cli.py -q`; expect failures (module not found).
- Write pyproject.toml, mise.toml, the package and cli.py; run `uv lock` and commit uv.lock.
- Rerun `uv run pytest tests/test_cli.py -q`; expect `3 passed`.
- Write ci.yaml and README.md; run `mise run lint`; expect `All checks passed!`.

## Notes

The repo, its GitHub origin and the superrepo submodule pointer are created by the orchestrator before the run; this task fills the empty repo. Declare every dependency now so later tasks never touch pyproject.toml or uv.lock (they would collide at merge). Mirror the wrapper's mise task names (code/claude-code-wrapper/mise.toml).
