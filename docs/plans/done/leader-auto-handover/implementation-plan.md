# leader auto handover implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: compaction status projection

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0006_compaction.sql`, `src/agents_orchestrator/db/status.py`, `src/agents_orchestrator/ingester/loop.py`, `tests/test_ingester.py`, `tests/test_migrations.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_ingester.py tests/test_migrations.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: cc336cb6b426e15c3689659727502205d4e2c3b8

#### Requirement

Goal G1: "the orchestrator moves leadership to another ready agent of the cluster" when the leader is about to compact. User call: "every compaction counts, auto and manual."

Design D2, verbatim: both `compacting` (before) and `compacted` (after, from the transcript boundary) count as a compaction of that agent. Auto, manual, the orchestrator's compact command, the wrapper's idle auto-compact and Claude Code's own idle compaction all count.

Design D3, verbatim: migration `0006_compaction.sql` adds `agent_status.compaction_at timestamptz` (nullable). The ingester's projection sets it from the event's own `ts` (the wrapper's clock, when the compaction was reported), never from the ingest time, and never moves it backwards (`greatest(compaction_at, ts)`), when it stores a `compacting` or `compacted` event of that agent; it NOTIFYs `status` as it does for `context` and wakes the dispatcher (D15). Nothing else writes it. An old event ingested late (a stream resume or replay) therefore carries its old time, and a leader elected after it (`since` later than the event's `ts`) is never handed over for it.

Design D15, verbatim (ingester half): when the ingester projects a compaction (D3) it also sends `NOTIFY leadership_requested {session_id}`.

Scope:
- `src/agents_orchestrator/db/migrations/0006_compaction.sql`: `ALTER TABLE agent_status ADD COLUMN IF NOT EXISTS compaction_at timestamptz;` (idempotent like 0003).
- `src/agents_orchestrator/db/status.py`: a `set_compaction(conn, agent_id, at)` (name left to the builder) that sets `compaction_at = greatest(compaction_at, at)` and `updated_at = now()`.
- `src/agents_orchestrator/ingester/loop.py` `_project`: a branch for `compacting` and `compacted` that calls it with the envelope's `ts` (`env.ts`), then `status.notify_status` and `NOTIFY leadership_requested {session_id}` (the channel constant `db/leadership.CHANNEL`); the event is still stored as an events row.
- README: the `agent_status` row of the tables list names the last compaction time (`compaction_at`, written by the ingester on `compacting` or `compacted`).
- Tests in `tests/test_ingester.py`: emitting `compacting` through the fake wrapper sets `compaction_at` to the event's `ts` and NOTIFYs `status` and `leadership_requested`; a later `compacted` moves it forward; an event whose `ts` is older than the stored value (a late or replayed event) never moves it backwards; other event types leave it unchanged.
- Tests no longer accurate, to update: `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `tests/test_migrations.py::test_presets_migration_on_existing_sessions` pin the applied migration versions as ending at `0005`; they now end at `0006`. Add a `0006` schema test there (column exists, nullable, rerun is a no-op).

Notes: the fake wrapper's `emit` does not validate event names (`tests/fakes/fake_wrapper.py:314`), so this task does not need the wrapper 0.3.0 pin. Reuse the `context` branch's shape (`ingester/loop.py:194-196`). The dispatcher reads the column in task leadership-auto-handover; do not touch `db/leadership.py` here. Docker disk: the DB tests need testcontainers (or the shared Postgres override); a full Docker VM disk is an environment blocker to report, not to work around.

#### Acceptance conditions

- AC1: a stored `compacting` event sets `agent_status.compaction_at` to the event's own `ts`, not the ingest time, and NOTIFYs `status` and `leadership_requested {session_id}` [evidence: test:tests/test_ingester.py::test_compacting_sets_compaction_at]
- AC2: a later `compacted` event moves `compaction_at` forward and other event types leave it unchanged [evidence: test:tests/test_ingester.py::test_compacted_moves_compaction_at]
- AC3: a late or replayed compaction event with an older `ts` never moves `compaction_at` backwards and never sets it later than its own `ts` [evidence: test:tests/test_ingester.py::test_late_compaction_event_keeps_its_time]
- AC4: migration 0006 adds the nullable column, is idempotent, and the applied versions end at 0006 [evidence: command:uv run --frozen pytest -q tests/test_migrations.py]
- AC5: README documents the column and every table stays documented [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/migrations/0006_compaction.sql`
- `src/agents_orchestrator/db/status.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
- `tests/test_migrations.py`
- `README.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add the three ingester tests to `tests/test_ingester.py` and the 0006 schema test plus the updated version lists to `tests/test_migrations.py`; run `uv run --frozen pytest -q tests/test_ingester.py tests/test_migrations.py`: the new tests fail (no column, no projection).
- Green: add `0006_compaction.sql`, the `db/status.py` setter, the ingester branch with the `leadership_requested` NOTIFY, and the README row; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): findings 2 and 3 (wake, event time)

- 2026-10-26 done

### S2: orch eligibility single source

- Status: done
- Files: `src/agents_orchestrator/db/eligibility.py`, `src/agents_orchestrator/db/leadership.py`, `src/agents_orchestrator/db/queue.py`, `src/agents_orchestrator/db/sessions.py`
- Verify: `uv run ruff check . && uv run ruff format --check . && uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py tests/test_queue_leader_routing.py tests/test_sessions_repo.py tests/test_agent_scale.py tests/test_api_scale.py tests/test_reconciler.py`
- Verified head: 059372fcd3ce0453be243bd7b62ad1a15fd67d56

#### Requirement

Epic review finding (leader-auto-handover review, 2026-10-27, Consider 2, scope-auditor duplicate sweep), accepted by the hive leader as a task: "orchestrator single source for eligibility/handover-pending predicates (agents-orchestrator, sonnet, behaviour unchanged)".

Evidence from the review (main b3a2975):
- `db/leadership.py` `_CANDIDATES` respells the eligible predicate inline (alias `x`: ready, gone_at IS NULL, wrapper_session_id IS NOT NULL, ordinal < REPLICAS) instead of `eligibility.ELIGIBLE`.
- `db/leadership.py` `_target_ready` respells ready / gone next to `STAYS` (it does not require `wrapper_session_id`; keep that exactly).
- The "compacted in its term or leaving" trigger is spelled three times: `_CANDIDATES`, `_leader` (`leaving`, `compacted` columns), `db/queue.py` `_HANDOVER_PENDING`.
- `eligibility.REPLICAS` repeats the `2147483647` literal instead of `NO_LIMIT`.

Scope: `db/eligibility.py` becomes the single source of these SQL fragments (stays / ready-and-stays / eligible, the compacted-or-leaving trigger, REPLICAS built from NO_LIMIT); `_CANDIDATES`, `_target_ready`, `_leader` and `_HANDOVER_PENDING` (and `sessions.set_replicas` if it respells any) use them. Behaviour unchanged: no SQL semantics change, no test edited or weakened; the existing tests (tests/test_leadership_pass.py, test_dispatcher_auto_handover.py, test_queue_leader_routing.py, test_sessions_repo.py, test_agent_scale.py, test_api_scale.py, test_reconciler.py) are the guard. This is a pure refactor (TDD exception: behaviour-preserving refactor under existing tests); add a unit test pinning that the shared fragments are what the call sites embed only if cheap.

Environment note: the DB tests use testcontainers and need Docker, which this pod lacks (no docker, no dockerd). Run lint and every test that does not need Docker locally; the PR's GitHub CI `test` job (`mise run test`) is the evidence for the DB tests and is checked by the orchestrator before merge.

#### Acceptance conditions

- AC1: eligibility.py holds the stays, ready-and-stays, eligible and compacted-or-leaving fragments and REPLICAS uses NO_LIMIT [evidence: symbol:src/agents_orchestrator/db/eligibility.py:ELIGIBLE]
- AC2: leadership.py and queue.py contain no inline respelling of those predicates [evidence: command:! grep -nE "x\.ready|2147483647" src/agents_orchestrator/db/leadership.py src/agents_orchestrator/db/queue.py]
- AC3: the leadership, queue and scale tests pass unchanged [evidence: command:uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py tests/test_queue_leader_routing.py tests/test_sessions_repo.py tests/test_agent_scale.py tests/test_api_scale.py tests/test_reconciler.py]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/eligibility.py`
- `src/agents_orchestrator/db/leadership.py`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/db/sessions.py`

