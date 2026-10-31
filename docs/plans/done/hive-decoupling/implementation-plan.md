# hive decoupling implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: orch activity route

- Status: done
- Files: `src/agents_orchestrator/api/agent.py`, `src/agents_orchestrator/db/events.py`, `openapi.json`, `README.md`, `tests/test_api_activity.py`
- Verify: `uv run --frozen pytest tests/test_api_activity.py tests/test_readme_api.py tests/test_hive_feed.py && mise run lint`
- Verified head: 1e3db5cd71272e39eabe812f90468d947c229a86

#### Requirement

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
It then replaces the placeholders `0011`, `v0.4.0` and `0.4.0` by `ticket.py amend` in orch-drop-feed-cursor, plugins-release-0-4-0, orch-plugins-pin-0-4-0 and helmfile-deploy-pin (Requirement and acceptance conditions), and edits the same placeholders in their frontmatter `files` and bodies. The task slugs keep their historical names.

#### Acceptance conditions

- ac1: the route returns the session's digest lines as {lines: [{id, agent, text, ts}]}, oldest first, own lines included, paths relative to the workdir [evidence: test:tests/test_api_activity.py::test_activity_lists_digest_lines]
- ac2: agent filters to one pod; an agent with no lines returns an empty list [evidence: test:tests/test_api_activity.py::test_activity_agent_filter]
- ac3: limit defaults to 50, keeps the newest limit lines, and a limit outside 1..200 answers 422 invalid_request [evidence: test:tests/test_api_activity.py::test_activity_limit_bounds]
- ac4: the route needs the agent identity (401 without credentials, 403 from a non-agent peer) and reads only the caller's session [evidence: test:tests/test_api_activity.py::test_activity_requires_agent_identity]
- ac5: a Bash call younger than PENDING_BASH_TIMEOUT_SECONDS without a result is omitted; once its result is stored it is listed with its status [evidence: test:tests/test_api_activity.py::test_activity_omits_pending_bash]
- ac6: the README documents the route [evidence: test:tests/test_readme_api.py::test_every_route_documented]
- ac7: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac8: the route only reads events; no INSERT, UPDATE or DELETE is added [evidence: judgement:reviewer reads the diff of api/agent.py and db/events.py]
- ac9: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_api_activity.py tests/test_readme_api.py tests/test_hive_feed.py && mise run lint]
- ac10: (orchestrator session, before dispatch) the real next migration number and plugins tag read from main replace the placeholders in orch-drop-feed-cursor, plugins-release-0-4-0, orch-plugins-pin-0-4-0 and helmfile-deploy-pin [evidence: judgement:orchestrator quotes the numbers read and a grep of the epic's other task files showing no 0011, v0.4.0 or 0.4.0 left]

#### Files

- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/db/events.py`
- `openapi.json`
- `README.md`
- `tests/test_api_activity.py`

#### Interfaces

- `GET /agent/v1/activity?agent=<pod>&limit=<1..200>` on the agent port; 200 `{"lines": [{"id": int, "agent": str, "text": str, "ts": datetime}]}`; 401/403 from `require_agent`; 422 `invalid_request` for a bad `limit`.
- Reuses `agents_orchestrator.dispatcher.feed.digest_lines(rows, now, workdir) -> (lines, pending)` unchanged; rows carry `id`, `type`, `data`, `ts`, `agent` (pod name).

#### Expected outcome

An agent calling the route sees the newest digest lines of its session (commands with status, files written, finished turns), bounded and on demand; nothing is written.

#### Steps

- First, before any implementer is dispatched (orchestrator session, settlement 1): read the next free migration number and plugins tag from main and amend the four dependent tasks (ac10).
- Red: write `tests/test_api_activity.py` (ac1-ac5; reuse the agent-identity setup of `tests/test_api_agent.py` and `factories.insert_event`); run `uv run --frozen pytest tests/test_api_activity.py`: fails (404 route).
- Green: the route and the bounded read; README section; `uv run python -m agents_orchestrator.api.openapi > openapi.json`; run the task's verify: passes. Quote the summary line.

#### Notes

- DB tests need testcontainers (Docker); there is none in agent pods, so CI on the PR is the gate for them (recurring retro). Run what runs locally and quote both.
- Shared files with slash-commands-from-chat (`api/agent.py`, `openapi.json`): read them as merged on `main` first.
- The newest-rows bound: `ORDER BY e.id DESC LIMIT 1000`, then reverse; filter by type in SQL.

- 2026-10-27 amended: builder check settlement 1: first task reads the real next migration number and plugins tag from main and amends the dependent tasks

- 2026-10-29 done

### S2: orch hive feed removal

- Status: done
- Files: `src/agents_orchestrator/dispatcher/hive.py`, `src/agents_orchestrator/dispatcher/feed.py`, `src/agents_orchestrator/dispatcher/loop.py`, `tests/test_hive_push.py`, `tests/test_hive_feed.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_hive_push.py tests/test_hive_feed.py tests/test_readme_api.py tests/test_dispatcher_auto_handover.py tests/test_leadership_pass.py && mise run lint`
- Verified head: ca0b11901ac6bc269295a1b1ad7d74fadfe5733b

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/dispatcher/feed.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_hive_push.py`
- `tests/test_hive_feed.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `hive.handover_threshold(spec: dict, settings: Settings) -> int`: `max(coalesce(auto_compact_pct, default_auto_compact_pct) - HANDOVER_MARGIN_PCT, 1)`.
- `hive.state_hash(leader, epoch, members) -> str`: leader, epoch, `[pod_name, wrapper_session_id, ready]` per member.
- `hive.render_hive_state(payload, slug, threshold: int) -> str` (the threshold replaces the optional `auto_compact_pct`).
- `HiveState`: keeps `last_tick` only (D4 and D6 add their own fields later).

#### Expected outcome

Members get only the keyed `hive_state` note, and only on structural change; the feed code is gone; the hint always names the real threshold.

#### Steps

- Red: rewrite and add the tests of ac1-ac5 in `tests/test_hive_push.py`, remove the four feed tests and `tests/test_hive_feed.py::test_render_feed` (named in the Requirement); run `uv run --frozen pytest tests/test_hive_push.py tests/test_hive_feed.py`: the new ones fail.
- Green: hive.py, feed.py, loop.py docstring, README, MEMORY; run the task's verify: passes. Quote the summary line.
- The removal of `render_feed` and the constants is pinned by ac6 (deletion pinned by a retirement grep).

#### Notes

- `feed_cursor` still exists in the schema after this task; only hive.py stops using it (orch-drop-feed-cursor drops it). `_set_leader` still writes it until then.
- Keep `_claim`/`_release`: one failing receiver retries alone; `state_pushed_at` moves only when every receiver took the state.
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-29 done

### S3: orch drop feed cursor

- Status: done
- Files: `src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql`, `src/agents_orchestrator/db/leadership.py`, `tests/test_migrations.py`, `tests/test_leadership_pass.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_migrations.py tests/test_leadership_pass.py tests/test_hive_push.py && mise run lint`
- Verified head: 88ed965f3db0692ab704e116f675a47d2af7ac2f

#### Requirement

README Goal G1, verbatim: "Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped."

Design D1, verbatim: "`session_leaders.feed_cursor` loses its only writer and readers (`hive.py`, `_set_leader`; probed: no view, export or other reader), so a migration (next free number, 0009 if nothing else lands) drops it."

Constraint, verbatim: "Orchestrator migration number: the next free one at build time (slash-commands adds 0008, so 0009 if nothing else lands); the task is amended to the free number if 0009 is taken."

Open question Q6 (pending gate, recommended yes): "Drop the session_leaders.feed_cursor column in a migration rather than leave it dead?"

Scope (agents-orchestrator):
- `src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql`: `ALTER TABLE session_leaders DROP COLUMN IF EXISTS feed_cursor;` with a header comment (idempotent like 0003 and 0006).
- `src/agents_orchestrator/db/leadership.py` `_set_leader`: the INSERT no longer names `feed_cursor` nor reads `max(events.id)`; the docstring sentence about the feed cursor goes.
- `README.md` `### Leadership` step 1: the sentence "The new row starts `feed_cursor` at the session's newest event id, so history is never pushed as current activity." goes.
- Tests no longer accurate, named: `tests/test_migrations.py::test_0003_hive_schema` (runs every migration, then asserts `feed_cursor` exists: it now copies only 0001-0003, like the other per-version tests, and keeps its 0003 assertions); `tests/test_migrations.py::test_0003_feed_cursor_default` (runs on the head schema through `pool`: it now runs 0001-0003 on `empty_dsn`, keeping its assertion); `tests/test_leadership_pass.py::test_initial_leader` (asserts the cursor starts at the newest event: that assertion is removed, the rule is gone; the rest stays).
- New: `tests/test_migrations.py::test_drop_feed_cursor_migration` (after every earlier migration the column exists; the new migration removes it; re-running its SQL is a no-op; `run_migrations` returns `["0011"]` then `[]`).
- Depends on orch-hive-feed-removal: no code reads or writes the column when it is dropped.

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.4.0` (the plugins release tag, `vX.Y.Z`), `0.4.0` (the same without the `v`) and `0011` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

#### Acceptance conditions

- ac1: the migration drops session_leaders.feed_cursor and is idempotent [evidence: test:tests/test_migrations.py::test_drop_feed_cursor_migration]
- ac2: the 0003 schema test still tests 0003 alone (updated, named) [evidence: test:tests/test_migrations.py::test_0003_hive_schema]
- ac3: the 0003 feed_cursor default test runs on the 0003 schema (updated, named) [evidence: test:tests/test_migrations.py::test_0003_feed_cursor_default]
- ac4: the initial election still writes epoch 1, reason initial, with no cursor (updated, named) [evidence: test:tests/test_leadership_pass.py::test_initial_leader]
- ac5: no source or README line names feed_cursor outside migration 0003 and the new migration [evidence: command:! grep -rn feed_cursor src/agents_orchestrator --include=*.py && ! grep -n feed_cursor README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_migrations.py tests/test_leadership_pass.py tests/test_hive_push.py && mise run lint]

#### Files

- `src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql`
- `src/agents_orchestrator/db/leadership.py`
- `tests/test_migrations.py`
- `tests/test_leadership_pass.py`
- `README.md`

#### Interfaces

- Migration `0011_drop_feed_cursor.sql` (or the next free number; amend the task if 0011 is taken): `ALTER TABLE session_leaders DROP COLUMN IF EXISTS feed_cursor;`.
- `db/leadership.py:_set_leader` INSERT columns `(session_id, agent_id, epoch, since, reason)`.

#### Expected outcome

The live schema has no `feed_cursor`; elections write no cursor; the 0003 tests still describe 0003.

#### Steps

- Check the free migration number: `ls src/agents_orchestrator/db/migrations/`; if 0011 exists, stop and report so the task is amended.
- Red: add `test_drop_feed_cursor_migration`, restrict `test_0003_hive_schema` and `test_0003_feed_cursor_default` to 0001-0003, drop the cursor assertion in `test_initial_leader`; run `uv run --frozen pytest tests/test_migrations.py tests/test_leadership_pass.py`: the new test fails.
- Green: the migration, `_set_leader`, README step 1; run the task's verify: passes. Quote the summary line.

#### Notes

- Data change: the column's values are dropped in the live database on deploy (listed in design.md Irreversible operations).
- Follow the per-version copy pattern of `test_0006_compaction_column` (`MIGRATIONS_DIR.glob("000[1-3]_*.sql")`).
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main

- 2026-10-29 done

### S4: orch handover due note

- Status: done
- Files: `src/agents_orchestrator/dispatcher/hive.py`, `tests/test_hive_push.py`, `tests/test_eligibility_fragments.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_hive_push.py tests/test_eligibility_fragments.py tests/test_dispatcher_auto_handover.py tests/test_leadership_pass.py && mise run lint`
- Verified head: e0e2f3c599f20a7aa508912a8377302395f45ec7

#### Requirement

User request (2026-10-27), verbatim: "Maybe leader could get a signal to pass on its session details to another agent when it hits a limit and both could talk to each other about details for handoff?"

README Goal G3, verbatim: "A leader at or above the effective handover threshold (its compaction percentage minus 15) gets one keyed `handover_due` note with ranked successor candidates, their ccw addresses and the handoff protocol; the `hive_state` hint and the plugin advice always use the effective threshold."

Design D4, verbatim: "per hive session, when the leader's `agent_status.context_pct` is at or above the D2 threshold, the push sends the leader only a keyed note `handover_due`. Text: "your context is N% of a limit that compacts at L%; hand leadership over before that", then candidates best first: `ELIGIBLE` (the `db/eligibility.py` fragment, embedded, never respelled), not the leader, idle before busy, lowest `context_pct` first, each as `<pod_name> (<pod_name>/<wrapper_session_id>, idle, 23% context)`, then the D5 protocol in three lines with the current epoch. With no candidate: "no ready successor; keep leading", plus "scale up with orchestrator_scale" when the session is scalable. With `spec.peers` false: the D7 no-conversation text. It is re-sent when the leader's 5% bucket, the candidate identity (the ordered `(pod_name, wrapper_session_id)` list, not their state or context, my call) or the epoch changes; never below the threshold; a new term starts clean. Tracking is per session in `HiveState` (dispatcher memory); a restart re-sends one note at most."

Design D4, verbatim: "Candidates at or above the threshold themselves are left out (my call, open question Q8): handing over to an agent that is already due would ping-pong leadership."

Design D5, verbatim (the protocol the note carries): "the leader (1) finishes the step it is in, reassigns or releases its locks; (2) sends the successor a brief with `mcp__ccw__send_message(to=<address from the note>, notify_when_idle=true)`: the user's goal, what is done, what is in flight, open questions to the user, pending user messages, locks and branches; then ends its turn; (3) the successor may ask back and replies "ready" (or "no" and why); (4) in the turn carrying the reply or the `<peer-idle-notice>`, the leader calls `orchestrator_leadership_handover(to=<successor>, epoch=<current>, reason="context")`; (5) the dispatcher applies it at the next pass [...] Leadership flips at step 5 only. With no reply within one further user turn the leader hands over anyway; a `<peer-delivery-failed>` or a send error means the next candidate."

Design D7, verbatim: "`spec.peers` false: the note tells the leader to call `orchestrator_leadership_handover` with a `reason` that summarises the state (500 chars); no conversation. The push reads `spec.peers` (default true) to choose the text."

Design D8, verbatim: "the `compacting` event, `compaction_at` projection and wake, steps 3 and 5 of the pass, the claim hold, the reconciler pod hold, the reasons and the UI caption are untouched and remain the backstop."

Scope (agents-orchestrator):
- `src/agents_orchestrator/dispatcher/hive.py`: constant `DUE_KEY = "handover_due"`; a candidate query that embeds `eligibility.ELIGIBLE` (module-level SQL, for example `_CANDIDATES`); the threshold from the helper orch-hive-feed-removal added; a renderer for the note (every peer string through `feed._clean`); per-session due tracking in `HiveState` (the last sent key: leader agent id, epoch, 5% bucket, candidate identity); the leader only receives it, through `_note(..., key=DUE_KEY)`; a failed push is retried next tick.
- `tests/test_hive_push.py`: the new tests below, using `set_agent_status` for `context_pct` and the fake wrapper notes store.
- `tests/test_eligibility_fragments.py::test_call_sites_embed_the_shared_fragments`: adds `assert eligibility.ELIGIBLE in hive._CANDIDATES` (or the name used).
- `README.md`: the hive-state push paragraph gains the `handover_due` note (threshold, receivers, candidates, re-send rule, protocol); `### Hive` names it.
- `MEMORY.md`: dated entry: third amendment of hive D26 (targeted advice), Q8's exclusion as decided at the gate.

Builder check settlement 7 (2026-10-27, my call): the `handover_due` evaluation (and the `leadership_request` outcome pass of orch-handover-outcome-note) runs on every push tick, outside the `_claim`/`_release` hash path of `hive_state`: an unchanged `hive_state` hash never skips it.

#### Acceptance conditions

- ac1: a leader at or above the threshold gets one keyed handover_due note; members get none; a leader below the threshold gets none [evidence: test:tests/test_hive_push.py::test_handover_due_sent_to_leader_at_threshold]
- ac2: candidates are ELIGIBLE agents other than the leader, idle before busy, then lowest context first, each with its pod_name/wrapper_session_id address; leaving, unready and at-or-above-threshold agents are left out [evidence: test:tests/test_hive_push.py::test_handover_due_candidates_ranked]
- ac3: the note is re-sent when the leader's 5% bucket, the candidate identity or the epoch changes, not when a candidate's state or context changes, and a new leader is judged on its own gauge [evidence: test:tests/test_hive_push.py::test_handover_due_resend_rules]
- ac4: with no candidate the note says "no ready successor; keep leading", plus the orchestrator_scale hint only when the session is scalable [evidence: test:tests/test_hive_push.py::test_handover_due_no_candidate]
- ac5: the note carries the protocol: mcp__ccw__send_message with notify_when_idle, wait for "ready", then orchestrator_leadership_handover with to, the current epoch and reason context [evidence: test:tests/test_hive_push.py::test_handover_due_protocol_text]
- ac6: with spec.peers false the note gives the no-conversation text (handover with a reason summarising the state) and names no ccw tool [evidence: test:tests/test_hive_push.py::test_handover_due_without_peers]
- ac7: the candidate SQL embeds the shared ELIGIBLE fragment [evidence: test:tests/test_eligibility_fragments.py::test_call_sites_embed_the_shared_fragments]
- ac8: the leader-auto-handover backstops are unchanged [evidence: command:uv run --frozen pytest tests/test_dispatcher_auto_handover.py tests/test_leadership_pass.py]
- ac9: README and MEMORY.md document handover_due [evidence: command:grep -q "handover_due" README.md && grep -q "handover_due" MEMORY.md]
- ac10: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_hive_push.py tests/test_eligibility_fragments.py && mise run lint]
- ac11: the handover_due evaluation runs on every tick even when the hive_state hash is unchanged (outside the _claim/_release path) [evidence: test:tests/test_hive_push.py::test_handover_due_runs_when_hive_state_unchanged]

