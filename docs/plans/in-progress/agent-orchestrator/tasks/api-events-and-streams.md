---
title: api events and streams
status: done
repo: agent-orchestrator
value: "Smart chat loading for any client: page history backwards, then follow live events and status changes over SSE."
files: [src/agent_orchestrator/api/streams.py, src/agent_orchestrator/api/listener.py, src/agent_orchestrator/api/app.py, tests/test_api_streams.py]
verify: "uv run pytest tests/test_api_streams.py -q && mise run lint"
depends_on: [api-messages-and-commands, events-store]
owns: []
uses: [api-app, events-repo]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-api-events-and-streams/agent-orchestrator
branch: agent-orchestrator-api-events-and-streams
verified_head: 77697b02faa60fe11b077e3cb45410cecd42ff5a
run: agent-orchestrator
provides: [notify-listener, agent-view-builder]
acs_for_audit: []
process_gaps: [Red-first not observed for the new tests]
---

# api events and streams

## Requirement

Event paging and both SSE streams (D11, D14).

Paging:
- `GET /api/v1/clusters/{id}/events?before_id=&after_id=&limit=&agent_id=&types=` returns `{events, has_more_before, next_after_id}`.
- Both cursors together are 400 `bad_request`.

`GET /api/v1/clusters/{id}/events/stream`:
- SSE through `fastapi.sse.EventSourceResponse`.
- Each event has `id` = events.id and `event` = the event type; data is the stored row.
- It resumes after `Last-Event-ID` or `?after_id`, replaying stored rows first. With neither, it starts at the current newest id.
- Then it follows NOTIFY `events` for that cluster.
- Ping every 15 s; headers include `X-Accel-Buffering: no` and `Cache-Control: no-cache`.

`GET /api/v1/stream`:
- On connect it sends one `snapshot` event (every cluster view with its agents).
- On NOTIFY `status {cluster_id}` it sends a `cluster_status` delta (cluster view), `agent_status` deltas (agent views) and a `message_status` delta (queued and failed counts plus changed messages) for that cluster.

`api/listener.py`:
- One LISTEN connection per process, fanning out to in-process subscribers through bounded queues; a slow subscriber is dropped and its stream closed.
- Both streams also poll every 5 s, so a lost NOTIFY delays at most one poll.
- A client disconnect unsubscribes.

## Acceptance conditions

- AC1: events page backwards with before_id and reports has_more_before [evidence: test:tests/test_api_streams.py::test_events_page_backwards]
- AC2: both cursors are a 400 in the error shape [evidence: test:tests/test_api_streams.py::test_events_page_rejects_both_cursors]
- AC3: the cluster stream delivers newly inserted events live with their ids [evidence: test:tests/test_api_streams.py::test_events_stream_live_append]
- AC4: the cluster stream resumes from Last-Event-ID without gaps or duplicates [evidence: test:tests/test_api_streams.py::test_events_stream_resumes_from_last_event_id]
- AC5: the status stream sends a snapshot then deltas on NOTIFY status [evidence: test:tests/test_api_streams.py::test_status_stream_snapshot_and_delta]
- AC6: a lost NOTIFY is recovered by the poll [evidence: test:tests/test_api_streams.py::test_stream_recovers_from_lost_notify]
- AC7: many subscribers share one LISTEN connection [evidence: test:tests/test_api_streams.py::test_shared_listener_single_connection]
- AC8: SSE responses carry X-Accel-Buffering no [evidence: test:tests/test_api_streams.py::test_sse_headers]

## Files

- `src/agent_orchestrator/api/streams.py`
- `src/agent_orchestrator/api/listener.py`
- `src/agent_orchestrator/api/app.py`
- `tests/test_api_streams.py`

## Interfaces

- `agent_orchestrator.api.streams:router`; `agent_orchestrator.api.listener:Listener` with `subscribe(channel) -> AsyncIterator[dict]`

## Expected outcome

The UI and headless clients load the newest page, scroll back, and follow live without polling the wrappers.

## Steps

- Write tests/test_api_streams.py with the eight named tests; insert events with tests/factories.py plus pool.notify; read SSE through a real uvicorn server on a random port, because ASGITransport buffers streams; run it; expect failures.
- Implement listener.py and streams.py and include the router.
- Rerun `uv run pytest tests/test_api_streams.py -q`; expect `8 passed`; run `mise run lint`.

## Notes

FastAPI 0.160 has native SSE (`fastapi.sse.EventSourceResponse`, 15 s ping, sets X-Accel-Buffering). The ingress proxy-read-timeout 3600 is set through the chart's ingress annotations by epic agents-helmfile.