#### Interfaces

- `src/agents_orchestrator/db/eligibility.py`: module constants (SQL fragments) `NO_LIMIT`, `REPLICAS`, `STAYS`, `ELIGIBLE`, plus new fragments for ready-and-stays and the compacted-or-leaving trigger; aliases documented as today.
- Kept unchanged: `leadership._CANDIDATES`, `leadership._leader` result columns (`leaving`, `compacted`), `leadership._target_ready`, `queue._HANDOVER_PENDING`, `sessions.set_replicas` semantics.

#### Expected outcome

Every eligibility and handover-pending predicate is spelled once in `eligibility.py`; the call sites embed the shared fragments; SQL semantics and all tests are unchanged.

#### Steps

- Read eligibility.py, leadership.py, queue.py, sessions.py and the guard tests in one pass.
- Behaviour-preserving refactor (TDD exception: refactor under existing tests). Baseline: `uv run ruff check . && uv run ruff format --check .` passes; non-Docker tests pass.
- Move the fragments into eligibility.py and replace the inline spellings; run AC2's grep: no output.
- `uv run ruff check . && uv run ruff format --check .`: `All checks passed!`.
- Run the task verify; DB tests need Docker (absent in this pod), so they error locally and the PR CI `test` job is the evidence.

#### Notes

Keep `_target_ready` without the `wrapper_session_id` requirement (manual make-leader target), exactly as today. `_CANDIDATES` uses alias `c` for the session and `REPLICAS`; `ELIGIBLE` uses a subquery `STAYS` - equivalent, choose the shared fragment that preserves semantics. The module docstring explains why eligibility.py lives apart from leadership.py (import cycle with queue.py).

- 2026-10-27 done: reviewer clean (SQL equivalence); PR #25 CI test '1083 passed, 56 deselected' and kind e2e pass on 059372f (DB tests need Docker, absent in this pod)

### S3: wrapper compacting event

- Status: done
- Files: `src/claude_code_wrapper/router.py`, `src/claude_code_wrapper/events.py`, `README.md`, `tests/test_command_signals.py`, `tests/test_event_log.py`
- Verify: `uv run pytest -q tests/test_command_signals.py tests/test_event_log.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: ef64fb0fbe913ca9f0a6a5ea2680ae242f04b485

#### Requirement

Goal G1 (user, 2026-10-26): "when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction runs". User decision: "hand over just before compaction. This needs a new pre-compaction event from the wrapper, from Claude Code's PreCompact hook, and so a claude-code-wrapper release."

Design D1, verbatim: the PreCompact relay handler (`router.py` `_on_compact_hook`) emits the event `compacting` with `{trigger}` (`manual`, `auto`, else `unknown`, the same vocabulary as `compacted`) to the event log before it returns allow, and keeps publishing the `pre_compact` signal. Claude Code waits for the hook, so the event is in the log before the compaction runs. `EVENT_TYPES` gains `compacting` just before `compacted`; README documents it. The handler still answers at once (no hold). `custom_instructions` is left out of the event.

Scope:
- `src/claude_code_wrapper/events.py`: add `"compacting"` to `EVENT_TYPES` immediately before `"compacted"`.
- `src/claude_code_wrapper/router.py` `_on_compact_hook`: for `PreCompact`, emit `compacting` through `self._emit` with `{"trigger": <normalised trigger>}` before returning `_allow()`; the `pre_compact` signal is still published with its current data. `PostCompact` is unchanged (no event).
- README: a `### compacting` section next to `### compacted` (when it is emitted: once per PreCompact hook call, before the compaction runs, for manual and auto compactions; `data`: `trigger`), and the `### compacted` text stays.
- Tests in `tests/test_command_signals.py`: the PreCompact relay emits exactly one `compacting` event whose data is `{"trigger": ...}`, it is in the log by the time `handle_claude_hook` returns, an unknown or missing trigger reads `unknown`, the relay response is still the immediate allow, and `PostCompact` emits no `compacting`.
- Test no longer accurate, to update: `tests/test_event_log.py::test_event_types_exact` pins the exact `EVENT_TYPES` list, which now gains `compacting` before `compacted`. Existing assertions in `tests/test_command_signals.py` (for example `h.events("compacted") == []` after the relays) stay as they are.

Notes: the fake claude's `auto_compact` step already runs the PreCompact hook (`tests/fake_claude/fake_claude.py:709-712`), so a scripted native compaction produces `compacting` end to end. `tests/test_readme_api.py::test_every_event_type_documented` fails until README has the section. Do not change the hook relay timeouts or make the handler wait on anything.

#### Acceptance conditions

- AC1: a PreCompact relay emits exactly one `compacting` event with data `{"trigger": "auto"}` (or `manual`) before `handle_claude_hook` returns, and still answers allow at once [evidence: test:tests/test_command_signals.py::test_pre_compact_emits_compacting]
- AC2: a PreCompact payload with a missing or unknown trigger emits `compacting` with trigger `unknown`, and PostCompact emits no `compacting` [evidence: test:tests/test_command_signals.py::test_compacting_trigger_normalised]
- AC3: `EVENT_TYPES` lists `compacting` immediately before `compacted` [evidence: test:tests/test_event_log.py::test_event_types_exact]
- AC4: README documents the `compacting` event [evidence: test:tests/test_readme_api.py::test_every_event_type_documented]
- AC5: the compaction signal tests still pass [evidence: command:uv run pytest -q tests/test_command_signals.py tests/test_fake_claude_commands.py]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/events.py`
- `README.md`
- `tests/test_command_signals.py`
- `tests/test_event_log.py`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add `test_pre_compact_emits_compacting` and `test_compacting_trigger_normalised` to `tests/test_command_signals.py`, update `tests/test_event_log.py::test_event_types_exact` (gains `compacting` before `compacted`); run `uv run pytest -q tests/test_command_signals.py tests/test_event_log.py`: the new tests and the exact-list test fail (no such event).
- Green: add `compacting` to `EVENT_TYPES`, emit it in `_on_compact_hook` for PreCompact, add README `### compacting`; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S4: leadership auto handover

- Status: done
- Files: `src/agents_orchestrator/db/leadership.py`, `tests/test_leadership_pass.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: d2ca76c8efe33e088a71b41117adfb526d579786

#### Requirement

Goals, verbatim:
- G1: when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction runs (the `compacting` event; only this report precedes the compaction) and the orchestrator then moves leadership to another ready agent of the cluster at the leader's turn boundary, which for a busy leader is after the native compaction has run.
- G2 (dispatcher half): a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks.
- G3: the new leader is chosen among ready agents that stay in the cluster (never one about to be removed); with no eligible agent the leader keeps leading and the move is retried.
- G4: always on for every hive (max_replicas > 1); a cluster of one never hands over.

User decision (binding): "auto handover is ALWAYS ON for hived agents (max_replicas > 1)". Orchestrator-session calls (design marks them `(my call)`): "Who takes over: the existing longest-free pick, restricted to agents that stay. With no eligible peer, the leader stays and the move is retried." "A busy leader moves at its turn boundary." Q1 (open, recommended yes): the retry lasts for the rest of the term.

Design, verbatim:
- D4: the leadership pass gets a compaction step: when the leader's `compaction_at` is later than its term's `since`, the leader is ready and not gone, and it is at its turn boundary (the existing `at_boundary`: state `idle` and no message `dispatching` or `verifying`), leadership moves to the staying agent free the longest (D7), at `epoch + 1`, reason `compaction`. A busy leader keeps leading until its turn ends (the native auto-compaction runs mid-turn), and the first pass after the turn moves it. (The claim-path hold that keeps a compacted leader from taking one more untargeted message within a drain is task claim-hold-and-handover-wake, D16.) With no eligible agent the leader stays, keeps receiving untargeted messages (G3), nothing is written, and the session stays a leadership candidate so every pass retries; the retry lasts for the rest of the leader's term, so a peer that becomes ready later (or a later scale-up of a hive running one agent) takes over. A new term (any leader change) starts clean. `_CANDIDATES` gains the clause "the leader's `compaction_at` > `since`". Each step of the pass re-reads the leader after a change, so after the scale-down step moves leadership the compaction and lease steps judge the new leader at its new epoch and fresh `since`, and do not move it again.
- D6: the leadership pass gets a scale-down step, run after the queued requests and before the lost-leader step: when the leader is not gone and its ordinal is at or above `spec.replicas`, leadership moves to the staying agent free the longest (D7), at `epoch + 1`, reason `scale_down`, without waiting for the leader's turn boundary. With no staying agent the leader stays and the pass retries (the session is a candidate while the leader is leaving). A gone leader keeps the lost-leader path (reason `leader_lost`). `_CANDIDATES` gains "the leader is not gone and its ordinal >= `spec.replicas`". A leaving leader that the reconciler has already marked not ready (`_observe` sets `ready = ordinal < replicas and pod ready`, `reconciler/loop.py:367`) but that is not gone is still handled by this step at once, before the lost-leader step can see it, so its change always reads `scale_down`, never `leader_lost`.
- D7: an agent stays when its ordinal is below the session's `spec.replicas`. `_FREE_LONGEST` (handover without a target, `leader_lost`, `lease_expired`, `compaction`, `scale_down`), `_target_ready` (named handover and user make-leader targets: a leaving target is rejected `target_not_ready`) and the initial election all filter on it. The order stays the existing one (idle first, then `free_since` ascending, then id). No context-aware choice.
- D9: both triggers apply to every session the pass already covers (`_HIVE`). No spec field. A session running one agent never hands over.
- D13: the README `### Leadership` lists every pass step in order: 1 initial, 2 queued requests, 3 scale-down, 4 lost leader, 5 compaction, 6 lease (it says "three steps" today and omits the lease). Compaction runs before the lease so a leader that both compacted and outlived its lease reads `compaction`. MEMORY.md gets dated entries amending hive D26 (a second system handover of the current term at a turn boundary, after `leader_lease_seconds`; never a takeover, hive D21 holds) and cluster-scaling D7 ("scaling never moves leadership") and its anti-goal "leadership moving because of scaling".
- D14: no change to the hive_state handover hint, the any-mcp tool text or `/agent/v1/me`.

