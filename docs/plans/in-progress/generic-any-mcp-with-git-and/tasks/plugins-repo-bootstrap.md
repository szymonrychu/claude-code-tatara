---
title: plugins repo bootstrap
status: in-progress
repo: any-mcp-tatara-plugins
value: "the plugins bucket has Python 3.12 tooling, CI and a documented topic layout and notation"
files: [.mise.toml, pyproject.toml, uv.lock, .github/workflows/ci.yml, tests/test_smoke.py, tests/test_repo.py, README.md]
verify: "mise run install && mise run test && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins repo bootstrap

## Requirement

Goal G3 (epic README), verbatim: "any-mcp-tatara-plugins is a working repo: topic subdirectories, per-plugin packages, tests and lint in CI, documented source notation." User request, verbatim: "Create separate any-mcp-tatara-plugins repo, which will serve as a bucket for platform specific tools. Group them into topics in subdirs." Orchestrator design call, verbatim: "any-mcp-tatara-plugins layout: `<topic>/<plugin>/` (pyproject, src, tests); first topic `orchestration/` with the orchestrator plugin moved out of any-mcp ...; repo-level mise tasks run every plugin's tests and lint; README documents the topic layout and the source notation." Design D6 (tooling part). The scaffold pins `python = "3.14.6"` while any-mcp uses 3.12: this task moves the repo to 3.12.

Scope (any-mcp-tatara-plugins):
- `.mise.toml`: `python = "3.12"`, `uv`; tasks `install` (`uv sync` covering every workspace member), `test` (`uv run pytest`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `fmt` (`uv run ruff format . && uv run ruff check --fix .`); drop the `pipx:pytest` and standalone `ruff` tools.
- `pyproject.toml` (root, not a package): a uv workspace whose members are every `<topic>/<plugin>` directory holding a `pyproject.toml`; dev group `pytest>=8.3`, `pytest-asyncio`, `ruff`; ruff line-length 100, rules `E F I UP B SIM`, target py312; pytest collecting `tests/` and every `<topic>/<plugin>/tests/`, `asyncio_mode = "auto"`. any-mcp is added to the dev group by task plugins-orchestration-plugin.
- `uv.lock`.
- `.github/workflows/ci.yml`: like any-mcp's (`on: push, pull_request`, `permissions: contents: read`, `actions/checkout` and `jdx/mise-action` pinned by sha, `mise run install`, `mise run lint`, `mise run test`). No secrets.
- Delete `tests/test_smoke.py`: no longer accurate, it is the scaffold placeholder (`assert True`) and asserts nothing.
- New `tests/test_repo.py`: the tooling, CI, layout and README tests in the acceptance conditions.
- `README.md`: what the repo is (the platform-specific plugin bucket for any-mcp), the topic layout `<topic>/<plugin>/` (pyproject with an `any_mcp.plugins` entry point, `src/`, `tests/`), how to add a plugin, the source notation (local `./`, `../`, `/`; `git::https://github.com/szymonrychu/any-mcp-tatara-plugins.git//<topic>/<plugin>?ref=vX.Y.Z`; `github.com/szymonrychu/any-mcp-tatara-plugins//<topic>/<plugin>?ref=vX.Y.Z`), install with `any-mcp plugins install <source>` or a `source:` config entry, and releases as `vX.Y.Z` tags on main.

## Acceptance conditions

- ac1: mise pins python 3.12 and defines install, test, lint (ruff check and format check) and fmt tasks run through uv [evidence: test:tests/test_repo.py::test_mise_tooling]
- ac2: the interpreter running the tests is 3.12 [evidence: test:tests/test_repo.py::test_interpreter_is_312]
- ac3: CI runs mise run install, lint and test on push and pull_request with read-only permissions and sha-pinned actions [evidence: test:tests/test_repo.py::test_ci_workflow]
- ac4: every topic/plugin directory with a pyproject.toml is a uv workspace member, declares an any_mcp.plugins entry point and has a tests directory that the test run collects [evidence: test:tests/test_repo.py::test_plugin_layout]
- ac5: README documents the topic layout, adding a plugin, and the source notation with a git::, a github.com/ and a local example [evidence: test:tests/test_repo.py::test_readme_documents_layout_and_notation]
- ac6: the scaffold placeholder test is no longer tracked [evidence: command:test -z "$(git ls-files tests/test_smoke.py)"]
- ac7: install, test and lint pass [evidence: command:mise run install && mise run test && mise run lint]

## Files

- `.mise.toml`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/ci.yml`
- `tests/test_smoke.py`
- `tests/test_repo.py`
- `README.md`

## Interfaces

- `.mise.toml` tasks `install`, `test`, `lint`, `fmt` (the commands in the Requirement); later tasks and CI call only these.
- Layout contract pinned by `tests/test_repo.py::test_plugin_layout`: `<topic>/<plugin>/pyproject.toml` with an `[project.entry-points."any_mcp.plugins"]` table, `<topic>/<plugin>/src/`, `<topic>/<plugin>/tests/`; every such directory is a uv workspace member.

## Expected outcome

`mise run install && mise run test && mise run lint` pass on Python 3.12 locally and in CI, and the README tells a plugin author where a plugin goes and how users reference it.

## Steps

- Red: write `tests/test_repo.py`; run `uv run pytest -q tests/test_repo.py` (after a first `.mise.toml` python change so the interpreter is 3.12): fails.
- Green: `.mise.toml`, root `pyproject.toml`, `uv lock`, CI workflow, README; `git rm tests/test_smoke.py`; run the task's verify: passes.

## Notes

- The scaffold's `.mise.toml` pins `python = "3.14.6"`, `uv = "0.12.23"`, `ruff`, `pipx:pytest`; replace with any-mcp's shape (`python = "3.12"`, `uv`, `_.python.venv`).
- The workspace member glob must not pick up `tests/` or `.github/` (uv refuses a member without a pyproject); with no plugin yet, ac4 holds vacuously and becomes concrete in task plugins-orchestration-plugin.
- Same-named test modules in several plugins need pytest `--import-mode=importlib` or unique names: choose one and pin it in test_repo.py.
- CI action shas: copy any-mcp's `.github/workflows/ci.yml` pins.
- The repo is public and its CI needs no secrets (user, 2026-10-26).