#### Files

- `src/agents_orchestrator/dispatcher/hive.py`
- `tests/test_hive_push.py`
- `tests/test_eligibility_fragments.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- Keyed note `handover_due` (wrapper `POST /v1/sessions/{id}/notes` with `key`), leader only.
- `hive._CANDIDATES` (or the chosen name): SQL embedding `eligibility.ELIGIBLE`, ordered idle first, then `context_pct` ascending (nulls last), then ordinal.
- Candidate line: `<pod_name> (<pod_name>/<wrapper_session_id>, <state>, <N>% context)`.

#### Expected outcome

A leader at or above the threshold sees, within one push tick plus wrapper delivery, who can take over, how to reach them, and the brief-then-handover protocol; nobody else is disturbed.

#### Steps

- Red: the tests of ac1-ac6 and ac11 in `tests/test_hive_push.py` and the ac7 assertion; run `uv run --frozen pytest tests/test_hive_push.py tests/test_eligibility_fragments.py`: they fail.
- Green: hive.py, README, MEMORY; run the task's verify: passes. Quote the summary line.

#### Notes

- Threshold: the helper from orch-hive-feed-removal; never respell it.
- Q8 (candidates at or above the threshold left out) is an open gate question; if answered no, the task is amended before it starts.
- The scalable test is `spec.scalable` (as `on_start.orchestrator_allow` uses it).
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-27 amended: builder check settlement 7: handover_due and outcome pass run every tick outside the _claim/_release hash path

- 2026-10-29 done

### S5: helmfile orch slice1 pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`
- Verified head: 0db3588ac99980f84c4366c75c3cc54dbd3418c3

