---
title: api messages and commands
status: in-progress
repo: agent-orchestrator
value: "The headless way to talk to a cluster: send a message, watch its status, cancel or retry it, and control agents and checks."
files: [src/agent_orchestrator/api/messages.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/api/schemas.py, tests/test_api_messages.py]
verify: "uv run pytest tests/test_api_messages.py -q && mise run lint"
depends_on: [api-clusters-and-agents, dispatch-queue-sql]
owns: []
uses: [api-app, queue-sql]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-api-messages-and-commands/agent-orchestrator
branch: agent-orchestrator-api-messages-and-commands
verified_head: ""
run: ""
provides: []
---

# api messages and commands

## Requirement

Message, command and check routes (D4, D11, D24).

Messages:
- `POST /api/v1/clusters/{id}/messages {text, target_agent_id?}` returns 202 `{message_id, status: queued}`. Unknown cluster is 404. A deleting cluster is 409 `cluster_deleting`. A target agent not in the cluster is 422; a target agent that is gone is 422 `target_gone` (D23). Empty text is 422.
- `GET /api/v1/clusters/{id}/messages?status=&limit=` lists messages, newest first; `status` takes a comma list.
- `GET /api/v1/messages/{id}` returns the message (status queued, dispatching, verifying, sent, failed or cancelled; `attempts`, `max_attempts` from the cluster spec, `next_attempt_at` = `not_before`, `error`) plus `turn {status, started_at, completed_at, final_text}`, joined from turns by turn_id.
- `DELETE /api/v1/messages/{id}` cancels a queued message (204); otherwise 409 `not_queued`.
- `POST /api/v1/messages/{id}/retry` re-queues a failed message (202), resetting attempts, including one that failed with `ambiguous` after the verifier could not decide (the user's explicit choice, D24); otherwise 409 `not_failed`. Automatic retries need no call: the dispatcher requeues definite non-accepts with backoff.

Agent commands:
- `POST /api/v1/agents/{id}/interrupt|compact|restart` returns 202 `{command_id}`. Unknown agent is 404; a gone agent is 409.
- `GET /api/v1/commands/{id}`.

Checks:
- `POST /api/v1/clusters/{id}/checks {command}` returns 202 `{check_id}`.
- `GET /api/v1/checks/{id}` returns status, exit_code and log_tail.

## Acceptance conditions

- AC1: posting a message queues it and returns 202 with its id [evidence: test:tests/test_api_messages.py::test_post_message_queues_202]
- AC2: a deleting cluster or a foreign target agent is rejected [evidence: test:tests/test_api_messages.py::test_post_message_validation]
- AC3: GET message joins the turn status and final_text [evidence: test:tests/test_api_messages.py::test_get_message_with_turn]
- AC4: cancel works only while queued [evidence: test:tests/test_api_messages.py::test_cancel_only_queued]
- AC5: retry works only for failed messages [evidence: test:tests/test_api_messages.py::test_retry_only_failed]
- AC6: interrupt, compact and restart queue commands [evidence: test:tests/test_api_messages.py::test_agent_commands_queue_202]
- AC7: checks are queued and readable [evidence: test:tests/test_api_messages.py::test_checks_enqueue_and_get]
- AC8: the message list filters by status [evidence: test:tests/test_api_messages.py::test_list_messages_status_filter]
- AC9: a gone target agent is rejected with 422 target_gone [evidence: test:tests/test_api_messages.py::test_post_message_to_gone_target_rejected]
- AC10: a message that failed as ambiguous can be retried and carries its error reason in the view [evidence: test:tests/test_api_messages.py::test_retry_allowed_for_ambiguous_failure]
- AC11: the message view shows verifying, attempts, max_attempts and next_attempt_at for a message waiting out its backoff [evidence: test:tests/test_api_messages.py::test_message_view_retry_fields]

## Files

- `src/agent_orchestrator/api/messages.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/api/schemas.py`
- `tests/test_api_messages.py`

## Interfaces

- `agent_orchestrator.api.messages:router`; schemas `PostMessage`, `MessageView`, `CommandView`, `CheckView`

## Expected outcome

Headless clients and the UI can send, track, cancel and retry messages and drive agents.

## Steps

- Write tests/test_api_messages.py with the eleven named tests; run it; expect failures.
- Implement messages.py and include the router in create_app.
- Rerun `uv run pytest tests/test_api_messages.py -q`; expect `11 passed`; run `mise run lint`.

## Notes

The API only inserts and cancels queue rows (D3); all other transitions belong to the dispatcher and reconciler.