Scope:
- `src/agents_orchestrator/db/leadership.py`: the staying filter (`ordinal < (spec->>'replicas')::int` of the session) in `_FREE_LONGEST`, `_target_ready` and the initial election; the two `_CANDIDATES` clauses; `_leader` exposes what the steps need (the leader's ordinal, whether it is leaving, whether `agent_status.compaction_at > since`); the scale-down step and the compaction step in the order above; module docstring and step comments updated. Keep the single transaction and the claim lock.
- `tests/test_leadership_pass.py`: new tests (names in the acceptance conditions). Existing tests stay accurate; none is edited to pass.
- README `### Leadership` (steps, the two reasons, the new candidate conditions, "always on for hives") and `### Leader lease` (now step 6).
- MEMORY.md: the two dated amendment entries (2026-10-26, epic leader-auto-handover).

Notes: `compaction_at` is the wrapper's event time (task compaction-status-projection), compared with `since`; a compaction reported before the leader's term began never triggers. Reuse the lease step pattern (`db/leadership.py:320-332`), `_set_leader` (epoch bump, `unready_since` cleared, `leader_changed` NOTIFY, hive push and frame for free) and `at_boundary` (`leadership.py:143-146`). The column `agent_status.compaction_at` comes from task compaction-status-projection. The NOTIFY payload change (reason) belongs to task leader-changed-reason; do not change it here. The candidate query must not select a healthy, uncompacted, staying leader every poll (`test_candidates` and `test_lease_candidates` show the pattern).

#### Acceptance conditions

- AC1: a leader whose `compaction_at` is after its `since` hands over at its turn boundary to the staying agent free the longest, at epoch + 1, reason `compaction` [evidence: test:tests/test_leadership_pass.py::test_compaction_hands_over_at_boundary]
- AC2: a busy compacted leader keeps leading until its turn ends, then moves on the next pass [evidence: test:tests/test_leadership_pass.py::test_compaction_waits_for_turn_boundary]
- AC3: a compacted leader with no eligible agent stays, nothing is written, and it moves on a later pass once an agent becomes ready; a new term clears the trigger [evidence: test:tests/test_leadership_pass.py::test_compaction_without_peer_retries]
- AC4: a compaction reported before the current term began (`compaction_at <= since`, including an old event of an agent elected after it) and a compaction of a non-leader trigger nothing [evidence: test:tests/test_leadership_pass.py::test_compaction_before_term_ignored]
- AC5: a leader whose ordinal is at or above `spec.replicas` moves at once (even when busy) to a staying agent, reason `scale_down`; a leaving leader already marked not ready by the reconciler but not gone, including one whose unready grace has run out, also moves at once with reason `scale_down` and never `leader_lost`; with no staying agent it stays and is retried [evidence: test:tests/test_leadership_pass.py::test_scale_down_hands_over_leader]
- AC6: `_FREE_LONGEST`, named handover targets, user targets and the initial election never pick an agent with `ordinal >= spec.replicas`, even while it is still ready [evidence: test:tests/test_leadership_pass.py::test_picks_skip_leaving_agents]
- AC7: the candidate query selects sessions with a compacted leader or a leaving leader, and not a hive whose leader is healthy, uncompacted and staying; a hive running one agent (`spec.replicas` 1, `max_replicas` > 1) whose leader compacted stays a candidate with the leader unchanged, and its leader moves with reason `compaction` once a peer becomes ready; an alone session (`max_replicas` 1) is never a candidate [evidence: test:tests/test_leadership_pass.py::test_auto_handover_candidates]
- AC8: when the leader both compacted and outlived its lease the reason is `compaction` [evidence: test:tests/test_leadership_pass.py::test_compaction_before_lease]
- AC9: in one pass, after the scale-down step moves a leaving leader that had also compacted and outlived its lease, the compaction and lease steps re-read the leader and judge the new one at its new epoch: exactly one change, epoch + 1, reason `scale_down` [evidence: test:tests/test_leadership_pass.py::test_steps_reread_leader_after_change]
- AC10: the existing leadership and routing tests still pass [evidence: command:uv run --frozen pytest -q tests/test_leadership_pass.py tests/test_queue_leader_routing.py tests/test_api_leadership.py]
- AC11: README Leadership lists the six steps and MEMORY.md records the D26 and D7 amendments [evidence: command:grep -q "scale_down" README.md && grep -q "compaction" README.md && grep -q "leader-auto-handover" MEMORY.md && uv run --frozen pytest -q tests/test_readme_api.py]
- AC12: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/leadership.py`
- `tests/test_leadership_pass.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add the new tests of the acceptance conditions to `tests/test_leadership_pass.py`; run `uv run --frozen pytest -q tests/test_leadership_pass.py`: they fail (no staying filter, no scale-down or compaction step).
- Green: add the staying filter, the two candidate clauses, the scale-down step (before the lost-leader step) and the compaction step (before the lease step) to `db/leadership.py`; run the same command: passes.
- Docs: rewrite README `### Leadership` and `### Leader lease`, add the two MEMORY.md entries; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): findings 1, 2, 4, 6, 7, 8

- 2026-10-26 done

### S5: wrapper release 0.3.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py`
- Verify: `uv run pytest -q tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 6d1d36ef05da8f88467915b0ae340a6c15b26347

#### Requirement

Goal G6: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Design D12: claude-code-wrapper 0.3.0 (version bump, tag `v0.3.0` on the merge commit after the `main` build). Precedent: done epic hive-mode-leadership-handove task wrapper-release-0-2-0.

Scope:
- Version `0.3.0` in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`; `uv lock`.
- `tests/test_packaging.py::test_version_matches_pyproject` keeps pyproject, `__version__` and the installed metadata in agreement.
- Release steps, run by the orchestrator session (never a subagent) once this epic's wrapper PR is merged to `main`: wait for `build.yaml` to push `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, push tag `v0.3.0` on the merge commit (`release.yaml` retags `:0.3.0` and `:latest`; irreversible, listed in design.md), then amend `orch-wrapper-pin-0-3-0` and `helmfile-deploy-pin` with the merge sha.

Notes: README `### Release`: `release.yaml` fails when the `:<shortsha>` image is missing, so tag only after the main build is green. Dependency bump with no behaviour change: the TDD exception for a version bump applies; the packaging test is the guard.

#### Acceptance conditions

