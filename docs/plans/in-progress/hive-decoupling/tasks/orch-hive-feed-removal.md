---
title: orch hive feed removal
status: done
repo: agents-orchestrator
value: "members stop receiving the leader's truncated activity stream and the per-flip hive_state churn"
files: [src/agents_orchestrator/dispatcher/hive.py, src/agents_orchestrator/dispatcher/feed.py, src/agents_orchestrator/dispatcher/loop.py, tests/test_hive_push.py, tests/test_hive_feed.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_hive_push.py tests/test_hive_feed.py tests/test_readme_api.py tests/test_dispatcher_auto_handover.py tests/test_leadership_pass.py && mise run lint"
depends_on: [orch-activity-route]
model: opus
review: ""
verified_head: ca0b11901ac6bc269295a1b1ad7d74fadfe5733b
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: 5
actual_minutes: 72
actual_tokens: 3139018
actual_roles: "impl 36, review 37"
actual_role_tokens: "impl 2584814, review 554204"
---

# orch hive feed removal

## Requirement

User request (2026-10-27), verbatim: "Decouple agents in session more. Right now non-leaders get truncated stream of what's leader is doing. Ask fable architect to decouple or use handoff or something to consume non-leaders less."

README Goal G1, verbatim: "Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped." (This task: no feed note, the narrowed hash, hive.py stops reading and writing `feed_cursor`; orch-drop-feed-cursor drops the column.)

Design D1, verbatim: "`dispatcher/hive.py` stops reading `events` and stops sending appended notes: `_read` no longer queries `events`; `_Plan.lines`, `_Plan.feed_cursor`, `_Plan.new_cursor`, `HiveState.watermark`, `HiveState.carried`, `FEED_SETTLE_SECONDS`, `FEED_BATCH`, `FEED_MAX_CHARS` and `_FEED_TYPES` go; `feed.render_feed` goes (no other caller); `feed.digest_lines`, `FeedLine`, `_clean`, `_status`, `_EDIT_TOOLS` stay as the pure digest of D3."

Design D2, verbatim: "`state_hash` covers leader, epoch, the member set (pod_name, wrapper_session_id) and `ready`; `state` and the `context_pct` bucket leave the hash. The rendered text keeps each member's state and context as of the push and gains one sentence: "Call orchestrator_me for live state and context, orchestrator_activity for what peers did." The handover hint line becomes unconditional and uses the effective threshold `max(coalesce(spec.auto_compact_pct, settings.default_auto_compact_pct) - HANDOVER_MARGIN_PCT, 1)`, one helper in `hive.py` reused by D4."

Fix-as-ac (brief): "The handover hint is rendered only when `spec.auto_compact_pct` is set while pods compact at `default_auto_compact_pct` (95): make the hint and the plugin advice use the effective value." "`state_hash` re-pushes `hive_state` on every busy/idle flip and 10% context step (D2)." "README "Hive" says notes carry "an appended feed note with the peers' activity": rewrite."

Scope (agents-orchestrator):
- `src/agents_orchestrator/dispatcher/hive.py`: remove the feed phase and its state (D1); `_claim` writes only `state_hash` (no `feed_cursor`); `_read` no longer selects `l.feed_cursor`; narrowed `state_hash` (D2); the effective-threshold helper (for example `handover_threshold(spec, settings) -> int`); `render_hive_state` always renders the hint with it and the new sentence; module docstring rewritten (no feed).
- `src/agents_orchestrator/dispatcher/feed.py`: `render_feed` removed; module docstring says the digest serves `GET /agent/v1/activity`.
- `src/agents_orchestrator/dispatcher/loop.py`: `_push_loop` docstring ("Hive state and feed pushes") updated; no behaviour change here.
- `README.md`: `### Hive` bullet "`hive_state` and the feed" and the "Hive state push" paragraph under Routing rewritten (no feed note, structural re-push, effective hint, the pull tool).
- `MEMORY.md`: dated entry (hive-decoupling) recording the feed removal, the narrowed hash and the amendment of hive D9/D23 and leader-auto-handover D14.
- Tests no longer accurate, named: `tests/test_hive_push.py::test_feed_push_and_cursor`, `::test_feed_cursor_starts_at_max`, `::test_feed_cursor_settle_window`, `::test_feed_pending_bash_carried` (the feed is retired: removed, replaced by `test_no_feed_note`); `::test_hive_state_on_membership_change_only` (asserts re-pushes on context and busy changes: renamed and rewritten as `test_hive_state_on_structural_change_only`); `::test_hive_state_threshold_hint` (asserts no hint without `auto_compact_pct`: rewritten to the effective threshold); `::test_concurrent_pushes_claim_once` (counts 2 feed notes: counts 3 hive_state notes); `tests/test_hive_feed.py::test_render_feed` (render_feed retired: removed). `tests/test_hive_feed.py::test_pending_bash_carried_over` tests `digest_lines` and stays.

## Acceptance conditions

- ac1: peers' tool calls, writes and finished turns produce no unkeyed note to any member; only the keyed hive_state note is pushed [evidence: test:tests/test_hive_push.py::test_no_feed_note]
- ac2: hive_state is re-pushed on a leader, epoch, membership, wrapper session or ready change and not on a busy/idle flip or a context change [evidence: test:tests/test_hive_push.py::test_hive_state_on_structural_change_only]
- ac3: the hint always renders with the effective threshold: auto_compact_pct 80 gives 65%, no auto_compact_pct gives 80% (default 95), auto_compact_pct 10 gives 1% [evidence: test:tests/test_hive_push.py::test_hive_state_threshold_hint]
- ac4: the hive_state text carries "Call orchestrator_me for live state and context, orchestrator_activity for what peers did." [evidence: test:tests/test_hive_push.py::test_hive_state_points_to_pull_tools]
- ac5: two concurrent dispatchers push the 3 hive_state notes once [evidence: test:tests/test_hive_push.py::test_concurrent_pushes_claim_once]
- ac6: the feed code and constants are gone from the dispatcher [evidence: command:! grep -nE 'render_feed|FEED_SETTLE_SECONDS|FEED_BATCH|FEED_MAX_CHARS|_FEED_TYPES|feed_cursor' src/agents_orchestrator/dispatcher/hive.py src/agents_orchestrator/dispatcher/feed.py tests/test_hive_feed.py tests/test_hive_push.py && ! grep -nwE 'watermark|carried' src/agents_orchestrator/dispatcher/hive.py]
- ac7: the README no longer describes a feed note and names the pull tool [evidence: command:! grep -q "appended feed note" README.md && grep -q "orchestrator_activity" README.md]
- ac8: MEMORY.md records the decision [evidence: command:grep -q "hive-decoupling" MEMORY.md]
- ac9: the leader-auto-handover backstops are unchanged [evidence: command:uv run --frozen pytest tests/test_dispatcher_auto_handover.py tests/test_leadership_pass.py]
- ac10: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_hive_push.py tests/test_hive_feed.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/dispatcher/feed.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_hive_push.py`
- `tests/test_hive_feed.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `hive.handover_threshold(spec: dict, settings: Settings) -> int`: `max(coalesce(auto_compact_pct, default_auto_compact_pct) - HANDOVER_MARGIN_PCT, 1)`.
- `hive.state_hash(leader, epoch, members) -> str`: leader, epoch, `[pod_name, wrapper_session_id, ready]` per member.
- `hive.render_hive_state(payload, slug, threshold: int) -> str` (the threshold replaces the optional `auto_compact_pct`).
- `HiveState`: keeps `last_tick` only (D4 and D6 add their own fields later).

## Expected outcome

Members get only the keyed `hive_state` note, and only on structural change; the feed code is gone; the hint always names the real threshold.

## Steps

- Red: rewrite and add the tests of ac1-ac5 in `tests/test_hive_push.py`, remove the four feed tests and `tests/test_hive_feed.py::test_render_feed` (named in the Requirement); run `uv run --frozen pytest tests/test_hive_push.py tests/test_hive_feed.py`: the new ones fail.
- Green: hive.py, feed.py, loop.py docstring, README, MEMORY; run the task's verify: passes. Quote the summary line.
- The removal of `render_feed` and the constants is pinned by ac6 (deletion pinned by a retirement grep).

## Notes

- `feed_cursor` still exists in the schema after this task; only hive.py stops using it (orch-drop-feed-cursor drops it). `_set_leader` still writes it until then.
- Keep `_claim`/`_release`: one failing receiver retries alone; `state_pushed_at` moves only when every receiver took the state.
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-29 done
