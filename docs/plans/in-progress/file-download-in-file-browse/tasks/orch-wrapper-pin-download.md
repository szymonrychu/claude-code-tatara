---
title: orch wrapper pin download
status: in-progress
repo: agents-orchestrator
value: "CI's real-wrapper contract leg and kind e2e prove the download against the wrapper agents will run"
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/e2e/test_e2e_kind.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint"
depends_on: [orch-file-download-route, wrapper-file-download-route]
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

# orch wrapper pin download

## Requirement

Design D9, verbatim: "once the wrapper change is merged on claude-code-wrapper `main`, the orchestrator pins that merge commit in the dev dependency (`pyproject.toml`, `uv.lock`), README `## Images` and `e2e/agent-test.Dockerfile` (`BASE_IMAGE`, `WRAPPER_SHA`), and the kind e2e gets a download case, so CI's integration leg and e2e run the real route. Precedent: done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin`."

Needs a merged upstream: the claude-code-wrapper PR carrying task wrapper-file-download-route merged on `main`. Do not start before `git -C <wrapper checkout> fetch origin main` shows a `main` commit whose `src/claude_code_wrapper/api/files.py` has the `files/download` route; the pin is that merge commit (40-character sha, image tag its first 7 characters). Merged (2026-10-27): claude-code-wrapper PR #5, merge commit `4581f3bff79741d934272653c1a93d0ccfc95ba8`; `<sha>` is that value and `<sha7>` is `4581f3b`.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<sha>`; `uv.lock` refreshed with `uv lock`.
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, `ARG WRAPPER_SHA=<sha>`.
- `README.md` `## Images`: the recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/e2e/test_e2e_kind.py`: new `test_files_download_through_api`, modelled on `test_files_list_and_read_through_api`: the agent writes a text file and a binary file (bytes 0-255) through its shell; the API download returns them byte-exact with `Content-Disposition` attachment; `..`, `../etc/passwd` and `/etc/passwd` are 400 invalid_path; the listing entry of the file has `target_type` null.

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the merge commit carrying the download route [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency and README image pin agree [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper package has the download route [evidence: command:unset VIRTUAL_ENV && uv run --frozen python -c "import claude_code_wrapper.api.files as f, sys; sys.exit(0 if any(getattr(r, 'path', '').endswith('/files/download') for r in f.router.routes) else 1)"]
- ac4: (CI only, kind) the e2e download case passes against the real agent image (new) [evidence: command:mise run test:e2e]
- ac5: images and render suites and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py tests/test_render.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/e2e/test_e2e_kind.py`

## Interfaces

- The wrapper pin (pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` `BASE_IMAGE` and `WRAPPER_SHA`, README `## Images`), all one sha, the claude-code-wrapper `main` merge commit carrying wrapper-file-download-route.
- New kind e2e case `tests/e2e/test_e2e_kind.py::test_files_download_through_api`.

## Expected outcome

CI's integration contract leg and kind e2e build the agent image from the wrapper commit that has the download route, and the e2e proves a byte-exact download through the API.

## Steps

- Confirm the merged upstream (the requirement's precondition) and read the merge sha.
- Change the pyproject pin, run `uv lock`; run `unset VIRTUAL_ENV && uv run --frozen pytest tests/test_images.py`: the Dockerfile and README checks fail on the old sha.
- Update the Dockerfile args and README `## Images`, add the e2e case; run the task's verify: passes, quote the pytest summary line. The e2e runs in CI only.

## Notes

- `tests/test_images.py` ties pyproject, uv.lock, README Images and the Dockerfile to one sha (`test_ccw_dev_dependency_matches_agent_image_sha`, `test_agent_test_dockerfile_matches_dev_dependency`); `tests/test_render.py` validates rendered configs against the pinned wrapper's config schema.
- The Harbor image exists only for wrapper `main` builds; check with `regctl image digest` when credentials allow, else `scripts/e2e.sh` builds from source.
- Precedent: done epic web-ui-cluster-tabs-with-fil task `wrapper-sha-pin` (amended with the merge sha when the wrapper PR merged).

- 2026-10-27 amended: wrapper PR #5 merged at 4581f3b