#### Requirement

Deploy slice 1 of hive-decoupling (user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #33 (tasks orch-activity-route, orch-hive-feed-removal, orch-drop-feed-cursor; migration 0011_drop_feed_cursor): chart `0.1.0-main.342cad8` in helmfile.yaml.gotmpl and `image.tag` `342cad8` in values/agents-orchestrator/common.yaml. Wait until the orchestrator main CI run for 342cad8 is green including chart-publish before pinning. Keep every other pin unchanged. Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #33 merge sha 342cad8 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync to origin/main; wait for the orchestrator main CI run on 342cad8 to be green including chart-publish (`gh run list -R szymonrychu/agents-orchestrator -b main`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to 342cad8 and run the verify: the pin tests fail.
- Set the chart version and image tag to 342cad8, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch hive-decoupling-slice1-pin, push, open a PR to main.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S6: orch handover outcome note

- Status: done
- Files: `src/agents_orchestrator/dispatcher/hive.py`, `src/agents_orchestrator/dispatcher/loop.py`, `tests/test_hive_push.py`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_hive_push.py tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py && mise run lint`
- Verified head: 97bd7000e9418969bdeb0cc3e6f6e6c0d26752d6

#### Requirement

README Goal G4, verbatim: "The leader briefs a chosen successor directly over ccw peer messaging, then hands over with `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied, or rejected with its reason) as a keyed `leadership_request` note."

Design D6, verbatim: "the push pass reads, per hive session, the `handover` requests decided (`status` applied or rejected) within the last 300 s (module constant `OUTCOME_WINDOW_SECONDS`, my call) and sends each `from_agent_id`, once per request id per dispatcher process (tracked in `HiveState`), a keyed note `leadership_request`: "handover request <id> applied: <pod> leads at epoch N" or "handover request <id> rejected: <reason>" (`not_leader`, `stale_epoch`, `target_not_ready`, `no_peers`). `_drain_leadership` sets the push wake after it ran a pass for any session (my call: no change to `leadership_pass`'s signature); the per-session 10 s throttle still applies. The DB read makes it work with any number of dispatchers (live: one dispatcher pod, chart default `components.dispatcher.replicas: 1`); a duplicate keyed note replaces itself in the wrapper inbox."

Fix-as-ac (brief), verbatim: "Plugin `leadership_handover` text claims "the outcome arrives as a hive-state note"; untrue for rejections: D6 and the text fix." (This task: the note; plugin-activity-tool: the text.)

Scope (agents-orchestrator):
- `src/agents_orchestrator/dispatcher/hive.py`: `OUTCOME_KEY = "leadership_request"`, `OUTCOME_WINDOW_SECONDS = 300`; the read of decided `kind = 'handover'` requests of the session within the window (`decided_at > now() - OUTCOME_WINDOW_SECONDS`). An applied request is rendered with the session's current leader row, "handover request <id> applied: <pod> leads at epoch N", which is true at push time even for an untargeted request (its row has no `to_agent_id`) or after a later change (design D6 my call). Notes go only to the request's `from_agent_id` when it is not gone and has a wrapper session; a per-process "sent" set of request ids in `HiveState`, pruned to the window; a failed push is retried next tick. `user` requests (no `from_agent_id`) get no note.
- `src/agents_orchestrator/dispatcher/loop.py` `_drain_leadership`: `self._push_wake.set()` after it ran a pass for at least one session, changed or not.
- `tests/test_hive_push.py`: the new tests below.
- `README.md` `### Leadership` step 2: the outcome note; the hive-state push paragraph lists it.
- `MEMORY.md`: dated entry (window constant, per-process tracking, why).

#### Acceptance conditions

- ac1: an applied agent handover request gives its requester a keyed leadership_request note naming the request id, the new leader and the epoch [evidence: test:tests/test_hive_push.py::test_leadership_request_applied_note]
- ac2: a request the dispatcher rejects gives its requester a keyed leadership_request note naming the request id and the reason (target_not_ready and no_peers at least) [evidence: test:tests/test_hive_push.py::test_leadership_request_rejected_note]
- ac3: each outcome is sent once per request id; requests decided more than OUTCOME_WINDOW_SECONDS ago and user requests get no note [evidence: test:tests/test_hive_push.py::test_leadership_request_once_and_window]
- ac4: a running dispatcher pushes the outcome after a pass that rejected a request without a leader change, with no poll tick in between [evidence: test:tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision]
- ac5: README documents the outcome note under Leadership step 2 [evidence: command:grep -q "leadership_request" README.md]
- ac6: MEMORY.md records the window and the tracking [evidence: command:grep -q "OUTCOME_WINDOW_SECONDS" MEMORY.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_hive_push.py tests/test_leadership_pass.py tests/test_dispatcher_auto_handover.py && mise run lint]

