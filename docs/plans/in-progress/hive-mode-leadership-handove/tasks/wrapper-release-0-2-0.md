---
title: wrapper release 0.2.0
status: in-progress
repo: claude-code-wrapper
value: the orchestrator can pin an image with the notes inbox and the main-agent gate
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest tests/test_packaging.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-notes-delivery, main-agent-only-tools]
owns: [wrapper-release-0-2-0]
uses: [wrapper-notes-inbox, wrapper-main-agent-only-tools]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-wrapper-release-0-2-0/claude-code-wrapper
branch: hive-mode-leadership-handove-wrapper-release-0-2-0
verified_head: ""
run: ""
provides: []
---

# wrapper release 0.2.0

## Requirement

Foundation part F2 release. claude-code-wrapper 0.2.0 carries the notes inbox and `claude.main_agent_only_tools`.

- Version `0.2.0` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject`: pyproject version, `__version__` and `importlib.metadata.version("claude-code-wrapper")` agree.
- Release steps, run by the orchestrator once this epic's wrapper PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.2.0` on the merge commit (`release.yaml` retags `:0.2.0` and `:latest`; irreversible, listed in design.md), and amend `orch-pin-bumps` with the merge sha.

## Acceptance conditions

- AC1: pyproject, __version__ and the installed metadata all say 0.2.0 [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- AC2: after the merge the image claude-code-wrapper:<sha7> exists and tag v0.2.0 is pushed with a green release run [evidence: judgement:]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

## Interfaces

- Owns part `wrapper-release-0-2-0`: image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>` of the merge commit and tag `v0.2.0`.

## Expected outcome

Version 0.2.0 in the repo; after the merge the image and tag exist.

## Steps

- Red: add `test_version_matches_pyproject` expecting 0.2.0; run `uv run pytest tests/test_packaging.py -q`: fails.
- Green: bump the version and `uv lock`; run the verify command: passes.
- After merge (orchestrator): wait for `build.yaml` green, `git tag v0.2.0 <merge sha> && git push origin v0.2.0`, watch `release.yaml`.

## Notes

- README `### Release`: `release.yaml` fails when the `:<shortsha>` image is missing, so tag only after the main build is green.
