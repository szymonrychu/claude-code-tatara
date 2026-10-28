---
title: orch wrapper pin patch
status: in-progress
repo: agents-orchestrator
value: orchestrator tests and the kind e2e run the released wrapper
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md]
verify: "uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [wrapper-patch-release]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper pin patch

## Requirement

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Design D13, verbatim: "Precedent: leader-auto-handover tasks wrapper-release-0-3-0, orch-wrapper-pin-0-3-0, helmfile-deploy-pin, helmfile-apply-smoke. Live applies and the tag push are run by the orchestrator session, never a subagent."

Needs a merged upstream: the claude-code-wrapper PR of this epic merged on `main` and tagged (task wrapper-patch-release). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@5fd93ff52236790a7131755141d328b25826213a`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `5fd93ff` and `WRAPPER_SHA` `5fd93ff52236790a7131755141d328b25826213a` (`scripts/e2e.sh` builds the wrapper from source when the sha7 image was pruned).
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:5fd93ff` (`tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha` requires the sha7 form; the release tag `0.3.2` is what agents-helmfile pins).

Steps: pin, `uv lock`, run the verify; the real contract leg runs in CI.

Notes: in-progress epic slash-commands-from-chat pins the wrapper in the same files (task orch-wrapper-pin-0-4-0); rebase on it and keep the higher wrapper commit that carries both epics' changes.

## Acceptance conditions

- AC1: pyproject, uv.lock and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the dev dependency matches the README agent image [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the pinned wrapper is the release [evidence: command:uv run --frozen python -c "import claude_code_wrapper; assert claude_code_wrapper.__version__ == '0.3.2'"]
- AC4: (Docker host or CI) the real contract leg passes [evidence: command:mise run test:integration]
- AC5: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run --frozen pytest -q tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 amended: wrapper PR #7 merged as 5fd93ff, tagged v0.3.2 (release image retagged)
