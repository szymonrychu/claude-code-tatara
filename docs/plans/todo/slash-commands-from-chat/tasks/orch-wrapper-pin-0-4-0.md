---
title: orch wrapper pin 0.4.0
status: todo
repo: agents-orchestrator
value: "CI's contract leg and kind e2e prove slash commands from chat against the wrapper agents will run"
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, e2e/agent-test.config.yaml, README.md]
verify: "uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [wrapper-release-0-4-0, orch-dispatch-commands]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper pin 0.4.0

## Requirement

Design D14, verbatim: "claude-code-wrapper 0.4.0 (version bump, tag `v0.4.0` on the merge commit after the `main` build, run by the orchestrator session), then agents-orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) and enables `client: ["*"]` in `e2e/agent-test.config.yaml` for the real contract leg and e2e. No agents-helmfile task (user decision 4). [...] Kind e2e placement (my call, interrogate item 12): the e2e job runs on every PR and agents get `client: ["*"]` only from the render change (D11), so an e2e case in the pin PR would be red with 403. The case is its own task orch-e2e-slash-command, right after orch-render-client-commands (a separate task keeps orch-render-client-commands at 8 files); orch-wrapper-pin-0-4-0 no longer touches `tests/e2e/test_e2e_kind.py`."

Interrogate item 12 (interrogate.md), verbatim: "Kind e2e case placed before the render change (A). The e2e job runs on every PR and agents get `client: ["*"]` only in orch-render-client-commands, so the pin PR would be red with 403. Move the e2e case and its AC to orch-render-client-commands."

Needs a merged upstream: the claude-code-wrapper PR of this epic merged on `main` and tagged `v0.4.0` (task wrapper-release-0-4-0). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`.
- `e2e/agent-test.config.yaml`: `sessions.commands.client: ["*"]` (the real contract leg).
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- This task does not touch `tests/e2e/test_e2e_kind.py` (the kind e2e slash case is task orch-e2e-slash-command).

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper accepts "*" and its deny list holds the interrogate item 5 additions [evidence: command:uv run --frozen python -c "from claude_code_wrapper.config import CommandsConfig, DEFAULT_COMMAND_DENY; CommandsConfig(client=['*']); assert {'exit', 'reset', 'cd'} <= set(DEFAULT_COMMAND_DENY)"]
- ac4: (Docker host) the real contract leg passes, test_commands_any_name_and_denied included [evidence: command:mise run test:integration]
- ac5: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.config.yaml`
- `README.md`

## Interfaces

- The wrapper pin (pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` `BASE_IMAGE` and `WRAPPER_SHA`, README `## Images`), all one sha: the claude-code-wrapper `main` merge commit tagged v0.4.0.

## Expected outcome

CI's contract leg and kind e2e run the wrapper that takes any slash command; the e2e slash case itself lands in orch-e2e-slash-command.

## Steps

- Confirm the merged upstream and read the merge sha (`git -C /workdir/workdir/code/claude-code-wrapper fetch origin main` and the `v0.4.0` tag).
- Change the pyproject pin, run `uv lock`; run `uv run --frozen pytest tests/test_images.py`: the Dockerfile and README checks fail on the old sha.
- Update the Dockerfile args, the agent-test config and README `## Images`; run the task's verify: passes. Quote the summary line. The integration leg runs in CI or on a Docker host.

## Notes

- `tests/test_images.py` ties pyproject, uv.lock, README Images and the Dockerfile to one sha; `tests/test_render.py` validates rendered configs against the pinned wrapper's config model.
- Dependency bump: the TDD exception for the pin values applies; the equality tests are the guard.
- Depends on wrapper-release-0-4-0, orch-wrapper-command-client and orch-dispatch-commands.

- 2026-10-27 amended: interrogate item 12 (the kind e2e case moved out of the pin task to orch-e2e-slash-command after orch-render-client-commands, so the pin PR is not red with 403), design D14 revised
