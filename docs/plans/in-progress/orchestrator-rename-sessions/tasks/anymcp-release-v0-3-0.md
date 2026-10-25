---
title: anymcp release v0.3.0
status: in-progress
repo: any-mcp
value: the orchestrator can pin an any-mcp release that speaks the session agent API
files: [pyproject.toml, uv.lock, CHANGELOG.md, README.md, tests/test_release.py]
verify: "uv run pytest -q tests/test_release.py -k \"versions_agree or pinned_install_line\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [anymcp-plugin-session]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 689196
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# anymcp release v0.3.0

## Requirement

Release any-mcp v0.3.0 carrying the session plugin (design D11; contract `any-mcp-release-v0-3-0`). Paths are in code/any-mcp.

- `pyproject.toml`: `version = "0.3.0"`; `uv.lock` refreshed with `uv lock`.
- `CHANGELOG.md`: `## v0.3.0` on top, a Breaking entry: the orchestrator plugin's config key `cluster` is now `session`, the header is `X-Orch-Session`, codes `static_session` and `next_session`; requires agents-orchestrator with the session agent API.
- `README.md` and `tests/test_release.py`: every pinned install line names `@v0.3.0` (`PINNED_LINE` included); `test_versions_agree` and `test_pinned_install_line_documented` pass on 0.3.0.
- Release step, run by the orchestrator (main session) once this epic's any-mcp PR is merged to main: push tag `v0.3.0` on the merge commit (irreversible, listed in design.md), confirm the tag's CI is green and `uv pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.3.0"` installs in a fresh venv. Until then orch-agent-api-sessions stays blocked.

## Acceptance conditions

- AC1: pyproject, package metadata and the CHANGELOG top entry agree on 0.3.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: the README documents the v0.3.0 pinned install line [evidence: test:tests/test_release.py::test_pinned_install_line_documented]
- AC3: tag v0.3.0 exists on origin on the main merge commit and installs [evidence: judgement:the task notes quote git ls-remote --tags origin v0.3.0 and the install output]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

## Interfaces

- Tag `v0.3.0` (contract `any-mcp-release-v0-3-0`): `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.3.0`.

## Expected outcome

any-mcp 0.3.0 is documented, versioned and, after the orchestrator's release step, tagged on origin.

## Steps

- Red: set the expected version and `PINNED_LINE` in `tests/test_release.py` to 0.3.0; `uv run pytest -q tests/test_release.py -k "versions_agree or pinned_install_line"` fails.
- Green: bump pyproject, `uv lock`, CHANGELOG and README; the verify passes.
- End the round "ready for tag": the orchestrator tags after the PR merges and pastes the `git ls-remote` line into the notes.

## Notes

- Tags are never re-pointed; a wrong tag means v0.3.1.