#### Files

- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/dispatcher/loop.py`
- `tests/test_hive_push.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- Keyed note `leadership_request` to the request's `from_agent_id`: "handover request <id> applied: <pod> leads at epoch N" or "handover request <id> rejected: <reason>".
- `hive.OUTCOME_WINDOW_SECONDS = 300`; `Dispatcher._drain_leadership` sets `self._push_wake` after any pass.

#### Expected outcome

A leader that asked for a handover always learns the outcome, within the push throttle, including rejections.

#### Steps

- Red: the tests of ac1-ac4 in `tests/test_hive_push.py`; run `uv run --frozen pytest tests/test_hive_push.py`: they fail.
- Green: hive.py, loop.py, README, MEMORY; run the task's verify: passes. Quote the summary line.

#### Notes

- `leadership_pass` keeps its signature; `_decide` already stamps `decided_at` and `reject_reason`.
- For ac4, follow `test_dispatcher_run_pushes_on_leader_changed`; force a dispatcher-side rejection with a `to_agent_id` target that goes unready after the API accepted the request.
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-29 done

### S7: helmfile orch slice2 pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`
- Verified head: 96b2e5e211be50d7bb2f12d5ce826619b52d5c91

#### Requirement

Deploy slice 2 of hive-decoupling (user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #34 (tasks orch-handover-due-note, orch-handover-outcome-note; no migration): chart `0.1.0-main.98d3c23` in helmfile.yaml.gotmpl and `image.tag` `98d3c23` in values/agents-orchestrator/common.yaml. Wait until the orchestrator main CI run for 98d3c23 is green including chart-publish before pinning. Keep every other pin unchanged. Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #34 merge sha 98d3c23 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync to origin/main; wait for the orchestrator main CI run on 98d3c23 to be green including chart-publish (`gh run list -R szymonrychu/agents-orchestrator -b main`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to 98d3c23 and run the verify: the pin tests fail.
- Set the chart version and image tag to 98d3c23, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch hive-decoupling, push, open a PR to main.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S8: plugin activity tool

- Status: done
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`
- Verify: `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint`
- Verified head: 825e97cbac127a69eff74264cbad451cf387cd63

#### Requirement

README Goal G2, verbatim: "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

README Goal G4, verbatim: "The leader briefs a chosen successor directly over ccw peer messaging, then hands over with `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied, or rejected with its reason) as a keyed `leadership_request` note."

Design D3, verbatim: "Plugin tool `activity` (`GET /agent/v1/activity`, query `agent`, `limit`), description: "What the other agents did recently (commands with exit status, files written, finished turns): newest last. Call it when you need it; nothing is streamed to you.""

Design D5, verbatim: "carried by the `handover_due` text and the plugin `leadership_handover` and `me` descriptions; no CLAUDE.md fragment".

Fix-as-ac (brief), verbatim: "Plugin `leadership_handover` text claims "the outcome arrives as a hive-state note"; untrue for rejections: D6 and the text fix."

Scope (any-mcp-tatara-plugins, `orchestration/orchestrator`):
- `src/any_mcp_tatara_orchestrator/__init__.py`: tool `activity` after `me` in `load_tools`: `HttpBinding("GET", "/agent/v1/activity", query=("agent", "limit"))` (the `spec()` helper gains a `query` argument), schema `{agent?: string (pod name), limit?: integer 1..200}`, description as D3 (with the hive prefix). `leadership_handover` description: the D5 protocol in short (brief the successor named in the handover_due note with mcp__ccw__send_message and notify_when_idle, wait for its "ready", then call this tool with to, the current epoch and a reason), and "the outcome arrives as a leadership-request note (applied, or rejected with the reason)" replacing "The outcome arrives as a hive-state note."; the threshold advice stays computed from `auto_compact_pct` (the orchestrator now always renders the effective value, task orch-hive-tools-activity). `me` description: names `orchestrator_activity` and says nothing is streamed.
- `tests/test_orchestrator_plugin.py`: the new tests below. Named as no longer accurate: the tool-listing test (today `test_lists_eleven_tools`; whatever count-named test the epics before left) is renamed `test_lists_all_tools` and expects the current set plus `activity`; `test_descriptions_from_config` where it asserts the old hive-state outcome sentence.
- `README.md` (plugin): the tool table gains `orchestrator_activity(agent?, limit?)` | `GET /agent/v1/activity`; the tool count sentence follows.
- Read the file as merged by slash-commands-from-chat and matrix-connector-agent-initi first (shared file); keep their tools.

#### Acceptance conditions

