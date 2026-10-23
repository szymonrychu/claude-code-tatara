---
title: ambiguous send verifier
status: in-progress
repo: agent-orchestrator
value: "Automatic retry never pastes a message twice: an ambiguous send is checked against the wrapper before it is re-sent"
files: [src/agent_orchestrator/dispatcher/verify.py, src/agent_orchestrator/dispatcher/loop.py, tests/test_ambiguous_verify.py, README.md]
verify: "uv run pytest tests/test_ambiguous_verify.py -q && mise run lint"
depends_on: [dispatcher-loop]
owns: []
uses: [queue-sql, wrapper-client, fake-wrapper, cluster-tokens, pg-fixture, settings, cluster-spec]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-ambiguous-send-verifier/agent-orchestrator
branch: agent-orchestrator-ambiguous-send-verifier
verified_head: ""
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# ambiguous send verifier

## Requirement

The ambiguous-send verifier (D24). Before any automatic retry, it checks with the wrapper whether a turn whose outcome was ambiguous actually started, so a message is never pasted into a session twice.

`dispatcher/verify.py`: `Verifier(pool, settings, wrapper_factory)`. Its `verify_once()` handles at most 50 messages per pass, from `list_verifying` (task dispatch-queue-sql). For each message it builds a `WrapperClient` for the message's original agent, with the cluster's derived token, and decides:

- Started. The wrapper snapshot has `current_turn_id` and that turn record's `metadata.orch_message_id` equals the message id, or one of the newest 10 turns of `list_turns` has a record carrying it. Then `resolve_started(id, turn_id)`. The reservation stays.
- Definitely not started. The wrapper answered the snapshot and the turn lookups, no record carries the id, and `age_seconds >= settings.ambiguous_settle_seconds`. Then `resolve_not_started` with the cluster's `spec.max_attempts` and the settings backoff. This clears the reservation only while it is still this message's. The message is then retried automatically after its backoff, through the normal claim, possibly by another agent.
- Unknown. The wrapper is unreachable (`WrapperUnreachable`), the session answers 404, or the message is still inside the settle window. Then nothing changes and the message is checked again on the next pass.
- Deadline. `age_seconds >= settings.ambiguous_deadline_seconds` without a definite answer. Then `fail_ambiguous(id)`: failed with `ambiguous`. Only the user's explicit Retry re-sends it.

Database rules: every write is one of the guarded queue functions, so two dispatcher replicas verifying the same message never both resolve it. Time comparisons use only `age_seconds` from the database clock (D23).

Wiring in `dispatcher/loop.py`: `Dispatcher.verify_pending()` delegates to `Verifier.verify_once()`, so every drain pass runs it, once per wake and poll.

README.md gains `## Delivery and retries`. It covers:
- the outcome table: accepted, busy, unavailable, gone, config error, rejected and ambiguous
- the backoff formula and its settings
- the verifying state
- the settle window and deadline
- the never-twice rule, and the residual case of a turn the wrapper holds for longer than the settle window

## Acceptance conditions

- AC1: a reset after the turn was recorded resolves to sent with the wrapper's turn_id and keeps the reservation [evidence: test:tests/test_ambiguous_verify.py::test_started_turn_resolves_to_sent]
- AC2: a reset before the turn was recorded is requeued with backoff only after the settle window, and is then delivered exactly once [evidence: test:tests/test_ambiguous_verify.py::test_not_started_requeued_after_settle_and_sent_once]
- AC3: inside the settle window nothing changes even when no turn is found [evidence: test:tests/test_ambiguous_verify.py::test_no_decision_inside_settle_window]
- AC4: an unreachable wrapper or a 404 session never triggers a resend, and the deadline fails the message as ambiguous [evidence: test:tests/test_ambiguous_verify.py::test_unknown_outcome_waits_then_fails_at_deadline]
- AC5: a stale dispatching row (dispatcher_lost) whose turn started resolves to sent [evidence: test:tests/test_ambiguous_verify.py::test_stale_dispatching_resolved_by_verifier]
- AC6: two verifiers on one message resolve it once [evidence: test:tests/test_ambiguous_verify.py::test_two_verifiers_resolve_once]
- AC7: the match uses metadata.orch_message_id, so a peer turn running on the agent is not mistaken for the message [evidence: test:tests/test_ambiguous_verify.py::test_matches_on_message_id_not_any_turn]
- AC8: README documents delivery and retries [evidence: doc-section:README.md#Delivery and retries]

## Files

- `src/agent_orchestrator/dispatcher/verify.py`
- `src/agent_orchestrator/dispatcher/loop.py`
- `tests/test_ambiguous_verify.py`
- `README.md`

## Interfaces

- `agent_orchestrator.dispatcher.verify:Verifier(pool, settings, wrapper_factory)` with `verify_once() -> int` (messages resolved)
- `agent_orchestrator.dispatcher.loop:Dispatcher.verify_pending()` delegating to it
- uses `queue.list_verifying`, `resolve_started`, `resolve_not_started`, `fail_ambiguous` (contract `queue-sql`) and `WrapperClient.get_session`, `list_turns`, `get_turn` (contract `wrapper-client`)

## Expected outcome

A message whose send timed out or was reset becomes `sent` when its turn started, and is retried with backoff when the wrapper shows it never did. If neither is provable by the deadline, it becomes `failed`/`ambiguous`. It is never pasted twice.

## Steps

- Write tests/test_ambiguous_verify.py with the seven named tests. Use FakeWrapper's `reset_connection_after_receive`, `reset_connection_before_receive` and `set_unreachable` controls, the pool fixture and factories, with small settle and deadline settings. Run `uv run pytest tests/test_ambiguous_verify.py -q` and expect failures.
- Implement dispatcher/verify.py, wire `verify_pending` in loop.py, and write the README section.
- Rerun and expect `7 passed`, then run `mise run lint`.

## Notes

The wrapper records the turn, including its `metadata`, synchronously in `Router._submit_turn` (claude-code-wrapper router.py:770-806) before it answers 202. A missing record after the settle window therefore means the request never reached the router.

The turns list carries summaries only (turns.py:32-39, SUMMARY_FIELDS), so fetch each candidate's full record with `get_turn`. Never compare wrapper timestamps with database time (D23).

For AC6, run two Verifier instances with asyncio.gather on separate pool connections.

- 2026-10-23 run agent-orchestrator: dependency-failed on dispatcher-loop