- AC1: pyproject, `__version__` and the installed metadata agree [evidence: test:tests/test_packaging.py::test_version_matches_pyproject]
- AC2: the version is 0.3.0 in pyproject and the package [evidence: command:grep -q '^version = "0.3.0"' pyproject.toml && grep -q '__version__ = "0.3.0"' src/claude_code_wrapper/__init__.py]
- AC3: after the merge, tag v0.3.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.3.0)"]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Bump the version to 0.3.0 in `pyproject.toml` and `src/claude_code_wrapper/__init__.py`, run `uv lock` (dependency-bump exception; the packaging test is the guard); run the task's verify command: passes.
- After the merge (orchestrator session): wait for `build.yaml` green on the merge commit, `git tag v0.3.0 <merge sha> && git push origin v0.3.0`, watch `release.yaml` green, then amend orch-wrapper-pin-0-3-0 and helmfile-deploy-pin with the merge sha.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S6: scale down staying peer

- Status: done
- Files: `src/agents_orchestrator/db/sessions.py`, `tests/test_sessions_repo.py`, `tests/test_api_scale.py`, `tests/test_agent_scale.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest -q tests/test_sessions_repo.py tests/test_api_scale.py tests/test_agent_scale.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8d03b3830508c724abff19565ade9a7c82c4dae7

#### Requirement

Goal G2, verbatim: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks; with no such agent it is refused as today." User decision: "Scale-down that would remove the leader's pod: hand over first, then shrink. If no ready peer that stays is available, the scale-down is still refused."

Design D5, verbatim: `db/sessions.set_replicas` refuses `leader_would_leave` only when the leader's ordinal is at or above the new replica count and no staying peer exists: another agent of the session that is ready, not gone, has a wrapper session and has `ordinal < replicas` (the same predicate as the pick, D7). Otherwise it writes `spec.replicas` as today and answers 202. The api never moves the leader; the dispatcher derives the move from `spec.replicas` (D6). The error code keeps its name and now means "the leader would leave and no ready agent that stays can take over". Refusal order and every other code are unchanged.

Design D15, verbatim (api half): `set_replicas` sends `NOTIFY leadership_requested {session_id}` when it accepts a count at or below the leader's ordinal.

Scope:
- `src/agents_orchestrator/db/sessions.py` `set_replicas`: the refusal above, reading `agents` only (never writing `session_leaders` or `agents`); one predicate shared with the pick of `db/leadership.py` (where it lives is left to the builder); in the same transaction, after the write, `NOTIFY leadership_requested {session_id}` when the accepted count is at or below the leader's ordinal (no NOTIFY otherwise beyond today's `session_changed`). Docstrings updated.
- Tests:
  - `tests/test_sessions_repo.py`: a new test that a scale-down below the leader is written when a staying peer exists (no `session_leaders` change, one `leadership_requested` NOTIFY), and refused `leader_would_leave` when the only other agents are not ready, gone, without a wrapper session, or themselves leaving.
  - `tests/test_api_scale.py`: a new test that `POST /api/v1/sessions/{id}/scale` below the leader answers 202 with a staying ready peer.
  - `tests/test_agent_scale.py`: a new test that the leader's `POST /agent/v1/scale` below its own ordinal answers 202 with a staying ready peer.
- Tests no longer accurate, to update (each asserted "a scale-down below the leader is always refused", which the user's decision replaces):
  - `tests/test_sessions_repo.py::test_set_replicas_leader_rules`: its `leader_would_leave` cases must use a session with no eligible staying agent (ordinal 0 not ready or without a wrapper session); the `not_leader` case and the accepted 4 to 3 case stay.
  - `tests/test_api_scale.py::test_scale_leader_would_leave`: agents 0 and 1 are ready, so 3 to 2 is now accepted; it keeps asserting 409 `leader_would_leave` with agents 0 and 1 made ineligible.
  - `tests/test_agent_scale.py::test_agent_scale_refusals`: its `leader_would_leave` case (leader ordinal 1, scale to 1) must make ordinal 0 ineligible; the other refusals stay.
- README: the error code list (`leader_would_leave` (409, a scale-down that would remove the leader while no ready agent that stays can take over)), `POST /api/v1/sessions/{session_id}/scale`, `POST /agent/v1/scale`, and the Scaling bullet "The leader is never removed ..." replaced by: a scale-down below the leader's ordinal hands leadership to a ready agent that stays (reason `scale_down`, see Leadership), then shrinks; with no such agent it is 409 `leader_would_leave`.
- MEMORY.md: a dated entry (2026-10-26, leader-auto-handover) amending the 2026-10-24 cluster-scaling entry's `leader_would_leave` rule.

Notes: `hive()` in `tests/test_agent_scale.py` and the `insert_agent` factory decide readiness and the wrapper session; check them before writing fixtures. openapi.json does not list `leader_would_leave`, so it does not change (verify with `tests/test_readme_api.py`).

#### Acceptance conditions

- AC1: `set_replicas` below the leader's ordinal writes `spec.replicas` when another ready, not gone agent with a wrapper session and `ordinal < replicas` exists, touches no `session_leaders` row, and sends `NOTIFY leadership_requested {session_id}`; a scale that leaves the leader in place sends none [evidence: test:tests/test_sessions_repo.py::test_set_replicas_below_leader_with_staying_peer]
- AC2: with no such agent (others not ready, gone, without a wrapper session, or leaving) it is refused `leader_would_leave` and nothing is written [evidence: test:tests/test_sessions_repo.py::test_set_replicas_leader_rules]
- AC3: the public scale route answers 202 below the leader with a staying ready peer [evidence: test:tests/test_api_scale.py::test_scale_below_leader_accepted]
- AC4: the public scale route still answers 409 `leader_would_leave` with no staying ready peer [evidence: test:tests/test_api_scale.py::test_scale_leader_would_leave]
- AC5: the leader's agent scale route answers 202 below its own ordinal with a staying ready peer, and the refusals stay [evidence: command:uv run --frozen pytest -q tests/test_agent_scale.py]
- AC6: README and openapi stay in sync and MEMORY.md records the amendment [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py && grep -q "leader_would_leave" MEMORY.md]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/sessions.py`
- `tests/test_sessions_repo.py`
- `tests/test_api_scale.py`
- `tests/test_agent_scale.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add the new tests and update the three named inaccurate tests; run `uv run --frozen pytest -q tests/test_sessions_repo.py tests/test_api_scale.py tests/test_agent_scale.py`: the new acceptance tests fail (still refused, no NOTIFY).
- Green: change `set_replicas` (shared predicate, NOTIFY), README and MEMORY.md; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): finding 2 (set_replicas wakes the dispatcher)

- 2026-10-26 done

### S7: claim hold and handover wake

- Status: done
- Files: `src/agents_orchestrator/db/queue.py`, `tests/test_queue_leader_routing.py`, `tests/test_dispatcher_auto_handover.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 712cc8c629b80940ed080dc8b25cb9682d4adec8

#### Requirement

Goal G1: "the orchestrator then moves leadership to another ready agent of the cluster at the leader's turn boundary". Goal G3: "with no eligible agent the leader keeps leading and the move is retried." Interrogate finding 1 (2026-10-26): the pass runs once per drain and `_drain_messages` then loops `claim_and_pick`; `_claim_in_session` routes untargeted messages to the leader without checking `compaction_at > since` (`dispatcher/loop.py:129-131,155-171`, `db/queue.py:245-279`). The claim path must never route an untargeted message to a leader whose compaction is pending. Interrogate finding 2: the compaction projection and `set_replicas` must wake the dispatcher.

Design D16, verbatim: `_claim_in_session` (`db/queue.py`) treats the leader like a gone leader (untargeted messages hold, targeted ones flow) while its handover is pending and possible: its `compaction_at` is later than `since` or it is leaving (not gone, `ordinal >= spec.replicas`), and an eligible staying agent exists by the same predicate the pass picks with (D7). With no eligible agent the leader keeps receiving untargeted messages (G3, "the leader keeps leading").

Design D15, verbatim: when the ingester projects a compaction (D3) it also sends `NOTIFY leadership_requested {session_id}`, and `set_replicas` sends it when it accepts a count at or below the leader's ordinal (D5). The dispatcher already listens on that channel (`dispatcher/loop.py:37`), so an idle compacted leader or a leaving leader moves on the wake, not on the next `ORCH_DISPATCH_POLL_SECONDS` poll. A busy compacted leader is moved on the `agent_free` wake at its turn end.