- ac1: the activity tool calls GET /agent/v1/activity with agent and limit as query parameters and the session credentials [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_activity_tool_calls_route]
- ac2: the plugin lists every tool including activity (renamed count test, named) [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_lists_all_tools]
- ac3: the leadership_handover description carries the brief-then-handover protocol and the leadership-request outcome note, and no longer says the outcome arrives as a hive-state note [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_handover_description_protocol]
- ac4: the me description names orchestrator_activity and says nothing is streamed [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_me_description_points_to_activity]
- ac5: the threshold advice still follows auto_compact_pct [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_handover_threshold_hint]
- ac6: the plugin README lists the tool [evidence: command:grep -q "orchestrator_activity" orchestration/orchestrator/README.md]
- ac7: the plugin tests and lint pass [evidence: command:uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`

#### Interfaces

- Tool `orchestrator_activity(agent?: string, limit?: integer)`: `HttpBinding("GET", "/agent/v1/activity", query=("agent", "limit"), base_url=...)` (any-mcp `HttpBinding.query`, `any_mcp/types.py:82`).
- Route contract: agents-orchestrator README `### GET /agent/v1/activity` (task orch-activity-route).

#### Expected outcome

The plugin offers the activity tool and describes the brief-then-handover protocol and the outcome note.

#### Steps

- Red: the tests of ac1-ac4 (and the renamed listing test); run `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: they fail.
- Green: `__init__.py`, plugin README; run the task's verify: passes. Quote the summary line.

#### Notes

- Shared file with slash-commands-from-chat and matrix-connector-agent-initi: build on their merged tools.
- No release here (plugins-release-0-4-0).

- 2026-10-29 done

### S9: plugins release 0.4.0

- Status: done
- Files: `orchestration/orchestrator/pyproject.toml`, `uv.lock`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py`
- Verify: `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint`
- Verified head: b511c90951dbace68b60e01fbd1097ef20b0997f

#### Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Constraint, verbatim: "Plugin release rule: the next minor after the plugins pin the Matrix epic leaves (slash-commands releases v0.2.0, Matrix v0.3.0, so v0.4.0 if nothing else lands). If another release landed first, the release and pin tasks are amended to the next free minor before they start."

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `0.4.0`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.4.0`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): it pins the previous release version; it asserts `0.4.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.4.0 <merge sha> && git push origin v0.4.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push.

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.4.0` (the plugins release tag, `vX.Y.Z`), `0.4.0` (the same without the `v`) and `0011` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

#### Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.4.0 (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=v0.4.0"]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.4.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

#### Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `0.4.0`; git tag `v0.4.0` on the `main` merge commit.

#### Expected outcome

The orchestrator plugin with the activity tool is released as tag v0.4.0, so the orchestrator can pin it.

#### Steps

- Confirm the newest release tag on origin (`git ls-remote --tags origin 'v*'`) is the one `main` carries and that `v0.4.0` does not exist yet; stop and report otherwise (the task is amended to the next free minor).
- Red: change `test_orchestrator_distribution_metadata` to 0.4.0; run `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the plugin README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag v0.4.0 <merge sha> && git push origin v0.4.0`, then check ac3.

#### Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in agent pods with git 2.39 (`--end-of-options`); CI is the gate for it.

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main

- 2026-10-29 done

### S10: orch plugins pin 0.4.0

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `README.md`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint`
- Verified head: ff6c6dece6aa1ee7082aad45b54f9e07cb3a1893

#### Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D9, verbatim: "`any_mcp_plugins_ref` default, dev dependency and README Images move to the new plugins tag."

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.4.0` on origin (task plugins-release-0-4-0).

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `v0.4.0`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.4.0#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `v0.4.0` and the `## Images` plugins release tag.
- `tests/test_settings.py::test_defaults` is no longer accurate (named): it pins the previous plugins tag; it asserts `v0.4.0`.
- No agents-helmfile change here (helmfile-deploy-pin).

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.4.0` (the plugins release tag, `vX.Y.Z`), `0.4.0` (the same without the `v`) and `0011` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

#### Acceptance conditions

- ac1: the settings default is v0.4.0 (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the v0.4.0 default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `v0.4.0` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc 'v0.4.0')" = 0]
- ac4: the pinned orchestrator plugin carries the activity tool [evidence: command:grep -rq "/activity" "$(uv run --frozen python -c 'import os, any_mcp_tatara_orchestrator as m; print(os.path.dirname(m.__file__))')"]
- ac5: settings, images and on-start suites and lint pass [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_settings.py`

#### Interfaces

- `Settings.any_mcp_plugins_ref` default `v0.4.0` (`ORCH_ANY_MCP_PLUGINS_REF`); dev dependency `any-mcp-tatara-orchestrator` at `v0.4.0`.

#### Expected outcome

Agent pods rendered by this orchestrator install the plugins release that offers the activity tool.

#### Steps

- Confirm tag `v0.4.0` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins v0.4.0`); stop and report if absent.
- Red: change `test_defaults` to v0.4.0; run `uv run --frozen pytest tests/test_settings.py tests/test_images.py`: fails.
- Green: settings default, pyproject pin, `uv lock`, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties dev dependency, uv.lock and the default to one tag.
- Shared file `settings.py` with the epics before; build on their pins.
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); the deploy is helmfile-apply-live-proof.

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main

- 2026-10-29 done

### S11: plugin advice threshold floor

- Status: done
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- Verify: `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint`
- Verified head: 76d7fb3407cd9955eb55be48ce9e9aadbf0b41f9

#### Requirement

Phase 5 review finding (Act on), README G3 verbatim: "the `hive_state` hint and the plugin advice always use the effective threshold". The effective threshold is `max(compact - HANDOVER_MARGIN_PCT, 1)` (agents-orchestrator dispatcher/hive.py:handover_threshold, HANDOVER_MARGIN_PCT 15). The orchestrator plugin (orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, the `me` tool description) renders `{cfg.auto_compact_pct - 15}%` with no floor, so a session with `auto_compact_pct` 1..15 (valid: spec Field ge=1) is advised 0% or a negative number. Make the advice use `max(auto_compact_pct - 15, 1)`, with the margin named once in the plugin as a constant whose comment points to the orchestrator's HANDOVER_MARGIN_PCT. Release it as plugin patch 0.5.1 on top of cct2's v0.5.0 (bump the orchestrator plugin version the way commit 3dfd403 did for 0.5.0). The git tag v0.5.1 is pushed by the supervisor after merge. No deploy in this task: the plugins ref pin rides with cct2's slash deploy.

#### Acceptance conditions

- ac1: auto_compact_pct 10 renders the advice "passes 1%" and 80 renders "passes 65%" [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_handover_advice_uses_the_floored_threshold]
- ac2: the orchestrator plugin version is 0.5.1 [evidence: judgement:reviewer reads the version files changed as in 3dfd403]
- ac3: plugin tests and lint pass [evidence: command:uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Branch `plugin-advice-floor` from fresh origin/main (dfa0355, v0.5.0).
- Add test_handover_advice_uses_the_floored_threshold (auto_compact_pct 10 -> "passes 1%", 80 -> "passes 65%"); run the verify: red on the 10 case.
- Floor the advice with a named margin constant; rerun: green. Bump the orchestrator plugin version to 0.5.1 as 3dfd403 did. Commit, push, open a PR to main. Known pod-only failure: tests/test_source_install (git 2.39 --end-of-options), also red on origin/main; quote it, do not fix it.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress

- 2026-10-29 done: PR #5 review pass, merged ef17204, main CI green, tag v0.5.1 pushed; ref pin rides with cct2's slash deploy

- 2026-10-29 actuals: no agent records

### S12: orch hive tools activity

- Status: done
- Files: `src/agents_orchestrator/k8s/on_start.py`, `tests/test_on_start.py`, `README.md`
- Verify: `uv run --frozen pytest tests/test_on_start.py tests/test_render.py && mise run lint`
- Verified head: b883ca92b3e2e34a48f110c541e6b28ef076800b

#### Requirement

README Goal G2, verbatim: "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

README Goal G3, verbatim (the plugin part): "the `hive_state` hint and the plugin advice always use the effective threshold."

Design D9, verbatim: "`activity` joins `HIVE_TOOLS` after `me`; the rendered plugin config carries the effective `auto_compact_pct` (`spec.auto_compact_pct or settings.default_auto_compact_pct`) so the plugin advice always shows (fix-as-ac)".

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/on_start.py`: `HIVE_TOOLS = ["me", "activity", "leadership_handover", ...]`; `_orchestrator_entry` config `auto_compact_pct: spec.auto_compact_pct or settings.default_auto_compact_pct`.
- `tests/test_on_start.py`: its `HIVE_TOOLS` list is no longer accurate (named): it gains `activity` after `me`; `test_hive_entry_and_allow` keeps 70 from the spec; new `test_plugin_config_effective_auto_compact` (a spec without `auto_compact_pct` renders `settings.default_auto_compact_pct`, 95 by default).
- `README.md` `### Hive` tool gating bullet: the allowlist reads `me`, `activity`, `leadership_handover`, ...
- Read the file as merged by matrix-connector-agent-initi first (it adds its chat tools to `orchestrator_allow`); keep them.
- Changing the rendered config rolls agent pods on deploy (README Images); the deploy is helmfile-apply-live-proof.

#### Acceptance conditions

- ac1: a hive session's allowlist has activity right after me (test list updated, named) [evidence: test:tests/test_on_start.py::test_hive_session_tools]
- ac2: a spec without auto_compact_pct renders the settings default in the plugin config [evidence: test:tests/test_on_start.py::test_plugin_config_effective_auto_compact]
- ac3: a spec auto_compact_pct is rendered unchanged [evidence: test:tests/test_on_start.py::test_hive_entry_and_allow]
- ac4: every allowed tool exists in the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac5: the README tool gating lists activity after me [evidence: command:grep -qF '`me`, `activity`, `leadership_handover`' README.md]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_on_start.py tests/test_render.py && mise run lint]

#### Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `README.md`

#### Interfaces

- `k8s/on_start.py:HIVE_TOOLS` order `me, activity, leadership_handover, lock_claim, lock_release, lock_list, lock_reassign`; rendered plugin `config.auto_compact_pct` is the effective value.

#### Expected outcome

Hive agents see `orchestrator_activity`; the plugin's threshold advice shows for every hive, with the real value.

#### Steps

- Red: update the test `HIVE_TOOLS` list and add `test_plugin_config_effective_auto_compact`; run `uv run --frozen pytest tests/test_on_start.py`: fails.
- Green: on_start.py, README; run the task's verify: passes. Quote the summary line.

#### Notes

