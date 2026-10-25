---
title: wrapper sha pin
status: done
repo: agent-orchestrator
value: integration and e2e runs exercise the real wrapper with the new file and terminal APIs
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/test_images.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-ws-relay, wrapper-workspace-e2e]
model: ""
review: ""
verified_head: 2edeb38eb5b2d6a1f279722387444ec0b6291f04
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 6
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper sha pin

## Requirement

Pin agent-orchestrator to the claude-code-wrapper commit that carries this epic's file and terminal APIs (design D9), so the integration contract suite and the kind e2e run against the real new wrapper.

The pin is claude-code-wrapper main merge commit `1ced7750483ee3eecdda5b6b26adc87405680ab1` (sha7 `1ced775`), the merge of PR szymonrychu/claude-code-wrapper#2 carrying this epic's file and terminal APIs.

- `pyproject.toml` dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@1ced7750483ee3eecdda5b6b26adc87405680ab1` and `uv.lock` (`uv lock`).
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:1ced775` and `ARG WRAPPER_SHA=1ced7750483ee3eecdda5b6b26adc87405680ab1`.
- README `## Images`: the recommended agent image is `harbor.szymonrichert.pl/containers/claude-code-wrapper:1ced775`.
- `tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha` keeps passing (it ties pyproject, uv.lock and README together); a new `test_agent_test_dockerfile_matches_dev_dependency` ties the Dockerfile `BASE_IMAGE` tag and `WRAPPER_SHA` to the same sha.
- `tests/test_render.py` keeps passing against the new wrapper's config schema.

## Acceptance conditions

- AC1: pyproject, uv.lock, README Images and the agent-test Dockerfile all name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the existing pin consistency test passes on the new sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the renderer's config validation passes on the new wrapper [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_render.py]
- AC4: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/test_images.py`

## Interfaces

- The wrapper pin (owns part `wrapper-main-pin`, consumed by kind-e2e-workspace): pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` args, README `## Images`.

## Expected outcome

`mise run test:integration` and the CI e2e job build the test agent image from the wrapper commit that has the file and terminal APIs.

## Steps

- Add `test_agent_test_dockerfile_matches_dev_dependency` to `tests/test_images.py`, then change the pyproject pin and run `uv lock`; run `uv run pytest -q -p no:cacheprovider tests/test_images.py`: the new test and `test_ccw_dev_dependency_matches_agent_image_sha` fail (Dockerfile and README still name ca2ddf3).
- Update the Dockerfile args and README `## Images`; run the verify command: passes.

## Notes

- Precedent: done epic agent-orchestrator task `container-images-ci` (dev dependency pinned to the wrapper main merge commit; README Images names the image).
- The Harbor image `claude-code-wrapper:<sha7>` exists only for main builds of the wrapper; check with `docker manifest inspect` or `regctl image digest` when credentials allow; without credentials `scripts/e2e.sh` builds the same commit from source.
- `tests/test_fake_wrapper_contract.py` without `-m integration` runs the fake only; the real-image run is the CI integration and e2e jobs.

- 2026-10-24 amended: wrapper PR #2 merged as 1ced775
