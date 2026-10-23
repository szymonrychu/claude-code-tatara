---
title: wrapper sha pin
status: todo
repo: agent-orchestrator
value: integration and e2e runs exercise the real wrapper with the new file and terminal APIs
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/test_images.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [terminal-ws-relay, wrapper-workspace-e2e]
owns: [wrapper-main-pin]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# wrapper sha pin

## Requirement

Pin agent-orchestrator to the claude-code-wrapper commit that carries this epic's file and terminal APIs (design D9), so the integration contract suite and the kind e2e run against the real new wrapper.

The pin is the commit of the claude-code-wrapper main merge of this epic's wrapper PR (40-hex sha, 7-hex short sha). The orchestrator supplies both values by amending this requirement (`ticket.py amend`) once that PR has merged; until then this task reports `blocked` with `whoCanClear: orchestrator (merge the claude-code-wrapper PR)`.

- `pyproject.toml` dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<sha40>` and `uv.lock` (`uv lock`).
- `e2e/agent-test.Dockerfile`: `ARG BASE_IMAGE=harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>` and `ARG WRAPPER_SHA=<sha40>`.
- README `## Images`: the recommended agent image is `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha` keeps passing (it ties pyproject, uv.lock and README together); a new `test_agent_test_dockerfile_matches_dev_dependency` ties the Dockerfile `BASE_IMAGE` tag and `WRAPPER_SHA` to the same sha.
- `tests/test_render.py` keeps passing against the new wrapper's config schema.

## Acceptance conditions

- AC1: pyproject, uv.lock, README Images and the agent-test Dockerfile all name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the existing pin consistency test passes on the new sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the renderer's config validation passes on the new wrapper [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_render.py]
- AC4: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/test_images.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
