---
title: orch render session tools
status: done
repo: agents-orchestrator
value: "the leader of every session, hive or alone, sees the session tools"
files: [src/agents_orchestrator/k8s/on_start.py, tests/test_on_start.py, tests/test_render.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, tests/e2e/test_e2e_kind.py, README.md, MEMORY.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py && mise run lint"
depends_on: [orch-agent-session-messaging, orch-any-mcp-pin-0-4-0]
model: opus
review: ""
verified_head: 87c7833de203c4bb53159591197429159b98ddb7
points: 3
expected_minutes: 6
expected_tokens: 553016
points_actual: 2
actual_minutes: 4
actual_tokens: 1565873
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 1399565, review 166308"
---

# orch render session tools

## Requirement

User decision at the gate 2026-10-26, verbatim: "session_messaging is required only on one end. ... So session that has this option turned on, sees all leaders in all sessions. Leaders in sessions that have this turned off, will see its members plus the superleader. This implies, that messaging functionality is there for non hived sessions as well (they alone will see only superleaders if such exist)." Goal G1 (epic README), verbatim: "... the leader of every other session, alone sessions included, lists only the superleader sessions and can send only to them ...". Design D11: the messaging tools are rendered for every session, alone sessions included; the server decides what each caller may list and send.

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/on_start.py`: `SESSION_TOOLS = ["sessions_list", "session_send"]`; `orchestrator_allow(spec)` returns, for a hive, the hive tools (plus `scale` when scalable) followed by `SESSION_TOOLS`; for an alone session, exactly `SESSION_TOOLS`. It does not depend on `session_messaging`. The entry is still omitted without `agent_api_url` or slug, and its `config` keys do not change (an alone session renders `hive: false`, `max_replicas: 1`).
- Tests no longer accurate because design D11 now renders the session tools for every session (named, with the change):
  - `tests/test_on_start.py::test_alone_has_no_orchestrator_entry` asserts an alone session gets no entry: replaced by `test_alone_session_tools_entry`;
  - `tests/test_on_start.py::test_static_hive_has_no_scale_tool` and `::test_hive_entry_and_allow` pin the exact allow list: they gain the two session tools at the end; their scale assertions stay;
  - `tests/test_render.py::test_on_start_orchestrator_entry_only_for_hive` asserts no plugin for an alone session: replaced by `test_on_start_orchestrator_entry_for_every_session`;
  - `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`: regenerated with the golden helper of `tests/test_render.py`;
  - `tests/e2e/test_e2e_kind.py::test_alone_session_has_no_hive_tools` and `::test_static_single_pod_is_alone` assert no orchestrator entry for an alone session: they assert the entry exists with allow exactly `sessions_list`, `session_send` and still no hive tool, notes off and peers off.
- `README.md`: the hive/tools section says every session gets the two session tools and the server applies the superleader rule.
- `MEMORY.md`: dated entry replacing hive D24 ("an alone session gets no hive, peers or messaging tools") for the session tools, with the user's decision as the why.

Depends on any-mcp v0.4.0 pinned (task orch-any-mcp-pin-0-4-0).

## Acceptance conditions

- ac1: an alone session, with or without session_messaging, gets an orchestrator plugin entry whose allow list is exactly sessions_list and session_send, and its config validates under the installed any-mcp [evidence: test:tests/test_on_start.py::test_alone_session_tools_entry]
- ac2: a hive, with or without session_messaging, gets the hive tools, scale when scalable, then sessions_list and session_send [evidence: test:tests/test_on_start.py::test_hive_session_tools]
- ac3: without an agent API URL or a slug no orchestrator entry is rendered, for an alone session and for a hive [evidence: test:tests/test_on_start.py::test_omitted_without_agent_api_url_or_slug]
- ac4: the rendered on-start of an alone and of a hive session both carry the orchestrator plugin [evidence: test:tests/test_render.py::test_on_start_orchestrator_entry_for_every_session]
- ac5: the regenerated goldens and the render, onStart, README and nomenclature tests pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py tests/test_readme_api.py tests/test_nomenclature.py]
- ac6: the kind e2e module still collects with the updated alone-session assertions (it runs in CI through mise run test:e2e) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q --collect-only -m e2e tests/e2e/test_e2e_kind.py]
- ac7: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `tests/e2e/test_e2e_kind.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `k8s/on_start.py:SESSION_TOOLS: list[str]`, `orchestrator_allow(spec: SessionSpec) -> list[str]` (contract `orch-plugin-entry`: the only extension point).
- Rendered tool names seen by Claude: `mcp__any-mcp__orchestrator_sessions_list`, `mcp__any-mcp__orchestrator_session_send` (already main-agent only through `main_agent_only_tools`, render.py:134).

## Expected outcome

The leader of every session, hive or alone, sees the two session tools; what each may list and send is the server's superleader rule (task orch-agent-session-messaging).

## Steps

- Red: write `test_alone_session_tools_entry` and `test_hive_session_tools`, update the inaccurate tests named in the Requirement; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py`: fails.
- Green: change `orchestrator_allow`; regenerate the goldens; update the e2e assertions; run the task's verify: passes.
- README and MEMORY; run ac5, ac6 and ac7 commands: pass.

## Notes

- Rulings and their pin tests: tool order hive tools, scale, session tools (ac2); alone sessions get only the session tools, never the hive tools (ac1, and the e2e assertions); independent of session_messaging (ac1, ac2).
- Tool visibility is fixed at render (hive D2); rendering for every session means a running session gets the tools only after its pods re-render on upgrade (design Rollout R3 rolls them once).
- Notes stay hive-only (`render.py:169`): an alone session receives cross-session messages as turns, not notes.
- The kind e2e runs in CI (`mise run test:e2e`, kind); locally ac6 only proves it collects. Keep the assertions in the style of the file.
- Orchestrator tests need Docker; run with `VIRTUAL_ENV` unset; `uv sync` if the `.venv` shebang is stale.

- 2026-10-26 amended: gate 2026-10-26: one-sided superleader messaging (tools for every session, target_not_superleader), Q1 no orchestrator kubectl install, Q2 yes

- 2026-10-26 done
