---
title: wrapper peer priority
status: todo
repo: claude-code-wrapper
value: "hive peers' messages reach a busy session at once, with wait-until-idle on request"
files: [src/claude_code_wrapper/mcp_server.py, src/claude_code_wrapper/peer_service.py, src/claude_code_wrapper/peer_client.py, src/claude_code_wrapper/peer_inbox.py, README.md, tests/test_peer_priority.py]
verify: "uv run pytest tests/test_peer_priority.py tests/test_peer_inbox.py tests/test_peer_inbox_outcomes.py tests/test_mcp_peers.py tests/test_peer_service.py tests/test_peer_client.py tests/test_peers_readme.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-merge-stop-gate]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper peer priority

## Requirement

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D17, verbatim: "`send_message` gains `priority` (`immediate` default, `idle`), carried on the peer wire to the receiving instance; the receiver's `PeerInbox` delivers an `immediate` item while the session is busy through `SessionRouter.submit_turn(priority="immediate")` (a merge), and an `idle` item as today. Refusals (D4 409s, 429) keep the item queued for the next state change. `notify_when_idle` is unchanged and reports `delivered` once the handling turn, merged or not, is terminal; several items may map to one turn."

Scope (claude-code-wrapper): `mcp_server.py` (`send_message` schema, argument check, description), `peer_service.py` (send and receive carry `priority`), `peer_client.py` (wire model field), `peer_inbox.py` (`InboxItem.priority`, the immediate delivery path, several items per turn for `notify_when_idle`), `README.md` (peer tool and wire docs), `tests/test_peer_priority.py` (new).

## Acceptance conditions

- ac1: send_message accepts priority immediate or idle, defaults to immediate, and answers invalid arguments for any other value (new) [evidence: test:tests/test_peer_priority.py::test_send_message_priority_argument]
- ac2: the priority travels on the peer wire and reaches the receiving inbox item (new) [evidence: test:tests/test_peer_priority.py::test_priority_travels_on_the_peer_wire]
- ac3: an immediate item for a busy session is delivered at once as a merge into the running turn; peer_message_delivered carries that turn id (new) [evidence: test:tests/test_peer_priority.py::test_immediate_peer_message_merges_into_busy_turn]
- ac4: an idle item waits for a ready session as today (new) [evidence: test:tests/test_peer_priority.py::test_idle_peer_message_waits_for_ready]
- ac5: an immediate item refused with command_active, dialog_open, interrupting or merge_queue_full stays queued and is delivered after the next state change (new) [evidence: test:tests/test_peer_priority.py::test_refused_immediate_item_stays_queued]
- ac6: with notify_when_idle, each of two items merged into one turn gets its delivered outcome once that turn is terminal (new) [evidence: test:tests/test_peer_priority.py::test_notify_when_idle_for_items_merged_into_one_turn]
- ac7: the peer inbox, MCP and README guards stay green unchanged [evidence: command:uv run pytest tests/test_peer_inbox.py tests/test_peer_inbox_outcomes.py tests/test_mcp_peers.py tests/test_peers_readme.py]
- ac8: targeted suites and lint pass [evidence: command:uv run pytest tests/test_peer_priority.py tests/test_peer_inbox.py tests/test_peer_inbox_outcomes.py tests/test_mcp_peers.py tests/test_peer_service.py tests/test_peer_client.py tests/test_peers_readme.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/mcp_server.py`
- `src/claude_code_wrapper/peer_service.py`
- `src/claude_code_wrapper/peer_client.py`
- `src/claude_code_wrapper/peer_inbox.py`
- `README.md`
- `tests/test_peer_priority.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
