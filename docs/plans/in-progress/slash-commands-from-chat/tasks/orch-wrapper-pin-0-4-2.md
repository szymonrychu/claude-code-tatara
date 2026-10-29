---
title: orch wrapper pin 0.4.2
status: todo
repo: agents-orchestrator
value: the orchestrator tests and deploys against the wrapper with the 64-name deny list
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py]
verify: "uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [wrapper-release-0-4-2, orch-wrapper-pin-0-4-1, orch-plugins-pin-0-5-1]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper pin 0.4.2

## Requirement

User decision PENDING (mx-34 #471 Q1-3, recommended yes to all; tatara #473 confirmed the version v0.4.2). The leader amends this paragraph with the user verbatim answer before the merge; nothing merges or is tagged before it. Questions, verbatim: "1) Deny the account or cloud group too? That means wrapper v0.4.2 (patch, after v0.4.1) before the slash deploy, about 1 h of agent time. Recommended: yes. 2) Also deny mcp, permissions, config and hooks in v0.4.2? Recommended: yes, so that chat cannot rewrite the session's tool and permission settings. 3) Bump the version to wrapper v0.4.2? Live is 0.3.3, v0.4.1 is tagged but not deployed, and v0.4.2 would replace it in the same deploy. Recommended: yes, pending tatara's confirmation."

Scope (agents-orchestrator, branch slash-commands-from-chat, same files as orch-wrapper-pin-0-4-1): dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>` and `uv lock`; `e2e/agent-test.Dockerfile` `BASE_IMAGE` `<sha7>` and `WRAPPER_SHA` `<merge sha>`; README `## Images` agent image `<sha7>`; `tests/fakes/fake_wrapper.py` `COMMAND_DENY` mirrors the pinned wrapper's 64-name `DEFAULT_COMMAND_DENY`; `tests/test_fake_wrapper_contract.py` `test_commands_any_name_and_denied` also refuses "ultrareview", "MCP", "allowed-tools", "remote" and "settings". `<merge sha>`/`<sha7>` are amended by the leader after wrapper-release-0-4-2.

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the fake wrapper's COMMAND_DENY equals the pinned wrapper's DEFAULT_COMMAND_DENY, lower-cased [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_deny_mirrors_wrapper_default]
- ac4: on the fake leg, and on the real leg on a Docker host, "ultrareview", "MCP", "allowed-tools", "remote" and "settings" are refused 403 command_denied while "context" still queues (updated) [evidence: test:tests/test_fake_wrapper_contract.py::test_commands_any_name_and_denied]
- ac5: (Docker host, CI e2e) the real contract leg passes [evidence: command:mise run test:integration]
- ac6: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
