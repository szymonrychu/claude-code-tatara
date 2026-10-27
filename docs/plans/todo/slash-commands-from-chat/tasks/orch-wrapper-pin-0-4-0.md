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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
