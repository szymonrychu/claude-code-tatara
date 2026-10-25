---
title: common release v0.3.0
status: done
repo: agents-common
value: agents-webhook and agents-schedule can pin the session client
files: [pyproject.toml, uv.lock, CHANGELOG.md, README.md, tests/test_release.py]
verify: "uv run pytest -q tests/test_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-client-sessions]
model: sonnet
review: ""
verified_head: 931b1de
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: 1
actual_minutes: 3
actual_tokens: 266028
actual_roles: impl 3
actual_role_tokens: impl 266028
---

# common release v0.3.0

## Requirement

Release agents-common v0.3.0 with the session client (design D11; contract `agents-common-release-v0-3-0`). Paths are in code/agents-common.

- `pyproject.toml` `version = "0.3.0"`; `uv.lock` refreshed.
- `CHANGELOG.md`: `## v0.3.0` on top, Breaking: `Cluster` is `Session`, `create_cluster`/`get_cluster`/`running_cluster`/`set_cluster`/`discard_cluster`/`remove_cluster` are `create_session`/`get_session`/`running_session`/`set_session`/`discard_session`/`remove_session`, `RunRef.session_id`, reason `session_not_found`, routes `/api/v1/sessions` (needs agents-orchestrator with the session API).
- `README.md` install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0`; `tests/test_release.py` `INSTALL` and the expected version 0.3.0.
- Release step, run by the orchestrator once this epic's agents-common PR is merged to main: push tag `v0.3.0` on the merge commit (irreversible, listed in design.md), confirm the tag's CI and `uv pip install "agents-common @ git+https://github.com/szymonrychu/agents-common@v0.3.0"` in a fresh venv. Until then webhook-worker-sessions stays blocked.

## Acceptance conditions

- AC1: version, CHANGELOG, README install line and package metadata agree on 0.3.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: tag v0.3.0 exists on origin on the main merge commit and installs [evidence: judgement:the task notes quote git ls-remote --tags origin v0.3.0 and the install output]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

## Interfaces

- Tag `v0.3.0` (contract `agents-common-release-v0-3-0`).

## Expected outcome

agents-common 0.3.0 is documented, versioned and, after the release step, tagged on origin.

## Steps

- Red: set `INSTALL` and the expected version in `tests/test_release.py` to 0.3.0; it fails.
- Green: bump, `uv lock`, CHANGELOG, README; the verify passes. End "ready for tag".

## Notes

- Tags are never re-pointed.

- 2026-10-25 done
