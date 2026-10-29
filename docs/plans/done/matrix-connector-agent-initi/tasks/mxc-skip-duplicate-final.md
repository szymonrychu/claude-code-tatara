---
title: mxc skip duplicate final
status: done
repo: agents-matrix-connector
value: "an answer the agent already sent is not posted a second time as the turn's final reply"
files: [src/agents_matrix_connector/tracker.py, src/agents_matrix_connector/db/sends.py, README.md, tests/test_tracker.py, tests/test_readme_api.py]
verify: "uv run pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint"
depends_on: [mxc-bot-sends-delivery, mxc-agent-routes]
model: sonnet
review: ""
verified_head: f9d489922cfa4ac63b49747906c4e83be4ea6ba0
points: 5
expected_minutes: 8
expected_tokens: 1847647
points_actual: 5
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc skip duplicate final

## Requirement

README Non-goal, verbatim: "No automatic forwarding of every final reply of every turn to the chat (agents use the send tool)."

Design D10, verbatim:

> When a chat-started run's turn completes, the tracker compares its `final_text`, stripped, with the
> stripped `text` of every `message` send of the same session created at or after the run's
> `started_at`. Only a send that reached the user counts (interrogate Act 3, the lead's call):
>
> - a matching send that is `sent`: the run closes `handled` with reason `already_sent` and no outbound row is stored;
> - else a matching send still `queued` or `sending`: the run stays in progress and the check repeats each tick until that send settles, bounded by the run timeout (`MATRIX_RUN_TIMEOUT_SECONDS` from the run's `started_at`); when the timeout passes first, the final answer is posted (my call: a late duplicate beats a lost answer);
> - a matching send that ended `failed` or `refused` does not count, so the final answer is posted.
>
> Anything else posts as today.

Design anti-goal, verbatim: "Double output: the same text posted twice because the agent sent it and its final answer repeated it."

Scope (agents-matrix-connector): `tracker.py` (the match in the completed-turn branch, a new reason constant `ALREADY_SENT = "already_sent"`), the query in `db/sends.py`, README (the reason). `tests/test_readme_api.py::test_readme_lists_every_reason` gains `tracker.ALREADY_SENT` in its reason set (extended, nothing removed).

Interrogate verdict, verbatim: "3. Failed send suppresses the final answer (A,B,C medium): D10 matching must count only sends that reached the user. My call: match only `sent` sends; a matching send still `queued`/`sending` when the final answer is ready delays the close until it settles (bounded by the run timeout), and if it ends `failed` the final answer is posted. AC for failed and for queued-then-failed."

## Acceptance conditions

- ac1: a completed chat run whose final text equals a sent message send of the same session made during the run is handled with reason already_sent and stores no outbound row [evidence: test:tests/test_tracker.py::test_final_text_already_sent_is_not_posted]
- ac2: a different text, a send made before the run started, a reaction and another session's send all leave the reply posted as today [evidence: test:tests/test_tracker.py::test_final_text_posted_unless_already_sent]
- ac3: a matching send that ended failed, and one that ended refused, do not count: the final answer is posted [evidence: test:tests/test_tracker.py::test_final_text_posted_when_matching_send_failed]
- ac4: while a matching send is queued or sending the completed run stays in progress; when that send then fails the final answer is posted, and when it is then sent the run closes already_sent with no outbound row [evidence: test:tests/test_tracker.py::test_pending_matching_send_delays_close]
- ac5: a matching send still pending when the run timeout passes does not hold the run longer: the final answer is posted [evidence: test:tests/test_tracker.py::test_pending_match_bounded_by_run_timeout]
- ac6: README names the already_sent reason and the rule that only a delivered send suppresses the final answer [evidence: test:tests/test_readme_api.py::test_readme_lists_every_reason]
- ac7: the existing tracker behaviour is unchanged [evidence: test:tests/test_tracker.py::test_completed_turn_replies]
- ac8: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_tracker.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_matrix_connector/tracker.py`
- `src/agents_matrix_connector/db/sends.py`
- `README.md`
- `tests/test_tracker.py`
- `tests/test_readme_api.py`

## Interfaces

- `tracker.py:ALREADY_SENT = "already_sent"`.
- `db/sends.py:message_sends_since(conn, session_id, since) -> list[tuple[str, str]]` (name left to the builder): `(text, status)` of the session's message sends created at or after `since`.
- `tracker.py:Tracker._outcome`: a completed turn with a `sent` match closes `already_sent`; with only a `queued`/`sending` match returns None (still running) until the run timeout, then posts; otherwise posts.

## Expected outcome

An agent that sends its answer with `orchestrator_chat_send` during a chat-started turn and ends the turn with the same text does not post it twice.

## Steps

- Red: add the two tracker tests and `ALREADY_SENT` to the README reason test; run `uv run pytest tests/test_tracker.py tests/test_readme_api.py`: they fail.
- Green: tracker, query, README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Compare `str.strip()` of both sides only; no fuzzy matching (D10).
- While the close waits on a pending match, the run stays in progress, so the room's next batch waits too (as for any running run); typing stays on as for a running turn.
- The inbound rows of the run settle `handled` with the same reason, as for `empty_reply`.
- DB-backed tracker tests (CI); `test_readme_api.py` runs locally.

- 2026-10-27 amended: interrogate.md Act 3: only sent sends suppress the final answer; pending matches delay the close within the run timeout

- 2026-10-28 done: CI 40747755877 green

- 2026-10-28 actuals: no agent records