- `test_allowed_tools_exist_in_plugin` needs the v0.4.0 dev pin (orch-plugins-pin-0-4-0) to see `activity`.
- Golden render files (`tests/golden/*.yaml`) may embed the on-start config; if `tests/test_render.py` fails on them, stop and report (they are not in this task's files) so the task is amended.

- 2026-10-29 done

### S13: helmfile smoke activity

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint`
- Verified head: 84197ef8c4ad52005afc24aa5c7093b731b4675a

#### Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D11, verbatim: "the agents-helmfile smoke grows: step 4a also requires `orchestrator_activity` in `--list-tools` (parsed as JSON), and a step 6a calls `GET /agent/v1/activity` from the agent pod with its own env and requires 200 with a `lines` array."

Scope (agents-helmfile):
- `scripts/smoke.sh`: step 4a requires `orchestrator_activity` in the `--list-tools` JSON array (jq, like the existing `orchestrator_sessions_list` check); new step 6a after step 6: from the hive pod, with its own `ORCH_AGENT_URL`, `ORCH_AGENT_TOKEN`, `ORCH_SESSION_ID`, `GET /agent/v1/activity?limit=5` must answer 200 with a JSON object whose `lines` is an array (python3 in the pod prints the status and `isinstance(body.get("lines"), list)`; nothing else printed); header comment updated. Any wait added has its own deadline.
- `tests/test_smoke_script.py`: the fake kubectl answers the activity call with the real route shape `{"lines": [{"id": 1, "agent": "agent-x-0", "text": "agent-x-0 ran: true (ok)", "ts": "2026-10-27T00:00:00+00:00"}]}` as rendered status lines; the fake `--list-tools` output gains `orchestrator_activity` in its JSON array; the new tests below.
- The smoke runs against the deployed release only after helmfile-deploy-pin's apply; the step is in the same agents-helmfile PR as the pin.

#### Acceptance conditions

- ac1: step 6a calls /agent/v1/activity inside the hive pod with the pod's own env and passes on 200 with a lines array [evidence: test:tests/test_smoke_script.py::test_agent_activity_check_runs_in_pod_with_its_own_env]
- ac2: step 6a fails the smoke on a non-200 answer or a body without a lines array [evidence: test:tests/test_smoke_script.py::test_agent_activity_check_fails_without_lines]
- ac3: step 4a fails the smoke when --list-tools lists no orchestrator_activity [evidence: test:tests/test_smoke_script.py::test_plugin_tools_require_activity]
- ac4: every new wait has its own deadline and the fakes answer the real route and --list-tools JSON shapes [evidence: judgement:reviewer checks each timeout in the smoke diff and compares the fakes with the route contract in agents-orchestrator README Agent API]
- ac5: the smoke script tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

#### Interfaces

- Smoke step 4a: `jq -e 'any(.[]?; .name == "orchestrator_activity")'` over `--list-tools`; step 6a: in-pod python prints `<status> <has_lines>`.

#### Expected outcome

Every `mise run smoke` proves the activity route from an agent pod and the tool in the plugin listing.

#### Steps

- Red: the tests of ac1-ac3 in `tests/test_smoke_script.py` with the fake kubectl; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py`: they fail.
- Green: `scripts/smoke.sh` steps 4a and 6a and the header comment; run the task's verify: passes. Quote the summary line.

#### Notes

- Mirror the step 6 `/agent/v1/me` check (`smoke.sh:346-356`) and its tests `test_agent_me_check_*` (`tests/test_smoke_script.py:950-964`).
- Recurring retro: fakes must answer the real output shapes; each wait gets its own deadline.

- 2026-10-29 done

### S14: orch e2e hive activity

- Status: done
- Files: `tests/e2e/test_e2e_kind.py`
- Verify: `uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint`
- Verified head: f7e44f6c4fd50c94deacbf5d54780ca262bcb4fa

#### Requirement

README Goals G1 and G2, verbatim: "Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped." "Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`."

Design D10, verbatim: "The kind e2e replaces the feed assertion of `test_hive_notes_delivered` with the activity route and "no appended orchestrator note" and adds `activity` to `HIVE_ONLY_TOOLS`. D4 is not in the kind e2e (my call): the fake claude emits no statusline, so no `context_pct` exists there; D4 is proven by DB tests and the live proof (D11)."

Fix-as-ac (brief), verbatim: "`tests/e2e/test_e2e_kind.py` feed assertions (not read in this discovery; the builder lists them in the task) are replaced by an `activity` route assertion." Listed (F3): `test_hive_notes_delivered` (`feed_on_reader`) and the `HIVE_PUSH_TIMEOUT` comment (line 78, "feed rows settle for 5 s").

Scope (agents-orchestrator, `tests/e2e/test_e2e_kind.py` only):
- `test_hive_notes_delivered` is no longer accurate (named: it waits for a feed note on the reader): after the writer's turn writing `NOTE_FILE`, the reader's `GET /agent/v1/activity` (through the existing `agent_call` helper) lists a line naming `NOTE_FILE` by the writer; both agents still have a keyed `hive_state` note; no `note_received` event with a null key reaches either agent.
- `HIVE_ONLY_TOOLS` gains `activity` (the alone session must not render it).
- `HIVE_PUSH_TIMEOUT` comment no longer mentions the feed settle.
- The leader-auto-handover e2e tests (`test_leader_compaction_hands_over`, `test_scale_down_below_leader_hands_over`) stay unchanged and green.

#### Acceptance conditions

- ac1: in kind, the reader pulls the writer's file write through GET /agent/v1/activity, both agents hold a keyed hive_state note and no unkeyed note arrives (rewritten, named) [evidence: test:tests/e2e/test_e2e_kind.py::test_hive_notes_delivered]
- ac2: an alone session renders none of the hive-only tools, activity included [evidence: test:tests/e2e/test_e2e_kind.py::test_alone_session_has_no_hive_tools]
- ac3: the e2e file has no feed wording left [evidence: command:! grep -nE 'feed_on_reader|feed note|feed rows' tests/e2e/test_e2e_kind.py && grep -q '"activity"' tests/e2e/test_e2e_kind.py]
- ac4: the kind e2e CI job is green on the PR head, leader-auto-handover e2e cases included [evidence: judgement:reviewer quotes the e2e job conclusion of the PR head commit]
- ac5: the file compiles and lint passes [evidence: command:uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint]

#### Files

- `tests/e2e/test_e2e_kind.py`

#### Interfaces

- Uses `agent_call(pod, "GET", "/agent/v1/activity?agent=<writer pod>")` and the `note_received` events of `all_events`.

#### Expected outcome

The kind e2e proves the pull path and the absence of the feed note end to end.

#### Steps

- Red/green under the e2e harness: the kind job runs only in CI; rewrite the test, run `uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint` locally, push, and read the PR's e2e job result.

#### Notes

- No kind in agent pods: the reviewer judges ac1, ac2 and ac4 from the CI e2e job of the PR head.
- slash-commands-from-chat and matrix-connector-agent-initi also edit this file; build on their merged cases.

- 2026-10-29 done

### S15: helmfile deploy pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && mise run lint`
- Verified head: 9d78895b088339e9354e296fb7fedb4a42d472b2

#### Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D9, verbatim: "agents-helmfile: orchestrator chart version and image tag (CI-published merge sha7), `ORCH_ANY_MCP_PLUGINS_REF` to the new tag; agent image unchanged (whatever release tag the epics before left)."

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<orchestrator merge sha7>`, the agents-orchestrator `main` commit that carries every orchestrator task of this epic (CI-published).
- `values/agents-orchestrator/common.yaml`: `image.tag` `<the same sha7>`; `env.ORCH_ANY_MCP_PLUGINS_REF: v0.4.0`. `agentImage` and `ORCH_AGENT_IMAGES` unchanged.
- `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` is no longer accurate (named): it asserts the previous plugins ref; it asserts `v0.4.0`.
- The sha7 is filled in by `ticket.py amend` when the orchestrator PR merges; confirm the image tag and chart version exist in Harbor before changing the values.
- No apply here (helmfile-apply-live-proof).

Builder check settlement 1 (2026-10-27, my call): the build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged. `v0.4.0` (the plugins release tag, `vX.Y.Z`), `0.4.0` (the same without the `v`) and `0011` (the orchestrator migration number, four digits) in this task are placeholders: orch-activity-route reads the real values from main and replaces them here with `ticket.py amend` before this task starts. No number in this task is assumed; `0.4.0` and `0009` in design.md are only the expectation.

#### Acceptance conditions

- ac1: the orchestrator chart version and image tag agree on the orchestrator merge sha7 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: new sessions get the v0.4.0 plugins ref (updated, named) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: the agent image pins still agree [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- ac4: the pinned sha7 is an agents-orchestrator main commit that contains every orchestrator task of this epic, with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each orchestrator task's verified_head against the pinned sha and the CI run of that sha]
- ac5: the release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

- `values/agents-orchestrator/common.yaml`: `image.tag`, `env.ORCH_ANY_MCP_PLUGINS_REF`; `helmfile.yaml.gotmpl`: agents-orchestrator chart `version`.

#### Expected outcome

agents-helmfile pins the hive-decoupling orchestrator and the v0.4.0 plugins release, ready to apply.

#### Steps

- Red: point the expectations of `test_any_mcp_configured_for_new_sessions` at v0.4.0 and run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: fails.
- Green: values and chart version (the sha7 from the amendment, after confirming it exists in Harbor); run the task's verify: passes. Quote the summary line.

#### Notes

- Dependency-bump TDD exception (a pin change); the release tests are the guard.
- `tests/test_orchestrator_release.py` also holds `test_values_dir_moved`, which once blocked an apply; it must pass.
- `test_release_chart_version_and_needs` runs `helmfile build` and needs network; environmental in agent pods, run before the apply.
- The Matrix epic also edits these values; build on its merged pins (agent image untouched here).

- 2026-10-27 amended: builder check settlement 1: migration number and plugins tag are placeholders until orch-activity-route amends them from main

- 2026-10-29 done

### S16: orch flaky push after decision

- Status: done
- Files: `tests/test_hive_push.py`, `src/agents_orchestrator/dispatcher/hive.py`, `src/agents_orchestrator/dispatcher/loop.py`
- Verify: `uv run --frozen pytest tests/test_hive_push.py && mise run lint`
- Verified head: fe2c623a49ffe556325d06f236cbe8668a0a6238

#### Requirement

Reported by hive cct2 (via mx-34 msg 391, 2026-10-29), verbatim: "orchestrator main has a flaky test from hive-decoupling: test_hive_push.py::test_dispatcher_run_pushes_after_decision fails about 1 in 4 on clean origin/main (local Postgres)."

Find the root cause of the intermittent failure of tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision (added by orch-handover-outcome-note) and fix it at the cause. If the race is in the dispatcher (the leadership-request outcome push after a decision), fix the code; if the test's own timing or ordering is wrong, fix the test so it waits on the real condition rather than a sleep. Do not quarantine, skip, xfail or loosen what the test asserts (the rejection note reaches the requester and the epoch stays 1). Reproduce first: run the test repeatedly against a local Postgres (pgserver worked in this pod for earlier tasks) and record the failure rate before and after; the fix must hold over at least 40 consecutive runs.

#### Acceptance conditions

- AC1: the test passes 40 consecutive runs against a local Postgres after the fix, and the failure was reproduced before it [evidence: command:for i in $(seq 1 40); do uv run --frozen pytest -q -p no:cacheprovider tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision || exit 1; done]
- AC2: the test still asserts the rejection note and epoch 1, with no skip, xfail or weakened assertion [evidence: test:tests/test_hive_push.py::test_dispatcher_run_pushes_after_decision]
- AC3: the hive push suite and lint pass [evidence: command:uv run --frozen pytest tests/test_hive_push.py && mise run lint]

#### Files

- `tests/test_hive_push.py`
- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/dispatcher/loop.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync the branch to origin/main; start a local Postgres (pgserver) and run the test 40 times: record the failure count (expect about 1 in 4).
- Read the test and the dispatcher outcome-push path; name the race.
- Fix at the cause; rerun 40 times: 0 failures. Run the verify.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S17: helmfile apply live proof

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run lint && grep -q 'hive-decoupling live handoff' MEMORY.md`
- Verified head: 054d0517fc7de4859e4c02b67e42fed044a25e5a

#### Requirement

User request (2026-10-27), verbatim: "Maybe leader could get a signal to pass on its session details to another agent when it hits a limit and both could talk to each other about details for handoff?"

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D11, verbatim: "After the apply the orchestrator session runs a live proof in a throwaway 2-agent hive with `auto_compact_pct` 20 (threshold 5%, which a fresh leader already exceeds): the leader receives `handover_due`, briefs the named successor over ccw, the handover is applied with reason `handover: context`, the ex-leader receives `leadership_request`, and no member receives an unkeyed orchestrator note after the apply. Results go to agents-helmfile MEMORY.md. Standing rule (user): deploy whenever possible; live applies need no approval."

Steps, run by the orchestrator session (never a subagent: subagent `kubectl exec` is denied), in `code/agents-helmfile` on `main` after the helmfile PR merged, least destructive first:
1. Check the orchestrator image tag and chart version exist in Harbor.
2. `mise run diff -- --selector name=agents-orchestrator`: the change is the chart version, the image tag and `ORCH_ANY_MCP_PLUGINS_REF`; anything else stops the task.
3. Handoff checkpoint first (settlement 2): the orchestrator session writes a handoff checkpoint (`workbench:handoff`) that names the remaining steps: the apply, step 4 (diff and smoke), step 5 (read-only checks), step 6 (live proof), step 7 (MEMORY.md entry), the task Notes recorded so far and the pinned chart, image and plugins ref. Then `mise run apply -- --selector name=agents-orchestrator` (live; listed in design.md); the helm apply runs to completion before the reconciler rolls any pod. The orchestrator applies the feed_cursor migration on start; agent pods of running sessions roll (config hash), including the pod of the session that runs this task. After the roll the resumed leader re-runs the smoke (step 4) and the live proof (step 6) from the checkpoint, then steps 5 and 7.
4. (after the roll, by the resumed leader if the session was rolled) `mise run diff` shows no pending change; `mise run smoke` green, including steps 4a and 6a (task helmfile-smoke-activity).
5. Read-only checks: `session_leaders` has no `feed_cursor` column; live leaders report a non-null `context_pct` after the roll (F1 re-check).
6. Live proof: a throwaway 2-agent hive from the default preset with `auto_compact_pct: 20`; post one untargeted message (a short read-only task) so the leader's gauge is set; confirm a `note_received` event with key `handover_due` on the leader; post one more untargeted message so the leader acts on it; confirm a peer turn on the successor carrying the brief, a handover with `leader_reason` `handover: context`, and a `note_received` event with key `leadership_request` on the ex-leader; confirm no `note_received` event with a null key on either agent, counting only notes posted by the dispatcher (orchestrator-originated; settlement 3): peer messages that the agents send each other over ccw are not counted. The orchestrator reads which event field tells the dispatcher's notes from peer messages before it counts, and records the filter in the task Notes; if no field distinguishes them it raises a question instead of guessing. Discard the session afterwards. A leader that does not follow the note within two user turns is a finding (a sharper note text becomes a new task), not a pass.
7. MEMORY.md entry containing the words `hive-decoupling live handoff`, dated, with the applied chart, image, plugins ref, the step 6 session id, request id and the event ids, and the F1 values.

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25).

