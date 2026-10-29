# Immediate message delivery with per-message priority design

## Summary

A message sent to a session whose leader is busy no longer waits for idle: the orchestrator
dispatches it at once and the wrapper pastes it into the running turn, carrying that turn's own
marker plus a per-paste merge marker, so Claude Code queues it internally and the running turn
absorbs it (D3). The message joins the running turn and shares its final answer; the wrapper
records each merged paste on the turn record and confirms it from the transcript (D5). A Stop with
a paste still unconfirmed waits a bounded time for it (D6). Every message carries `priority`:
`immediate` (default) or `idle` (today's wait-until-idle) through the orchestrator API, the
superleader's `session_send`, the ccw peer `send_message`, the wrapper `POST /turns` and a web
composer toggle (D1). Slash commands are unaffected (D8). The Matrix connector stops holding a
room's new messages behind its running run (D18). A real-binary probe of Claude Code 2.1.304
comes first and may amend later tasks (D11). Releases: wrapper 0.5.0, plugins 0.5.0, agents-common
0.4.0; the orchestrator and the connector pin them; deploy is decided at the gate (D19). Cost of
the priority option alone (the user's "maybe"): about 13 of the epic's 65 points (tasks
orch-priority-column, orch-session-send-priority, plugin-session-send-priority,
web-sync-message-priority, web-composer-send-when-idle and the `priority` legs of the wrapper and
peer tasks); flagged at the gate as Q10.

## Intent and why

User (2026-10-28 21:02Z via mx-34 #262), verbatim: "Improvement idea to messaging system- currently
the messages wait for too long. Ask agents to queue another epic- message should get through PTY
immediately and let either Claude Code or even agent queue them internally." Scope addition
(21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default
reaching instantly, option to wait until idle)".

Today a message waits at four places for an idle leader: the orchestrator pick (`db/queue.py:_PICK`
needs `state = 'idle'` and `free_since > last_dispatched_at`), the busy-leader hold of
`_claim_in_session` (every later untargeted message waits, FIFO), the wrapper's 409 `busy`
(`Session.check_submittable`) and, for Matrix, the connector's `rooms_ready`, which claims no new
row of a room while its run is in progress (cartographer brief section 1). A long agent turn
therefore holds every message for its whole length. Claude Code already queues input submitted
while it works and hands it to the model at the next tool boundary within the same turn, or sends
it right after the turn (docs brief A1, A2). The wedge of 2026-10-28 (debug record) showed the
same mechanism by accident; the 0.3.3 parser fix made it safe to rely on.

## Goals

- G1: a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and
  Claude Code queues it internally; by default no message waits for the leader to go idle.
- G2: each message carries a priority, immediate (the default) or idle (today's behaviour),
  settable from the web composer, the orchestrator messages API, the superleader's session_send
  and the ccw peer send_message.
- G3: a message delivered mid-turn never wedges the session: the running turn still ends on its
  Stop, and the message is linked to the turn that answered it (hop guard, delivery verifier).
- G4: Matrix chat messages in a room whose run is in progress are delivered at once, and an answer
  shared by merged messages is relayed to the room once.
- G5: slash commands keep running at the turn's Stop whatever the priority; nothing is pasted while
  a command runs or a dialog is open.
- G6: how Claude Code 2.1.304 treats input pasted mid-turn is probed on the real binary and
  recorded before the wrapper relies on it.

## Non-goals

- No new `messages.status` value for "answered"; it stays derived from the linked turn
  (`views._MESSAGE_SELECT`).
- No delivery through the notes channel (hive only, newline-collapsing, throttled, tool-boundary
  only), Claude Code's native cross-session messaging (frames text as peer-originated) or queue
  keystrokes (Ctrl+Enter send-now, Ctrl+X chords, Up take-back; terminal-dependent, docs A6, A7).
- No slash command typed mid-turn; Claude Code's own immediate commands (slash epic Q2) stay out.
- No orchestrator stale-busy detector and no wrapper turn watchdog (debug record follow-up; retro
  matrix-connector-agent-initi tech debt): noted, not doing now.
- No agents-helmfile pin, apply or smoke task (Q9).
- No priority control in Matrix, webhook or schedule: they post `{text}` and take the server
  default (Q3).
- No change to `limits.turn_max_seconds`: it keeps counting from the first submit (wrapper MEMORY
  2026-10-28), so merged messages do not extend a bounded turn.

## Anti-goals

- A mid-turn paste carrying a new turn id marker: `Router._last_marker` would move and the running
  turn's Stop would be dropped as stale, the 2026-10-28 wedge in reverse. Pinned by a test (D3).
- A Stop that never completes the running turn because a merged paste was never seen: the defer is
  bounded (D6).
- Text pasted while a slash command runs, while the turn is in its command phase or while a dialog
  is on screen (a CR answers a dialog, probe outA of the slash epic).
- An unbounded number of pastes into one turn (flood): capped, 429 (D4).
- An ambiguous send resent after it was merged (duplicate delivery): the verifier recognises merged
  deliveries (D14).
- The same final answer relayed twice to a Matrix room (D18).
- A backward-compatibility shim (Housekeeping rule 4): no alias for the old behaviour beyond the
  `idle` priority the user asked for.

## Constraints

- Python only (wrapper, orchestrator, plugin, agents-common, connector); TypeScript for agents-web.
- Services talk only through HTTP; `messages` keeps one writer per transition, every status change
  a guarded UPDATE in `db/queue.py`; the connector's `inbound` and `runs` likewise.
- Built on the merged slash-commands-from-chat epic (README blocker): its command queue held until
  Stop (D9), `_PICK_COMMAND` and the per-session order rule (D10), `DialogScanner` (D7), migration
  0010 and wrapper 0.4.0, plugins 0.3.0. Built on hive-decoupling (README blocker): migration 0011,
  plugins 0.4.0 and its orchestrator plugin pin. This epic therefore takes migration 0012, wrapper
  0.5.0, plugins 0.5.0; when a number is taken at build time the task takes the next free one and
  the orchestrator amends its `files`.
- Wrapper tests use the fake claude (`tests/fake_claude/fake_claude.py`), never a real claude; only
  the probe task (wrapper-midturn-probe) runs the real binary, in a throwaway dir under
  `/workdir/workdir/.scratchpad/probe-midturn`; only wrapper-fake-claude-queue edits
  `tests/conftest.py`.
- Generated files are regenerated, never hand-edited: orchestrator `openapi.json`
  (`uv run python -m agents_orchestrator.api.openapi > openapi.json`), agents-web
  `src/api/schema.d.ts` (`npm run sync:api -- orchestrator`).
- Claude Code pin 2.1.304 (`code/claude-code-wrapper/Dockerfile:21`). The transcript format is
  internal and unstable (docs A9); every rule here is verified at 2.1.304 only.
- Environment of this container (as the slash epic's Constraints): orchestrator and connector
  Postgres tests need Docker and run in CI; wrapper `tests/test_manager.py::test_shutdown_stops_all`,
  `tests/test_pty_proc.py::test_exit_without_eof_still_fires` and
  `tests/test_pty_proc.py::test_close_terminates_group_then_kill` fail here (PID 1) and are
  deselected; agents-web verifies name the chat test files only (10 load-dependent timeouts).
- agents-web design rules (`src/layout/designRules.ts`): no colour literals outside `theme.ts`, no
  arrows or decorative Unicode.

## Decisions

### D1: one `priority` field, `immediate` by default, `idle` on request

Every message route takes an optional `priority`: `"immediate"` (the default) or `"idle"`. Routes:
orchestrator `POST /api/sessions/{id}/messages` (`schemas.PostMessage`), the agent route
`POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:SessionMessageIn`), `MessageView.priority`,
the plugin `session_send` param, the ccw peer `send_message` param and the wrapper
`POST /v1/sessions/{id}/turns` (`TurnRequest.priority`). `idle` is exactly today's behaviour: it
waits for an idle leader and the wrapper refuses it with 409 `busy` while a turn runs. The wrapper
default is `immediate` too (Q8), and the orchestrator always sends the field explicitly. The web
composer shows a "Send when idle" toggle, off by default (D16).
Alternatives: a boolean `wait_until_idle` (does not extend to more levels); separate endpoints per
priority (doubles every route); naming `delivery` (the user said "priority").
Why: the user asked for "priority meta to messages (by default reaching instantly, option to wait
until idle)". Names and values are Q2.

### D2: the channel is the PTY paste the wrapper already uses

The wrapper writes the message with its existing `PtyProcess.send_prompt` (bracketed paste, then CR
after `boot.submit_delay_seconds`, under the PTY lock, so no other writer interleaves). Claude Code
queues text submitted while it works (docs A1) and passes it to the model at the next tool
boundary or after the turn (A2).
Alternatives: the notes channel (hive only, collapses newlines, throttled, delivered only at tool
boundaries, lost from accounting when the turn makes no further tool call, cartographer F2);
Claude Code's native cross-session messaging (frames text as from another session, needs socket
setup, docs H1); send-now keystrokes (terminal-dependent, interrupt text-only turns, docs A7).
Why: the user asked for "through PTY immediately and let either Claude Code or even agent queue
them internally".

### D3: a mid-turn message joins the running turn (merge), never a new turn marker

When a turn runs, an `immediate` message is pasted as
`<text>\n\n<!-- ccw turn: <running turn id> -->\n<!-- ccw merge: <merge id> -->`, the running
turn's marker (the `continue_turn` / `_with_marker` convention) plus a new per-paste merge marker.
The wrapper answers 202 `{turn_id: <running turn id>, state: "running", merged: true, merge_id}`.
Several messages then share one turn and its `final_text`; the orchestrator links each to that
turn (`messages.turn_id`). A test pins that a mid-turn paste never carries another turn id in its
turn marker. A session that is ready takes an `immediate` message as a normal new turn, as today
(`merged: false`). A turn of any origin (client, agent, peer) can absorb a merge (my call).
Alternatives: a record per message with multi-marker Stop attribution (P): needs `stop_target` to
accept any absorbed marker of an open record and copies one `final_text` into several records, and
every stale-marker rule must change (cartographer F1); interrupting the turn and starting a new one
(destroys work).
Why: the merge reuses the marker path that `continue_turn` proved and cannot produce a stale Stop by
construction. Q1 asks the user to confirm the shared-answer semantics.

### D4: a field on `POST /turns`, with refusals and a cap while busy

No new endpoint: `TurnRequest.priority`. While a turn runs, an `immediate` message is refused, and
nothing is pasted, when: the turn is in its command phase or a slash command is running or queued
for the Stop (409 `command_active`); the slash epic's `DialogScanner` patterns match the current
screen (409 `dialog_open`); an interrupt of the turn is in flight (409 `interrupting`); the turn
already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or
`sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) (my call, the
numbers mirror the command queue's `MAX_QUEUED` 4 and Claude Code's own queue bounds). `idle` while
busy stays 409 `busy`; booting and dead stay 503. The onTurn hook fires for a merge too, with
`merge_into: <turn id>` in its payload; a deny is 403 `vetoed`; its annotations shallow-merge into
the turn's (my call). `files` are written as for a turn; a merge's `callbackUrl` is kept on its
merge entry and receives the turn's terminal event (my call). Events: `user_message` at paste time
(turn_id of the running turn, `merged: true`), `turn_merged {turn_id, merge_id, origin, metadata}`
at paste time, `turn_merge_absorbed {turn_id, merge_id}` when the transcript shows the paste.
Alternatives: a separate `POST /sessions/{id}/inject` (a second client contract for the same
write, cartographer F3).
Why: one route keeps the orchestrator's `TurnAccepted` shape (it gains `merged`), and the refusals
are the anti-goals.

### D5: each merged paste is tracked on the turn record and confirmed from the transcript

`TurnRecord.merged: list[MergedPrompt]`, `MergedPrompt {merge_id, origin, metadata, callback_url,
pasted_at, absorbed_at}` (persisted with the record, served by `GET /turns/{id}`). The transcript
parser reads `<!-- ccw merge: <id> -->` into `UserPrompt.merge_marker` from every prompt-bearing
line: a `user` line, a `queued_command` attachment (wrapper 0.3.3) and a `user` line with
`promptSource: "queued"` (docs A10, issue 92478); the probe records which ones 2.1.304 writes. The
router sets `absorbed_at` once (first sighting) and emits `turn_merge_absorbed`. A merge marker
never moves `_last_marker` by itself: the turn marker on the same line names the running turn.
Alternatives: the UserPromptSubmit hook as the acknowledgement (docs C1: silent on mid-turn
injections; only if the probe's P3 confirms it, and it would still need the per-paste id); no
tracking (D6 and D14 would have nothing to look at).
Why: the transcript is the only documented place a queued prompt shows (A10), and the turn record
is what the orchestrator's verifier already reads.

### D6: a Stop with an unconfirmed paste waits, bounded

At a Stop that targets the running turn, after the onStop gate allowed it, when the turn holds a
merge with no `absorbed_at`: the relay answers allow, the turn stays running and busy
(`turn_deferred` with reason `merge_pending` and the pending `merge_ids`), and the wrapper waits up
to `sessions.merge.settle_seconds` (default 15, my call) for the merge markers. Claude Code sends
input still queued at the turn's end without another key press (docs A2), so the queued prompt
starts and its own Stop (same turn marker) completes the turn normally. If the bound expires first,
the wrapper completes the turn from the deferred Stop's payload (`last_assistant_message`, usage)
and leaves the unseen merges with `absorbed_at: null`. Order inside `_stop_gate`: onStop block wins,
then the hook or background defer, then `merge_pending`, then the slash epic's command hold; queued
commands stay queued until the turn really completes. A Stop with every merge confirmed completes
as today.
Alternatives: complete at the first Stop and adopt the follow-up prompt as a new `origin="agent"`
turn (the messages would link to an answer that never addressed them); wait without a bound (a
dropped paste would wedge the session, the anti-goal).
Why: one record answers all of its messages, and nothing can hold the session past the bound.
Depends on probe P2 (one Stop or two at a turn end with queued input); a contradiction amends task
wrapper-merge-stop-gate.

### D7: an interrupt ends the turn with its merged messages

`POST /interrupt` ends the running turn `interrupted` as today, its merged messages with it; the
merges never seen stay `absorbed_at: null` and the wrapper never resends them. Claude Code sends
queued input right after Esc (docs B1); if it does so, the run that follows surfaces through the
existing ready-state Stop path (`stop_target` while ready makes an `origin="agent"` record), so the
session cannot wedge. The second ESC stays conditional on a missing interrupt line, so it does not
hit the auto-sent prompt or open the rewind menu (docs B3).
Alternatives: keep the turn running after an interrupt with queued input (contradicts the
interrupt's contract); retract queued input with Up (keystroke emulation, docs A6, a non-goal).
Why: the interrupt keeps its contract, and the only cost is an agent turn the user can see.
Depends on probe P5; a contradiction (for example the queued text returning to the input box)
amends task wrapper-merge-stop-gate.

### D8: slash commands are unaffected by priority

`kind = 'command'` messages keep the slash epic's path (D9 run at the Stop, D10 dispatch); their
`priority` is stored as sent and ignored (Q4). Immediate prose is never pasted while a command runs
or waits for the Stop (D4 `command_active`), and the slash epic's slot handover at Stop keeps queued
client commands ahead of prose.
Alternatives: refuse `priority` on slash text (an error for a harmless field); let `immediate`
commands interrupt (destroys work, slash epic D9 rejected it).
Why: Claude Code itself holds commands until the turn ends (docs A3, F1), and the slash design
already settled when commands run.

### D9: invisible characters are stripped before every paste (my call)

`paste_bytes` removes Unicode tag characters (U+E0000-U+E007F), bidi controls (U+202A-U+202E,
U+2066-U+2069) and zero-width spaces (U+200B, U+FEFF) besides ESC, keeping ZWJ and ZWNJ (U+200C,
U+200D) and variation selectors. Claude Code removes them itself on Enter, and then "that Enter
sends nothing" and the cleaned prompt stays in the input box (docs G3); mid-turn, the next merged
paste would be concatenated onto it. Applies to every paste, idle turns included.
Alternatives: refuse such text with 422 (rejects legitimate content that only carries a stray
zero-width space); leave it (a stuck prompt corrupts the next message).
Why: immediate delivery makes a swallowed submit corrupt the following message. Probe P10 confirms
the swallow at 2.1.304.

### D10: the fake claude models Claude Code's queue, opt-in per scenario (my call)

Scenario key `"midturn_input": "queue"` (default `"drop"`, today's behaviour). With `queue`, a paste
plus CR arriving while a turn runs is queued; it is written and handed to the turn at the next tool
boundary, and input still queued at the turn end is sent as the next prompt, in the shapes and order
the probe recorded (P1-P5). Every input is still logged in `fake-inputs.jsonl` with state `busy`.
Alternatives: change the default (rewrites the meaning of pins such as
`tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy` that prove nothing is typed into
a running turn for commands).
Why: the existing pins stay accurate and the new tests opt in explicitly.

### D11: the real binary is probed first, and its results may amend later tasks

Task wrapper-midturn-probe runs claude 2.1.304 under a PTY in
`/workdir/workdir/.scratchpad/probe-midturn` (existing login, as the slash epic's probes did) and
records P1-P12 of the docs brief in `docs/claude-midturn-input.md` of the wrapper, with captured
transcript lines as a fixture and a consequences table naming each design decision it confirms or
contradicts. A contradiction is a `ticket.py amend` of the named task by the orchestrator before
that task starts; nothing downstream guesses.
Alternatives: build on the docs alone (silent on the Stop count, the hook for injections and
compaction, docs synthesis).
Why: the docs brief lists facts only the binary can settle (P1-P12); the user decision requires a
probe, never a guess.

### D12: the orchestrator stores `messages.priority`; rows queued at deploy keep idle

Migration `0012_message_priority.sql` (the next free number after hive-decoupling's 0011):
`ALTER TABLE messages ADD COLUMN IF NOT EXISTS priority text NOT NULL DEFAULT 'idle' CHECK
(priority IN ('immediate', 'idle'))`, then `ALTER TABLE messages ALTER COLUMN priority SET DEFAULT
'immediate'`. Existing rows take `idle`, new rows default to `immediate` (my call, Q11). The api
writes it once at insert (`enqueue_message(priority=)`); `MessageView` and `views._MESSAGE_SELECT`
expose it.
Alternatives: one `DEFAULT 'immediate'` (silently turns rows already queued at deploy into immediate
ones, cartographer section 5).
Why: a deploy does not change the semantics of messages already waiting.

### D13: immediate dispatch skips the idle pick, the reservation and the busy-leader hold

In `_claim_in_session`, a `priority = 'immediate'` head picks with `_PICK_IMMEDIATE`: the target
or the leader, `ready`, not gone, with a wrapper session, any state; no `state = 'idle'`, no
`free_since` predicate and no `agents.last_dispatched_at` write (the slash D10 rule for commands; a
busy agent has no turn slot to reserve). It is exempt from the busy-leader hold, so it overtakes
older queued `idle` messages of its session (Q5), and it still waits for backoff (`not_before`),
the handover hold (`_handover_pending`, so it reaches the successor leader) and a gone leader.
Order: an immediate message is not claimed while an older message of its session is `dispatching`
(the slash D10 per-session order rule), so pastes reach the wrapper in id order. `loop._send` sends
`priority`; 202 `merged` or not is `mark_sent` with the returned turn id; a 409 other than
booting|dead (`busy`, `command_active`, `dialog_open`, `interrupting`) and 429 `merge_queue_full`
requeue with `not_before = now() + retry_backoff_base_seconds`, no attempt counted, no reservation
to release (my call: an immediate requeue would spin against a busy wrapper). `idle` messages keep
today's path exactly.
Alternatives: keep the idle pick and only skip the wrapper's 409 (the message would still wait for
`agent_free`); write the reservation (a rejected immediate send would leave `last_dispatched_at >
free_since` and starve idle messages).
Why: the four idle waits of the Intent section are exactly the predicates this skips.

### D14: merged deliveries keep the hop guard, the verifier and the run trackers honest

`queue.turn_hop` takes `max(hop)` over the messages with a sender linked to the agent's current
turn (today `ORDER BY m.id DESC LIMIT 1`), so a merged session message cannot reset the hop count.
The verifier's `_carries` matches a turn whose `metadata.orch_message_id` or any
`merged[].metadata.orch_message_id` equals the message id, so an ambiguous send that was merged
resolves `started` with that turn instead of being resent. The orchestrator's `TurnRecord` model
gains `merged`. `messages.status` stays `sent`; "answered" stays derived through `turn_id` (all
messages merged into one turn read its `final_text`). agents-common's run tracker reads the linked
turn as today.
Alternatives: a new `answered` status (a second writer of a derived fact); per-message turns (D3
rejected).
Why: the brief's fix-as-AC list (cartographer Plan inputs) names exactly these two.

### D15: the superleader's tool and the chat tool say what immediate means

any-mcp-tatara-plugins `session_send` gains `priority` (enum `immediate`, `idle`, default
`immediate`) and its description says: a message to a busy leader joins its running turn at once
and shares that turn's answer; `idle` waits until the leader is idle. The `chat_send` description's
"chat-started turn" rule extends to a turn a chat message joined. Released as plugins 0.5.0 on top
of hive-decoupling's 0.4.0; the orchestrator pins it.
Alternatives: no plugin change (superleaders could not ask for `idle`).
Why: G2 names the superleader's tool, and a merged `<chat>` message breaks the old wording.

### D16: the web composer offers "Send when idle"; the queue strip names idle waits

agents-web `Composer.tsx` gains a "Send when idle" toggle (off by default) beside the target
select; when on, `postMessage` sends `priority: "idle"`, when off it sends no `priority` (the server
default), so the existing `{ text }` call shapes stay. `QueueStrip.tsx` adds "waits until idle" to
a queued `idle` message's detail. The vendored orchestrator spec and `schema.d.ts` are re-synced
first.
Alternatives: a per-session default setting (not asked); a priority select (two values do not need
one).
Why: G2 names the web composer.

### D17: the ccw peer `send_message` carries the same priority

`send_message` gains `priority` (`immediate` default, `idle`), carried on the peer wire to the
receiving instance; the receiver's `PeerInbox` delivers an `immediate` item while the session is
busy through `SessionRouter.submit_turn(priority="immediate")` (a merge), and an `idle` item as
today. Refusals (D4 409s, 429) keep the item queued for the next state change. `notify_when_idle`
is unchanged and reports `delivered` once the handling turn, merged or not, is terminal; several
items may map to one turn.
Alternatives: leave hive peers on wait-until-idle (Q7).
Why: hive peers are the other half of the messaging system; Q7 confirms.

### D18: the Matrix connector delivers new chat messages while a run is in progress

`inbound.rooms_ready` also returns a room whose in-progress runs are all `follow` runs with a
posted message (`message_id` set) and a session, so its new rows are claimed into a new follow run
and posted at once (server default `immediate`); a room whose first run has not posted yet still
waits (there is no session to post to). The tracker relays a completed turn's final text once per
turn: among in-progress runs whose messages link to the same `turn_id`, the run with the lowest id
relays and the others finish `handled` with reason `merged` and no reply. agents-common
`Message.turn_id` (new, released 0.4.0, connector pin moved) carries the link; the fake orchestrator
can complete one turn for several messages.
Alternatives: leave the connector (Matrix chat, the user's own channel, would still wait for the
turn, cartographer section 1 item 8); dedupe by `completed_at` and text (a heuristic).
Why: G4; Q6 confirms adding the two repos.

### D19: release and pin like the slash epic; no deploy task

claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.5.0 and agents-common 0.4.0 are version bumps
whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). The
orchestrator pins the wrapper merge commit of v0.5.0 (pyproject, uv.lock, `e2e/agent-test.Dockerfile`,
README Images) with a real-wrapper contract case and a kind e2e case for a merged message, then the
plugins ref v0.5.0; the connector pins agents-common v0.4.0. The wrapper is pinned by its release
tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags).
No agents-helmfile task (Q9).
Alternatives: pin branch commits (pruned images, unreachable shas).
Why: precedent slash D14, leader-auto-handover.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code (cartographer) | ran: `.scratchpad/immediate-delivery/brief-cartographer.md` | merge shape M with a per-message delivery list (section 6 F1); field on POST /turns (F3); immediate overtakes idle (F4); `_PICK_COMMAND`-shaped non-idle pick, no reservation (section 4); `turn_hop` max(hop), verifier merged match, unconfirmed-paste cap, fake absorption, handover hold, no paste in command phase (Plan inputs, fix-as-AC); connector `rooms_ready` (section 1 item 8) | per-message records P (F1); notes channel (F2); a migration default of immediate for existing rows (section 5) |
| research-docs (docs purist) | ran: `.scratchpad/immediate-delivery/brief-docs.md` | queueing and tool-boundary injection (A1, A2); commands held to turn end (A3); Esc sends queued input (B1) and the double-Esc hazard (B3); invisible-character strip (G3); dialog Enter hazard (D1); probes P1-P12 | send-now and queueSubmit keystrokes (A7, A8); native cross-session messaging (H1); UserPromptSubmit as the ack before P3 (C1) |
| debug record | ran: `docs/plans/2026-10-28-wrapper-queued-command-wedge-debug-record.md` | the stale-Stop mechanism the merge marker must never trigger; 0.3.3 `queued_command` parsing to extend | the stale-busy detector follow-up (noted, not doing now) |
| slash-commands-from-chat design | ran: `docs/plans/in-progress/slash-commands-from-chat/design.md` | D7 `DialogScanner`, D9 commands at Stop and slot handover, D10 pick and order rule, D14 release and pin, D16 fake key log separation | none |
| research-code-external | skipped: no analogue drives Claude Code's TUI queue; the forks are settled by the probe | none | none |
| architect (fable) | skipped: every fork has a user decision or a probe; no framed question remained | none | none |

## Research inputs

Retro proposals of the most recently done epics (`ticket.py retro --history`), recurring workflow
ones first:

- recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, parked-epic-stage): task
  files with empty Steps; the planner writes Interfaces, Expected outcome, Steps and Notes before
  the gate: every task of this epic.
- recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions): defects found only at the
  epic review; per-task security check for tools that send on a user's behalf (rate and size
  limits, session trust): wrapper-immediate-turn-merge (cap, size, veto), wrapper-peer-priority,
  orch-session-send-priority, orch-dispatch-immediate (Notes of each).
- recurring (deploy-safe-agent-sessions): check the epic's headline promise end to end (a
  reservation or busy flag respected everywhere): orch-dispatch-immediate (handover hold, no
  reservation), orch-wrapper-pin-0-5-0 (kind e2e of a merged message).
- recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions): seeds off by task kind,
  wrapper behaviour tasks ran far over: points set high on wrapper-immediate-turn-merge (8) and
  wrapper-merge-stop-gate (5).
- recurring (deploy-safe-agent-sessions, file-download-in-file-browse): no Docker in the pod; DB
  tests are CI-only: verifies stay Docker-free where a Docker-free test exists (orch-*,
  mxc-relay-once-per-turn and mxc-deliver-during-run Notes).
- recurring (file-editor-with-tabs-and-hi, markdown-rendering-in-chat): save the failing test name
  and output tail before any rerun; a named flake becomes a task: web-composer-send-when-idle Notes.
- recurring (file-editor-with-tabs-and-hi): pin the wrapper by release tag and cut it before the
  orchestrator task (Harbor prunes sha7 tags): wrapper-release-0-5-0 before orch-wrapper-pin-0-5-0.
- matrix-connector-agent-initi tech debt: the wrapper has no turn timeout or busy watchdog; the
  merge-specific guard is D6's bound: wrapper-merge-stop-gate; the general watchdog is a non-goal.

Findings:

- A mid-turn paste with a new turn marker makes the running turn's Stop stale (debug record root
  cause; cartographer section 3): wrapper-immediate-turn-merge.
- Claude Code queues mid-turn input and injects it at the next tool boundary within the turn, or
  sends it after the turn (docs A1, A2): wrapper-midturn-probe, wrapper-merge-stop-gate.
- Queued prompts show as `queued_command` attachments (wrapper MEMORY 2026-10-28) or `user` lines
  with `promptSource: "queued"` (docs A10): wrapper-merge-marker-parse.
- Esc sends queued input right away; double Esc on an empty input opens rewind (docs B1, B3):
  wrapper-merge-stop-gate.
- A CR with a dialog focused answers it (docs D1; slash probe outA): wrapper-immediate-turn-merge.
- Invisible characters make the first Enter submit nothing (docs G3): wrapper-paste-hygiene.
- The fake claude drops input typed while busy (`fake_claude.py:119-122`): wrapper-fake-claude-queue.
- Four idle waits in the orchestrator and wrapper (cartographer section 1): orch-dispatch-immediate,
  wrapper-immediate-turn-merge.
- `turn_hop` reads the newest message only; the verifier matches `metadata.orch_message_id` only
  (cartographer section 3): orch-merged-delivery.
- `target_queue_full` counts queued rows only, so a flood needs a wrapper cap (cartographer section 5):
  wrapper-immediate-turn-merge.
- The connector never claims a room's new rows during a run (`db/inbound.py:rooms_ready`):
  mxc-deliver-during-run; agents-common `Message` has no `turn_id`: common-message-turn-id,
  mxc-relay-once-per-turn.
- agents-common posts `{text}` only, so webhook, schedule and matrix take the server default
  (cartographer section 4): orch-priority-column.
- `session_send` description edited on the slash branch, plugins 0.4.0 taken by hive-decoupling:
  plugin-session-send-priority, plugins-release-0-5-0, orch-plugins-pin-0-5-0.
- `chat_send` defines a chat-started turn by its first `<chat>` message (plugin `__init__.py`):
  plugin-session-send-priority.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 one priority field | wrapper-immediate-turn-merge, orch-priority-column, orch-session-send-priority, orch-wrapper-client-priority, plugin-session-send-priority, wrapper-peer-priority, web-composer-send-when-idle |
| D2 PTY paste channel | wrapper-immediate-turn-merge |
| D3 merge into the running turn | wrapper-immediate-turn-merge |
| D4 field on POST /turns, refusals and cap | wrapper-immediate-turn-merge |
| D5 merged paste tracking | wrapper-merge-marker-parse, wrapper-immediate-turn-merge |
| D6 bounded Stop defer | wrapper-merge-stop-gate |
| D7 interrupt with merged messages | wrapper-merge-stop-gate |
| D8 slash commands unaffected | wrapper-immediate-turn-merge, orch-dispatch-immediate |
| D9 invisible characters stripped | wrapper-paste-hygiene |
| D10 fake claude queue | wrapper-fake-claude-queue |
| D11 real-binary probe first | wrapper-midturn-probe |
| D12 messages.priority storage | orch-priority-column |
| D13 immediate dispatch | orch-dispatch-immediate, orch-wrapper-client-priority |
| D14 merged delivery accounting | orch-merged-delivery, orch-wrapper-client-priority |
| D15 plugin descriptions and release | plugin-session-send-priority, plugins-release-0-5-0, orch-plugins-pin-0-5-0 |
| D16 web composer and queue strip | web-sync-message-priority, web-composer-send-when-idle |
| D17 ccw peer priority | wrapper-peer-priority |
| D18 Matrix connector delivery | common-message-turn-id, common-release-0-4-0, mxc-relay-once-per-turn, mxc-deliver-during-run |
| D19 release and pin | wrapper-release-0-5-0, orch-wrapper-pin-0-5-0, orch-plugins-pin-0-5-0, plugins-release-0-5-0, common-release-0-4-0, mxc-relay-once-per-turn |

## Review focus

- The marker rule (D3): every mid-turn paste carries the running turn's id in its turn marker; a
  grep of the paste path for `new_turn_id` on the merge leg must find nothing. The pin test is the
  invariant.
- `_stop_gate` order and the D6 bound: no path leaves a turn busy past `merge.settle_seconds`
  without a Stop; the defer timer is cancelled when the turn ends any other way.
- Every refusal of D4 writes nothing to the PTY (assert on `fake-inputs.jsonl`).
- `_claim_in_session` (D13): an immediate message never writes `last_dispatched_at`, still waits
  for the handover hold and a gone leader, and keeps per-session id order; idle messages behave
  byte for byte as before (the existing `test_queue_leader_routing.py` cases stay green unchanged).
- The verifier (D14): an ambiguous send merged into a turn resolves `started`, never resent.
- Connector dedupe (D18): exactly one reply per turn, and a room whose first run has no session
  still waits.
- Security per task (retro): size limits on merged text (`limits.max_prompt_bytes` applies), the
  429 cap, the onTurn veto on merges, peer rate limits unchanged.

## Left to the builder

- Internal names of helpers, timers and the exact placement of the merge-pending wait inside the
  router, within D6's order and bound.
- How `dialog_open` reads the screen (the slash epic's scanner over the ring or a screen snapshot),
  as long as a dialog footer pattern on the current screen refuses the paste.
- Log lines and metrics; a `ccw_turn_merges_total`-style counter is allowed, not required.
- The probe's driver (the wrapper's own `PtyProcess` from a scratch script, `expect`, or similar),
  under `/workdir/workdir/.scratchpad/probe-midturn`.
- The exact wording of the plugin descriptions and the web toggle label, within D15 and D16.

## Assumptions and unknown facts

- U1/P1-P2: whether a paste during a tool call is injected at the tool boundary as a
  `queued_command` attachment, and whether one queued at a text-only turn end yields one Stop or
  two: wrapper-midturn-probe; D6 depends on it.
- U3/P3: whether UserPromptSubmit fires for an injected prompt (affects notes and the slash D8
  signal): probe; D5 does not depend on it.
- U4/P4: two quick pastes queue as two items or one: probe; D5 assumes two (each has its marker).
- U5/P5: Esc with queued input: probe; D7 depends on it.
- U6/P7: a paste during auto-compaction or `/compact`: probe; assumed kept and delivered after
  (D4 refuses during a running `/compact` command anyway via `command_active`); a loss amends
  wrapper-immediate-turn-merge to refuse during compaction.
- U7/P6: a paste with a permission or elicitation dialog open: probe; D4 refuses on a dialog
  pattern regardless.
- U8: `last_assistant_message` at the single Stop covers the absorbed prompt's answer: probe.
- P9: `submit_delay_seconds` suffices for a collapsed long paste mid-turn: probe.
- P10: the invisible-character swallow at 2.1.304: probe; D9 stays harmless if refuted.
- P12: any state where plain Enter interrupts instead of queueing: probe; a hit amends D2.
- The slash epic merges with D7, D9 and D10 as designed (README blocker); a change there is
  re-checked against D4, D8 and D13 before this epic starts.
- hive-decoupling takes migration 0011 and plugins 0.4.0; if it lands differently, the numbers here
  move to the next free ones.

## Open questions
- Q1: Should a message sent while the leader is busy join the running turn and share that turn's final answer, instead of getting a turn record of its own? [recommended: yes, it joins the running turn and shares its answer (D3)]
- Q2: Name the field priority with values immediate (the default) and idle, the same in the orchestrator API, session_send, the ccw send_message, the wrapper POST /turns, with a web composer toggle labelled Send when idle? [recommended: yes, priority = immediate | idle everywhere (D1)]
- Q3: Should webhook, schedule and Matrix messages, which post text only, become immediate through the server default? [recommended: yes, they take the immediate default with no code change (D1)]
- Q4: Should slash commands keep running only at the turn's Stop, with any priority they carry stored and ignored? [recommended: yes, commands ignore priority (D8)]
- Q5: Should an immediate message overtake older idle messages still queued for the same session? [recommended: yes, immediate overtakes queued idle messages (D13)]
- Q6: Add agents-matrix-connector and agents-common to the epic, so new chat messages in a room with a run in progress are delivered at once and a shared answer is relayed once? [recommended: yes, include both repos (D18); without it Matrix chat still waits for the turn]
- Q7: Should the ccw peer send_message (hive peers) get the same priority option and mid-turn delivery? [recommended: yes, same option for hive peers (D17)]
- Q8: Should the wrapper's own POST /turns default to immediate for every client, not only the orchestrator? [recommended: yes, the wrapper default is immediate too (D1)]
- Q9: Keep deploy out of this epic (no agents-helmfile pin, apply or smoke task) and decide it at the gate? [recommended: yes, deploy is decided at the gate (D19)]
- Q10: Keep the per-message priority option (the idle choice) in this epic, at about 13 of its 65 points? [recommended: yes, keep it in scope]
- Q11: Should messages already queued when the migration runs keep today's wait-until-idle behaviour, with only new messages defaulting to immediate? [recommended: yes, existing queued rows stay idle (D12)]
- Q12: Builder Q3: may the probe (wrapper-midturn-probe) run the real claude 2.1.304 in this container with the existing login, spending real tokens on P1 to P12 (permission dialog, AskUserQuestion, /compact, MCP elicitation), and may the epic continue when P6 or another probe the container cannot run is recorded unsettled, the orchestrator then amending wrapper-merge-guards to the dialog footers it can prove? [recommended: yes, run every probe possible, record the rest unsettled, and continue; P1, P2, P4 and P5 must be observed]
- Q13: Builder Q7: are Q1 to Q11 accepted as recommended, including Q8 (the wrapper's POST /turns defaults to immediate for every client) and Q10 (the priority option stays in scope, now about 13 of the epic's 78 points)? [recommended: yes, all eleven accepted as recommended]
- Q14: During a deploy the orchestrator rolls agent pods itself, idle only, after it is deployed, so pods still on wrapper 0.4.0 answer 422 invalid_request to the new priority field and today's mapping fails those messages for good (rejected). For this rollout window only, should the orchestrator requeue such a message with backoff and no attempt counted until that pod rolls (a temporary compatibility shim, pinned by a dispatcher test in orch-dispatch-immediate and removed in a later epic)? [recommended: yes, requeue on a 422 that names priority until the pod rolls; without it, messages to not-yet-rolled pods fail and need Retry]

## Irreversible operations in scope

- Migration 0012 (additive, idempotent, no data rewrite beyond the default on existing rows): runs
  only when the orchestrator deploys, which is decided at the gate.
- Tags v0.5.0 (wrapper), v0.5.0 (plugins), v0.4.0 (agents-common): pushed by the orchestrator
  session after each release PR merges green; a wrong tag is never moved, a new patch is cut.
