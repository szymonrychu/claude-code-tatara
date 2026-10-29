---
title: orch wrapper pin 0.5.0
status: todo
repo: agents-orchestrator
value: "deployed agents run a wrapper that takes messages mid-turn, proven against the real wrapper and a kind cluster"
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/test_fake_wrapper_contract.py, tests/e2e/test_e2e_kind.py]
verify: "uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py -m \"not integration\" && mise run lint"
depends_on: [wrapper-release-0-5-0, orch-merged-delivery]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch wrapper pin 0.5.0

## Requirement

Goal G1 (README), verbatim: "a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle."

Design D19, verbatim: "The orchestrator pins the wrapper merge commit of v0.5.0 (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) with a real-wrapper contract case and a kind e2e case for a merged message, then the plugins ref v0.5.0; the connector pins agents-common v0.4.0. The wrapper is pinned by its release tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags)."

Scope (agents-orchestrator): `pyproject.toml` and `uv.lock` (the claude-code-wrapper dev dependency at the v0.5.0 merge commit), `e2e/agent-test.Dockerfile`, `README.md` (Images), `tests/test_fake_wrapper_contract.py` (remove the real-leg skip of `test_immediate_while_busy_merges`), `tests/e2e/test_e2e_kind.py` (one case: a message posted while the agent is busy joins its running turn).

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the v0.5.0 merge commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper takes priority with immediate as its default and its turn record has merged [evidence: command:uv run --frozen python -c "from claude_code_wrapper.api.turns import TurnRequest; from claude_code_wrapper.turns import TurnRecord; assert TurnRequest(text='x').priority == 'immediate'; assert 'merged' in TurnRecord.model_fields"]
- ac4: (CI or a Docker host) the real contract leg passes with the merge case enabled [evidence: command:mise run test:integration]
- ac5: (CI kind job) the kind e2e passes, including a case where a chat message posted while the agent is busy reaches it mid-turn and both messages link to the one turn that completes (new) [evidence: command:mise run test:e2e]
- ac6: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/test_fake_wrapper_contract.py`
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
