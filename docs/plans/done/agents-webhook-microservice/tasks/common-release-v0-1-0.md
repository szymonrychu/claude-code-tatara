---
title: common release v0.1.0
status: done
repo: agents-common
value: "agents-webhook and later agents-schedule pin one tagged, documented library version"
files: [pyproject.toml, uv.lock, README.md, CHANGELOG.md, MEMORY.md, tests/test_release.py]
verify: "uv run pytest tests/test_release.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-db-helpers, common-settings-runtime, common-orchestrator-client, common-run-tracker]
model: ""
review: ""
verified_head: df9cb19
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 2
actual_tokens: 280505
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 204591, review 75914"
---

# common release v0.1.0

## Requirement

Document and release agents-common v0.1.0 (design D1; contract `agents-common-lib`). Paths are in code/agents-common.

- `README.md`: install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0`; one `##` section per module (`settings`, `db`, `runtime`, `orchestrator`, `fake_orchestrator`, `runs`, `testing`) with its public names and a short usage example; a `## Versioning` section: tags are never re-pointed, consumers pin a tag.
- `CHANGELOG.md`: `## v0.1.0` entry naming each module.
- `MEMORY.md`: dated 2026-10-25 lines: why a shared library (D1), the marker idempotency (D8).
- `tests/test_release.py`: pyproject version, `__version__`, CHANGELOG top entry and README install line agree on 0.1.0; every module named in the README exists.
- Release step, run by the orchestrator once this epic's agents-common PR is merged to `main`: push tag `v0.1.0` on the merge commit (irreversible, listed in design.md), confirm CI on the tag is green and `uv pip install "agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0"` installs in a fresh venv. Until then task webhook-scaffold stays blocked.

## Acceptance conditions

- AC1: version, CHANGELOG, README install line and package metadata agree on 0.1.0 [evidence: command:uv run pytest tests/test_release.py -q -k versions]
- AC2: the README documents every public module [evidence: command:uv run pytest tests/test_release.py -q -k modules]
- AC3: tag v0.1.0 exists on origin on the main merge commit and installs [evidence: judgement:the task notes quote git ls-remote --tags origin v0.1.0 and the install output]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `CHANGELOG.md`
- `MEMORY.md`
- `tests/test_release.py`

## Interfaces

- Owns `agents-common-lib`: tag `v0.1.0` of `github.com/szymonrychu/agents-common`, installable as `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.1.0`.

## Expected outcome

The library is documented and tagged; agents-webhook can pin it.

## Steps

- Red: `tests/test_release.py`; run: fails (no CHANGELOG).
- Green: README, CHANGELOG, MEMORY; tests pass. Run the verify command.
- After merge (orchestrator): `git tag v0.1.0 <merge sha> && git push origin v0.1.0`; `gh run watch` on the tag run.

## Notes

- Precedent: docs/plans/done/hive-mode-leadership-handove/tasks/any-mcp-release-v0-2-0.md.

- 2026-10-25 done
