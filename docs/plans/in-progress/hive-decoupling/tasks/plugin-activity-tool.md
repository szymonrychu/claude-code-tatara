---
title: plugin activity tool
status: in-progress
repo: any-mcp-tatara-plugins
value: agents get the orchestrator_activity tool and handover texts that describe the brief-then-handover protocol
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py, orchestration/orchestrator/README.md]
verify: "uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint"
depends_on: [orch-activity-route, orch-handover-outcome-note]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugin activity tool

## Requirement

README Goal G2, verbatim: "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

README Goal G4, verbatim: "The leader briefs a chosen successor directly over ccw peer messaging, then hands over with `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied, or rejected with its reason) as a keyed `leadership_request` note."

Design D3, verbatim: "Plugin tool `activity` (`GET /agent/v1/activity`, query `agent`, `limit`), description: "What the other agents did recently (commands with exit status, files written, finished turns): newest last. Call it when you need it; nothing is streamed to you.""

Design D5, verbatim: "carried by the `handover_due` text and the plugin `leadership_handover` and `me` descriptions; no CLAUDE.md fragment".

Fix-as-ac (brief), verbatim: "Plugin `leadership_handover` text claims "the outcome arrives as a hive-state note"; untrue for rejections: D6 and the text fix."

Scope (any-mcp-tatara-plugins, `orchestration/orchestrator`):
- `src/any_mcp_tatara_orchestrator/__init__.py`: tool `activity` after `me` in `load_tools`: `HttpBinding("GET", "/agent/v1/activity", query=("agent", "limit"))` (the `spec()` helper gains a `query` argument), schema `{agent?: string (pod name), limit?: integer 1..200}`, description as D3 (with the hive prefix). `leadership_handover` description: the D5 protocol in short (brief the successor named in the handover_due note with mcp__ccw__send_message and notify_when_idle, wait for its "ready", then call this tool with to, the current epoch and a reason), and "the outcome arrives as a leadership-request note (applied, or rejected with the reason)" replacing "The outcome arrives as a hive-state note."; the threshold advice stays computed from `auto_compact_pct` (the orchestrator now always renders the effective value, task orch-hive-tools-activity). `me` description: names `orchestrator_activity` and says nothing is streamed.
- `tests/test_orchestrator_plugin.py`: the new tests below. Named as no longer accurate: the tool-listing test (today `test_lists_eleven_tools`; whatever count-named test the epics before left) is renamed `test_lists_all_tools` and expects the current set plus `activity`; `test_descriptions_from_config` where it asserts the old hive-state outcome sentence.
- `README.md` (plugin): the tool table gains `orchestrator_activity(agent?, limit?)` | `GET /agent/v1/activity`; the tool count sentence follows.
- Read the file as merged by slash-commands-from-chat and matrix-connector-agent-initi first (shared file); keep their tools.

## Acceptance conditions

- ac1: the activity tool calls GET /agent/v1/activity with agent and limit as query parameters and the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_activity_tool_calls_route]
- ac2: the plugin lists every tool including activity (renamed count test, named) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_all_tools]
- ac3: the leadership_handover description carries the brief-then-handover protocol and the leadership-request outcome note, and no longer says the outcome arrives as a hive-state note [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_handover_description_protocol]
- ac4: the me description names orchestrator_activity and says nothing is streamed [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_me_description_points_to_activity]
- ac5: the threshold advice still follows auto_compact_pct [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_handover_threshold_hint]
- ac6: the plugin README lists the tool [evidence: command:grep -q "orchestrator_activity" orchestration/orchestrator/README.md]
- ac7: the plugin tests and lint pass [evidence: command:uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

## Interfaces

- Tool `orchestrator_activity(agent?: string, limit?: integer)`: `HttpBinding("GET", "/agent/v1/activity", query=("agent", "limit"), base_url=...)` (any-mcp `HttpBinding.query`, `any_mcp/types.py:82`).
- Route contract: agents-orchestrator README `### GET /agent/v1/activity` (task orch-activity-route).

## Expected outcome

The plugin offers the activity tool and describes the brief-then-handover protocol and the outcome note.

## Steps

- Red: the tests of ac1-ac4 (and the renamed listing test); run `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: they fail.
- Green: `__init__.py`, plugin README; run the task's verify: passes. Quote the summary line.

## Notes

- Shared file with slash-commands-from-chat and matrix-connector-agent-initi: build on their merged tools.
- No release here (plugins-release-0-4-0).
