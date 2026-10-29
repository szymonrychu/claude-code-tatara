# hive decoupling design

## Summary

Hive members stop receiving the leader's activity stream. The dispatcher no longer sends the appended feed note;
members keep only the keyed `hive_state` note, re-pushed when the leader, epoch, membership or readiness changes, and
pull what peers did through a new agent route `GET /agent/v1/activity` and the plugin tool `orchestrator_activity`.
A leader whose context reaches the effective handover threshold (its compaction percentage minus 15) gets one keyed
`handover_due` note naming successor candidates with their ccw addresses and the handoff protocol. It briefs the
successor over the existing ccw peer channel, then calls the existing `orchestrator_leadership_handover(to=...)`.
Every handover request outcome reaches the requester as a keyed `leadership_request` note. Repos:
agents-orchestrator, any-mcp-tatara-plugins (next minor release), agents-helmfile (pin, apply, smoke, live proof).
claude-code-wrapper and agents-web are untouched. Architecture: fable brief
`.scratchpad/design/hive-decoupling-arch.md` (D1-D9 there; D1-D11 here).

## Intent and why

User request (2026-10-27, verbatim in README): "Decouple agents in session more. Right now non-leaders get truncated
stream of what's leader is doing. Ask fable architect to decouple or use handoff or something to consume non-leaders
less. Maybe leader could get a signal to pass on its session details to another agent when it hits a limit and both
could talk to each other about details for handoff?"

Today every member gets up to 8000 characters of `<peer-notes>` every 30 s of a busy turn (the feed, produced by
`dispatcher/hive.py` `_push_agent` with `feed.render_feed`, truncated with "... N earlier lines omitted"), plus a
`hive_state` block on every idle/busy flip of any member. Nothing warns a leader near its limit: the system only
reacts after the compaction (done epic leader-auto-handover), when the details are gone.

## Goals

- G1: Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed
  only when the leader, epoch, membership (pod, wrapper session) or readiness changes, and
  `session_leaders.feed_cursor` is dropped.
- G2: Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200,
  default 50) and the plugin tool `orchestrator_activity`.
- G3: A leader at or above the effective handover threshold gets one keyed `handover_due` note with ranked successor
  candidates, their ccw addresses and the handoff protocol; the `hive_state` hint and the plugin advice always use the
  effective threshold.