Builder check settlements 2 and 3 (2026-10-27, my call): the live apply rolls the agent pods of the session that runs it, so the handoff checkpoint (step 3) precedes the apply, the helm apply completes before the reconciler rolls pods, and the resumed leader re-runs smoke and the live proof from the checkpoint. The unkeyed-note count of step 6 counts only dispatcher-posted (orchestrator-originated) notes.

#### Acceptance conditions

- ac1: (orchestrator session) the orchestrator image tag and chart version exist in Harbor before the apply [evidence: judgement:orchestrator records the registry check in the task Notes]
- ac2: after the apply helmfile reports no pending change [evidence: command:mise run diff]
- ac3: the smoke passes against the applied release, including the activity steps [evidence: command:mise run smoke]
- ac4: (orchestrator session) the live database has no session_leaders.feed_cursor column and live leaders report a non-null context_pct [evidence: judgement:orchestrator quotes the two read-only psql results in the task Notes]
- ac5: (orchestrator session) in the throwaway hive the leader received handover_due, briefed the successor over ccw, leadership moved with reason "handover: context" and the ex-leader received leadership_request [evidence: judgement:orchestrator quotes the session id, event ids, request id and leader_reason in the task Notes]
- ac6: (orchestrator session) no agent of the throwaway hive received an unkeyed note posted by the dispatcher (orchestrator-originated notes only; ccw peer messages are not counted) after the apply [evidence: judgement:orchestrator quotes the filter used and the count of dispatcher-posted note_received events with a null key]
- ac7: MEMORY.md records the live handoff and the applied versions [evidence: command:grep -q "hive-decoupling live handoff" MEMORY.md]
- ac8: (orchestrator session) before the apply a handoff checkpoint naming the apply, smoke and proof steps was written, and after the pods rolled the resumed leader re-ran the smoke and the live proof from it [evidence: judgement:orchestrator quotes the checkpoint path in the task Notes, and the smoke and proof results recorded after the roll]

