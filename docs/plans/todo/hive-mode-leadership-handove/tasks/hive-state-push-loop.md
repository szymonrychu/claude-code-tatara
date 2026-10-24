---
title: hive state push loop
status: todo
repo: agent-orchestrator
value: "every hived agent knows the leader, its peers and their recent activity without asking"
files: [src/agent_orchestrator/dispatcher/hive.py, src/agent_orchestrator/dispatcher/loop.py, src/agent_orchestrator/db/leadership.py, src/agent_orchestrator/wrapper/client.py, tests/fakes/fake_wrapper.py, tests/test_hive_push.py, tests/test_fake_wrapper_contract.py]
verify: "uv run pytest tests/test_hive_push.py tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [dispatcher-leadership-pass, hive-feed-digest, orch-pin-bumps]
owns: [orch-hive-state-note]
uses: [orch-leadership-pass, orch-feed-digest, orch-hive-pins]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# hive state push loop

## Requirement

Every agent knows the hive and sees the others' activity (D3, Q6, Q7, Q9). `dispatcher/hive.py` `push_once(pool, settings, client_factory)`, run by the dispatcher process (never the singleton ingester), for each hive cluster under the per-cluster advisory lock (try; skip when held):

- `hive_state` note: `{leader, epoch, you, members: [{pod_name, ready, state, context_pct, leader}], max_replicas, static}` rendered as a `<hive-state>` text block ("You are <you> (leader|member) in hive <slug> of up to <N> agents. Leader: <x> (epoch <e>). Members: ...") plus "Hand over leadership instead of compacting above <auto_compact_pct - 15>% context" when `auto_compact_pct` is set (Q9). Pushed keyed (`key: hive_state`) to every not-gone agent with a session when the state hash (leader, epoch, member set, ready, state, context in 10% buckets) differs from `cluster_leaders.state_hash`; the hash and `state_pushed_at` are stored only when every push succeeded.
- Feed: events of the cluster with `id > cluster_leaders.feed_cursor` (at most 500 rows per tick), digested with `feed.digest_lines`, rendered per receiving agent with `feed.render_feed`, pushed as an appended note when non-empty; `feed_cursor` advances to the last processed id (best effort: a failed push is logged and not retried).
- At most one push per cluster every `PUSH_INTERVAL_SECONDS = 10` (module constant, my call); the loop also wakes on `leader_changed`.
- `WrapperClient.post_note(session_id, text, key=None, source="orchestrator")` -> `POST /v1/sessions/{id}/notes`; 409 `notes_disabled` and unavailable answers are logged and skipped.
- The fake wrapper (`tests/fakes/fake_wrapper.py`) serves the notes route and records notes per session; `tests/test_fake_wrapper_contract.py` covers the route against the real wrapper (integration marker).
- Alone clusters get nothing.

## Acceptance conditions

- AC1: a leader change pushes a keyed hive_state note to every live agent [evidence: test:tests/test_hive_push.py::test_hive_state_on_leader_change]
- AC2: an agent joining or leaving pushes a new hive_state; an unchanged state pushes nothing [evidence: test:tests/test_hive_push.py::test_hive_state_on_membership_change_only]
- AC3: the hive_state text carries the handover threshold when auto_compact_pct is set [evidence: test:tests/test_hive_push.py::test_hive_state_threshold_hint]
- AC4: feed notes exclude the receiver's own activity and the cursor advances [evidence: test:tests/test_hive_push.py::test_feed_push_and_cursor]
- AC5: pushes are throttled per cluster and skipped when another dispatcher holds the lock [evidence: test:tests/test_hive_push.py::test_throttle_and_lock]
- AC6: alone clusters get no notes and a 409 notes_disabled is tolerated [evidence: test:tests/test_hive_push.py::test_alone_and_disabled]
- AC7: the wrapper client and fake wrapper agree on the notes route [evidence: command:uv run pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -q]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/dispatcher/hive.py`
- `src/agent_orchestrator/dispatcher/loop.py`
- `src/agent_orchestrator/db/leadership.py`
- `src/agent_orchestrator/wrapper/client.py`
- `tests/fakes/fake_wrapper.py`
- `tests/test_hive_push.py`
- `tests/test_fake_wrapper_contract.py`

## Interfaces

- Owns part `orch-hive-state-note` (cross-epic contract): `dispatcher/hive.py` `push_once`, the `hive_state` note text and schema; `WrapperClient.post_note`.

## Expected outcome

Hived agents receive a hive-state note on every leader or membership change and feed notes about the others' work.

## Steps

- Red: write `tests/test_hive_push.py` for AC1-AC6 against the fake wrapper; run `uv run pytest tests/test_hive_push.py -q`: fails.
- Green: `post_note`, the fake route, `hive.py`, the drain wiring; run the verify command: passes.

## Notes

- Wrapper client at `wrapper/client.py:46`; fake at `tests/fakes/fake_wrapper.py:204`; real-wrapper contract runs under `-m integration`.
- `events.page(types=...)` (`db/events.py:117-170`) or a direct keyset query by `(cluster_id, id)`.
