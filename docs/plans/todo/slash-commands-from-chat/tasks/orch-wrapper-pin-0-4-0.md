---
title: orch wrapper pin 0.4.0
status: todo
repo: agents-orchestrator
value: "CI's contract leg and kind e2e prove slash commands from chat against the wrapper agents will run"
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, e2e/agent-test.config.yaml, README.md, tests/e2e/test_e2e_kind.py]
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

Design D14, verbatim: "claude-code-wrapper 0.4.0 (version bump, tag `v0.4.0` on the merge commit after the `main` build, run by the orchestrator session), then agents-orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) and enables `client: ["*"]` in `e2e/agent-test.config.yaml` for the real contract leg and e2e. No agents-helmfile task (user decision 4)."

User decision: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." The kind e2e case below proves it against the real agent image.

Needs a merged upstream: the claude-code-wrapper PR of this epic merged on `main` and tagged `v0.4.0` (task wrapper-release-0-4-0). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`.
- `e2e/agent-test.config.yaml`: `sessions.commands.client: ["*"]`.
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/e2e/test_e2e_kind.py`: new `test_slash_command_from_chat_keeps_session_responsive`: POST a chat message "/reload-plugins" through the API; the session's events show `command_completed` for reload-plugins; the agent returns idle; a following prose message completes its turn; POST "/exit" fails with error `command_denied`.

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper accepts "*" and has the deny list [evidence: command:uv run --frozen python -c "from claude_code_wrapper.config import CommandsConfig, DEFAULT_COMMAND_DENY; CommandsConfig(client=['*']); assert 'exit' in DEFAULT_COMMAND_DENY"]
- ac4: (CI only, kind) the e2e slash case passes against the real agent image (new) [evidence: command:mise run test:e2e]
- ac5: (Docker host) the real contract leg passes, test_commands_any_name_and_denied included [evidence: command:mise run test:integration]
- ac6: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.config.yaml`
- `README.md`
- `tests/e2e/test_e2e_kind.py`

## Interfaces

- The wrapper pin (pyproject dev dependency, `uv.lock`, `e2e/agent-test.Dockerfile` `BASE_IMAGE` and `WRAPPER_SHA`, README `## Images`), all one sha: the claude-code-wrapper `main` merge commit tagged v0.4.0.
- New kind e2e case `tests/e2e/test_e2e_kind.py::test_slash_command_from_chat_keeps_session_responsive`.

## Expected outcome

CI's contract leg and kind e2e run the wrapper that takes any slash command, and the e2e proves the reported case end to end.

## Steps

- Confirm the merged upstream and read the merge sha (`git -C /workdir/workdir/code/claude-code-wrapper fetch origin main` and the `v0.4.0` tag).
- Change the pyproject pin, run `uv lock`; run `uv run --frozen pytest tests/test_images.py`: the Dockerfile and README checks fail on the old sha.
- Update the Dockerfile args, the agent-test config, README `## Images`, add the e2e case; run the task's verify: passes. Quote the summary line. The e2e and integration legs run in CI or on a Docker host.

## Notes

- `tests/test_images.py` ties pyproject, uv.lock, README Images and the Dockerfile to one sha; `tests/test_render.py` validates rendered configs against the pinned wrapper's config model.
- The e2e asserts on the wrapper's error code `command_denied`, not on a hard-coded deny list (retro proposal of cross-session-messaging-and).
- Dependency bump: the TDD exception for the pin values applies; the equality tests are the guard. The e2e case is written before the pin is final and fails against the 0.3.0 image.
- Depends on wrapper-release-0-4-0, orch-wrapper-command-client and orch-dispatch-commands.
