# hive-self-close: plan delta, inactivity limits

Status: Approved 2026-11-02 by the user (mx-99 #919, chat m184: 'Go for preset and inactivity. Put
into the hive which can pick it up faster'). Every Recommended option accepted. Assigned to
claude-code-tatara-2. Not yet built.

Coordination notes:
- Starts only after hive-self-close merges (orchestrator branch `hive-self-close`, migration 0026,
  owned by claude-code-tatara-1). It builds on that branch's `close_requested_at` and
  `close_reason` columns and the autoclose sweeper.
- Orchestrator migrations take the next free number at merge time, 0029 or later (0028 is claimed
  by session-orchestration-mcp; `migrate.py` is set-based, never reuse a number). Wherever this
  plan says 0028, read "next free number at merge". The delivery vehicle is the follow-up branch
  `hive-inactivity-limits` (Q11 b), so the "extend the unmerged 0026" alternative does not apply.
- Versions are the next free minor at merge, whatever this plan names.
- agent-preset-editing (`docs/future/agent-preset-editing.md`) is a separate plan; its small
  first step should go first.
- The "Date" and "Status of the base item" lines below are as of 2026-11-02 when the plan was
  written; the worktree paths there are the planning hive's and may not exist for the builder.

Date: 2026-11-02. Delta to `docs/plans/hive-self-close/plan.md` (spec) and `implementation.md`.
Status of the base item: orchestrator O1-O6 and web W1-W2 done and reviewed, unmerged
(`.worktrees/hive-self-close/agents-orchestrator` HEAD `84264db`, not pushed; ledger
`.superpowers/sdd/implementation-hive-self-close/progress.md`). This delta is a human gate: nothing
below is built until the questions at the end are answered.

The user's addition, verbatim: "With agents able to close their own hives I also want to set two
limits instead of one:
* gentle reminder- after some inactivity time agent will politely asked to either post updates more frequently or free its hive resources
* hard limit- hive is terminated externally, agent can do handoff (doesn't have to), then hive is closed"

## 1. What and why

Today one silent limit exists for "the session is no longer doing anything useful":
`spec.discard_after_idle_seconds`, which discards an idle session with no word to the agent and
never touches a busy one, plus the creation-based `autoclose_after_seconds`. Now that a leader can
close its own session (`orchestrator_self_close`), the orchestrator can ask it to, and only use
force when asking did not work:

1. Reminder: after `reminder_seconds` without a user-visible update, the orchestrator sends the
   session's leader one polite message: post a progress update, or report and call
   `orchestrator_self_close`.
2. Hard limit: after `close_seconds` without a user-visible update, the orchestrator requests the
   close itself (the same `close_requested_at` path as a self-close), tells the leader it has a
   handoff window, and discards the session when the leader's turn ends plus the close grace, or at
   the end of the window even mid-turn. The handoff is optional. The user can still press "Keep
   session".

Both limits have a global default (settings, helmfile values) and a sparse per-preset override
(web preset form), the same shape as `usage_quota` over `ORCH_USAGE_QUOTA_DEFAULT`.

## 2. Research findings

Verified 2026-11-02 in the worktree (`84264db`) and agents-orchestrator `origin/main` (`2ff61fa`,
PR #58 merged). Paths under `src/agents_orchestrator/` unless named.

Versions and migrations:

- Tags: orchestrator latest `v3.5.0`; agents-web `v0.15.2`; any-mcp-tatara-plugins `v0.11.0`.
- origin/main migrations end at `0024_agent_permission_mode_state.sql` then `0027_labels.sql`
  (0010 is an old gap; 0025 and 0026 are absent on main). `0025_cache_sweep_settings.sql` is on the
  unmerged branch `cache-retention-settings`; `0026_session_close_request.sql` is on this unmerged
  branch. `migrate.py` applies by set, so 0025/0026 apply after 0027 (tatara-2 #842). Next free
  number: **0028**. No remote branch carries 0028 or higher; no local worktree does either.

Existing limits:

- `spec.autoclose_after_seconds` `spec.py:653` (1 to 2592000; floor `ORCH_AUTOCLOSE_MIN_SECONDS`
  `settings.py:157`, check `spec.py:1033-1040`), counted from `created_at`; swept by
  `close_expired` `db/sessions.py:337`; shown as `closes_at` `api/sessions.py:80-82`; in the web form
  (`agents-web src/presets/PresetForm.tsx:386`, `src/sessions/sessionSpecForm.ts:226,395,469`) and
  used by the helmfile smoke test (`agents-helmfile tests/test_smoke_script.py:789`). A lifetime
  cap, not an inactivity rule.
- `spec.discard_after_idle_seconds` `spec.py:654-656` (60 to 2592000, unset = off), API only: not
  in the web form, not used by any other repo (grep of `code/*` and the helmfile). README
  "Idle discard" `README.md:439`.
- Idle predicate `_IDLE_PREDICATE` `db/sessions.py:363-385`: live agent, all idle, no turn, no
  attention, no queued/dispatching/verifying message, init not running; clock `GREATEST` of
  creation, `free_since`/`waiting_since`, turn start/end, message created/dispatched, init
  start/finish, `close_requested_at`. Threshold `_IDLE_THRESHOLD` `db/sessions.py:359-362` =
  `LEAST(grace if close requested, spec idle)`. `discard_idle` `db/sessions.py:389-421` locks the
  row `FOR UPDATE` then re-checks. The idle clock measures "nothing running", not "nothing said to
  the user": a busy agent silent for hours is never idle.
- Sweeper `api/autoclose.py:17-29`: every 10 s, `close_expired` then `discard_idle(grace)`;
  started at `api/app.py:72-73` with `settings.close_grace_seconds` (`settings.py:160`, default 30).
- Self-close (this branch): `request_close` `db/sessions.py:302` (first request wins),
  `cancel_close` `db/sessions.py:321`, `POST /agent/v1/close` `api/agent.py:192-226`
  (`own_session` 422 for superleaders), `DELETE /api/v1/sessions/{id}/close`
  `api/sessions.py:494`, `SessionView.close_requested_at/close_reason` `api/schemas.py:142-143`,
  export `db/export.py:64`. `close_reason` is free text from the agent; nothing records who closed.

Messaging the leader:

- `queue.enqueue_message` `db/queue.py:135-186` is the one insert path (api only), share-locks the
  session row, raises `SessionBeingDeleted`. An untargeted message routes to the leader
  (`db/queue.py:422-425`). Lanes (`0012_message_lane.sql`): `idle` waits for a free agent,
  `regular` is typed into the running turn, `priority` interrupts; `_PICK_LIVE`
  `db/queue.py:337-351` lets the wrapper refuse `busy`/`dialog_open` itself (no text typed into a
  permission dialog).
- Precedent for an orchestrator-written message: the self-restart note `api/admin.py:295-307`
  (`enqueue_message(..., lane="priority", held=True)`, plain text "This restart was
  self-initiated..."). Nothing marks it as orchestrator-written; the web shows it like a user
  message.
- Wrapper notes (`dispatcher/hive.py`, `wrapper/client.py:223`) are not usable: enabled only for
  hives (`k8s/render.py:384`) and delivered only on `UserPromptSubmit`/`PostToolUse` hooks
  (`claude-code-wrapper README.md:2609`), so an idle leader never sees one.
- No "Task T-<n> was updated" notice exists in the orchestrator (grep of src and docs); the
  taskboard relay `api/tasks.py` stores nothing. Session messages are framed by
  `dispatcher/session_frame.py:13-19`.

Activity signals available:

- `turns` (`started_at`, `completed_at`, `final_text`, `origin`; `0001_init.sql:63-72`), linked to
  the message they carried by `messages.turn_id` (`db/queue.py:574-579` `mark_sent`).
- `messages.created_at`, `dispatched_at`, `sender_session_id` (peer session messages, index on
  `(sender_session_id, created_at)` `0007_session_messages.sql:5-9`). User (web), trigger (service
  port) and Matrix connector messages are indistinguishable (`api/messages.py:80-111`).
- `events` with `ACTIVITY_TYPES` tool_call/tool_result/turn_completed `db/events.py:17`: tool
  activity, not user-visible.
- Chat relay `POST /agent/v1/chat/messages` `api/chat.py:121-129` (leader only, upstream is the
  Matrix connector's agent listener, README:102) and taskboard relay writes
  `api/tasks.py:122-160` (any agent): user-visible, but the relays store nothing, so the
  orchestrator has no record of them today.
- Prod has both upstreams wired (`agents-helmfile helmfile.yaml.gotmpl:86-89`).

Settings vs per-preset precedence:

- `usage_quota` is the precedent for "global default plus sparse override": `UsageQuota`
  `spec.py:619-625` (each metric unset = default), `ORCH_USAGE_QUOTA_DEFAULT` `settings.py:244`,
  resolved live at use (`api/sessions.py:328,665`), exposed in `/meta` (`api/sessions.py:249`) and
  shown by the web as "Empty uses the default (N%)" (`PresetForm.tsx:390-394`).
- `kube_access` / `docker` are sparse booleans gated by a setting (`spec.py:664-672`,
  `spec.py:991-993`); `auto_compact_pct` falls back to `default_auto_compact_pct`
  (`dispatcher/hive.py:98-100`). Presets stay sparse: unset fields are not stored.

## 3. Design

### 3.1 Configuration

Settings (api), resolved live by the sweeper so a helmfile change applies to running sessions:

| Env | Default in code | Meaning |
|---|---|---|
| `ORCH_INACTIVITY_REMINDER_SECONDS` | `0` (off) | quiet time before the reminder; 0 = off |
| `ORCH_INACTIVITY_CLOSE_SECONDS` | `0` (off) | quiet time before the hard limit; 0 = off |
| `ORCH_INACTIVITY_HANDOFF_SECONDS` | `300` (0 to 3600) | handoff window after the hard-limit notice |

helmfile values enable them: reminder `3600`, close `14400`, handoff `300` (Q4). Settings
validation: when both are non-zero, reminder < close.

Spec, sparse like `usage_quota`: `spec.inactivity: InactivityLimits | None` with
`reminder_seconds: int | None` and `close_seconds: int | None` (each `0` = off for this preset,
else 60 to 2592000; unset = the setting). Validation: effective reminder < effective close when
both are on (422 `invalid_request` naming the field). Effective value =
`COALESCE(spec.inactivity.x, setting)`, computed in SQL by the sweeper and in Python for the view.
The handoff window is global only (no per-preset knob).

`/meta` gains `inactivity {reminder_seconds, close_seconds, handoff_seconds}`. Web preset form:
two number fields "Reminder after quiet seconds" and "Close after quiet seconds", helper text
"Empty uses the default (1 h); 0 turns it off", next to "Autoclose after seconds".

Superleader sessions (`spec.session_messaging`) are exempt from both limits (Q8): they cannot
self-close (422 `own_session`) and the user manages them.

### 3.2 What counts as inactivity (recommended: time since the last user-visible update)

Candidates considered:

- (a) No turn or tool activity: the existing idle clock. Misses the case the user names: a busy
  agent that says nothing for hours.
- (b) No chat post or status update to the user: right signal, but alone it ignores the web user,
  who reads turn answers in the web chat, not Matrix.
- (c) Wall-clock since the last user-visible update, where "update" is defined below.
  **Recommended.**

The quiet clock (`last_update`) is the latest of:

1. `sessions.created_at`;
2. `sessions.last_update_at` (new column, api-written): a 2xx chat relay `POST /messages`, a 2xx
   taskboard relay write (`POST`, `PUT`, `PATCH`), a user "Keep session" (cancel), and the
   migration time for sessions that exist at deploy;
3. creation of an inbound message that is not an orchestrator notice (user, trigger, connector,
   peer session): someone engaged with the session;
4. `completed_at` of a turn that carried such a message (`messages.turn_id`): the answer the user
   or caller reads;
5. creation of a message this session's leader sent to another session
   (`messages.sender_session_id = s.id`): an update to an orchestrating superleader.

Not counted: tool calls and events, chat reactions, wrapper notes, turns that carried only a
notice (the reminder reply alone does not extend the session; the agent must post or close).

### 3.3 Reminder

Sweeper step `remind_inactive` (new, `db/sessions.py`), per candidate under the row lock with a
re-check, like `discard_idle`. Fires when: `desired='active'`, not a superleader, no close pending,
effective reminder on, `last_update + reminder <= now()`, `inactivity_reminded_at IS NULL OR
inactivity_reminded_at < last_update` (once per quiet period, Q5), and no live agent has attention
(`waiting_since`: the agent is waiting on a person, a nudge cannot help). It sets
`inactivity_reminded_at = now()` and enqueues one untargeted `regular`-lane message with
`notice = 'inactivity_reminder'` in the same transaction (an idle leader gets a turn; a busy one
gets it typed into its turn at the next tool boundary; an open dialog makes the wrapper refuse and
the queue retries).

Wording (one paragraph, durations humanised, times UTC; the update-tool sentence names only the
tools whose upstream is configured):

"Orchestrator notice (inactivity reminder): this session has sent no update to the user for 1 h
(last update 2026-11-02 10:00Z) while holding 3 agent pods and a session slot. If the work is
still going, please post a short progress update now with orchestrator_chat_send or a comment on
your task (orchestrator_task_comment), and keep posting at least hourly. If the work is done or
blocked, report it and call orchestrator_self_close to free the hive. Without an update the session
will be closed at about 2026-11-02 14:00Z, with 5 minutes to hand off. Replying here alone does not
count as an update."

### 3.4 Hard limit

Sweeper step `close_inactive` (new). Fires when: `desired='active'`, not a superleader, no close
pending, effective close on, `last_update + close <= now()`. Attention does not block it (a session
waiting forever on an absent user is exactly what it frees). In one transaction under the row lock
with a re-check:

- `close_requested_at = now()`, `close_kind = 'inactivity'`,
  `close_reason = 'No update for 4 h (inactivity limit 14400 s)'`,
  `close_deadline_at = now() + handoff_seconds`;
- one untargeted `regular`-lane message, `notice = 'inactivity_close'`:

"Orchestrator notice (inactivity limit): this session has sent no update to the user for 4 h, so
the orchestrator is closing it. You may hand off before it closes, you do not have to: post a final
status (orchestrator_chat_send or a task comment) and, since this session saves its workspace,
write handoff notes into the workdir. The session is discarded 30 s after your turn ends, or at
14:05Z even mid-turn. Only the user can keep it."
(The workdir sentence appears only when the view's `backup.workdir` is true.)

Discard: the existing `discard_idle` flips it once idle plus `ORCH_CLOSE_GRACE_SECONDS` (unchanged
self-close path). New step `close_overdue` flips `desired='deleting'` for
`close_deadline_at <= now()` regardless of idleness (lock, re-check, `desired='active'` guard). A
mid-turn agent at the deadline is quiesced by the reconciler's normal discard (`_quiesce` scales the
StatefulSet to 0): the turn is lost, the transcripts and workdir follow the cache rules. Logs:
`inactivity: session <id> reminded`, `inactivity: session <id> closing, deadline <t>`,
`inactivity: session <id> deadline passed, discarding`.

Extension: the agent cannot extend (no tool, Q7). The user's "Keep session" (existing
`DELETE /api/v1/sessions/{id}/close`) cancels: `cancel_close` also clears `close_kind` and
`close_deadline_at` and sets `last_update_at = now()`, so the quiet clock restarts and the hard
limit does not refire on the next poll. An inbound non-notice message created after an
`inactivity` close request cancels it the same way (Q10): `close_overdue` and `discard_idle` skip
such a session and `close_inactive`'s pass clears it first. A self-close requested by the agent
(`close_kind = 'self'`) is unchanged: messages only delay it.

If the leader calls `orchestrator_self_close` during the window, `request_close` keeps the first
request (`already_requested: true`), so the inactivity record and deadline stay; it closes at turn
end plus grace as before.

### 3.5 Relation to `autoclose_after_seconds` and `discard_after_idle_seconds`

- `autoclose_after_seconds`: kept unchanged. It is a lifetime cap from creation (smoke test, web
  form), orthogonal to inactivity.
- `discard_after_idle_seconds`: replaced by `inactivity.close_seconds` (Q3), no alias, no shim
  (housekeeping rule 2). Migration 0028 moves stored values in `presets.spec` and `sessions.spec`
  (`spec - 'discard_after_idle_seconds' || jsonb_build_object('inactivity',
  jsonb_build_object('close_seconds', <value>))`), the field leaves `SessionSpec` (extra=forbid
  then refuses it with 422) and README "Idle discard" is rewritten as "Inactivity limits".
  `_IDLE_THRESHOLD` shrinks to the grace of a pending close. Behaviour change for migrated
  presets: a busy-but-silent session is now closed too, after a notice and the handoff window.

### 3.6 Audit

- `sessions.close_kind text CHECK (close_kind IN ('self', 'inactivity'))`, set with
  `close_requested_at` (`request_close` writes `'self'`), in `SessionView`, the stream and the
  discard-hook export `session` record (after `close_reason`).
- `close_reason` for the hard limit is the orchestrator's text above; for a self-close the agent's.
- `sessions.inactivity_reminded_at` in the view and export.
- `messages.notice text CHECK (notice IN ('inactivity_reminder', 'inactivity_close'))`, in
  `MessageView` and the `message` export records, so the web renders notices as system lines and
  the clock excludes them.
- `SessionView` adds `last_update_at` (the computed quiet clock), `reminder_at` and
  `inactivity_closes_at` (null when off or superleader), and `close_deadline_at`.

### 3.7 Data and versions

Migration `0028_inactivity_limits.sql` (next free on origin/main; re-check at implementation,
rename on collision):

```sql
-- Inactivity limits (hive-self-close delta). Written only by the api.
ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS last_update_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS inactivity_reminded_at timestamptz,
    ADD COLUMN IF NOT EXISTS close_kind text,
    ADD COLUMN IF NOT EXISTS close_deadline_at timestamptz;
-- plus close_kind CHECK, backfill close_kind = 'self' where close_requested_at IS NOT NULL,
-- messages.notice with its CHECK, and the discard_after_idle_seconds spec rewrite (idempotent).
```

`last_update_at DEFAULT now()` fills existing rows with the migration time, so a deploy does not
remind or close every long-lived session at once: the quiet clock of every live session starts at
the deploy. Shipped as a follow-up branch (Q11 b) this is a new 0028; shipped on this branch
(Q11 a) the same statements could extend the unmerged 0026 instead.

Releases: orchestrator next free minor (v3.6.0 if self-close ships first, else together), web next
free minor (v0.16.0), helmfile values plus pins. any-mcp-tatara-plugins: no change (the reminder
text names existing tools). Allow list unchanged, so this delta does not roll live sessions; the
helmfile env change rolls only the orchestrator api.

## 4. Tasks to add to implementation.md (outline)

- O7 (sonnet): migration 0028 (columns, CHECKs, backfill, spec rewrite), `InactivityLimits` in
  `spec.py` with validation, removal of `discard_after_idle_seconds`, three settings, `/meta`
  `inactivity`; tests `test_migrations.py`, `test_spec.py`, `test_settings.py`, `test_presets*`.
- O8 (opus): `db/sessions.py` quiet-clock SQL fragment, `remind_inactive`, `close_inactive`,
  `close_overdue`, `request_close(kind=...)`, `cancel_close` extensions, inbound-message cancel,
  `_IDLE_THRESHOLD` simplification; `api/autoclose.py` wiring and log lines; notice texts module.
  Race tests: message vs close, Keep session vs deadline flip, reminder once per quiet period.
- O9 (sonnet): relays touch `last_update_at` on 2xx (`api/chat.py` POST messages, `api/tasks.py`
  writes); view fields, `MessageView.notice`, export columns, README ("Inactivity limits", env
  table, Self-close, session view, message view), `openapi.json`, MEMORY.md.
- W3 (sonnet): schema sync, preset form fields with `/meta` defaults, `sessionSpecForm.ts`
  mapping and validation; vitest.
- W4 (sonnet): chat renders `notice` messages as orchestrator lines; `ClosingBanner` and the tab
  line show the inactivity kind with the deadline ("Closing for inactivity at 14:05Z"), "Keep
  session" unchanged; optional "quiet for 2 h, reminder sent" in the tab line; vitest.
- H3 (sonnet): `values/agents-orchestrator/common.yaml` env `ORCH_INACTIVITY_*`, release pins,
  `tests/test_orchestrator_release.py`; live check at deploy with short per-preset limits
  (reminder 120, close 300) on a test preset.
- Stops: LEADER STOP for the user's answers to this delta before O7; existing stops otherwise.

## 5. Risks

1. Mass reminders or closes at deploy: prevented by `last_update_at DEFAULT now()` backfill and
   code defaults off; pinned by a migration test.
2. A busy agent killed at the deadline loses its turn: accepted for a hard limit; the notice says
   so and gives 5 minutes; least destructive lane (`regular`, not `priority`).
3. Token cost: the reminder starts a turn on an idle leader. Once per quiet period only.
4. Gaming: an agent posting empty chat messages to stay alive. Visible to the user in Matrix;
   reactions excluded. Accepted.
5. Peer ping-pong between two sessions keeps both alive (inbound peer messages count). Bounded by
   the existing pair rate limits (`session_message_pair_max_per_hour`). Accepted.
6. Chat or taskboard upstream unconfigured: the agent can only update via turn answers to user
   messages; the notice names only configured tools, so the agent's real choice is self-close.
7. Migrated `discard_after_idle_seconds` presets change behaviour (busy sessions are now covered).
   Named in the release notes and MEMORY.md.
8. Sweeper load: three more statements per 10 s poll over active sessions with per-session
   subqueries on `messages` and `turns`, the same shape as the idle predicate. Fine at
   `ORCH_MAX_SESSIONS` 20.
9. Migration numbering collision with cache-retention-settings 0025 or a new main migration:
   re-check and rename before commit (as H-R1).

## 6. Scope, MVP to complete

- MVP: settings only (no per-preset override, no web form), quiet clock = existing idle clock,
  one reminder per idle period, hard limit = existing silent discard after the close threshold (no
  notice), `discard_after_idle_seconds` kept, audit by reason text, superleaders exempt.
- Recommended (this delta): section 3 as written: settings default plus sparse `spec.inactivity`
  with web form, quiet clock of user-visible updates, one reminder per quiet period, hard limit
  with notice, 5-minute handoff window and deadline, user Keep session and inbound messages cancel,
  `discard_after_idle_seconds` replaced, `close_kind`/`notice`/`inactivity_reminded_at` audit,
  shipped as a follow-up branch after self-close.
- Complete (noted, not doing now): per-preset handoff window, an agent "extend" tool with a cap,
  repeat reminders at a configurable interval, a superleader-facing "close child for inactivity"
  relay, quiet-time charts in the web.

## 7. Decisions (user, 2026-11-02)

The user accepted every Recommended option. Rejected options, one line each.

1. What counts as inactivity: (c) wall-clock since the last user-visible update: inbound
   message, the answer turn to it, a chat post or task write, a message to another session,
   Keep session; notice-only turns excluded. Rejected: (a) time since the last turn or tool
   activity, the existing idle clock (MVP); (b) last chat post or task update only.
2. Where the limits are configured: (c) global settings default plus sparse per-preset
   `spec.inactivity` override, in the web preset form. Rejected: (a) global settings only (MVP);
   (b) per preset only.
3. `discard_after_idle_seconds`: (b) replace it with `inactivity.close_seconds`, migrating
   stored values, no alias. Rejected: (a) keep it as a separate silent idle discard (MVP).
4. Defaults: (a) code defaults off; helmfile enables reminder 1 h, close 4 h, handoff 5 min (MVP
   and Recommended). Rejected: (b) code defaults on with those values; (c) other numbers.
5. Reminder repeat policy: (a) once per quiet period; the hard-limit notice is the second contact
   (MVP and Recommended). Rejected: (b) every `reminder_seconds` until an update or the hard
   limit.
6. Hard-limit flow: (b) `regular`-lane notice, 5-minute handoff window, close at turn end plus
   grace or at the deadline even mid-turn. Rejected: (a) no notice, silent discard through the
   existing path (MVP); (c) as (b) with a `priority`-lane notice that interrupts the running turn.
7. Who may extend after the hard limit fires: (b) only the user, with the existing "Keep session"
   (restarts the quiet clock) (MVP and Recommended). Rejected: (a) nobody; (c) the user and the
   agent via a new extend tool with a cap.
8. Superleader sessions: (a) exempt from both limits (MVP and Recommended). Rejected: (b) reminder
   only; (c) same limits as every session.
9. Audit: (b) `close_kind` column, `inactivity_reminded_at`, `messages.notice`, all in the view,
   the export and the web. Rejected: (a) reason text only, prefixed "Inactivity limit:" (MVP).
10. An inbound user or trigger message during the handoff window: (b) it cancels the inactivity
    close and restarts the quiet clock. Rejected: (a) only "Keep session" cancels; the message
    waits and the close proceeds (MVP).
11. Delivery vehicle: (b) follow-up branch `hive-inactivity-limits` after self-close merges, with
    a new migration (see the coordination notes for the number). Rejected: (a) same branch and
    release as hive-self-close, one migration 0026 extended (MVP).
