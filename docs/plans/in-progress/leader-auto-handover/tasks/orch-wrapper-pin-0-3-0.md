---
title: orch wrapper pin 0.3.0
status: in-progress
repo: agents-orchestrator
value: the orchestrator validates and tests against the wrapper that emits compacting
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/test_images.py]
verify: "uv run pytest -q tests/test_images.py tests/test_render.py tests/test_settings.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-release-0-3-0, leader-changed-reason]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 662742
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper pin 0.3.0

## Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Design D12: the orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images). Precedent: done epic hive-mode-leadership-handove task orch-pin-bumps.

Scope: pin agents-orchestrator to the claude-code-wrapper `main` merge commit that carries version 0.3.0 and the `compacting` event:
- `pyproject.toml`: `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`, the same commit.
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/test_images.py` equality tests (wrapper sha agrees across pyproject, uv.lock, README and the Dockerfile) pass unchanged; `tests/test_render.py` still validates the rendered config against the new wrapper; `tests/fakes/fake_wrapper.py` validates event names against the pinned `EVENT_TYPES`, which now includes `compacting`.

The merge sha is filled in by `ticket.py amend` when the wrapper PR merges. Dependency bump: the TDD exception for a dependency bump applies to the pin values; the equality tests are the guard.

## Acceptance conditions

- AC1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the pinned wrapper knows the `compacting` event [evidence: command:uv run python -c "from claude_code_wrapper.events import EVENT_TYPES; assert 'compacting' in EVENT_TYPES"]
- AC4: the rendered config validates against the pinned wrapper and the fake wrapper contract holds [evidence: command:uv run pytest -q tests/test_render.py tests/test_settings.py tests/test_fake_wrapper_contract.py]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/test_images.py`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Change the pins in `pyproject.toml`, `uv.lock` (`uv lock`), `e2e/agent-test.Dockerfile` and README Images to the wrapper 0.3.0 merge commit (dependency-bump exception); run `uv run pytest -q tests/test_images.py`: the equality tests fail until every pin agrees, then pass.
- Run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.
