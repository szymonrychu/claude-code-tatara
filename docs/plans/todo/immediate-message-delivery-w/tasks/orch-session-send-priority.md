---
title: orch session send priority
status: todo
repo: agents-orchestrator
value: a superleader can choose whether its message reaches a busy leader at once or waits until idle
files: [src/agents_orchestrator/api/agent.py, openapi.json, README.md, tests/test_agent_session_messaging.py]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-priority-column]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch session send priority

## Requirement

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D1 (agent route part), verbatim: "Routes: [...] the agent route `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:SessionMessageIn`), `MessageView.priority`, [...]"

Design D15 (orchestrator side), verbatim: "any-mcp-tatara-plugins `session_send` gains `priority` (enum `immediate`, `idle`, default `immediate`) [...]"

Scope (agents-orchestrator): `api/agent.py` (`SessionMessageIn.priority`, passed to `enqueue_message`), `openapi.json` (regenerated), `README.md` (both message routes: the `priority` field and what `immediate` and `idle` do, the dispatch summary in the intro), `tests/test_agent_session_messaging.py`.

## Acceptance conditions

- ac1: (CI or a Docker host) a superleader's session_send stores priority (immediate by default, idle when sent) on the queued message, and an unknown value answers 422 (new) [evidence: test:tests/test_agent_session_messaging.py::test_session_send_priority]
- ac2: SessionMessageIn defaults to immediate, accepts idle and refuses other values [evidence: command:uv run --frozen python -c "from agents_orchestrator.api.agent import SessionMessageIn; assert SessionMessageIn(text='x').priority == 'immediate'; assert SessionMessageIn(text='x', priority='idle').priority == 'idle'" && ! uv run --frozen python -c "from agents_orchestrator.api.agent import SessionMessageIn; SessionMessageIn(text='x', priority='soon')" 2>/dev/null]
- ac3: openapi.json is regenerated from the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac4: the README documents `priority` on both message routes and says that immediate reaches a busy leader mid-turn and idle waits for an idle leader [evidence: command:grep -q '`priority`' README.md && grep -qi 'mid-turn' README.md && uv run --frozen pytest tests/test_readme_api.py]
- ac5: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/api/agent.py`
- `openapi.json`
- `README.md`
- `tests/test_agent_session_messaging.py`

## Interfaces

- `api/agent.py:SessionMessageIn.priority: MessagePriority = "immediate"` (the type from `api/schemas.py`, task orch-priority-column); `session_send` passes `priority=body.priority` to `q.enqueue_message`. The D7 checks, hop guard, rate, pair and `target_queue_full` checks are unchanged and run before the insert as today.

## Expected outcome

A superleader can ask for a message to reach the target's busy leader at once (the default) or to wait until it is idle, and the README tells API users what each does.

## Steps

- Read `api/agent.py` (`SessionMessageIn`, `session_send`), `api/schemas.py`, `tests/test_agent_session_messaging.py` and the README message sections in one pass.
- Red: add `test_session_send_priority` and run ac2's command; expect ac2 to fail.
- Green: add the field and pass it through; regenerate `openapi.json`; document both routes in the README; run the task's verify; expect all passed. Quote the summary line.

## Notes

- Per-task security check (retro, recurring): this route sends on a session's behalf; the rate, pair, hop and queue limits must still apply to immediate messages exactly as before (no new bypass).
- The README is overlap-ignored but shared with orch-dispatch-immediate; this task writes the route docs, that task the dispatch section.
- Tree state: tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR; the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
