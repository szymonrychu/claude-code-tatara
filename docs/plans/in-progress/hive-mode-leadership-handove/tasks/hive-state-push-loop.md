---
title: hive state push loop
status: in-progress
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
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-hive-state-push-loop/agent-orchestrator
branch: hive-mode-leadership-handove-hive-state-push-loop
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
- Interrogate item 2: the per-cluster advisory lock (pg_try_advisory_xact_lock) is held only around the DB read and write (reading members, hashes and events, storing hash and cursor), never across HTTP. Wrapper pushes run outside any transaction and outside drain's critical path (their own task in the dispatcher loop) with a short per-push timeout (`PUSH_TIMEOUT_SECONDS = 3`, module constant).
- Interrogate item 3(a): event ids commit out of order across per-agent ingester transactions, so the feed cursor only advances over a committed-safe window: rows newer than `FEED_SETTLE_SECONDS = 5` (module constant) are not consumed yet, so no row is skipped for good.
- Interrogate item 3(b): Bash calls reported pending by `digest_lines` are carried over to the next tick (kept in memory per cluster) and the cursor does not move past the oldest pending call until its result lands or the timeout elapses.
- Interrogate item 3(c): `feed_cursor` starts at the current max events id for the cluster when a cluster first becomes a hive (the leader row is created in the leadership pass) and in migration-0003-hive for existing hive clusters, so history is never pushed as current activity.

## Acceptance conditions

- AC1: a leader change pushes a keyed hive_state note to every live agent [evidence: test:tests/test_hive_push.py::test_hive_state_on_leader_change]
- AC2: an agent joining or leaving pushes a new hive_state; an unchanged state pushes nothing [evidence: test:tests/test_hive_push.py::test_hive_state_on_membership_change_only]
- AC3: the hive_state text carries the handover threshold when auto_compact_pct is set [evidence: test:tests/test_hive_push.py::test_hive_state_threshold_hint]
- AC4: feed notes exclude the receiver's own activity and the cursor advances [evidence: test:tests/test_hive_push.py::test_feed_push_and_cursor]
- AC5: pushes are throttled per cluster and skipped when another dispatcher holds the lock [evidence: test:tests/test_hive_push.py::test_throttle_and_lock]
- AC6: alone clusters get no notes and a 409 notes_disabled is tolerated [evidence: test:tests/test_hive_push.py::test_alone_and_disabled]
- AC7: the wrapper client and fake wrapper agree on the notes route [evidence: command:uv run pytest tests/test_wrapper_client.py tests/test_fake_wrapper_contract.py -q]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC9: a hanging wrapper does not delay claim_and_pick or the leadership pass of that cluster [evidence: test:tests/test_hive_push.py::test_hanging_wrapper_does_not_block_claim]
- AC10: a row committed late with a lower id than the cursor is still pushed once the settle window has passed [evidence: test:tests/test_hive_push.py::test_feed_cursor_settle_window]
- AC11: a pending Bash call is carried to a later tick and pushed with its exit status [evidence: test:tests/test_hive_push.py::test_feed_pending_bash_carried]
- AC12: a newly created leader row starts feed_cursor at the current max events id and old history is not pushed [evidence: test:tests/test_hive_push.py::test_feed_cursor_starts_at_max]

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

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 2

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 3
