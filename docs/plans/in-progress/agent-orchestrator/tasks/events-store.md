---
title: events store
status: in-progress
repo: agent-orchestrator
value: "Every agent's activity stored once in a merged, pageable timeline that survives pod and cluster deletion."
files: [src/agent_orchestrator/db/events.py, tests/test_events_store.py]
verify: "uv run pytest tests/test_events_store.py -q && mise run lint"
depends_on: [migrations-and-schema]
owns: [events-repo]
uses: [schema-v1, pg-fixture]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-events-store/agent-orchestrator
branch: agent-orchestrator-events-store
verified_head: ""
run: ""
provides: []
---

# events store

## Requirement

The `events` table repository (D5).

- `insert_events(conn, cluster_id, agent_id, session_id, envelopes) -> int | None`: inserts wrapper envelopes `{seq, ts, type, data}` (turn_id lifted from data) with `ON CONFLICT DO NOTHING`, returns the max inserted id, and NOTIFYs `events {cluster_id, max_id}` only when at least one row was new.
- `insert_gap(conn, cluster_id, agent_id, session_id, after_seq, before_seq)`: a synthetic `gap` row with `data {after_seq, before_seq}`.
- `last_seq(conn, agent_id, session_id) -> int`.
- `page(conn, cluster_id, before_id=None, after_id=None, limit=200, agent_id=None, types=None) -> Page`. Rows come back in ascending id order. Without cursors it returns the newest `limit` rows. `before_id` returns the `limit` rows just older. `after_id` returns rows newer. Passing both raises `ValueError`. `limit` is capped at 500. `Page` carries `events`, `has_more_before` and `next_after_id`.
- Rows of all agents of a cluster interleave by the global id.

## Acceptance conditions

- AC1: inserting the same envelopes twice stores them once [evidence: test:tests/test_events_store.py::test_insert_is_idempotent]
- AC2: NOTIFY events fires only when rows were new [evidence: test:tests/test_events_store.py::test_notify_only_on_new_rows]
- AC3: a cursorless page is the newest rows; before_id pages backwards with has_more_before [evidence: test:tests/test_events_store.py::test_page_newest_then_before]
- AC4: after_id returns newer rows [evidence: test:tests/test_events_store.py::test_page_after_id]
- AC5: agent_id and types filter the page [evidence: test:tests/test_events_store.py::test_filter_agent_and_types]
- AC6: two agents' events interleave by global id [evidence: test:tests/test_events_store.py::test_merged_order_across_agents]
- AC7: a gap row records the missing seq range [evidence: test:tests/test_events_store.py::test_gap_row]
- AC8: before_id and after_id together raise ValueError [evidence: test:tests/test_events_store.py::test_before_and_after_rejected]

## Files

- `src/agent_orchestrator/db/events.py`
- `tests/test_events_store.py`

## Interfaces

- `agent_orchestrator.db.events` (contract `events-repo`): `insert_events`, `insert_gap`, `last_seq`, `page`, `Page`

## Expected outcome

The ingester can store, and the API can page, one merged timeline per cluster.

## Steps

- Write tests/test_events_store.py with the eight named tests; run it; expect failures.
- Implement db/events.py.
- Rerun `uv run pytest tests/test_events_store.py -q`; expect `8 passed`; run `mise run lint`.

## Notes

The NOTIFY payload is ids only, never content (design section 1). Index (cluster_id, id DESC) serves the newest page.