- G4: The leader briefs a chosen successor directly over ccw peer messaging, then hands over with
  `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied,
  or rejected with its reason) as a keyed `leadership_request` note.
- G5: Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply,
  smoke covering the activity route and tool, and a live handoff proof.

## Non-goals

- Any claude-code-wrapper change or release (no threshold hook, no new event, no notes config).
- A digest or summarised stream to members (option B), or a shared journal file.
- An automatic threshold handover by the orchestrator (H3), or any new automatic pick rule.
- An orchestrator-mediated handoff protocol, or a new table or writer for the brief.
- A new `session_leaders.reason` value or stream frame; any agents-web change.
- A per-session switch for the signal or the pull tool.
- Pushing the compact summary to the successor (H4).
- Changing any leader-auto-handover backstop (compaction step 5, scale-down step 3, claim hold, reconciler pod hold).
- Rate limiting `activity` (brief idea; only if a polling member is observed).
- Dropping `events.created_at` (added for the feed settle window, but `db/export.py` `SELECT * FROM events` exports
  it).

## Anti-goals

- A member learns a leader change late or not at all (`hive_state` must still push on every structural change).
- Leadership flips before the successor has the brief (step 5 of D5 is the only flip).
- A rejected handover stays invisible to the leader that asked.
- The leader-auto-handover backstops regress (its kind e2e and DB tests stay green, unchanged).
- Dead feed code or a dead column left behind "for compatibility".

## Constraints

- One writer per table: `session_leaders` dispatcher; `agent_status` and `events` ingester; `leadership_requests` api
  inserts, dispatcher decides. The new route only reads `events`.
- The agent API is the only agent-facing surface; tools come through the any-mcp orchestrator plugin; tool visibility
  is fixed at render from `max_replicas`/`static`.
- `PUSH_INTERVAL_SECONDS`, `LEADER_GRACE_SECONDS` and `HANDOVER_MARGIN_PCT` are module constants, not settings
  (orchestrator MEMORY 2026-10-24).
- No backward-compat shims (housekeeping 4).
- Shared files with the epics before this one (slash-commands-from-chat, then matrix-connector-agent-initi): the
  plugin `__init__.py`, `k8s/on_start.py`, `settings.py` and the agents-helmfile values. This epic is blocked on
  matrix-connector-agent-initi and builds on whatever both merged; every task reads the current file first.
- Plugin release rule: the next minor after the plugins pin the Matrix epic leaves (slash-commands releases v0.2.0,
  Matrix v0.3.0, so v0.4.0 if nothing else lands). If another release landed first, the release and pin tasks are
  amended to the next free minor before they start.
- Orchestrator migration number: the next free one at build time (slash-commands adds 0008, so 0009 if nothing else
  lands); the task is amended to the free number if 0009 is taken.
- No Docker in agent pods: orchestrator DB tests (testcontainers) and the kind e2e run only in GitHub CI; CI on the PR
  is the gate for them.

## Decisions

### D1: The activity feed is removed, not reduced

Decision: `dispatcher/hive.py` stops reading `events` and stops sending appended notes: `_read` no longer queries
`events`; `_Plan.lines`, `_Plan.feed_cursor`, `_Plan.new_cursor`, `HiveState.watermark`, `HiveState.carried`,
`FEED_SETTLE_SECONDS`, `FEED_BATCH`, `FEED_MAX_CHARS` and `_FEED_TYPES` go; `feed.render_feed` goes (no other
caller); `feed.digest_lines`, `FeedLine`, `_clean`, `_status`, `_EDIT_TOOLS` stay as the pure digest of D3.
`session_leaders.feed_cursor` loses its only writer and readers (`hive.py`, `_set_leader`; probed: no view, export or
other reader), so a migration (next free number, 0009 if nothing else lands) drops it. README Hive and the
"Hive state push" paragraph are rewritten; MEMORY records the amendment of hive D9/D23.
Alternatives: keep the column dead (dead code, false single-writer bookkeeping); a digest (option B).
Why: the user's ask; D3 keeps the information reachable.

### D2: `hive_state` is pushed only on structural change

Decision: `state_hash` covers leader, epoch, the member set (pod_name, wrapper_session_id) and `ready`; `state` and
the `context_pct` bucket leave the hash. The rendered text keeps each member's state and context as of the push and
gains one sentence: "Call orchestrator_me for live state and context, orchestrator_activity for what peers did."
The handover hint line becomes unconditional and uses the effective threshold
`max(coalesce(spec.auto_compact_pct, settings.default_auto_compact_pct) - HANDOVER_MARGIN_PCT, 1)`, one helper in
`hive.py` reused by D4.
Alternatives: keep state churn (the second per-turn drain); no `hive_state` at all (option D: a member would report
to the wrong leader).
Why: members must learn a leader change unprompted; everything else is on demand. This amends leader-auto-handover
D14 ("the agent-facing advice stays as it is") on the user's new request.

### D3: On-demand activity: `GET /agent/v1/activity` and the plugin tool `activity`

Decision: route on the agent port (`require_agent`), query `agent` (pod name, optional) and `limit` (1..200, default
50; out of range 422 `invalid_request`). It reads the caller session's newest `events` rows of types `tool_call`,
`tool_result`, `turn_completed` (bounded: the newest 1000 such rows, then ascending), runs
`feed.digest_lines(rows, now(), workdir)` unchanged and returns the last `limit` lines as
`{"lines": [{"id", "agent", "text", "ts"}]}`, oldest first, own lines included; `agent` filters to one pod. Read-only.
Plugin tool `activity` (`GET /agent/v1/activity`, query `agent`, `limit`), description: "What the other agents did
recently (commands with exit status, files written, finished turns): newest last. Call it when you need it; nothing
is streamed to you."
My calls: an `agent` that names no line returns an empty list, not 404, because gone agents' lines are legitimate
history; paths are made relative to the session workdir (`digest_lines`' `workdir` argument); the route serves every
session (as `me` does), while the tool is rendered for hives only (D9); a Bash call younger than
`PENDING_BASH_TIMEOUT_SECONDS` without a result is omitted (it appears once its result is stored); `ts` is the
event's `ts` looked up by line id.
Left to the builder: index use (the existing `events(session_id, id)` path) and the exact row bound, within "bounded".
Why: a bounded pull replaces an unbounded push; the cost lands on the member that asked.

### D4: The limit signal is a keyed note `handover_due` computed in the push pass

Decision: per hive session, when the leader's `agent_status.context_pct` is at or above the D2 threshold, the push
sends the leader only a keyed note `handover_due`. Text: "your context is N% of a limit that compacts at L%; hand
leadership over before that", then candidates best first: `ELIGIBLE` (the `db/eligibility.py` fragment, embedded,
never respelled), not the leader, idle before busy, lowest `context_pct` first, each as
`<pod_name> (<pod_name>/<wrapper_session_id>, idle, 23% context)`, then the D5 protocol in three lines with the
current epoch. With no candidate: "no ready successor; keep leading", plus "scale up with orchestrator_scale" when
the session is scalable. With `spec.peers` false: the D7 no-conversation text. It is re-sent when the leader's 5%
bucket, the candidate identity (the ordered `(pod_name, wrapper_session_id)` list, not their state or context, my
call) or the epoch changes; never below the threshold; a new term starts clean. Tracking is per session in
`HiveState` (dispatcher memory); a restart re-sends one note at most.
Candidates at or above the threshold themselves are left out (my call, open question Q8): handing over to an agent
that is already due would ping-pong leadership.
Alternatives: a wrapper-side threshold (H2); a queued turn (user-visible, queues behind the user); a NOTIFY-driven
push (the 10 s tick suffices).
Why: the gauge, threshold, leader and candidates are orchestrator knowledge; a keyed note is the cheapest carrier
that exists. Third amendment of hive D26: still advice, now targeted.

### D5: The conversation protocol and when leadership flips

Decision (carried by the `handover_due` text and the plugin `leadership_handover` and `me` descriptions; no CLAUDE.md
fragment): the leader (1) finishes the step it is in, reassigns or releases its locks; (2) sends the successor a brief
with `mcp__ccw__send_message(to=<address from the note>, notify_when_idle=true)`: the user's goal, what is done, what
is in flight, open questions to the user, pending user messages, locks and branches; then ends its turn; (3) the
successor may ask back and replies "ready" (or "no" and why); (4) in the turn carrying the reply or the
`<peer-idle-notice>`, the leader calls `orchestrator_leadership_handover(to=<successor>, epoch=<current>,
reason="context")`; (5) the dispatcher applies it at the next pass, bumps the epoch, routes untargeted messages to the
successor, pushes `hive_state` to everyone and the outcome note to the leader (D6). Leadership flips at step 5 only.
With no reply within one further user turn the leader hands over anyway; a `<peer-delivery-failed>` or a send error
means the next candidate.
Alternatives: hand over first and brief after; a synchronous orchestrator-mediated exchange.
Why: the user asked for the two agents to talk; ccw peer turns are that channel, with the notices that detect loss.

### D6: Handover request outcomes reach the requester as a keyed note `leadership_request`

Decision: the push pass reads, per hive session, the `handover` requests decided (`status` applied or rejected)
within the last 300 s (module constant `OUTCOME_WINDOW_SECONDS`, my call) and sends each `from_agent_id`, once per
request id per dispatcher process (tracked in `HiveState`), a keyed note `leadership_request`: "handover request <id>
applied: <pod> leads at epoch N" or "handover request <id> rejected: <reason>" (`not_leader`, `stale_epoch`,
`target_not_ready`, `no_peers`). The applied text names the current leader row at push time, so it is true for an untargeted
request (its row has no `to_agent_id`) and after a later change (my call). `_drain_leadership` sets the push wake after it ran a pass for any session (my call:
no change to `leadership_pass`'s signature); the per-session 10 s throttle still applies. The DB read makes it work
with any number of dispatchers (live: one dispatcher pod, chart default `components.dispatcher.replicas: 1`); a
duplicate keyed note replaces itself in the wrapper inbox.
Alternatives: the leader polls `me` (a silent rejection mid-handoff loses the details); a decided-at column cursor
(a new writer field for a best-effort note).
Why: with the feed gone a rejection would be invisible; the plugin text "the outcome arrives as a hive-state note"
was true only for applied requests.

### D7: Failure modes

- Successor dies before step 4: `ready` flips, `hive_state` and `handover_due` re-push with a fresh candidate list.
- Successor dies after step 4, before the flip: `target_not_ready`, the D6 note, the leader retries another candidate.
- Successor dies after the flip: the lost-leader step (30 s grace), reason `leader_lost`; the ex-leader may re-brief.
- Leader crashes before the transfer: the lost-leader step as today.
- Leader ignores the note and compacts: leader-auto-handover step 5 moves leadership (`compaction`), unchanged.
- `spec.peers` false: the note tells the leader to call `orchestrator_leadership_handover` with a `reason` that
  summarises the state (500 chars); no conversation. The push reads `spec.peers` (default true) to choose the text.
- Both busy: the brief waits in the successor's inbox (32 deep); the leader keeps answering the user.
- Dispatcher restart: `HiveState` is memory; at most one duplicate `handover_due` and the outcomes of the last 300 s.

### D8: What stays from leader-auto-handover: everything

Decision: the `compacting` event, `compaction_at` projection and wake, steps 3 and 5 of the pass, the claim hold, the
reconciler pod hold, the reasons and the UI caption are untouched and remain the backstop. A leader-initiated handoff
is `handover: context` (the existing agent-supplied reason format); no new reason value. `HANDOVER_MARGIN_PCT` keeps
15 and is the one source of the threshold (D2, D4, and through the rendered config the plugin text).
Why: build on the done epic, never duplicate it.

### D9: Repos, release and pins

Decision:
- agents-orchestrator: D1-D6 code, README, MEMORY, tests; `activity` joins `HIVE_TOOLS` after `me`; the rendered
  plugin config carries the effective `auto_compact_pct` (`spec.auto_compact_pct or settings.default_auto_compact_pct`)
  so the plugin advice always shows (fix-as-ac); `any_mcp_plugins_ref` default, dev dependency and README Images move
  to the new plugins tag.
- any-mcp-tatara-plugins: the `activity` tool, new `me` and `leadership_handover` texts (protocol; outcome note), the
  next minor tag (v0.4.0 under the constraint rule), pushed by the orchestrator session after the merge with green CI.
- agents-helmfile: orchestrator chart version and image tag (CI-published merge sha7), `ORCH_ANY_MCP_PLUGINS_REF` to
  the new tag; agent image unchanged (whatever release tag the epics before left).
- Correction to the brief: existing sessions do not keep their old tool list until recreated. Orchestrator README
  Images: "Changing `ORCH_ANY_MCP_PLUGINS_REF` ... changes the config hash and rolls its pods", so the apply rolls the
  agent pods of every running session (listed under Irreversible operations).
Why: the release shape of leader-auto-handover D12 and the plugins release rule.

### D10: Test coverage by layer

Decision: unit and DB tests (`tests/test_hive_push.py`, `tests/test_api_activity.py`, `tests/test_migrations.py`,
the plugin tests) carry D1-D6. The kind e2e replaces the feed assertion of `test_hive_notes_delivered` with the
activity route and "no appended orchestrator note" and adds `activity` to `HIVE_ONLY_TOOLS`. D4 is not in the kind
e2e (my call): the fake claude emits no statusline, so no `context_pct` exists there; D4 is proven by DB tests and
the live proof (D11).
Why: each layer tests what it can produce.

### D11: Smoke and live proof

Decision: the agents-helmfile smoke grows: step 4a also requires `orchestrator_activity` in `--list-tools` (parsed as
JSON), and a step 6a calls `GET /agent/v1/activity` from the agent pod with its own env and requires 200 with a
`lines` array. After the apply the orchestrator session runs a live proof in a throwaway 2-agent hive with
`auto_compact_pct` 20 (threshold 5%, which a fresh leader already exceeds): the leader receives `handover_due`, briefs
the named successor over ccw, the handover is applied with reason `handover: context`, the ex-leader receives
`leadership_request`, and no member receives an unkeyed orchestrator note after the apply. Results go to agents-helmfile
MEMORY.md. Standing rule (user): deploy whenever possible; live applies need no approval.
Why: G5 and the recurring retro finding that deploys need a first-real-use acceptance.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| architecture (fable) | ran 2026-10-27: `.scratchpad/design/hive-decoupling-arch.md` | options C and H1 (brief sec 3) | B digest, D pull only, H2 wrapper threshold, H3 auto handover, H4 summary push (brief sec 3) |
| research-code-internal | ran: the fable discovery (brief sec 1, file:symbol) plus planner probes 2026-10-27 (`grep -rn feed_cursor`, `tests/e2e/test_e2e_kind.py:1124-1157`, `chart/agents-orchestrator/values.yaml:130-131`, `db/export.py:36`, `any_mcp/types.py:72-85` HttpBinding `query`) | `digest_lines` reuse; `HttpBinding(query=...)` for the tool | dropping `events.created_at` (export reads it) |
| research-docs | ran by the architect: https://code.claude.com/docs/en/hooks (2026-10-27): no context-threshold hook, `additionalContext` capped at 10,000 chars | threshold computed from `context_pct` | a hook-based signal |
| research-code-external | skipped: the protocol is the user's own ("both could talk to each other"); no analogue changes it | none | none |
| research-papers | skipped: no algorithmic core | none | none |

## Research inputs

| Finding | Source | Task |
|---|---|---|
| recurring workflow: live apply, smoke, e2e and release tasks run 3-4x the minutes seed; score them higher | RETRO leader-auto-handover, generic-any-mcp-with-git-and | helmfile-apply-live-proof (8), helmfile-smoke-activity (3), orch-e2e-hive-activity (3) |
| recurring workflow: defects per-task review missed (shared deadlines, duplicate predicates); run the duplicate sweep before the last code task merges | RETRO leader-auto-handover, file-editor-with-tabs-and-hi | orch-handover-due-note (ELIGIBLE embedded, pinned in test_eligibility_fragments), helmfile-smoke-activity (reviewer checks each timeout), Review focus |
| recurring workflow: no Docker in agent pods; orchestrator DB tests and kind e2e are CI-only | RETRO leader-auto-handover, file-download-in-file-browse, file-editor-with-tabs-and-hi | every agents-orchestrator task (Notes: CI on the PR is the gate) |
| recurring workflow: `new-task` leaves template sections; write Interfaces, Steps and Notes into each task | RETRO leader-auto-handover | every task (sections filled at plan time) |
| recurring workflow: Harbor prunes sha7 tags; pin by release tag and check tags exist before apply | RETRO file-editor-with-tabs-and-hi, generic-any-mcp-with-git-and | helmfile-deploy-pin (agent image stays a release tag), helmfile-apply-live-proof (ac1 Harbor check) |
| recurring workflow: fakes of shelled-out tools must match a captured real output | RETRO generic-any-mcp-with-git-and | helmfile-smoke-activity (fake kubectl answers the real route JSON shape; `--list-tools` parsed as JSON) |
| recurring workflow: work split across leader sessions loses review rounds | RETRO file-editor-with-tabs-and-hi, leader-auto-handover | none: epic-run orchestrator practice (notes at each task close) |
| code: `_target_ready` omits `wrapper_session_id IS NOT NULL` (READY_STAYS) | RETRO leader-auto-handover | not acted on: candidates use ELIGIBLE (stricter); noted, not doing now |
| reuse: `feed.digest_lines` behind the route | brief Plan inputs reuse | orch-activity-route |
| reuse: push loop, `_note`, `_claim`/`_release` per-agent hash bookkeeping | brief Plan inputs reuse | orch-hive-feed-removal, orch-handover-due-note, orch-handover-outcome-note |
| reuse: `db/eligibility.py:ELIGIBLE` for candidates | brief Plan inputs reuse | orch-handover-due-note |
| reuse: wrapper keyed notes and ccw peer tools (`notify_when_idle`, `<peer-delivery-failed>`) | brief Plan inputs reuse | orch-handover-due-note (note text), plugin-activity-tool (descriptions) |
| reuse: `POST /agent/v1/leadership/handover` with `to` and the epoch fence | brief Plan inputs reuse | orch-handover-outcome-note, helmfile-apply-live-proof |
| reuse: `require_agent`, `_member_id`, `_workdir` | brief Plan inputs reuse | orch-activity-route |
| reuse: `HIVE_TOOLS` ordering; plugin `spec()` helper; fake wrapper notes store | brief Plan inputs reuse | orch-hive-tools-activity, plugin-activity-tool, orch-handover-due-note |
| reuse: leader-auto-handover D12 release shape | brief Plan inputs reuse | plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin, helmfile-apply-live-proof |
| do-not-build: wrapper change, digest stream, auto threshold handover, mediated protocol, new reason or frame, switches, summary push | brief Plan inputs do-not-build | Non-goals |
| fix-as-ac: hint only with `spec.auto_compact_pct` while pods compact at 95 | brief Plan inputs fix-as-ac | orch-hive-feed-removal (hive_state), orch-hive-tools-activity (rendered plugin config) |
| fix-as-ac: plugin text claims the outcome arrives as a hive-state note | brief Plan inputs fix-as-ac | orch-handover-outcome-note, plugin-activity-tool |
| fix-as-ac: `state_hash` re-pushes on busy/idle and 10% context steps | brief Plan inputs fix-as-ac | orch-hive-feed-removal |
| fix-as-ac: README Hive describes the feed note | brief Plan inputs fix-as-ac | orch-hive-feed-removal |
| fix-as-ac: kind e2e feed assertions (F3: `test_hive_notes_delivered`, `HIVE_PUSH_TIMEOUT` comment) | brief Plan inputs fix-as-ac | orch-e2e-hive-activity |
| idea: rate-limit `activity` per agent | brief Plan inputs ideas | rejected for now (Non-goals) |
| idea: pending untargeted count in `handover_due` | brief Plan inputs ideas | rejected: not in D4; noted, not doing now |
| idea: a verifiable "ready" checklist | brief Plan inputs ideas | rejected: no writer for it (brief) |
| facts F1-F5 | brief Plan inputs facts | settled, see Assumptions |
| preference questions 1-7 | brief Plan inputs questions | Open questions Q1-Q7 |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 feed removed | orch-hive-feed-removal, orch-drop-feed-cursor |
| D2 hive_state on structural change | orch-hive-feed-removal |
| D3 activity route and tool | orch-activity-route, plugin-activity-tool, orch-hive-tools-activity |
| D4 handover_due note | orch-handover-due-note |
| D5 conversation protocol | orch-handover-due-note, plugin-activity-tool, helmfile-apply-live-proof |
| D6 leadership_request outcome note | orch-handover-outcome-note, plugin-activity-tool |
| D7 failure modes | orch-handover-due-note, orch-handover-outcome-note |
| D8 leader-auto-handover stays | orch-handover-due-note, orch-e2e-hive-activity |
| D9 repos, release and pins | plugins-release-0-4-0, orch-plugins-pin-0-4-0, orch-hive-tools-activity, helmfile-deploy-pin |
| D10 test coverage by layer | orch-e2e-hive-activity |
| D11 smoke and live proof | helmfile-smoke-activity, helmfile-apply-live-proof |

## Review focus

- `hive.py` claim/release bookkeeping after the feed phase is gone: one failing receiver still retries alone;
  `state_pushed_at` semantics unchanged.
- `handover_due` candidate SQL embeds `eligibility.ELIGIBLE` (never respelled); re-send rule and the "never below
  threshold" rule; the leader is the only receiver.
- The migration dropping `feed_cursor` is idempotent (`DROP COLUMN IF EXISTS`) and the 0003 tests still test 0003.
- The `leadership_request` window and once-per-request tracking: no note for `user` requests, none for requests
  outside the window.
- Note texts are XML-escaped single-line peer data (`feed._clean`) like `hive_state`.
- Duplicate-predicate sweep before the last orchestrator code task merges (recurring retro finding).
- Smoke step deadlines: each new wait has its own deadline.

## Left to the builder

- The activity row bound and index path (D3), within "bounded, newest first, then ascending".
- Exact note wording beyond the phrases the acceptance conditions quote.
- Internal helper names and the `HiveState` field shapes for D4 and D6.

## Assumptions and unknown facts

- F1 settled (planner probe 2026-10-27, read-only `psql` on agents-orchestrator-db-cluster-1): live leaders report
  `context_pct` (claude-code-tatara leader 17, mx-5 leader 7; members 6-36). helmfile-apply-live-proof re-checks it.
- F2 settled (same probe): every live session spec and preset has `peers` true or unset (default true).
- Live `auto_compact_pct`: mx-5 25 (threshold 10%), claude-code-tatara 50 (threshold 35%), preset "facebook chat" 25.
  This bears on Q3.
- F3 settled: `tests/e2e/test_e2e_kind.py::test_hive_notes_delivered` asserts the feed note (`feed_on_reader`), and
  line 78 `HIVE_PUSH_TIMEOUT` mentions the feed settle; `HIVE_ONLY_TOOLS` (line 276) lists the hive tools.
- F4 settled: `feed_cursor` readers are `dispatcher/hive.py`, `db/leadership.py:_set_leader`, and tests
  (`test_hive_push.py` feed tests, `test_leadership_pass.py::test_initial_leader`, `test_migrations.py::test_0003_hive_schema`,
  `test_migrations.py::test_0003_feed_cursor_default`); no view, export or other reader.
- F5 settled: the push loop and the leadership pass run in one `Dispatcher` object (`dispatcher/loop.py:run`); the
  chart default is one dispatcher replica and live runs one dispatcher pod. D6 does not rely on it (DB read).
- The ccw address of an agent is `<pod_name>/<wrapper_session_id>` (render sets `peers.name = ${POD_NAME}`); the live
  proof confirms a send to it is delivered.

## Builder check settlements (2026-10-27)

1. The build starts only after slash-commands-from-chat and matrix-connector-agent-initi have merged; the epic is blocked on them already (my call). The first task, orch-activity-route, makes the orchestrator session read the real next migration number and plugins tag from main and amend the dependent tasks (orch-drop-feed-cursor, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin). Their acceptance conditions hold the placeholders `<MIGRATION>`, `<TAG>` and `<VERSION>` until then; no number is assumed (`0009` and `v0.4.0` elsewhere in this document are only the expectation). The migration test is named `test_drop_feed_cursor_migration`, without the number.
2. The live apply rolls the agent pods of the session that runs it (my call). Before the apply the orchestrator session writes a handoff checkpoint (`workbench:handoff`) naming the apply, smoke and proof steps; the helm apply runs to completion before the reconciler rolls pods; after the roll the resumed leader re-runs smoke and the live proof from the checkpoint. Placed in helmfile-apply-live-proof (step 3, ac8).
3. ac6 of helmfile-apply-live-proof counts only notes posted by the dispatcher (orchestrator-originated), not ccw peer messages (my call).
4. `not_leader` and `stale_epoch` stay as 409 texts; the `leadership_request` note path tests only `target_not_ready` and `no_peers` (my call, intended).
5. "One further user turn" before the leader hands over anyway stays prose in the `handover_due` note (my call, accepted).
6. Staleness of the member lines and push-time candidate ranking in the note are accepted; the mitigation is the "Call orchestrator_me" sentence of the note (my call).
7. The `handover_due` and outcome pass runs on every push tick, outside the `_claim`/`_release` hash path of `hive_state` (my call); orch-handover-due-note states it (requirement and ac11).
8. `events.created_at` stays, per the non-goal (my call).

Q8 (exclude candidates at or above the threshold) stays open for the gate.

## Open questions
- Q1: Remove the activity feed entirely and give members an on-demand orchestrator_activity tool instead of any digest? [recommended: yes]
- Q2: Push hive_state only when the leader, epoch, membership or readiness changes (not on busy/idle or context changes)? [recommended: yes]
- Q3: Threshold for the leader's signal is the effective compaction percentage minus 15, no new spec field (live today: mx-5 compacts at 25% so it is signalled from 10%; claude-code-tatara at 50%, from 35%; default 95%, from 80%)? [recommended: yes]
- Q4: Two-step handoff (brief over ccw peer messaging, wait for the successor's reply, then leadership_handover(to=...)), with the leader free to hand over after one unanswered user turn? [recommended: yes]
- Q5: The leader picks its successor from an advised list (ready, staying, idle first, lowest context); the automatic picks of leader-auto-handover stay free-longest? [recommended: yes]
- Q6: Drop the session_leaders.feed_cursor column in a migration rather than leave it dead? [recommended: yes]
- Q7: Release and deploy in this epic: any-mcp-tatara-plugins next minor after the Matrix epic's pin (v0.4.0 if nothing else lands), orchestrator pins, agents-helmfile bump, apply (rolls every running session's agent pods) and a live handoff proof, same shape as leader-auto-handover? [recommended: yes]
- Q8: Leave out of the handover_due candidate list any agent already at or above the threshold, so leadership does not ping-pong between agents that are both due? [recommended: yes]

## Irreversible operations in scope

- Tag `v0.4.0` (or the next free minor under the release rule) pushed on the any-mcp-tatara-plugins merge commit
  (task plugins-release-0-4-0, orchestrator session, after green CI; covered by G5 and Q7).
- Migration dropping `session_leaders.feed_cursor` (0009 or the next free number) applied to the live orchestrator
  database by the deployed orchestrator: a data deletion of bookkeeping values, forward only (task
  orch-drop-feed-cursor, applied in helmfile-apply-live-proof; covered by G1 and Q6).
- `mise run apply` on the live namespace (task helmfile-apply-live-proof, orchestrator session only, after `mise run
  diff` shows only the pins): the orchestrator pods roll, and the plugins ref and on-start change roll the agent pods
  of every running session (mx-5 and claude-code-tatara included). Standing user rule: live applies need no approval.
- PR merges to `main` of agents-orchestrator, any-mcp-tatara-plugins and agents-helmfile (main stays green).

## Build-time settlements (2026-10-29, tatara-0)

- (my call) slash-commands-from-chat is dropped as a blocker: it is parked, owned by hive cct2 (split agreed 2026-10-28), and its branch is 46 commits behind orchestrator main. Waiting would stall this epic indefinitely; whichever epic merges second renumbers its migration and rebases onto the other. Matrix (the other blocker) is done.
- Migration number assigned at merge (agreed with cct2 via mx-34 msg 337): planned 0011 because slash-commands-from-chat claims 0010; the first epic to merge to orchestrator main takes 0010, the second renumbers to the next free one in its rebase and amends its own tasks and migration test.
- Plugins release v0.4.0 (confirmed by mx-34 msg 339): slash-commands keeps v0.3.0 (user pre-approved); this epic may tag v0.4.0 when plugins-release-0-4-0 is ready, under the standing approval, even before slash releases.
- Task slugs keep their historical names (plugins-release-0-4-0, orch-plugins-pin-0-4-0).