Scope:
- `src/agents_orchestrator/db/queue.py` `_claim_in_session`: the hold above, reading `session_leaders`, `agent_status.compaction_at`, `agents` and `sessions.spec` only; the eligible-agent predicate is the one `db/leadership.py` picks with (import or shared constant; mind that `db/leadership.py` imports `db/queue.py`, so the shared SQL lives where no import cycle appears).
- `tests/test_queue_leader_routing.py`: new tests (names in the acceptance conditions).
- `tests/test_dispatcher_auto_handover.py` (new): a running `Dispatcher` with `dispatch_poll_seconds` far above the test timeout (for example 60), so only a NOTIFY can wake it: (a) an idle hive leader gets `compaction_at` later than `since` through `db/status`'s setter plus `NOTIFY leadership_requested {session_id}` as the ingester sends it, and the leader moves with reason `compaction` within a few seconds; (b) `set_replicas` below the leader with a staying ready peer moves the leader with reason `scale_down` within a few seconds; (c) the race of finding 1: a busy compacted leader with an untargeted message queued turns idle (`agent_status` idle plus `agent_free` NOTIFY, as the ingester does) and the queued message is dispatched to the new leader, never to the compacted one (use the fake wrapper the other dispatcher tests use).
- README `### Routing`: the hold for a leader whose handover is pending; `### Leadership`: `leadership_requested` is sent by the api on a queued request, by the ingester on a compaction and by `set_replicas` on a scale-down below the leader.

Notes: the existing routing tests (`test_gone_leader_waits`, `test_new_leader_after_handover`) stay accurate. Find the dispatcher test harness in `tests/test_hive_push.py` (`test_dispatcher_run_pushes_on_leader_changed`) and the dispatcher send tests before writing the new file.

#### Acceptance conditions

- AC1: an untargeted message is never claimed for an idle leader whose `compaction_at` is later than its `since` while a staying ready agent exists; targeted messages to other agents still dispatch [evidence: test:tests/test_queue_leader_routing.py::test_compacted_leader_holds_untargeted]
- AC2: a leaving leader (not gone, `ordinal >= spec.replicas`) with a staying ready agent holds untargeted messages the same way [evidence: test:tests/test_queue_leader_routing.py::test_leaving_leader_holds_untargeted]
- AC3: with no eligible staying agent, a compacted leader keeps receiving untargeted messages [evidence: test:tests/test_queue_leader_routing.py::test_compacted_leader_without_peer_keeps_leading]
- AC4: an idle leader that compacts moves with reason `compaction` on the `leadership_requested` wake, without waiting for the poll [evidence: test:tests/test_dispatcher_auto_handover.py::test_idle_compaction_moves_without_poll]
- AC5: a scale-down below the leader moves it with reason `scale_down` on the wake from `set_replicas`, without waiting for the poll [evidence: test:tests/test_dispatcher_auto_handover.py::test_scale_down_moves_without_poll]
- AC6: a message queued while a compacted leader is busy is dispatched to the new leader after the leader's turn ends, never to the compacted leader [evidence: test:tests/test_dispatcher_auto_handover.py::test_compacted_leader_never_takes_next_message]
- AC7: the existing routing tests and README stay green [evidence: command:uv run --frozen pytest -q tests/test_queue_leader_routing.py tests/test_readme_api.py]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/queue.py`
- `tests/test_queue_leader_routing.py`
- `tests/test_dispatcher_auto_handover.py`
- `README.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add the three routing tests to `tests/test_queue_leader_routing.py` and the new `tests/test_dispatcher_auto_handover.py`; run `uv run --frozen pytest -q tests/test_queue_leader_routing.py tests/test_dispatcher_auto_handover.py`: the hold tests and the race test fail (the compacted leader is picked).
- Green: add the hold to `_claim_in_session` with the pass's predicate, update README Routing and Leadership; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S8: reconciler leader pod hold

- Status: done
- Files: `src/agents_orchestrator/reconciler/loop.py`, `tests/test_reconciler.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_reconciler.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: c61e41718c6f6dbe12bdade6cb2a8bfa604c887e

#### Requirement

Goal G2, verbatim: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks".

Design D8, verbatim: during a scale-down drain the current leader, when it is at or above the target, counts as busy in `_draining`, so `_drain_replicas` keeps the StatefulSet at least one above the leader's ordinal until the leader row names a staying agent. The existing `ORCH_SCALE_DRAIN_SECONDS` (900) deadline still applies the target regardless; the leader's pod then goes and the lost-leader step picks a successor. `status.drain.waiting` lists the leader's ordinal while it is held. A staying peer can become unready between the api's check and the pass's move (a pod restart); then the pass finds no eligible agent and the leader stays leading, busy or idle, and its pod is held until a peer is ready again (the pass retries and moves it) or until the drain deadline, whichever is first. At the deadline the pod goes, the leader becomes gone, and the lost-leader step picks the first staying agent that is ready; until one is, untargeted messages hold (the existing gone-leader rule). Targeted messages keep flowing throughout.

Scope:
- `src/agents_orchestrator/reconciler/loop.py` `_draining`: an agent at or above `replicas` that is the session's current leader (`session_leaders.agent_id`, read only) counts as busy. `_drain_replicas` is otherwise unchanged (never below the target, never above the replicas already applied, the deadline from `status.drain.since`).
- `tests/test_reconciler.py`: new tests (names in the acceptance conditions), including the busy-leader race: a busy leaving leader whose only staying peer became unready after the scale was accepted keeps its pod (busy and leading) until the deadline, and then the target applies.
- README: the scale-down drain paragraph (around README line 301) says the leader's pod is kept until leadership has moved, within the drain deadline; the sentence "Draining agents are never `ready`, so the dispatcher, leader selection and session bootstrap never pick them" also says leader selection skips agents at or above `spec.replicas` from the moment the count is written.

Notes: the reconciler only reads `session_leaders` (the dispatcher is its writer). Keep the hash invariant: only `StatefulSet.spec.replicas` differs (`tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas`). The existing `test_scale_down_*` and `test_drain_status_reported` tests stay accurate.

#### Acceptance conditions

- AC1: an idle leader at or above the target keeps its pod (StatefulSet replicas at least leader ordinal + 1) and its ordinal is in `status.drain.waiting` until the leader row names a staying agent, then the target applies [evidence: test:tests/test_reconciler.py::test_scale_down_holds_leader_pod_until_handover]
- AC2: after `scale_drain_seconds` from `status.drain.since` the target applies even while the leaving agent still leads [evidence: test:tests/test_reconciler.py::test_scale_down_leader_hold_bounded_by_deadline]
- AC3: a busy leaving leader whose only staying peer became unready after the scale was accepted keeps its pod until `scale_drain_seconds` from `status.drain.since`, then the target applies regardless [evidence: test:tests/test_reconciler.py::test_scale_down_busy_leader_peer_unready_bounded]
- AC4: the existing drain tests still pass [evidence: command:uv run --frozen pytest -q tests/test_reconciler.py tests/test_render.py]
- AC5: README documents the hold and stays in sync [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/reconciler/loop.py`
- `tests/test_reconciler.py`
- `README.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add the three new tests to `tests/test_reconciler.py`; run `uv run --frozen pytest -q tests/test_reconciler.py`: they fail (the leader's pod is removed at once).
- Green: count the leaving leader as busy in `_draining`, update README; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): finding 5 (busy leader, peer unready race)

- 2026-10-26 done

### S9: web scale hint

- Status: done
- Files: `src/chat/ScaleControl.tsx`, `src/chat/ScaleControl.test.tsx`
- Verify: `npx tsc -b && npx vitest run src/chat/ScaleControl.test.tsx && npm run lint`
- Verified head: d3998572f4fab98cc417c48e0513bd67a83aba1e

#### Requirement

Goal G2, verbatim: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks; with no such agent it is refused as today." Goal G5: the UI shows it.

Design D11, verbatim: ScaleControl's `leader_would_leave` hint becomes "No ready agent that stays can take over leadership." (replacing "Make another agent leader first.").

Scope:
- `src/chat/ScaleControl.tsx`: the hint text on an `ApiError` with code `leader_would_leave`.
- Test no longer accurate, to update: `src/chat/ScaleControl.test.tsx` (around line 75) asserts the old hint "Make another agent leader first.", which no longer describes the refusal; it asserts the new text.

Notes: use the word "session", never "cluster" (`src/nomenclature.test.ts`). Retro: run `npx tsc -b` and the full `npm test` before handing back.

#### Acceptance conditions

- AC1: a `leader_would_leave` refusal shows "No ready agent that stays can take over leadership." [evidence: command:npx vitest run src/chat/ScaleControl.test.tsx]
- AC2: the old hint is gone [evidence: command:test -z "$(git grep -n 'Make another agent leader first' -- src)"]
- AC3: types check and the full web suite passes [evidence: command:npx tsc -b && npm test]
- AC4: lint passes [evidence: command:npm run lint]

#### Files

- `src/chat/ScaleControl.tsx`
- `src/chat/ScaleControl.test.tsx`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: update the hint assertion in `src/chat/ScaleControl.test.tsx` (no longer accurate); run `npx vitest run src/chat/ScaleControl.test.tsx`: fails.
- Green: change the hint in `ScaleControl.tsx`; run the task's verify command and `npm test`: pass.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S10: leader changed reason

- Status: done
- Files: `src/agents_orchestrator/db/leadership.py`, `src/agents_orchestrator/api/streams.py`, `tests/test_leader_views.py`, `tests/test_leadership_pass.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_leader_views.py tests/test_leadership_pass.py tests/test_hive_push.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 8bb46459db60b14e86d848fa245c6b9ff7ea3f98

#### Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and API-only e2e test."

Design D10, verbatim: the two new `session_leaders.reason` values are `compaction` and `scale_down` (bare, like `lease_expired`; `handover: <reason>` stays for agent-requested handovers). `_set_leader`'s `NOTIFY leader_changed` payload and the `/api/v1/stream` `leader_changed` frame gain `reason` (additive). The session view's `leader_reason` already carries it. README documents every reason the code writes: `initial`, `user`, `handover: <reason>`, `leader_lost`, `lease_expired`, `scale_down`, `compaction` (discovery fix-as-ac: README lists `start` and omits values).

Scope:
- `src/agents_orchestrator/db/leadership.py` `_set_leader`: the NOTIFY payload is `{session_id, agent_id, epoch, reason}`.
- `src/agents_orchestrator/api/streams.py`: the `leader_changed` frame data is `{session_id, agent_id, epoch, reason}`.
- README: the Events table row of `leader_changed` (`{"session_id", "agent_id", "epoch", "reason"}`), `Every change sends NOTIFY leader_changed {...}` in Leadership, the session view's `leader_since` and `leader_reason` text (the full reason list above), and the `session_leaders` row of the tables list (the full reason list).
- Tests: a new test in `tests/test_leader_views.py` that a pass-driven change (for example reason `scale_down`) reaches the `/api/v1/stream` frame with its reason, and that the session view's `leader_reason` reads it.
- Tests no longer accurate, to update (they pin the payload without `reason`):
  - `tests/test_leader_views.py::test_leader_changed_frame`: its hand-sent NOTIFY and the expected frame gain `reason`.
  - `tests/test_leadership_pass.py`: the exact-payload assertions in `test_concurrent_passes_single_change` area (around lines 420-424) and the lease test around line 534 gain `reason`.

Notes: the hive push wakes on `leader_changed` regardless of payload (`tests/test_hive_push.py::test_dispatcher_run_pushes_on_leader_changed` must stay green). openapi.json is unchanged (the stream frame is documented in README only); `tests/test_readme_api.py` checks every frame is documented.

#### Acceptance conditions

- AC1: the `leader_changed` NOTIFY payload carries the change reason [evidence: command:uv run --frozen pytest -q tests/test_leadership_pass.py]
- AC2: the `/api/v1/stream` `leader_changed` frame carries `reason` [evidence: test:tests/test_leader_views.py::test_leader_changed_frame]
- AC3: a `scale_down` change made by the pass reaches the stream frame and the session view's `leader_reason` [evidence: test:tests/test_leader_views.py::test_auto_handover_reason_in_frame_and_view]
- AC4: the hive push still wakes on leader changes [evidence: test:tests/test_hive_push.py::test_dispatcher_run_pushes_on_leader_changed]
- AC5: README lists every reason and the frame's fields and stays in sync [evidence: command:uv run --frozen pytest -q tests/test_readme_api.py && grep -q "lease_expired., .scale_down., .compaction" README.md]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `src/agents_orchestrator/db/leadership.py`
- `src/agents_orchestrator/api/streams.py`
- `tests/test_leader_views.py`
- `tests/test_leadership_pass.py`
- `README.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add `test_auto_handover_reason_in_frame_and_view` and update the named payload assertions (`test_leader_changed_frame`, the exact payloads in `tests/test_leadership_pass.py`); run `uv run --frozen pytest -q tests/test_leader_views.py tests/test_leadership_pass.py`: they fail (no `reason`).
- Green: add `reason` to the `_set_leader` NOTIFY and the stream frame, update README; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S11: orch wrapper pin 0.3.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `e2e/agent-test.Dockerfile`, `README.md`, `tests/test_images.py`
- Verify: `uv run pytest -q tests/test_images.py tests/test_render.py tests/test_settings.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2529aaf34592abcf2e28e2b2db7e04f8a510d7b5

#### Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Design D12: the orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images). Precedent: done epic hive-mode-leadership-handove task orch-pin-bumps.

Scope: pin agents-orchestrator to the claude-code-wrapper `main` merge commit that carries version 0.3.0 and the `compacting` event:
- `pyproject.toml`: `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`, the same commit.
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `tests/test_images.py` equality tests (wrapper sha agrees across pyproject, uv.lock, README and the Dockerfile) pass unchanged; `tests/test_render.py` still validates the rendered config against the new wrapper; `tests/fakes/fake_wrapper.py` validates event names against the pinned `EVENT_TYPES`, which now includes `compacting`.

The merge sha is filled in by `ticket.py amend` when the wrapper PR merges. Dependency bump: the TDD exception for a dependency bump applies to the pin values; the equality tests are the guard.

#### Acceptance conditions

- AC1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: the pinned wrapper knows the `compacting` event [evidence: command:uv run python -c "from claude_code_wrapper.events import EVENT_TYPES; assert 'compacting' in EVENT_TYPES"]
- AC4: the rendered config validates against the pinned wrapper and the fake wrapper contract holds [evidence: command:uv run pytest -q tests/test_render.py tests/test_settings.py tests/test_fake_wrapper_contract.py]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/test_images.py`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Change the pins in `pyproject.toml`, `uv.lock` (`uv lock`), `e2e/agent-test.Dockerfile` and README Images to the wrapper 0.3.0 merge commit (dependency-bump exception); run `uv run pytest -q tests/test_images.py`: the equality tests fail until every pin agrees, then pass.
- Run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S12: smoke scale below leader

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint`
- Verified head: f73dc2c2148b1ea2ee36d03398e2530eb7428198

#### Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Goal G2: "a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that stays, then shrinks".

Scope, in `scripts/smoke.sh` step 7 (scale 1 to 2 to 1 through the public route, pod-0 must never restart):
- After pod-1 is Ready, read the agents of the smoke session (`GET /api/v1/sessions/{id}/agents`), make pod-1's agent the leader with `POST /api/v1/sessions/{id}/leader {agent_id}` (expects 202) and wait within `SMOKE_TIMEOUT_S` until the session view's `leader_agent_id` is pod-1's agent.
- `scale 1` still expects 202 (it was refused before this epic). Then wait within `SMOKE_TIMEOUT_S` until the session view's `leader_agent_id` is pod-0's agent and `leader_reason` is `scale_down`, and then until pod-1 is gone; each timeout fails with a named message (`scale down: leader did not move to pod-0 with reason scale_down`, `scale down: <pod1> still present`).
- pod-0's uid check stays. Cleanup stays in the existing trap.
- `tests/test_smoke_script.py`: the fake API serves the leader route, the agents list and a leader that moves to pod-0 with reason `scale_down` after the scale to 1; new tests for a leader that never moves and a wrong reason; the happy path stays green.
- README smoke section: the scale step makes pod-1 the leader and proves a scale-down below the leader hands leadership to pod-0 (reason `scale_down`) before pod-1 goes.

