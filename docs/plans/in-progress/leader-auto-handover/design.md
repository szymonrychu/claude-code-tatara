# leader auto handover design

## Summary

A hive leader (any session with `max_replicas > 1`) passes leadership on automatically in two cases: just before it
compacts, and before a scale-down removes its pod. claude-code-wrapper 0.3.0 emits a new SSE event `compacting` from
Claude Code's PreCompact hook; the orchestrator ingester projects every compaction signal (`compacting`, `compacted`)
into `agent_status.compaction_at`, and the dispatcher's leadership pass hands a compacted leader over at its turn
boundary (reason `compaction`). A scale-down below the leader's ordinal is accepted when a ready agent that stays
exists; the pass moves leadership to it (reason `scale_down`) and the reconciler keeps the leader's pod until it has.
Every pick is restricted to agents that stay. The reason reaches the session view, the `leader_changed` frame and the
agents-web UI. Released and deployed: wrapper 0.3.0, orchestrator pins, agents-helmfile bump, apply and a smoke that
scales down below the leader.

## Intent and why

User request 2026-10-26, verbatim: 'when session cluster leader gets compacted (or scaled down), pass it's leadership
to another agent in the cluster.' The leader is the agent that answers the user (untargeted messages go to it). A
compacted leader has lost the detail of the conversation, and a removed leader takes the user-facing context with it;
another agent should take the next request. Today a compaction changes nothing and a scale-down below the leader is
refused (`leader_would_leave`), so the user must move leadership by hand first.

The user's binding decisions are three (decisions.md, 2026-10-26): hand over just before compaction through a new
pre-compaction event from the wrapper; on a scale-down that would remove the leader's pod, hand over first and then
shrink, still refusing when no ready agent that stays exists; always on for hived agents, no switch. Every other call
here (which compactions count, the turn boundary, the retry, who takes over) is the orchestrator session's or the
planner's and is marked `(my call)`.

## Goals

- G1: when the leader of a hive is about to compact (auto or manual), the wrapper reports it before the compaction
  runs (the `compacting` event; only this report precedes the compaction) and the orchestrator then moves leadership
  to another ready agent of the cluster at the leader's turn boundary, which for a busy leader is after the native
  compaction has run.
- G2: a scale-down whose new replica count would remove the leader's pod first hands leadership to a ready agent that
  stays, then shrinks; with no such agent it is refused as today.
- G3: the new leader is chosen among ready agents that stay in the cluster (never one about to be removed); with no
  eligible agent the leader keeps leading and the move is retried.
- G4: always on for every hive (max_replicas > 1); a cluster of one never hands over.
- G5: the UI, API and stream show automatic handovers with their reason (compaction, scale-down); documented API and
  API-only e2e test.
- G6: released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering
  a scale-down below the leader.

## Non-goals

- No per-cluster switch for automatic handover.
- No holding or blocking Claude Code's compaction until the handover is acknowledged.
- No threshold-based early handover; the existing context advice stays as it is.
- No takeovers by agents, no consensus protocol; the orchestrator stays the single authority.

## Anti-goals

- A second writer of `session_leaders` (the api or the reconciler moving leaders): the dispatcher stays the only one.
- A leader moved mid-turn by the compaction trigger, or a message re-routed away from an agent already working on it.
- A scale-down that removes the leader's pod before leadership has moved (except after the bounded drain deadline).
- A pick that hands leadership to an agent whose pod is about to be removed.
- A slower PreCompact hook: the wrapper must still answer the relay at once (no hold, non-goal).
- Pod rolls or a rendered-config change caused by this epic beyond the image pins.

## Constraints

- Python only (wrapper, orchestrator, helmfile tests); agents-web TypeScript.
- Each table has exactly one writer: `session_leaders` dispatcher, `agent_status` ingester, `agents` reconciler,
  `sessions.spec.replicas` api (`set_replicas`), `leadership_requests` api inserts and dispatcher decides.
- `/api/v1` is additive only: new response fields and frame fields may appear, no codes change meaning.
- TDD per task; tests are never edited to pass unless no longer accurate, and each such test is named in its task.
- Wrapper release tag only after the `main` build is green (`release.yaml` needs `:<sha7>`); Harbor prunes sha7 tags,
  so agents-helmfile pins the agent image by release tag (`claude-code-wrapper:0.3.0`).
