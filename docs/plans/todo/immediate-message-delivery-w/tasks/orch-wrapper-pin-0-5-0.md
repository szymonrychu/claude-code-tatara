---
title: orch wrapper pin 0.5.0
status: todo
repo: agents-orchestrator
value: "deployed agents run a wrapper that takes messages mid-turn, proven against the real wrapper and a kind cluster"
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, e2e/agent-test.scenario.json, README.md, tests/test_fake_wrapper_contract.py, tests/e2e/test_e2e_kind.py]
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

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.5.0 and agents-common 0.4.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). The orchestrator pins the wrapper merge commit of v0.5.0 (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images) with a real-wrapper contract case and a kind e2e case for a merged message, then the plugins ref v0.5.0; the connector pins agents-common v0.4.0. The wrapper is pinned by its release tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags). The agent-test scenario (`e2e/agent-test.scenario.json`) sets `"midturn_input": "queue"`, so the real contract case and the kind e2e prove real delivery (the merge's `absorbed_at` set, the turn completed on the merged prompt's Stop), not the settle-bound fallback (interrogate 8). PR order: Constraints. No agents-helmfile task (Q9)."

Scope (agents-orchestrator): `pyproject.toml` and `uv.lock` (the claude-code-wrapper dev dependency at the v0.5.0 merge commit), `e2e/agent-test.Dockerfile`, `e2e/agent-test.scenario.json` (`"midturn_input": "queue"`), `README.md` (Images), `tests/test_fake_wrapper_contract.py` (remove the real-leg skip of `test_immediate_while_busy_merges`; the real leg asserts the merge absorbed), `tests/e2e/test_e2e_kind.py` (one case: a message posted while the agent is busy joins its running turn and is absorbed).

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit, the v0.5.0 merge commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper takes priority with immediate as its default and its turn record has merged [evidence: command:uv run --frozen python -c "from claude_code_wrapper.api.turns import TurnRequest; from claude_code_wrapper.turns import TurnRecord; assert TurnRequest(text='x').priority == 'immediate'; assert 'merged' in TurnRecord.model_fields"]
- ac4: the agent-test scenario puts the fake claude in queue mode, so mid-turn input is queued like Claude Code instead of dropped (new) [evidence: command:python3 -c "import json; assert json.load(open('e2e/agent-test.scenario.json')).get('midturn_input') == 'queue'"]
- ac5: (CI or a Docker host) the real contract leg passes with the merge case enabled, and on the real leg the merged entry has absorbed_at set (new) [evidence: command:mise run test:integration]
- ac6: (CI kind job) the kind e2e passes, including a case where a chat message posted while the agent is busy reaches it mid-turn, both messages link to the one turn, its record lists the merge with absorbed_at set and the turn completes on the merged prompt's Stop, not the settle bound (new) [evidence: command:mise run test:e2e]
- ac7: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py -m "not integration" && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `e2e/agent-test.scenario.json`
- `README.md`
- `tests/test_fake_wrapper_contract.py`
- `tests/e2e/test_e2e_kind.py`

## Interfaces

- Pin form as the slash epic's orch-wrapper-pin-0-4-0: the `claude-code-wrapper` dev dependency `@ git+https://github.com/szymonrychu/claude-code-wrapper@<v0.5.0 merge sha>`, the Dockerfile's `ARG`/image reference, README Images row.
- `e2e/agent-test.scenario.json`: top-level `"midturn_input": "queue"` (wrapper-fake-claude-queue), so the fake claude in the agent-test image queues mid-turn input like Claude Code instead of dropping it; the contract real leg and the kind e2e both use this scenario.
- e2e case in `tests/e2e/test_e2e_kind.py`: post a message whose scenario keeps the agent busy (the e2e fake claude's slow prompt), then post a second message; assert the second is `sent` with the first's `turn_id`, the turn record lists its merge with `absorbed_at` set, and the turn completes on the merged prompt's Stop (no `turn_deferred` with reason `merge_pending` left unresolved by the settle bound).

## Expected outcome

The orchestrator runs against a wrapper that merges mid-turn messages, and the real wrapper and a kind cluster prove a message to a busy agent is delivered into its running turn.

## Steps

- Read `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `e2e/agent-test.config.yaml`, the README Images section, `tests/test_images.py`, `tests/test_fake_wrapper_contract.py`, `tests/fakes/real_wrapper.py`, `tests/e2e/test_e2e_kind.py` and the slash epic's orch-wrapper-pin-0-4-0 task in one pass.
- Red: remove the real-leg skip and add the e2e case; run `uv run --frozen python -c` of ac3; expect it to fail on the 0.4.0 pin.
- Green: move the pin (`uv lock`), Dockerfile and README; run the task's verify; expect all passed. Quote the summary line; the reviewer quotes the CI integration and e2e job summaries.

## Notes

- Depends on the v0.5.0 tag on origin (wrapper-release-0-5-0 ac3, pushed by the orchestrator session); pin the release, never a branch sha (Harbor prunes sha7 tags).
- Headline promise (retro, recurring): the e2e case is the end-to-end proof of G1; it must post to a really busy agent, not to an idle one.
- The fake claude drops mid-turn input unless the scenario sets `"midturn_input": "queue"`; this task sets it, so the real contract case and the kind e2e prove real delivery (the merge absorbed), not the settle-bound fallback (interrogate 8). Every existing e2e case runs with the new key; read any that changes behaviour and report it.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design
