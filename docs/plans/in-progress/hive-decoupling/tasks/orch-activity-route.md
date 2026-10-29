---
title: orch activity route
status: in-progress
repo: agents-orchestrator
value: "any hive agent can pull what its peers did, on demand, instead of having it streamed"
files: [src/agents_orchestrator/api/agent.py, src/agents_orchestrator/db/events.py, openapi.json, README.md, tests/test_api_activity.py]
verify: "uv run --frozen pytest tests/test_api_activity.py tests/test_readme_api.py tests/test_hive_feed.py && mise run lint"
depends_on: []
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

# orch activity route

## Requirement

User request (2026-10-27), verbatim: "Decouple agents in session more. Right now non-leaders get truncated stream of what's leader is doing. Ask fable architect to decouple or use handoff or something to consume non-leaders less."

README Goal G2, verbatim: "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

Design D3, verbatim: "route on the agent port (`require_agent`), query `agent` (pod name, optional) and `limit` (1..200, default 50; out of range 422 `invalid_request`). It reads the caller session's newest `events` rows of types `tool_call`, `tool_result`, `turn_completed` (bounded: the newest 1000 such rows, then ascending), runs `feed.digest_lines(rows, now(), workdir)` unchanged and returns the last `limit` lines as `{"lines": [{"id", "agent", "text", "ts"}]}`, oldest first, own lines included; `agent` filters to one pod. Read-only."

Design D3 my calls, verbatim: "an `agent` that names no line returns an empty list, not 404, because gone agents' lines are legitimate history; paths are made relative to the session workdir (`digest_lines`' `workdir` argument); the route serves every session (as `me` does), while the tool is rendered for hives only (D9); a Bash call younger than `PENDING_BASH_TIMEOUT_SECONDS` without a result is omitted (it appears once its result is stored); `ts` is the event's `ts` looked up by line id."

Scope (agents-orchestrator):
- `src/agents_orchestrator/api/agent.py`: `GET /agent/v1/activity` with response models `ActivityLine {id: int, agent: str, text: str, ts: datetime}` and `Activity {lines: list[ActivityLine]}`; identity through `Caller` (`require_agent`); workdir through the existing `_workdir`.
- `src/agents_orchestrator/db/events.py`: the bounded read (newest 1000 rows of the three types for the session, joined to `agents` for `pod_name` as `agent`, returned ascending), when the builder places it there rather than in the route.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).
- `README.md` `## Agent API`: a `### GET /agent/v1/activity` section (query, response, errors, the omission of in-flight Bash calls, read-only).
- `tests/test_api_activity.py`: new.
- No writer is added: the route only reads `events` (single-writer rule; the ingester writes `events`).
- `dispatcher/feed.py` is not changed here (orch-hive-feed-removal drops `render_feed`).

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged (this epic is blocked on them already). This is the first task, so it also fixes the numbers the later tasks need, run by the orchestrator session (not a subagent: `ticket.py amend` and `git ls-remote` are its tools) before the first implementer is dispatched:
- the next free orchestrator migration number: the highest `NNNN_*.sql` in `src/agents_orchestrator/db/migrations/` on `main`, plus one;
- the next free plugins release: the newest `vX.Y.Z` tag on the any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins 'v*'`), next minor.
It then replaces the placeholders `0010`, `v0.3.0` and `0.3.0` by `ticket.py amend` in orch-drop-feed-cursor, plugins-release-0-4-0, orch-plugins-pin-0-4-0 and helmfile-deploy-pin (Requirement and acceptance conditions), and edits the same placeholders in their frontmatter `files` and bodies. The task slugs keep their historical names.

## Acceptance conditions

- ac1: the route returns the session's digest lines as {lines: [{id, agent, text, ts}]}, oldest first, own lines included, paths relative to the workdir [evidence: test:tests/test_api_activity.py::test_activity_lists_digest_lines]
- ac2: agent filters to one pod; an agent with no lines returns an empty list [evidence: test:tests/test_api_activity.py::test_activity_agent_filter]
- ac3: limit defaults to 50, keeps the newest limit lines, and a limit outside 1..200 answers 422 invalid_request [evidence: test:tests/test_api_activity.py::test_activity_limit_bounds]
- ac4: the route needs the agent identity (401 without credentials, 403 from a non-agent peer) and reads only the caller's session [evidence: test:tests/test_api_activity.py::test_activity_requires_agent_identity]
- ac5: a Bash call younger than PENDING_BASH_TIMEOUT_SECONDS without a result is omitted; once its result is stored it is listed with its status [evidence: test:tests/test_api_activity.py::test_activity_omits_pending_bash]
- ac6: the README documents the route [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- ac7: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac8: the route only reads events; no INSERT, UPDATE or DELETE is added [evidence: judgement:reviewer reads the diff of api/agent.py and db/events.py]
- ac9: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_api_activity.py tests/test_readme_api.py tests/test_hive_feed.py && mise run lint]
- ac10: (orchestrator session, before dispatch) the real next migration number and plugins tag read from main replace the placeholders in orch-drop-feed-cursor, plugins-release-0-4-0, orch-plugins-pin-0-4-0 and helmfile-deploy-pin [evidence: judgement:orchestrator quotes the numbers read and a grep of the epic's other task files showing no 0010, v0.3.0 or 0.3.0 left]

## Files

- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/db/events.py`
- `openapi.json`
- `README.md`
- `tests/test_api_activity.py`

## Interfaces

- `GET /agent/v1/activity?agent=<pod>&limit=<1..200>` on the agent port; 200 `{"lines": [{"id": int, "agent": str, "text": str, "ts": datetime}]}`; 401/403 from `require_agent`; 422 `invalid_request` for a bad `limit`.
- Reuses `agents_orchestrator.dispatcher.feed.digest_lines(rows, now, workdir) -> (lines, pending)` unchanged; rows carry `id`, `type`, `data`, `ts`, `agent` (pod name).

## Expected outcome

An agent calling the route sees the newest digest lines of its session (commands with status, files written, finished turns), bounded and on demand; nothing is written.

## Steps

- First, before any implementer is dispatched (orchestrator session, settlement 1): read the next free migration number and plugins tag from main and amend the four dependent tasks (ac10).
- Red: write `tests/test_api_activity.py` (ac1-ac5; reuse the agent-identity setup of `tests/test_api_agent.py` and `factories.insert_event`); run `uv run --frozen pytest tests/test_api_activity.py`: fails (404 route).
- Green: the route and the bounded read; README section; `uv run python -m agents_orchestrator.api.openapi > openapi.json`; run the task's verify: passes. Quote the summary line.

## Notes

- DB tests need testcontainers (Docker); there is none in agent pods, so CI on the PR is the gate for them (recurring retro). Run what runs locally and quote both.
- Shared files with slash-commands-from-chat (`api/agent.py`, `openapi.json`): read them as merged on `main` first.
- The newest-rows bound: `ORDER BY e.id DESC LIMIT 1000`, then reverse; filter by type in SQL.

- 2026-10-27 amended: builder check settlement 1: first task reads the real next migration number and plugins tag from main and amends the dependent tasks
