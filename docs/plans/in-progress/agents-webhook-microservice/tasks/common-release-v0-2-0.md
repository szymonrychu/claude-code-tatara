---
title: common release v0-2-0
status: todo
repo: agents-common
value: the webhook and schedule services can pin the agent-reuse support by tag
files: [pyproject.toml, uv.lock, src/agents_common/__init__.py, README.md, CHANGELOG.md, tests/test_release.py]
verify: "uv run pytest tests/test_release.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-reuse-running]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 13
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common release v0-2-0

## Requirement

Release agents-common v0.2.0 with the agent-reuse support (design D19; contract `agents-common-lib`). Paths are in code/agents-common.

- `pyproject.toml` and `src/agents_common/__init__.py`: version 0.2.0; `uv lock`.
- `README.md`: install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.2.0`.
- `CHANGELOG.md`: `## v0.2.0` entry naming `Preset.spec`, `Preset.reuse_running_agent`, `Cluster.status`, `runs.running_cluster`, `runs.deliver`, `runs.track_delivery` and the fake orchestrator helpers; v0.1.0 names unchanged.
- `tests/test_release.py`: pyproject version, `__version__`, CHANGELOG top entry and README install line agree on 0.2.0; every module named in the README exists.
- Release step, run by the orchestrator once this epic's agents-common PR with this task is merged to `main`: push tag `v0.2.0` on the merge commit (irreversible, listed in design.md; tags are never re-pointed), confirm CI on the tag is green and `uv pip install "agents-common @ git+https://github.com/szymonrychu/agents-common@v0.2.0"` installs in a fresh venv. Until then task webhook-reuse-routing stays blocked.

## Acceptance conditions

- AC1: version, CHANGELOG, README install line and package metadata agree on 0.2.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: the README documents every public module [evidence: test:tests/test_release.py::test_modules_documented_and_exist]
- AC3: tag v0.2.0 exists on origin on the main merge commit and installs [evidence: judgement:the task notes quote git ls-remote --tags origin v0.2.0 and the install output]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agents_common/__init__.py`
- `README.md`
- `CHANGELOG.md`
- `tests/test_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
