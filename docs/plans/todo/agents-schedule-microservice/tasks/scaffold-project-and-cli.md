---
title: scaffold project and cli
status: todo
repo: agents-schedule
value: "every later task gets a Python project that builds, lints and tests, and the `sched` command its entrypoints hang on"
files: [pyproject.toml, uv.lock, .mise.toml, src/agents_schedule/__init__.py, src/agents_schedule/cli.py, tests/test_cli.py, README.md]
verify: "uv run --frozen pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [create-agents-schedule-repo]
owns: [sched-cli]
uses: [agents-schedule-repo, agents-common-lib]
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

# scaffold project and cli

## Requirement

Create the Python project at the root of code/agents-schedule (design D1, D2, D4; approvals A1, A8).

- uv project `agents-schedule`, src layout, package `agents_schedule` with `__version__`, console script `sched = agents_schedule.cli:main`. Python version: the floor `agents-common` declares (contract `agents-common-lib`, owned by agents-webhook-microservice); the Dockerfile base image uses the same minor.
- Runtime dependencies, every one the epic needs, pinned: `agents-common @ git+https://github.com/szymonrychu/agents-common@<tag>` (the tag the contract names), `croniter==6.2.4`, `tzdata` (so `zoneinfo` works in a slim image), `fastapi`, `uvicorn[standard]`, `httpx`, `psycopg[binary,pool]`, `pydantic`, `pydantic-settings`. Dev group: `pytest`, `pytest-asyncio`, `testcontainers[postgres]`, `ruff`. No later task edits pyproject.toml or uv.lock.
- pytest config: `pythonpath = ["src", "tests"]`, `asyncio_mode = "auto"`, marker `e2e`, `addopts = "-q -m 'not e2e'"`. ruff: line length 100, rules E, F, I, UP, B, SIM.
- `.mise.toml` tasks: `test` (`uv run pytest`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `fmt`, `test:e2e` (`bash scripts/e2e.sh`), `test:chart` (`uv run pytest tests/test_chart.py tests/test_chart_ingress.py`), `lint:chart` (`helm lint chart/agents-schedule --set postgres.url=postgresql://x/y --set orchestrator.url=http://o --set orchestrator.token.existingSecret=t`); the files they name arrive with `helm-chart`, `chart-ingress-and-test-hook` and `kind-e2e-api`.
- `cli.py`: argparse front end with `register(name, func, help, configure=None)`; `sched --version` prints the version; no command prints help and exits 2; an unknown command exits 2; a registered command's return code is the exit code.
- README `## Development` names the mise tasks.
- `tests/test_smoke.py` from the scaffold is removed in favour of `tests/test_cli.py`.

## Acceptance conditions

- AC1: sched --version prints the package version [evidence: test:tests/test_cli.py::test_version_prints_package_version]
- AC2: a registered command is dispatched and its return code becomes the exit code [evidence: test:tests/test_cli.py::test_registered_command_dispatches]
- AC3: no command or an unknown command exits 2 with help [evidence: test:tests/test_cli.py::test_unknown_command_exits_2]
- AC4: the console script is installed [evidence: command:uv run sched --version]
- AC5: the shared library and the cron library import [evidence: command:uv run python -c 'import agents_common, croniter, zoneinfo; zoneinfo.ZoneInfo("Europe/Warsaw")']
- AC6: lint passes on the new project [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `.mise.toml`
- `src/agents_schedule/__init__.py`
- `src/agents_schedule/cli.py`
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

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