- Live `mise run apply` is run by the orchestrator session only, never by a subagent, and never as AC evidence.
- No backward compatibility shims.

## Decisions

### D1: The wrapper reports a compaction before it runs as a new SSE event `compacting`

Decision: the PreCompact relay handler (`router.py` `_on_compact_hook`) emits the event `compacting` with
`{trigger}` (`manual`, `auto`, else `unknown`, the same vocabulary as `compacted`) to the event log before it returns
allow, and keeps publishing the `pre_compact` signal. Claude Code waits for the hook, so the event is in the log
before the compaction runs. `EVENT_TYPES` gains `compacting` just before `compacted`; README documents it. The handler
still answers at once (no hold). claude-code-wrapper is released as 0.3.0.
Alternatives: a new blocking user hook event wrapping PreCompact (couples the wrapper to an orchestrator webhook and
invites holding, a non-goal); relaying SessionStart `source=compact` (that is after the compaction, discovery
do-not-build); reacting only to `compacted` (after the fact, against the user's decision); holding the compaction
for an orchestrator ack (non-goal; real-Claude behaviour unverified).
Why: the user chose "hand over just before compaction (a new pre-compaction event from the wrapper)"; an SSE event
reaches the orchestrator through the existing ingester stream with no new coupling. `custom_instructions` is left out
of the event: the orchestrator needs only the fact and the trigger, and the instructions are user text (my call).

### D2: Every compaction counts, from either signal

Decision: both `compacting` (before) and `compacted` (after, from the transcript boundary) count as a compaction of
that agent. Auto, manual, the orchestrator's compact command, the wrapper's idle auto-compact and Claude Code's own
idle compaction all count.
Alternatives: auto only; excluding idle-origin compactions; `compacting` only.
Why: "every compaction counts, auto and manual" (my call, orchestrator session). `compacted` also covers compactions
PreCompact does not relay (Claude Code's idle compaction is reported only as `compacted`, discovery section 2) and
agents still on a wrapper 0.2.0 image (my call).

### D3: The ingester projects compactions into `agent_status.compaction_at`

Decision: migration `0006_compaction.sql` adds `agent_status.compaction_at timestamptz` (nullable). The ingester's
projection sets it from the event's own `ts` (the wrapper's clock, when the compaction was reported), never from the
ingest time, and never moves it backwards (`greatest(compaction_at, ts)`), when it stores a `compacting` or
`compacted` event of that agent; it NOTIFYs `status` as it does for `context` and wakes the dispatcher (D15). Nothing
else writes it. An old event ingested late (a stream resume or replay) therefore carries its old time, and a leader
elected after it (`since` later than the event's `ts`) is never handed over for it.
Alternatives: the dispatcher scans `events` for the leader's compaction events newer than `session_leaders.since`
(no migration, but an unbounded per-agent scan every poll; a partial index would still need a migration); a new
`leadership_requests` kind inserted on compaction (only the api inserts requests; a new kind also needs a migration);
`events` added to the dispatcher's wake channels (wakes on every event).
Why: `agent_status` already belongs to the ingester and carries the per-agent projections (`context_pct`); the
candidate check becomes one row compare against `session_leaders.since` (my call). The event time, not the ingest
time, decides whether the compaction belongs to the current term (interrogate finding 3); this compares the wrapper
pod's clock with the database clock, which are NTP-synchronised in the lab (assumption below).

### D4: A compacted leader hands over at its turn boundary, reason `compaction`

Decision: the leadership pass gets a compaction step: when the leader's `compaction_at` is later than its term's
`since`, the leader is ready and not gone, and it is at its turn boundary (the existing `at_boundary`: state `idle`
and no message `dispatching` or `verifying`), leadership moves to the staying agent free the longest (D7), at
`epoch + 1`, reason `compaction`. A busy leader keeps leading until its turn ends (the native auto-compaction runs
mid-turn), and the first pass after the turn moves it. The pass runs once per drain, before the claim loop, and the
leader can turn idle while that loop runs, so the pass alone cannot keep the compacted leader from taking one more
untargeted message: the claim path holds untargeted messages while the leader's handover is pending and possible
(D16), and `agent_free` wakes the next drain, whose pass moves leadership before the held message is claimed. With no
eligible agent the leader stays, keeps receiving untargeted messages (G3), nothing is written, and the session stays
a leadership candidate so every pass retries; the retry lasts for the rest of the leader's term, so a peer that
becomes ready later (or a later scale-up of a hive running one agent) takes over (my call, Q1 asks the user). A new
term (any leader change) starts clean. `_CANDIDATES` gains the clause "the leader's `compaction_at` > `since`".
Alternatives: move at once; a lease-style timeout on the retry.
Why: "a busy leader moves at its turn boundary" and "with no eligible peer, the leader stays and the move is retried"
(my calls, orchestrator session). This amends hive D26 ("advised, never forced") a second time, after
`leader_lease_seconds`: a system handover of the current term at a turn boundary, never a takeover (hive D21 holds).
Each step of the pass re-reads the leader after a change, so after the scale-down step moves leadership the
compaction and lease steps judge the new leader at its new epoch and fresh `since`, and do not move it again.

### D5: A scale-down below the leader is accepted when a staying agent can lead, refused otherwise

Decision: `db/sessions.set_replicas` refuses `leader_would_leave` only when the leader's ordinal is at or above the new
replica count and no staying peer exists: another agent of the session that is ready, not gone, has a wrapper session
and has `ordinal < replicas` (the same predicate as the pick, D7). Otherwise it writes `spec.replicas` as today and
answers 202, and when the new count is at or below the leader's ordinal it also wakes the dispatcher (D15). The api
never moves the leader; the dispatcher derives the move from `spec.replicas` (D6). The error code
keeps its name and now means "the leader would leave and no ready agent that stays can take over" (my call). Refusal
order and every other code are unchanged.
Alternatives: the api queues a new `scale_down` request kind (migration, and a request the api must keep consistent
with the spec write); keep the refusal and queue a handover, answering 409 or a pending 202 (the caller must retry);
shrink at once and let `leader_lost` replace the leader after its 30 s grace (untargeted messages stall, the reason
reads `leader_lost`).
Why: the user's decision "hand over first, then shrink; still refusing when no ready agent that stays exists"; the
dispatcher stays the single authority and no new writer or request kind appears. This amends cluster-scaling D7
("scaling never moves leadership") and its anti-goal, and the 2026-10-24 MEMORY entry ("a scale-down never removes the
leader").

### D6: A leaving leader moves at once, reason `scale_down`

Decision: the leadership pass gets a scale-down step, run after the queued requests and before the lost-leader step:
when the leader is not gone and its ordinal is at or above `spec.replicas`, leadership moves to the staying agent free
the longest (D7), at `epoch + 1`, reason `scale_down`, without waiting for the leader's turn boundary. The leaving
leader's running turn still finishes on its pod during the drain. With no staying agent the leader stays and the pass
retries (the session is a candidate while the leader is leaving). A gone leader keeps the lost-leader path (reason
`leader_lost`). `_CANDIDATES` gains "the leader is not gone and its ordinal >= `spec.replicas`".
Alternatives: wait for the turn boundary as for compaction.
Why: a leaving agent is already excluded from routing (`ready = false` from the next reconciler tick), so waiting only
holds untargeted messages, and after 30 s the lost-leader step would replace a busy leaving leader mid-turn anyway,
with the wrong reason. Moving at once interrupts nothing (my call; the turn-boundary rule of D4 is itself a call
made for compaction, discovery fork 3). A leaving leader that the reconciler has already marked not ready (`_observe`
sets `ready = ordinal < replicas and pod ready`, `reconciler/loop.py:367`) but that is not gone is still handled by
this step at once, before the lost-leader step can see it, so its change always reads `scale_down`, never
`leader_lost`.

### D7: Every pick is restricted to agents that stay

Decision: an agent stays when its ordinal is below the session's `spec.replicas`. `_FREE_LONGEST` (handover without a
target, `leader_lost`, `lease_expired`, `compaction`, `scale_down`), `_target_ready` (named handover and user
make-leader targets: a leaving target is rejected `target_not_ready`) and the initial election all filter on it. The
order stays the existing one (idle first, then `free_since` ascending, then id). No context-aware choice.
Alternatives: prefer the lowest `context_pct`; lowest ordinal.
Why: "the existing longest-free pick, restricted to agents that stay" (my call, orchestrator session; discovery
fix-as-ac: between the `set_replicas` commit and the next reconciler tick a leaving agent is still `ready`).

### D8: The reconciler keeps the leader's pod until leadership has moved

Decision: during a scale-down drain the current leader, when it is at or above the target, counts as busy in
`_draining`, so `_drain_replicas` keeps the StatefulSet at least one above the leader's ordinal until the leader row
names a staying agent. The existing `ORCH_SCALE_DRAIN_SECONDS` (900) deadline still applies the target regardless; the
leader's pod then goes and the lost-leader step picks a successor. `status.drain.waiting` lists the leader's ordinal
while it is held. A staying peer can become unready between the api's check and the pass's move (a pod restart);
then the pass finds no eligible agent and the leader stays leading, busy or idle, and its pod is held until a peer is
ready again (the pass retries and moves it) or until the drain deadline, whichever is first. At the deadline the pod
goes, the leader becomes gone, and the lost-leader step picks the first staying agent that is ready; until one is,
untargeted messages hold (the existing gone-leader rule). Targeted messages keep flowing throughout.
Alternatives: no hold (the reconciler may remove an idle leader before the next pass, and the change would read
`leader_lost`); an unbounded hold (a session with no eligible agent could never shrink).
Why: "hand over first, then shrink" as an invariant, not a race; the deadline bound is the existing drain contract (my
call).

### D9: Always on for every hive, no switch

Decision: both triggers apply to every session the pass already covers (`_HIVE`, `coalesce(max_replicas, replicas) >
1`). No spec field. A session running one agent never hands over: there is no other agent to pick.
Alternatives: a spec flag like `leader_lease_seconds`.
Why: the user's correction "Sorry.. auto handover always on for hived agents".

### D10: Reasons `compaction` and `scale_down`, carried by the NOTIFY and the stream frame

Decision: the two new `session_leaders.reason` values are `compaction` and `scale_down` (bare, like `lease_expired`;
`handover: <reason>` stays for agent-requested handovers). `_set_leader`'s `NOTIFY leader_changed` payload and the
`/api/v1/stream` `leader_changed` frame gain `reason` (additive). The session view's `leader_reason` already carries it.
README documents every reason the code writes: `initial`, `user`, `handover: <reason>`, `leader_lost`,
`lease_expired`, `scale_down`, `compaction` (discovery fix-as-ac: README lists `start` and omits values).
Alternatives: `handover: compaction`; a new frame type.
Why: system handovers read like the lease's; the frame already exists and is additive (my call).

### D11: agents-web shows the reason and the new refusal meaning

Decision: agents-web reads `reason` from the `leader_changed` frame into the session's `leader_reason`; the leader
badge's tooltip names the epoch and the reason, and for the automatic reasons a caption next to the badge reads
"after compaction" or "after scale-down". ScaleControl's `leader_would_leave` hint becomes "No ready agent that stays
can take over leadership." (replacing "Make another agent leader first."). Wording (my call).
Alternatives: a toast per change; no UI change (G5 requires the UI).
Why: G5; the leader badge is where leadership is shown today (`AgentsStrip.tsx`).

### D12: Release and deploy in the shape of the hive and cluster-scaling epics

Decision: claude-code-wrapper 0.3.0 (version bump, tag `v0.3.0` on the merge commit after the `main` build); the
orchestrator pins that merge commit (pyproject, uv.lock, `e2e/agent-test.Dockerfile`, README Images); kind e2e runs
against it; agents-helmfile pins the orchestrator chart and image, the agent image `claude-code-wrapper:0.3.0` and the
agents-web chart and image; the orchestrator session runs `mise run diff`, `mise run apply` and `mise run smoke`. The
smoke grows a scale-down below the leader. Merge shas are filled in by `ticket.py amend` as the PRs merge.
Alternatives: none considered; the user named this shape.
Why: the caller's instruction and the precedent epics (`hive-mode-leadership-handove`, `cluster-scaling`).

### D13: Docs and memory record the amendments

Decision: the orchestrator README `### Leadership` lists every pass step in order (initial, queued requests,
scale-down, lost leader, compaction, lease; it says "three steps" today and omits the lease) and the Scaling section
replaces "The leader is never removed"; MEMORY.md gets dated entries amending hive D26 and cluster-scaling D7.
Why: discovery fix-as-ac and the repo rule to record non-obvious decisions (my call on step order: compaction before
the lease so a leader that both compacted and outlived its lease reads `compaction`).

### D14: The agent-facing advice and tools stay as they are

Decision: no change to the hive_state handover hint, the any-mcp tool text or `/agent/v1/me`. No any-mcp release.
Why: non-goal "the existing context advice stays as it is"; the any-mcp scale tool text does not describe the refusal
(`any-mcp/src/any_mcp/orchestrator.py:127-129`).

### D15: Compactions and scale-downs wake the dispatcher through `leadership_requested`

Decision: when the ingester projects a compaction (D3) it also sends `NOTIFY leadership_requested {session_id}`, and
`set_replicas` sends it when it accepts a count at or below the leader's ordinal (D5). The dispatcher already listens
on that channel (`dispatcher/loop.py:37`), so an idle compacted leader or a leaving leader moves on the wake, not on
the next `ORCH_DISPATCH_POLL_SECONDS` poll. A busy compacted leader is moved on the `agent_free` wake at its turn end.
Alternatives: a new channel (for example `leadership_check`) added to `CHANNELS`; `status` or `session_changed` added
to `CHANNELS` (wakes on every status write or reconciler tick); the poll alone (up to 2 s late, and the late move lets
a compacted leader be picked meanwhile).
Why: the channel already means "this session needs a leadership pass"; no dispatcher change and no new channel to
document (my call). README Leadership documents its three senders.

### D16: The claim path holds untargeted messages for a leader whose handover is pending

Decision: `_claim_in_session` (`db/queue.py`) treats the leader like a gone leader (untargeted messages hold, targeted
ones flow) while its handover is pending and possible: its `compaction_at` is later than `since` or it is leaving
(not gone, `ordinal >= spec.replicas`), and an eligible staying agent exists by the same predicate the pass picks
with (D7). With no eligible agent the leader keeps receiving untargeted messages (G3, "the leader keeps leading").
Alternatives: run `leadership_pass` for the session inside the claim loop before each untargeted claim (two lock
holders interleaving, and the pass would run on every claim); rely on the pass at the head of the drain (the race of
interrogate finding 1).
Why: a compacted leader must never take an untargeted message that a staying agent could take; one shared predicate
keeps the hold and the move from disagreeing, so the hold can never outlive a possible move (my call).

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| interrogate (fable, opus, sonnet) | ran 2026-10-26: eight findings, all acted on (D3 event time, D4 text, D6 unready leaving leader, D8 race, D15, D16, my-call marks, G1 wording) | claim hold, wake channel, event-time projection | none |
| research-code-internal | ran: `.scratchpad/leader-handover/discovery.md` | pass step pattern (`db/leadership.py:320-332`); `_set_leader` effects; `at_boundary` (`leadership.py:143-146`); drain busy hold (`reconciler/loop.py:275-315`); fake claude `auto_compact` step (`tests/fake_claude/fake_claude.py:709`) | scanning `events` per poll (D3); a SessionStart relay (discovery do-not-build) |
| research-docs | skipped: the PreCompact contract the plan relies on is already in the wrapper code (synchronous relay with `trigger`, `hook_relay.py:24-34`, `router.py:561-579`); the plan does not block or delay the hook, and D2 counts `compacted` too, so a PreCompact that does not fire still triggers | none | none |
| research-code-external | skipped: the handover rules are the user's decisions and the hive's single-authority design; no analogue would change them | none | Raft-style leadership transfer (non-goal: no consensus protocol) |
| research-papers | skipped: no algorithmic core | none | none |

## Research inputs

| Finding | Source | Task |
|---|---|---|
| recurring workflow: live apply and smoke tasks ran 3-5x their minutes; score live and smoke work higher | RETRO agents-matrix-connector-depl, agents-schedule-deploy, agents-schedule-microservice | helmfile-apply-smoke (5 points), smoke-scale-below-leader (3 points) |
| recurring workflow: defects missed by per-task review surfaced at whole-diff or security review | RETRO agents-matrix-connector, agents-schedule-microservice | Review focus below; phase 5 review of every repo |
| recurring workflow: Docker VM disk full blocked testcontainers | RETRO agents-matrix-connector, agents-schedule-microservice | epic-run preflight before compaction-status-projection, leadership-auto-handover, scale-down-staying-peer, reconciler-leader-pod-hold, leader-changed-reason |
| web briefs need `npx tsc -b` and the full `npm test` | RETRO agents-schedule-deploy | web-leader-reason, web-scale-hint (verify and AC) |
| deploy needs a first-real-message acceptance | RETRO agents-matrix-connector-depl | helmfile-apply-smoke AC3 |
| subagent `kubectl exec` is denied by the classifier: plan live proofs as orchestrator-run steps | RETRO agents-matrix-connector-depl | helmfile-apply-smoke (orchestrator-run) |
| a stale helmfile test blocked the first apply | RETRO agents-schedule-deploy | helmfile-deploy-pin (verify runs test_orchestrator_release.py, which holds test_values_dir_moved) |
| ticket.py new-task keeps only Requirement, AC and Files | RETRO agents-matrix-connector | every task: interfaces, steps and notes are written into the Requirement |
| leaving agents are pickable before the reconciler marks them unready | discovery fix-as-ac | leadership-auto-handover |
| README Leadership says three steps; reasons list wrong | discovery fix-as-ac | leadership-auto-handover, leader-changed-reason |
| handover hint only with `spec.auto_compact_pct` | discovery fix-as-ac | not acted on: the advice text is a non-goal (D14) |
| the compaction step reuses the lease step pattern and `at_boundary` | discovery reuse | leadership-auto-handover |
| fake claude can script a native compaction mid-turn | discovery reuse | wrapper-compacting-event, kind-e2e-auto-handover |
| push the compact summary to the new leader; context-aware pick; threshold handover | discovery ideas | rejected: non-goals and D7 |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 The wrapper reports a compaction before it runs as a new SSE event `compacting` | wrapper-compacting-event, wrapper-release-0-3-0 |
| D2 Every compaction counts, from either signal | compaction-status-projection |
| D3 The ingester projects compactions into `agent_status.compaction_at` | compaction-status-projection |
| D4 A compacted leader hands over at its turn boundary, reason `compaction` | leadership-auto-handover, claim-hold-and-handover-wake, kind-e2e-auto-handover |
| D5 A scale-down below the leader is accepted when a staying agent can lead, refused otherwise | scale-down-staying-peer, kind-e2e-auto-handover |
| D6 A leaving leader moves at once, reason `scale_down` | leadership-auto-handover, kind-e2e-auto-handover |
| D7 Every pick is restricted to agents that stay | leadership-auto-handover |
| D8 The reconciler keeps the leader's pod until leadership has moved | reconciler-leader-pod-hold |
| D9 Always on for every hive, no switch | leadership-auto-handover |
| D10 Reasons `compaction` and `scale_down`, carried by the NOTIFY and the stream frame | leader-changed-reason |
| D11 agents-web shows the reason and the new refusal meaning | web-leader-reason, web-scale-hint |
| D12 Release and deploy in the shape of the hive and cluster-scaling epics | wrapper-release-0-3-0, orch-wrapper-pin-0-3-0, smoke-scale-below-leader, helmfile-deploy-pin, helmfile-apply-smoke |
| D13 Docs and memory record the amendments | leadership-auto-handover, scale-down-staying-peer, reconciler-leader-pod-hold |
| D14 The agent-facing advice and tools stay as they are | leadership-auto-handover |
| D15 Compactions and scale-downs wake the dispatcher through `leadership_requested` | compaction-status-projection, scale-down-staying-peer, claim-hold-and-handover-wake |
| D16 The claim path holds untargeted messages for a leader whose handover is pending | claim-hold-and-handover-wake, kind-e2e-auto-handover |

## Review focus

- `db/leadership.py`: step order, the epoch fence and that the compaction step never fires off the turn boundary;
  that every pick (`_FREE_LONGEST`, `_target_ready`, initial) excludes `ordinal >= spec.replicas`; that the candidate
  query does not select a healthy, uncompacted, staying leader every poll.
- `db/queue.py` claim hold: one predicate with the pass's pick, so a hold never outlives a possible move, and no
  untargeted message reaches a leader whose handover is pending and possible.
- `db/sessions.set_replicas`: the staying-peer predicate equals the pick's; refusal order unchanged; no write to
  `session_leaders` or `agents` from the api.
- `reconciler/loop.py`: the leader hold is bounded by `ORCH_SCALE_DRAIN_SECONDS` and never raises replicas above the
  applied count; the hash invariant (`tests/test_render.py::test_runtime_fields_change_only_statefulset_replicas`).
- Wrapper: the PreCompact relay still answers at once and emits exactly one `compacting` per hook call.
- Tests changed because they are no longer accurate are exactly the ones each task names.
- Whole-diff review per repo at phase 5 (recurring retro finding).

## Left to the builder

- Where the staying-peer SQL lives (a shared constant in `db/leadership.py` imported by `db/sessions.py`, or an
  equivalent), as long as the pick and the refusal use one predicate.
- The exact `_leader` columns added for the new steps, and test helper names.
- The UI caption's exact MUI component and placement next to the leader badge.
- How the smoke makes pod-1 the leader (public `POST /api/v1/sessions/{id}/leader`) and its timeouts within
  `SMOKE_TIMEOUT_S`.

## Assumptions and unknown facts

- Real Claude Code 2.1.304 fires PreCompact for auto and manual compactions and waits for the hook before compacting
  (upstream hooks docs, cited at `claude-code-wrapper/docs/plans/done/agent-callable-slash-command/design.md:74`;
  never exercised live, `record.md:65`). If it does not fire, D2's `compacted` still triggers the move, after the
  compaction. Confirmed after the deploy by reading `GET /api/v1/sessions/{id}/events?types=compacting` of a live hive
  after its next compaction (helmfile-apply-smoke records it in MEMORY.md when one happened).
- Whether Claude Code's own idle compaction reports the session busy: irrelevant to correctness (an idle leader is at
  its boundary and moves on the next pass).
- The wrapper pods' clocks and the database clock agree to within a second or two (NTP in the lab). `compaction_at`
  (wrapper time) is compared with `since` (database time); a skew of seconds could misjudge only a compaction reported
  within seconds of an election. Confirmed by a probe at the gate if contested: `date -u` in an agent pod against
  `SELECT now()` on the orchestrator database.
- Ingestion order per agent is event order, so `compaction_at` is set before the `session_state` idle that ends the
  turn (ingester stores in seq order; asserted by kind-e2e-auto-handover end to end).
- Existing sessions keep their snapshotted agent image until they are recreated; their compactions still count
  through `compacted` (D2).

## Open questions

- Q1: When a compacted leader finds no eligible agent (for example a hive running one agent), is the move retried for the rest of its term, so a peer that becomes ready later or a later scale-up takes over? [recommended: yes, retried for the rest of the term; any leader change clears it]

## Irreversible operations in scope

- Tag `v0.3.0` pushed on the claude-code-wrapper merge commit; `release.yaml` retags `:0.3.0` and `:latest` (task
  wrapper-release-0-3-0, run by the orchestrator after the `main` build is green; covered by the user's request for a
  wrapper release, G6).
- Migration `0006_compaction.sql` applied to the live orchestrator database by the deployed orchestrator (additive,
  nullable column; forward only; covered by G6).
- `mise run apply` on the live namespace (task helmfile-apply-smoke, orchestrator session only, after `mise run diff`
  shows only the pins; covered by G6). The orchestrator pods roll; agent pods of existing sessions keep their image.
- PR merges to `main` of claude-code-wrapper, agents-orchestrator, agents-web and agents-helmfile (main stays green).
