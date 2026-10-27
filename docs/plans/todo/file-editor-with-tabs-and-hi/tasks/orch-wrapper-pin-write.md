---
title: orch wrapper pin write
status: todo
repo: agents-orchestrator
value: "CI's real-wrapper contract leg and kind e2e prove the save against the wrapper agents will run"
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/e2e/test_e2e_kind.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint"
depends_on: [orch-file-write-route, wrapper-file-write-route]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper pin write

## Requirement

Design D7, verbatim: "once the wrapper change is merged on claude-code-wrapper `main`, the orchestrator pins that merge commit in the dev dependency (`pyproject.toml`, `uv.lock`), README `## Images` and `e2e/agent-test.Dockerfile` (`BASE_IMAGE`, `WRAPPER_SHA`), and the kind e2e gets a write case, so CI's integration leg and e2e run the real route. Precedent: the download epic's `orch-wrapper-pin-download` and done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin`."

Needs a merged upstream: the claude-code-wrapper PR carrying task wrapper-file-write-route merged on `main`. Do not start before `git -C <wrapper checkout> fetch origin main` shows a `main` commit whose `src/claude_code_wrapper/api/files.py` has the `PUT` `files/content` route; the pin is that merge commit (40-character sha, image tag its first 7 characters). The orchestrator amends this task with the sha when the PR merges. The current pin (after the download epic) is replaced, not kept beside it.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<sha>`; `uv.lock` refreshed with `uv lock`.
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, `ARG WRAPPER_SHA=<sha>`.
- `README.md` `## Images`: the recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/e2e/test_e2e_kind.py`: new `test_files_write_through_api`, modelled on `test_files_list_and_read_through_api`: the agent writes a text file through its shell; the API reads it, writes new content with the loaded `mtime` and `size` (200, content read back equal), a second write with the old stamp answers 409 `file_changed`, `expected: null` overwrites, `../etc/passwd` answers 400 `invalid_path` and a missing path 404 `not_found`.

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the merge commit carrying the write route [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency and README image pin agree [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper package has the PUT content route [evidence: command:unset VIRTUAL_ENV && uv run --frozen python -c "import claude_code_wrapper.api.files as f, sys; sys.exit(0 if any(getattr(r, 'path', '').endswith('/files/content') and 'PUT' in getattr(r, 'methods', set()) for r in f.router.routes) else 1)"]
- ac4: (CI only, kind) the e2e write case passes against the real agent image (new) [evidence: command:mise run test:e2e]
- ac5: images and render suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/e2e/test_e2e_kind.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
