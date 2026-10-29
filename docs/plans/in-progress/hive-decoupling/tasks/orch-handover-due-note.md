---
title: orch handover due note
status: in-progress
repo: agents-orchestrator
value: "a leader near its limit is told to hand over, to whom and how, before its details are compacted away"
files: [src/agents_orchestrator/dispatcher/hive.py, tests/test_hive_push.py, tests/test_eligibility_fragments.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest tests/test_hive_push.py tests/test_eligibility_fragments.py tests/test_dispatcher_auto_handover.py tests/test_leadership_pass.py && mise run lint"
depends_on: [orch-hive-feed-removal]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch handover due note

## Requirement

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

## Acceptance conditions

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

## Files

- `src/agents_orchestrator/dispatcher/hive.py`
- `tests/test_hive_push.py`
- `tests/test_eligibility_fragments.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- Keyed note `handover_due` (wrapper `POST /v1/sessions/{id}/notes` with `key`), leader only.
- `hive._CANDIDATES` (or the chosen name): SQL embedding `eligibility.ELIGIBLE`, ordered idle first, then `context_pct` ascending (nulls last), then ordinal.
- Candidate line: `<pod_name> (<pod_name>/<wrapper_session_id>, <state>, <N>% context)`.

## Expected outcome

A leader at or above the threshold sees, within one push tick plus wrapper delivery, who can take over, how to reach them, and the brief-then-handover protocol; nobody else is disturbed.

## Steps

- Red: the tests of ac1-ac6 and ac11 in `tests/test_hive_push.py` and the ac7 assertion; run `uv run --frozen pytest tests/test_hive_push.py tests/test_eligibility_fragments.py`: they fail.
- Green: hive.py, README, MEMORY; run the task's verify: passes. Quote the summary line.

## Notes

- Threshold: the helper from orch-hive-feed-removal; never respell it.
- Q8 (candidates at or above the threshold left out) is an open gate question; if answered no, the task is amended before it starts.
- The scalable test is `spec.scalable` (as `on_start.orchestrator_allow` uses it).
- DB tests are CI-only in agent pods (no Docker); CI on the PR is the gate.

- 2026-10-27 amended: builder check settlement 7: handover_due and outcome pass run every tick outside the _claim/_release hash path