Notes: the smoke's header comment (lines 1-7) names the steps; update it. Keep the script strict, bounded and shellcheck clean (`test_script_is_shellcheck_clean`, `test_script_is_strict_bounded_and_traps`). Live runs happen only in task helmfile-apply-smoke, by the orchestrator session.

#### Acceptance conditions

- AC1: the happy path makes pod-1 leader, scales to 1 with 202, sees the leader move to pod-0 with reason scale_down, sees pod-1 gone and exits 0 with cleanup [evidence: test:tests/test_smoke_script.py::test_happy_path_exits_zero_and_cleans_up]
- AC2: a leader that never moves to pod-0 after the scale-down fails with a named message and cleans up [evidence: test:tests/test_smoke_script.py::test_scale_down_leader_not_moved_fails]
- AC3: a leader that moves with a reason other than scale_down fails with a named message [evidence: test:tests/test_smoke_script.py::test_scale_down_wrong_reason_fails]
- AC4: a scale answer other than 202 still fails [evidence: test:tests/test_smoke_script.py::test_scale_refused_fails]
- AC5: the script stays strict, bounded and shellcheck clean [evidence: test:tests/test_smoke_script.py::test_script_is_shellcheck_clean]
- AC6: lint passes [evidence: command:mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: extend the fake API in `tests/test_smoke_script.py` (agents list, leader route, leader moving with reason `scale_down`) and add the two failure tests; run `uv run --frozen pytest -q tests/test_smoke_script.py`: the happy path and the new tests fail.
- Green: extend step 7 of `scripts/smoke.sh`, its header and the README smoke section; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S13: web leader reason

- Status: done
- Files: `src/api/stream.ts`, `src/api/stream.test.ts`, `src/ribbon/useSessions.ts`, `src/chat/AgentsStrip.tsx`, `src/chat/AgentsStrip.test.tsx`, `src/chat/ChatView.tsx`
- Verify: `npx tsc -b && npx vitest run src/api/stream.test.ts src/chat/AgentsStrip.test.tsx && npm run lint`
- Verified head: b292688129e359cc918d54ecca42b18ea3cfb47c

#### Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down)".

Design D11, verbatim: agents-web reads `reason` from the `leader_changed` frame into the session's `leader_reason`; the leader badge's tooltip names the epoch and the reason, and for the automatic reasons a caption next to the badge reads "after compaction" or "after scale-down".

Scope:
- `src/api/stream.ts`: the `leader_changed` status event carries `reason: string | null` (from `d.reason`, null when absent).
- `src/ribbon/useSessions.ts`: the `leader_changed` case also sets the session's `leader_reason` from the frame.
- `src/chat/ChatView.tsx`: passes the session's `leader_reason` into AgentsStrip's `hive` prop.
- `src/chat/AgentsStrip.tsx`: `hive` gains `leaderReason: string | null`; the leader badge's `title` names the epoch and the reason (for example `leader epoch 3, reason compaction`); when the reason is `compaction` or `scale_down` a caption next to the badge reads `after compaction` or `after scale-down`; other reasons show no caption.
- Tests: `src/api/stream.test.ts` (the frame's reason is parsed, a missing one is null) and `src/chat/AgentsStrip.test.tsx` (badge title and the two captions; no caption for `user`, `initial`, `leader_lost`, `lease_expired`, `handover: ...`).

Notes: the orchestrator adds `reason` to the frame in task leader-changed-reason; the session view's `leader_reason` already exists in `src/api/schema.d.ts`, so no `npm run sync:api` is needed. Use the word "session", never "cluster" (`src/nomenclature.test.ts`). Retro: web tasks run `npx tsc -b` and the full `npm test` before handing back.

#### Acceptance conditions

- AC1: the `leader_changed` frame's reason is parsed and a missing reason reads null [evidence: command:npx vitest run src/api/stream.test.ts]
- AC2: the leader badge names the epoch and reason, and shows "after compaction" or "after scale-down" only for those reasons [evidence: command:npx vitest run src/chat/AgentsStrip.test.tsx]
- AC3: types check [evidence: command:npx tsc -b]
- AC4: the full web suite passes [evidence: command:npm test]
- AC5: lint passes [evidence: command:npm run lint]

#### Files

- `src/api/stream.ts`
- `src/api/stream.test.ts`
- `src/ribbon/useSessions.ts`
- `src/chat/AgentsStrip.tsx`
- `src/chat/AgentsStrip.test.tsx`
- `src/chat/ChatView.tsx`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: add the reason cases to `src/api/stream.test.ts` and `src/chat/AgentsStrip.test.tsx`; run `npx vitest run src/api/stream.test.ts src/chat/AgentsStrip.test.tsx`: they fail.
- Green: parse `reason`, set `leader_reason` in `useSessions`, pass it through `ChatView`, render the title and caption in `AgentsStrip`; run the task's verify command and `npm test`: pass.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S14: kind e2e auto handover

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`, `e2e/agent-test.scenario.json`
- Verify: `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: d56162d0a7d5a1fb2419d74301598fe054a17a09

#### Requirement

Goal G5, verbatim: "the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and API-only e2e test." Goals G1 and G2 end to end against the kind cluster with the pinned wrapper 0.3.0 test image.

Scope:
- `e2e/agent-test.scenario.json`: a new turn whose unique `match` (for example `compact mid turn`) runs `{"text": ...}`, then `{"auto_compact": {"pre_tokens": 150000}}` (the fake claude runs the PreCompact hook, so the wrapper emits `compacting`, then writes the compaction boundary), then a final `{"text": ...}`.
- `tests/e2e/test_e2e_kind.py`, API only (the public api client; kubectl only for pod presence as the existing scale tests do):
  - `test_leader_compaction_hands_over`: a 2-replica hive; after the first election, an untargeted message matching the new turn goes to the leader; the session's events include a `compacting` event of the leader; after that turn ends, the session view shows a different leader at a higher epoch with `leader_reason == "compaction"`, within `LEADER_TIMEOUT` after the turn completed; only after the view shows the new leader does the test send the next untargeted message, and that message is dispatched to the new leader (its `agent_id`).
  - `test_scale_down_below_leader_hands_over`: a hive of 3 (max 3); make the highest ordinal the leader through `POST /api/v1/sessions/{id}/leader`; `POST /scale {replicas: 2}` answers 202; the leader moves to an agent with a lower ordinal at a higher epoch with `leader_reason == "scale_down"`; the top pod is then gone and the surviving pods keep their uids.
  - Test no longer accurate, to update: `test_scale_refusals` asserts 409 `leader_would_leave` for a 3 to 2 scale with the top ordinal leading while both other agents are ready, which the user's decision now accepts. It keeps its `out_of_range` checks; its leader part moves to `test_scale_down_below_leader_hands_over`. The no-staying-agent refusal is covered by the unit tests of task scale-down-staying-peer (an e2e cannot make every lower agent unready without breaking the pods).
- Every session a test creates is discarded in its teardown (the existing context managers).

Notes: run locally or in PR CI with `mise run test:e2e` (`scripts/e2e.sh`; one test: `E2E_HOLD_FILE`, then `pytest tests/e2e/test_e2e_kind.py::<name>`). The agent-test image is built from the wrapper commit pinned by task orch-wrapper-pin-0-3-0, which must carry the `compacting` event. Reuse `wait_for`, `leader_view`, `wait_leader`, `live_agents`, `scale_to`, `scale_session` and the message helpers already in the file.

#### Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: on kind, a leader that compacts mid-turn hands over after its turn with reason `compaction`; the test sends its next untargeted message only after the session view shows the new leader, and that message is dispatched to the new leader [evidence: command:mise run test:e2e]
- AC3: on kind, a scale-down below the leader answers 202, moves leadership to a staying agent with reason `scale_down`, then removes the top pod [evidence: command:mise run test:e2e]
- AC4: the scenario file stays valid JSON with the new compaction turn [evidence: command:python3 -c "import json; d = json.load(open('e2e/agent-test.scenario.json')); assert any(any('auto_compact' in s for s in t['steps']) for t in d['turns'])"]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

#### Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/agent-test.scenario.json`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Add the scenario turn and the two e2e tests, move the leader part out of `test_scale_refusals`; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the new tests are collected.
- Run `mise run test:e2e` (kind; or the PR CI e2e job): the new tests pass with the pinned wrapper image.
- Run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 amended: interrogate 2026-10-26 (fable, opus, sonnet): finding 1 (send only after the new leader shows)

- 2026-10-26 done

### S15: helmfile deploy pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: e487037cfeae15573f98693d5daed71904a92a99

#### Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Design D12: agents-helmfile pins the orchestrator chart and image, the agent image `claude-code-wrapper:0.3.0` and the agents-web chart and image. Precedent: done epic hive-mode-leadership-handove task helmfile-deploy-pin.

Scope:
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<orchestrator merge sha7>`; agents-web chart `0.1.0-main.<agents-web merge sha7>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<orchestrator sha7>`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:0.3.0` (a release tag: Harbor prunes sha7 tags). `ORCH_ANY_MCP_REF` stays `v0.3.0`.
- `values/agents-web/common.yaml`: `image.tag` `<agents-web sha7>`.
- Tests: `tests/test_orchestrator_release.py` (chart version and image tag agree; agent image pins agree on 0.3.0) and `tests/test_web_release.py` (chart version and image tag agree).

The shas are filled in by `ticket.py amend` when the orchestrator and agents-web PRs merge. Chart-pull tests blocked by a container network policy may be deselected in a local run (precedent ruling in done epic web-ui-cluster-tabs-with-fil task deploy-pin); they run unblocked before the apply.

Notes: `tests/test_orchestrator_release.py` also holds `test_values_dir_moved`, which once blocked an apply (retro agents-schedule-deploy); it must pass here so the apply is not stopped by a stale test.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on claude-code-wrapper:0.3.0 [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC4: the agent image is the 0.3.0 release [evidence: command:grep -q "claude-code-wrapper:0.3.0" values/agents-orchestrator/common.yaml]
- AC5: the release test files pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py]
- AC6: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Red: update the pins expected by `tests/test_orchestrator_release.py` and `tests/test_web_release.py` (orchestrator and agents-web shas from the amendment, wrapper 0.3.0); run the task's verify command: fails.
- Green: change `helmfile.yaml.gotmpl` and the two values files; run the task's verify command: passes.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-26 done

### S16: helmfile apply smoke

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run smoke`
- Verified head: b5ae9c39ccd972dcbc8d354ab7130df0deec4ca7

#### Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Live applies are run by the orchestrator session only, never by a subagent.

Steps, run by the orchestrator session after the agents-helmfile PR merges, in `code/agents-helmfile` on `main`, least destructive first:
1. `mise run diff`: the change is the orchestrator and agents-web chart versions and image tags and the agent image 0.3.0; anything else stops the task.
2. `mise run apply` (live namespace; listed in design.md). The orchestrator applies migration 0006 on start.
3. `mise run smoke` green, including the scale-down below the leader (task smoke-scale-below-leader).
4. First real message (retro agents-matrix-connector-depl): in a live 2-agent hive created from a preset, make pod-1 leader, scale to 1, then post an untargeted message; it is dispatched to the new leader (pod-0) and answered (message `sent`, an assistant reply in the events). Discard the session afterwards.
5. MEMORY.md entry (containing the words `leader-auto-handover live reply`) dated with the applied orchestrator chart, orchestrator image, agents-web chart, wrapper image `0.3.0`, the step 4 session and message ids, and, when a live hive has compacted since the apply, whether a `compacting` event was recorded (design.md assumption on real Claude Code PreCompact).

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25). Subagent `kubectl exec` is denied by the permission classifier; the whole task is orchestrator-run. Existing sessions keep their snapshotted agent image; only new sessions get 0.3.0.

#### Acceptance conditions

- AC1: the smoke script passes against the applied release, including the scale-down below the leader [evidence: command:mise run smoke]
- AC2: MEMORY.md records the applied versions [evidence: command:grep -q "claude-code-wrapper:0.3.0" MEMORY.md]
- AC3: MEMORY.md records the live first-message proof after a scale-down handover [evidence: command:grep -q "leader-auto-handover live reply" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

See the Requirement and the acceptance conditions above.

#### Expected outcome

See the Requirement and the acceptance conditions above.

#### Steps

- Orchestrator session only: `mise run diff`; stop unless it shows only the chart versions, image tags and the agent image.
- `mise run apply`: succeeds.
- `mise run smoke`: exits 0, including the scale-down below the leader.
- The live first-message proof (Requirement step 4), then the MEMORY.md entry; commit it through the agents-helmfile PR flow.

#### Notes

See the Requirement and the acceptance conditions above.

- 2026-10-27 done: AC1 live smoke green on agents-helmfile main 0ed86cf (.logs/lah-smoke-ac1.log, exit 0, leader reason scale_down); live proof by hive leader (.logs/lah-live-proof.log); MEMORY entry b5ae9c3, reviewer clean

### S17: smoke step7 per-wait deadlines

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_smoke_script.py && mise run lint`
- Verified head: c8141fa00c2a2603470bf0dce369e36086353ed7

#### Requirement

Epic review finding (leader-auto-handover review, 2026-10-27, Consider 1), accepted by the hive leader as a task: "smoke step 7 per-wait deadlines + MEMORY line fix (agents-helmfile, sonnet)".

Evidence from the review: in `scripts/smoke.sh` step 7, the agent1 lookup loop and the "leader became pod-1" (make-leader) wait run on the `deadline` set before `scale 2`, which the pod-1 Ready wait already consumed (main 0ed86cf: deadline set at :538, reused at :564 and :577). A slow pod-1 Ready leaves those waits little or no budget, so the smoke can fail spuriously. MEMORY.md:24 claims "each wait gets its own SMOKE_TIMEOUT_S deadline", which is false for these two waits.

Scope:
- `scripts/smoke.sh` step 7: every wait in step 7 (pod-1 appear + Ready, agent1 lookup, make-leader wait including its retries, leader moved to pod-0 with `scale_down`, pod-1 gone) starts its own `SMOKE_TIMEOUT_S` deadline. Read the current main code first; d1c09ff ("wait for agent ready and retry make-leader") changed this region after the epic merge. Failure messages stay as they are.
- `tests/test_smoke_script.py`: a test, written first and seen failing, proving the agent1 lookup and the make-leader wait get their own window after a pod-1 Ready wait that used most of `SMOKE_TIMEOUT_S` (use the existing fake-binary harness).
- `MEMORY.md`: the 2026-10-26 step 7 line stays true (each wait gets its own deadline), with a dated note of this fix.
No other behaviour change.

#### Acceptance conditions

- AC1: each step 7 wait starts its own SMOKE_TIMEOUT_S deadline, pinned by a test where pod-1 Ready uses most of the timeout [evidence: command:uv run pytest -q tests/test_smoke_script.py]
- AC2: shellcheck, ruff and gitleaks pass [evidence: command:mise run lint]
- AC3: MEMORY.md records the per-wait deadline fix [evidence: command:grep -q "own SMOKE_TIMEOUT_S deadline" MEMORY.md]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `MEMORY.md`

#### Interfaces

- `scripts/smoke.sh` step 7 (scale 1 -> 2 -> 1): same log and failure messages, same order of waits; only the deadlines change.
- `tests/test_smoke_script.py` fake-binary harness (fake curl/kubectl) as used by the existing step 7 tests.

#### Expected outcome

Every wait in step 7 gets its own `SMOKE_TIMEOUT_S` window; a pod-1 Ready that uses most of the timeout no longer starves the agent lookup or the make-leader wait; MEMORY.md says so truthfully.

#### Steps

- Read scripts/smoke.sh step 7 on the current tree, tests/test_smoke_script.py and MEMORY.md in one pass.
- Red: add the test (pod-1 Ready slow, near SMOKE_TIMEOUT_S, then agent lookup / make-leader need time); `uv run pytest -q tests/test_smoke_script.py` fails on the new test only.
- Green: reset `deadline` before each step 7 wait; the same command passes.
- MEMORY.md: dated note of the fix; `grep -q "own SMOKE_TIMEOUT_S deadline" MEMORY.md` exits 0.
- `mise run lint`: exit 0.

#### Notes

d1c09ff (after the epic merge) added the agent-ready wait and make-leader retry in this region; build on it. Never run `mise run smoke` or `mise run apply` (live); the orchestrator does that. helmfile-apply-smoke commits its MEMORY.md entry first in the same tree; keep it.

- 2026-10-27 done: reviewer clean: 113 passed, lint green; new tests fail on pre-fix smoke.sh

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
