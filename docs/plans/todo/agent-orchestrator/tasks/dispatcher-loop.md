---
title: dispatcher loop
status: todo
repo: agent-orchestrator
value: "Delivers queued messages round-robin and runs interrupt and compact commands, safely with more than one replica."
files: [src/agent_orchestrator/dispatcher/__init__.py, src/agent_orchestrator/dispatcher/loop.py, tests/test_dispatcher.py]
verify: "uv run pytest tests/test_dispatcher.py -q && mise run lint"
depends_on: [dispatch-queue-sql, fake-wrapper-contract, cluster-token-derivation, clusters-repository]
owns: []
uses: [queue-sql, wrapper-client, fake-wrapper, cluster-tokens, pg-fixture, cluster-spec]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# dispatcher loop

## Requirement

The dispatcher (D4).

`Dispatcher.run(stop)` wakes on NOTIFY `agent_free` or `message_queued`, and also every `settings.dispatch_poll_seconds`.

Each wake drains:
- Loop `claim_and_pick` until it returns None.
- For each claim, POST the turn to the picked agent's URL and session with the cluster's derived auth token, up to 8 sends in flight. Result mapping:
  - TurnAccepted: `mark_sent` with turn_id
  - Busy: `requeue`
  - Unavailable: `record_failure` with the cluster's `spec.max_attempts`
- Claim `interrupt` and `compact` commands and call `interrupt` or `command(compact)`. Complete each as done with the wrapper response, or as failed with the error.
- Call `fail_stale_dispatching(60)`.

A crash between claim commit and send leaves a dispatching row, which the stale rule fails rather than re-sends.

## Acceptance conditions

- AC1: three messages to three idle agents go one per agent in free_since order [evidence: test:tests/test_dispatcher.py::test_round_robin_by_free_since]
- AC2: a message waits while every agent is busy and is sent when one frees [evidence: test:tests/test_dispatcher.py::test_message_waits_until_agent_free]
- AC3: a 409 requeues the message [evidence: test:tests/test_dispatcher.py::test_409_requeues]
- AC4: a 503 fails the message at max_attempts [evidence: test:tests/test_dispatcher.py::test_503_fails_at_max_attempts]
- AC5: two dispatcher instances never send one message twice [evidence: test:tests/test_dispatcher.py::test_two_dispatchers_no_double_send]
- AC6: a lost NOTIFY is recovered by the poll [evidence: test:tests/test_dispatcher.py::test_notify_loss_recovered_by_poll]
- AC7: interrupt and compact commands reach the wrapper and complete [evidence: test:tests/test_dispatcher.py::test_interrupt_and_compact_commands]

## Files

- `src/agent_orchestrator/dispatcher/__init__.py`
- `src/agent_orchestrator/dispatcher/loop.py`
- `tests/test_dispatcher.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
