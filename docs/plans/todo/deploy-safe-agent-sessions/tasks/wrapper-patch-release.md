---
title: wrapper patch release
status: todo
repo: claude-code-wrapper
value: agents can run a wrapper image that continues interrupted turns
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-shutdown-turn-resume]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 641999
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper patch release

## Requirement

Design D5, user decision verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next patch, 0.3.2) and pyproject version fixed to match."

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Open question Q1 decides the number when slash-commands-from-chat tags v0.4.0 first (recommended: the next patch above the latest tag); otherwise 0.3.2.

Scope (claude-code-wrapper):
- Version `0.3.2` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py` (pyproject says 0.3.0 at tag v0.3.1 today); `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject`: pyproject, `__version__` and the installed metadata agree (the same test name slash-commands-from-chat uses, so the later bump only changes the number).
- The wrapper PR of this epic merges to `main` through the normal PR flow before the orchestrator pin task starts.
- Release steps, run by the orchestrator session (never a subagent) once merged: wait for `build.yaml` to push `claude-code-wrapper:<sha7>`, push tag `v0.3.2` on the merge commit (`release.yaml` retags `:0.3.2` and `:latest`; irreversible, listed in design.md), then amend orch-wrapper-pin-patch with the merge sha.
- AC3 is checked by the orchestrator session after it pushed the tag; implementer and reviewer check AC1, AC2 and AC4.

Notes: precedent: done epic leader-auto-handover task wrapper-release-0-3-0; retro: Harbor prunes sha7 tags, so the helmfile pins the release tag.

## Acceptance conditions

- AC1: pyproject, __version__ and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- AC2: the version is 0.3.2 [evidence: command:grep -q '^version = "0.3.2"' pyproject.toml]
- AC3: tag v0.3.2 exists on origin (orchestrator session, after the push) [evidence: command:git ls-remote --exit-code --tags origin v0.3.2]
- AC4: packaging tests and lint pass [evidence: command:uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
