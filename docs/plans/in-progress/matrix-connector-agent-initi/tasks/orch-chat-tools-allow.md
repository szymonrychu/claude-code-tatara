---
title: orch chat tools allow
status: in-progress
repo: agents-orchestrator
value: "every new session's agents see the chat tools, proven against the real routes with the released plugin"
files: [src/agents_orchestrator/k8s/on_start.py, tests/test_on_start.py, tests/e2e/test_e2e_kind.py, tests/test_agent_chat.py, README.md]
verify: "uv run --frozen pytest tests/test_on_start.py tests/test_agent_chat.py && mise run lint"
depends_on: [orch-plugins-pin-0-3-0, orch-chat-contract]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chat tools allow

## Requirement

README Goal, verbatim: "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."

Design D13, verbatim: "The orchestrator then pins v0.3.0 and adds `CHAT_TOOLS` to every session's allow list (`k8s/on_start.py:orchestrator_allow`); the routes decide. (probe) The allow-list change must land with the pin, not with the routes: `tests/test_on_start.py::test_allowed_tools_exist_in_plugin` requires every allowed tool to exist in the pinned plugin. `claude.main_agent_only_tools` already covers `mcp__any-mcp__orchestrator_*` (`k8s/render.py:159`), so subagents cannot call them."

Design D16, verbatim: "The orchestrator's tools-parity test drives the released v0.3.0 plugin against the real routes and the fake upstream."

Retro proposal (cross-session-messaging-and), verbatim: "agents-orchestrator kind e2e tests: allow-list assertions hard-code tool names; derive them from the shared allow-list constant so a list change cannot break e2e only."

Scope (agents-orchestrator): `k8s/on_start.py` (`CHAT_TOOLS = ["chat_rooms", "chat_send", "chat_react", "chat_status"]` appended for every session, alone and hive), README (the Agent API chat section says the tools are in every allow list, leader only), `tests/test_agent_chat.py` (`test_chat_tools_parity`). Named tests no longer accurate: `tests/test_on_start.py::test_alone_session_tools_entry` and `tests/test_on_start.py::test_hive_session_tools` pin the allow lists without the chat tools; they are updated to include them. `tests/e2e/test_e2e_kind.py:assert_alone_session_tools` pins a literal list; it is changed to compare with `on_start.orchestrator_allow(SessionSpec(replicas=1))` (retro proposal).

Design D5, verbatim (orchestrator caps): "The orchestrator caps the forwarded request body at 256 KiB (413 `payload_too_large`) and the upstream call at 10 s. The cap covers the worst case of a valid maximal request (interrogate Act 6; my call on the figure): 16000 characters of 4 bytes each are 64000 bytes raw (the plugin's httpx encodes JSON as raw UTF-8), and up to 192000 bytes when a client escapes every character as a JSON surrogate pair (12 bytes), plus a room id of up to 255 characters, `reply_to` and the JSON keys; 256 KiB (262144 bytes) covers all of it, where the verdict's example of 80 KiB would refuse the escaped form."

Interrogate verdict, verbatim: "6. Size caps (A,C medium): 16000 characters can exceed the orchestrator's 32 KiB body cap. Make the relay cap cover the worst case (4 bytes per character plus JSON overhead, e.g. 80 KiB) with an AC sending 16000 4-byte characters end to end." (this task: the end-to-end leg through the released plugin, the real relay route and the fake upstream).

## Acceptance conditions

- ac1: an alone session's allow list is the session, init-scripts and chat tools (updated) [evidence: test:tests/test_on_start.py::test_alone_session_tools_entry]
- ac2: a hive session's allow list ends with the chat tools (updated) [evidence: test:tests/test_on_start.py::test_hive_session_tools]
- ac3: every allowed tool, the chat tools included, exists in the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac4: the released plugin drives chat_rooms, chat_send, chat_react and chat_status against the real agent routes and the fake chat upstream, and the results equal the direct route answers [evidence: test:tests/test_agent_chat.py::test_chat_tools_parity]
- ac5: orchestrator_chat_send through the released plugin with a text of 16000 4-byte characters is relayed and the fake upstream receives that exact text [evidence: test:tests/test_agent_chat.py::test_chat_send_max_text_through_plugin]
- ac6: the kind e2e allow-list assertion is derived from on_start instead of a literal list [evidence: command:grep -q "orchestrator_allow" tests/e2e/test_e2e_kind.py && ! grep -q '"init_scripts_edit",$' tests/e2e/test_e2e_kind.py]
- ac7: the README says the chat tools are in every session's allow list [evidence: command:grep -q "orchestrator_chat_send" README.md]
- ac8: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_on_start.py tests/test_agent_chat.py && mise run lint]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `tests/e2e/test_e2e_kind.py`
- `tests/test_agent_chat.py`
- `README.md`

## Interfaces

- `k8s/on_start.py:CHAT_TOOLS`; `orchestrator_allow(spec)` returns `[*SESSION_TOOLS, *INIT_SCRIPTS_TOOLS, *CHAT_TOOLS]` for alone sessions and the hive list followed by `CHAT_TOOLS`.

## Expected outcome

Every new session's agents see the four chat tools; only the leader's calls succeed, and the released plugin is proven against the real routes.

## Steps

- Red: update the two on-start tests, add `test_chat_tools_parity`, change the e2e helper; run `uv run --frozen pytest tests/test_on_start.py tests/test_agent_chat.py`: they fail.
- Green: `CHAT_TOOLS`, README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- `test_chat_tools_parity` follows `tests/test_agent_session_messaging.py::test_session_tools_parity` (PluginHarness with an ASGI transport and the caller's pod IP) and uses `tests/fakes/fake_chat.py:FakeChat` as the upstream. It is DB-backed (CI).
- The kind e2e runs only in CI (kind); the local check is ac5.
- Changing the allow list changes the rendered on-start config hash: existing sessions roll on deploy (chat-live-smoke).

- 2026-10-27 amended: interrogate.md Act 6: 16000 4-byte characters end to end through the released plugin
