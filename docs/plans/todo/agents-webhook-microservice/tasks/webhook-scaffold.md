---
title: webhook scaffold
status: todo
repo: agents-webhook
value: the webhook service repo builds an image and runs a CLI pinned to the shared library
files: [pyproject.toml, uv.lock, mise.toml, Dockerfile, .dockerignore, src/agents_webhook/__init__.py, src/agents_webhook/cli.py, tests/test_cli.py]
verify: "uv run pytest tests/test_cli.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-release-v0-1-0]
owns: []
uses: [agents-common-lib]
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

# webhook scaffold

## Requirement

Turn the scaffolded `code/agents-webhook` into a Python service package (design D1, D2, D15). Paths are in code/agents-webhook.

Precondition, checked first: `code/agents-webhook` is a submodule with origin `https://github.com/szymonrychu/agents-webhook` (created by epic agents-webhook-component, task create-agents-webhook-repo), and tag `v0.1.0` of agents-common exists on origin. Otherwise end `blocked`, whoCanClear "orchestrator: run epic agents-webhook-component / push agents-common v0.1.0".

- `pyproject.toml`: project `agents-webhook` 0.1.0, `requires-python >=3.12`, dependencies `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0`, `fastapi`, `uvicorn[standard]`; dev group with `agents-common[testing]` (same tag), ruff, pytest, pytest-asyncio; console script `agents-webhook = agents_webhook.cli:main`; ruff config as agent-orchestrator. `uv lock`.
- `mise.toml`: tasks install, test, lint, fmt, `test:chart` (`uv run pytest tests/test_chart_*.py -q`), `lint:chart`, `test:e2e` (`uv run pytest tests/e2e -q`).
- `Dockerfile`: `python:3.12-slim`, uv sync from the lock, non-root USER 1000, entrypoint `agents-webhook` (no node stage); `.dockerignore`.
- `cli.py`: `main(argv)` with argparse subcommands `migrate`, `ingest`, `api`, `worker` and `--version`; this task implements `--version` and `--help` only and makes the four subcommands exit 2 with "not wired" until task webhook-cli-entrypoints.
- `tests/test_cli.py`: `--help` lists the four subcommands and exits 0; `--version` prints 0.1.0.

## Acceptance conditions

- AC1: the CLI help lists migrate, ingest, api and worker and --version prints 0.1.0 [evidence: command:uv run pytest tests/test_cli.py -q]
- AC2: agents-common is pinned to tag v0.1.0 [evidence: command:grep -q "agents-common@v0.1.0" pyproject.toml]
- AC3: the image builds and its entrypoint answers --help [evidence: command:docker build -q -t agents-webhook:dev . && docker run --rm agents-webhook:dev --help]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `mise.toml`
- `Dockerfile`
- `.dockerignore`
- `src/agents_webhook/__init__.py`
- `src/agents_webhook/cli.py`
- `tests/test_cli.py`

## Interfaces

- Uses `agents-common-lib` (tag v0.1.0). Console script `agents-webhook`.

## Expected outcome

`uv run agents-webhook --help` and the image work; later tasks fill the subcommands.

## Steps

- Check the preconditions.
- Red: `tests/test_cli.py`; run: fails.
- Green: pyproject, lock, cli; tests pass. Dockerfile; build it. Run the verify command.

## Notes

- Model on `code/agent-orchestrator/Dockerfile` (Python stage only) and `mise.toml`.
