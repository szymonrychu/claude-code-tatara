---
title: ingester
status: todo
repo: agent-orchestrator
value: "Turns each agent's event stream into stored history and live state: idle or busy, free since when, how full its context is."
files: [src/agent_orchestrator/ingester/__init__.py, src/agent_orchestrator/ingester/loop.py, src/agent_orchestrator/db/status.py, tests/test_ingester.py]
verify: "uv run pytest tests/test_ingester.py -q && mise run lint"
depends_on: [events-store, fake-wrapper-contract, cluster-token-derivation]
owns: []
uses: [events-repo, wrapper-client, fake-wrapper, cluster-tokens, schema-v1, pg-fixture, wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# ingester

## Requirement

The ingester (D5). It depends on epic claude-code-wrapper-orchestr.

`Ingester.run(stop)` keeps one task per agent that has a session and no `gone_at`. It refreshes that set every `settings.ingest_refresh_seconds`, starts a task for each new agent and cancels the task of each removed one.

Per agent:
- On attach, GET the snapshot and upsert `agent_status`.
  - State mapping: ready becomes idle, busy stays busy, creating becomes booting, and stopped, failed or dead become dead.
  - `free_since` is `idle_since` when idle.
  - The context columns come from `snapshot.context`, and null clears them.
- Also on attach, GET `/v1/peers` into `agent_status.peers`.
- Then stream events with `Last-Event-ID = last_seq` of that session.

Per envelope:
- Store it with `insert_events`. A seq greater than last_seq+1 first writes `insert_gap`.
- `session_state`: set state. A transition into idle sets `free_since = data.since` and NOTIFYs `agent_free {cluster_id, agent_id}`. Every state change NOTIFYs `status {cluster_id}`.
- `context`: set the context columns, then NOTIFY `status`.
- `turn_started`, `turn_completed`, `turn_failed`: upsert `turns` (origin, started_at, completed_at, status, final_text, usage).
- `session_closed`: state dead; the stream stops until the reconciler records a new session.
- Update `last_seq` and `updated_at`.

On disconnect, reconnect with backoff from 1 s doubling to 30 s, reset by a received event.

`db/status.py` (ingester is the writer): `upsert_status`, `set_state`, `set_context`, `set_peers`, `upsert_turn`.

## Acceptance conditions

- AC1: attaching seeds agent_status from the snapshot including idle_since and context [evidence: test:tests/test_ingester.py::test_attach_seeds_status_from_snapshot]
- AC2: streamed events are stored and NOTIFY events fires [evidence: test:tests/test_ingester.py::test_events_stored_and_notified]
- AC3: a reconnect resumes with Last-Event-ID and stores no duplicates [evidence: test:tests/test_ingester.py::test_resume_uses_last_event_id_no_duplicates]
- AC4: a seq hole writes a gap row [evidence: test:tests/test_ingester.py::test_gap_row_on_seq_hole]
- AC5: going idle sets free_since from data.since and notifies agent_free [evidence: test:tests/test_ingester.py::test_idle_sets_free_since_and_notifies_agent_free]
- AC6: a context event updates the context columns [evidence: test:tests/test_ingester.py::test_context_event_updates_status]
- AC7: turn events project into turns with final_text and usage [evidence: test:tests/test_ingester.py::test_turn_projection]
- AC8: a dropped stream reconnects with backoff [evidence: test:tests/test_ingester.py::test_reconnect_backoff_after_disconnect]
- AC9: a removed agent's stream task is cancelled [evidence: test:tests/test_ingester.py::test_agent_removed_stops_stream]
- AC10: the peers view is recorded on attach [evidence: test:tests/test_ingester.py::test_peers_view_recorded]

## Files

- `src/agent_orchestrator/ingester/__init__.py`
- `src/agent_orchestrator/ingester/loop.py`
- `src/agent_orchestrator/db/status.py`
- `tests/test_ingester.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