#### Files

- `MEMORY.md`

#### Interfaces

- None new; uses `mise run diff`, `mise run apply`, `mise run smoke`, the public orchestrator API (port-forward as the smoke does) and read-only `psql` on the orchestrator database.

#### Expected outcome

The decoupled hive runs live: members get no feed note, the activity route answers, and a real leader near its threshold briefed a successor over ccw and handed over.

#### Steps

- Orchestrator session only: steps 1-7 of the Requirement, in order; stop at step 2 if the diff shows more than the pins. Write the handoff checkpoint (step 3) before the apply; after the roll, resume from it.
- Record each result in the task Notes as it happens (session id, event ids, request id, smoke tail), then the MEMORY.md entry; commit it through the agents-helmfile PR flow.

#### Notes

- Recurring retro: live apply and proof tasks run several times their seed; budget for more than one proof attempt.
- The apply rolls the agent pods of every running session (mx-5 and claude-code-tatara included; orchestrator README Images, design.md D9, gate question Q7). If the session running this task lives in one of those pods, it restarts at step 3: write the Notes and the handoff checkpoint (settlement 2) before the apply, and resume from the checkpoint.

- 2026-10-27 amended: builder check settlements 2 and 3: handoff checkpoint around the pod-rolling apply; ac6 counts dispatcher-posted notes only

- 2026-10-29 done: PR #53 review pass (ac1-ac8 against live-proof.md and logs), merged

- 2026-10-29 actuals: no agent records

### S18: helmfile orch flaky fix pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`
- Verified head: 26aa34004d50de67a908e861ed0cf8252985bda5

#### Requirement

Deploy the flaky-test fix alone (mx-34 #430, relaying cct2: "Tatara should deploy be554bb on its own"; user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #37 (task orch-flaky-push-after-decisi, fix fe2c623; no migration): chart `0.1.0-main.be554bb` in helmfile.yaml.gotmpl and `image.tag` `be554bb` in values/agents-orchestrator/common.yaml, replacing df2b80e. Wait until the orchestrator main CI run for be554bb is green including chart-publish before pinning. Keep every other pin unchanged (plugins v0.4.0, agent image, connector, web). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #37 merge sha be554bb [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync to origin/main; wait for the orchestrator main CI run on be554bb to be green including chart-publish (`gh run list -R szymonrychu/agents-orchestrator -b main`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to be554bb and run the verify: the pin tests fail.
- Set the chart version and image tag to be554bb, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch orch-flaky-fix-pin (from origin/main; PR #53 holds branch hive-decoupling), push, open a PR to main.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress

- 2026-10-29 todo: handed to cct2 (tatara decommissioned, mx-34 #437); implementer stopped before any change; be554bb main CI was in progress

- 2026-10-29 in-progress: resumed per mx-34 #440 (user: let it finish)

- 2026-10-29 done: PR #54 review pass, merged; deploy follows in the supervisor session

- 2026-10-29 actuals: no agent records

### S19: orch feed dead code and compact helper

- Status: done
- Files: `src/agents_orchestrator/dispatcher/feed.py`, `src/agents_orchestrator/api/agent.py`, `src/agents_orchestrator/dispatcher/hive.py`, `src/agents_orchestrator/k8s/on_start.py`, `src/agents_orchestrator/k8s/render.py`, `src/agents_orchestrator/db/views.py`, `tests/test_hive_feed.py`
- Verify: `uv run --frozen pytest -q tests/test_hive_feed.py && mise run lint`
- Verified head: 35e8f2a4e1dd9ec19b7b1614a949d302be729d6f

#### Requirement

Scope audit gaps at close (scope-auditor, 2026-10-29), against design.md anti-goal verbatim: "Dead feed code or a dead column left behind \"for compatibility\"." and design D5 (line 106): "`max(coalesce(spec.auto_compact_pct, settings.default_auto_compact_pct) - HANDOVER_MARGIN_PCT, 1)`, one helper in" hive.py.
(1) Remove the unreachable `leadership` branch from `dispatcher/feed.py:digest_lines` (nothing in src produces a `leadership` row any more) and its docstring lines, and drop the unused `pending` return: `digest_lines` returns only the lines; update every caller (`api/agent.py` activity route, any other) and tests/test_hive_feed.py (retire the leadership-row tests; a retirement test pins the removal).
(2) Collapse the effective compaction point to the one helper `dispatcher/hive.py:compact_pct`, reused by `k8s/on_start.py`, `k8s/render.py` and `db/views.py`, keeping today's behaviour for each caller (note: hive.py uses `is None`, the others `or`; spec Field ge=1 makes 0 impossible, so both agree; keep it so). No behaviour change, no migration.

#### Acceptance conditions

- ac1: no `leadership` row handling remains in feed.py and digest_lines returns only lines [evidence: test:tests/test_hive_feed.py::test_digest_lines_has_no_leadership_row_kind]
- ac2: one helper computes the effective compaction point: `grep -rn default_auto_compact_pct src` hits only settings, hive.py:compact_pct and call sites passing settings to it [evidence: judgement:reviewer runs the grep and reads each hit]
- ac3: orchestrator tests and lint pass in CI on the PR head (DB tests are CI-only) [evidence: command:gh pr checks]

#### Files

- `src/agents_orchestrator/dispatcher/feed.py`
- `src/agents_orchestrator/api/agent.py`
- `src/agents_orchestrator/dispatcher/hive.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/db/views.py`
- `tests/test_hive_feed.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Branch `orch-feed-cleanup` from fresh origin/main (be554bb).
- Red: add test_digest_lines_has_no_leadership_row_kind (a `leadership` row yields no line, and digest_lines returns a list, not a tuple); retire the leadership-row tests; run the verify: red.
- Green: remove the branch, docstring lines and `pending` return; update callers. Reuse hive.compact_pct in on_start.py, render.py and views.py. Rerun the verify plus the unit tests of the touched callers (DB-free ones): green. Commit, push, open a PR to main; DB tests and e2e are CI-only, so wait for `gh pr checks` green with `gh pr checks --watch`.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress

- 2026-10-29 done: PR #38 review pass (CI test/lint/e2e/chart green), merged 2d6d722

- 2026-10-29 actuals: no agent records

### S20: helmfile orch cleanup pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`
- Verified head: eafa60b4027f81680c8e1204d9686eed90719b59

#### Requirement

Deploy the scope-audit cleanup alone (mx-34 #461 go-ahead; user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #38 (task orch-feed-dead-code-and-comp; no migration): chart `0.1.0-main.2d6d722` in helmfile.yaml.gotmpl and `image.tag` `2d6d722` in values/agents-orchestrator/common.yaml, replacing be554bb. Wait until the orchestrator main CI run for 2d6d722 is green including chart-publish before pinning. Keep every other pin unchanged (plugins v0.4.0, agent image, connector, web). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

#### Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #38 merge sha 2d6d722 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync to origin/main (4e29e70 or newer); wait for the orchestrator main CI run on 2d6d722 to be green including chart-publish (`gh run watch <id> -R szymonrychu/agents-orchestrator --exit-status`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to 2d6d722 and run the verify: the pin tests fail.
- Set the chart version and image tag to 2d6d722, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch orch-cleanup-pin from origin/main, push, open a PR to main.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress

- 2026-10-29 done: PR #55 review pass, merged; orch CI 40915663717 green

- 2026-10-29 actuals: no agent records

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
