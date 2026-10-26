---
title: orch render session tools
status: todo
repo: agents-orchestrator
value: "the leader of an opted-in session, hive or alone, sees the session tools"
files: [src/agents_orchestrator/k8s/on_start.py, tests/test_on_start.py, tests/test_agent_session_messaging.py, README.md, MEMORY.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_agent_session_messaging.py && mise run lint"
depends_on: [orch-agent-session-messaging, orch-any-mcp-pin-0-4-0, orch-kube-access-render]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 553016
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch render session tools

## Requirement

Epic description, verbatim: "the leader of a session can send messages to the leaders of other sessions and receive messages from them, through orchestrator tools in the agent pods." Goal G1 (epic README), verbatim: "a session with it on can list messaging-enabled sessions and send a message to another one's leader". Design D11.

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/on_start.py`: `SESSION_TOOLS = ["sessions_list", "session_send"]`; `orchestrator_allow(spec)` returns, for a hive, the hive tools (plus `scale` when scalable) followed by `SESSION_TOOLS` when `spec.session_messaging`; for an alone session, exactly `SESSION_TOOLS` when `spec.session_messaging`, else `[]` as today. The plugin entry and its `config` keys do not change (an alone session renders `hive: false`, `max_replicas: 1`).
- `tests/test_on_start.py`: new tests (acceptance conditions); `test_alone_has_no_orchestrator_entry` stays accurate unchanged.
- `tests/test_agent_session_messaging.py` (from task orch-agent-session-messaging): add a parity test that drives the installed any-mcp v0.4.0 `OrchestratorPlugin` through `any_mcp.testing.PluginHarness` against the app on the agent port, like `tests/test_agent_init_scripts.py::test_plugin_parity`.
- `README.md`: the hive/tools section says which sessions get the session tools.
- `MEMORY.md`: dated entry amending hive D24 ("an alone session gets no hive, peers or messaging tools") for sessions with `session_messaging`, with the why.

Depends on any-mcp v0.4.0 pinned (task orch-any-mcp-pin-0-4-0).

## Acceptance conditions

- ac1: an alone session with session_messaging gets an orchestrator plugin entry whose allow list is exactly sessions_list and session_send, and its config validates under the installed any-mcp [evidence: test:tests/test_on_start.py::test_alone_messaging_entry]
- ac2: a hive with session_messaging gets the hive tools, scale when scalable, then sessions_list and session_send; a hive without it gets neither session tool [evidence: test:tests/test_on_start.py::test_hive_messaging_tools]
- ac3: an alone session without the option still renders no orchestrator entry [evidence: test:tests/test_on_start.py::test_alone_has_no_orchestrator_entry]
- ac4: through the real any-mcp plugin, orchestrator sessions_list returns the server's session list and session_send queues a message and returns its message_id [evidence: test:tests/test_agent_session_messaging.py::test_session_tools_parity]
- ac5: render, onStart, messaging and README tests pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py tests/test_agent_session_messaging.py tests/test_readme_api.py tests/test_nomenclature.py]
- ac6: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `tests/test_agent_session_messaging.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
