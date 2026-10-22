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
  - `free_since` is the database `now()` at the moment the ingester records a transition into idle (D23: one clock; wrapper timestamps are never compared with database time). The wrapper `idle_since` is stored in `agent_status.wrapper_idle_since` for display only. An attach whose snapshot is idle while the stored state was not idle counts as such a transition.
  - The context columns come from `snapshot.context`, and null clears them.
- Also on attach, GET `/v1/peers` into `agent_status.peers` (the member list as returned: `enabled`, `self`, `members[{instance, url, sessions, last_seen_at, missed}]`) and set the peer count to `len(members)`, 0 when `enabled` is false. Refresh it on every `session_state` transition into idle.
- Then stream events with `Last-Event-ID = last_seq` of that session.

Per envelope:
- Store it with `insert_events`. A seq greater than last_seq+1 first writes `insert_gap`.
- `session_state`: set state. A transition into idle (stored state was not idle) sets `free_since = now()` (database clock), stores `data.since` in `wrapper_idle_since`, and NOTIFYs `agent_free {cluster_id, agent_id}`. Every state change NOTIFYs `status {cluster_id}`.
- `context`: set the context columns, then NOTIFY `status`.
- `user_message`: stored as an `events` row like every other type and rendered by the chat as a user chat row, or a peer chat row when `origin` is `peer`. It uses the wrapper origin vocabulary `client|initial|agent|peer|restart|command` (turns.py:27 plus `restart` and `command`; `command` has `turn_id` null); `restart` rows are rendered as a system continue line. The ingester does not project it into `turns`.
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
- AC5: going idle sets free_since from the database clock (not data.since), stores data.since as wrapper_idle_since, and notifies agent_free [evidence: test:tests/test_ingester.py::test_idle_sets_free_since_and_notifies_agent_free]
- AC6: a context event updates the context columns [evidence: test:tests/test_ingester.py::test_context_event_updates_status]
- AC7: turn events project into turns with final_text and usage [evidence: test:tests/test_ingester.py::test_turn_projection]
- AC8: a dropped stream reconnects with backoff [evidence: test:tests/test_ingester.py::test_reconnect_backoff_after_disconnect]
- AC9: a removed agent's stream task is cancelled [evidence: test:tests/test_ingester.py::test_agent_removed_stops_stream]
- AC10: the peers view and peer count are recorded on attach, and enabled false gives count 0 [evidence: test:tests/test_ingester.py::test_peers_view_recorded]
- AC11: a user_message event is stored as an events row with its origin and is not projected into turns [evidence: test:tests/test_ingester.py::test_user_message_stored_as_event_row]
- AC12: a repeated or replayed idle event while already idle does not move free_since [evidence: test:tests/test_ingester.py::test_repeated_idle_does_not_move_free_since]

## Files

- `src/agent_orchestrator/ingester/__init__.py`
- `src/agent_orchestrator/ingester/loop.py`
- `src/agent_orchestrator/db/status.py`
- `tests/test_ingester.py`

## Interfaces

- `agent_orchestrator.ingester.loop:Ingester(pool, settings, wrapper_factory)` with `run(stop)`
- `agent_orchestrator.db.status`: `upsert_status`, `set_state`, `set_context`, `set_peers`, `upsert_turn`

## Expected outcome

agent_status, turns and events reflect every agent live; the dispatcher wakes when an agent frees.

## Steps

- Write tests/test_ingester.py with the twelve named tests against FakeWrapper and the pool fixture; run it; expect failures.
- Implement db/status.py and ingester/loop.py.
- Rerun `uv run pytest tests/test_ingester.py -q`; expect `12 passed`; run `mise run lint`.

## Notes

The ingester does not page wrapper history for gap backfill (a gap writes `insert_gap` only), so it does not use wrapper-history-backward. Event types and the context fields follow the wrapper README of epic claude-code-wrapper-orchestr. Make backoff delays injectable so tests run fast. Never move free_since except on a transition into idle: the dispatcher's reservation rule depends on it.
