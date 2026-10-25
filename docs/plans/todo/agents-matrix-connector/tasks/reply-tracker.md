---
title: reply tracker
status: todo
repo: agents-matrix-connector
value: "the agent's answer arrives in the Messenger chat exactly once, with typing while it works"
files: [src/agents_matrix_connector/chunks.py, src/agents_matrix_connector/tracker.py, tests/test_tracker.py]
verify: "uv run --frozen pytest tests/test_tracker.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-settings-model, matrix-client-and-fake-hs, inbound-queue-repository, runs-and-outbound-repo]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 14
expected_tokens: 1883475
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# reply tracker

## Requirement

The reply tracker: turn results back into the Matrix room, typing, failure notices, idempotent sending and retention (design D9, D10). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/chunks.py`: `split(text: str, limit: int) -> list[str]`: no chunk longer than `limit`; split at the last blank line before the limit, else the last newline, else hard at the limit; chunks are stripped of leading and trailing blank lines; an empty or whitespace-only text gives `[]`.

`src/agents_matrix_connector/tracker.py`:

- `Tracker(orchestrator, matrix, pool, settings, *, now=utcnow)`, `async tick() -> None`.
- For each run `in-progress` with a message id: `orchestrator.get_message`:
  - turn `completed`: in one transaction `add_outbound(kind="reply", chunks=split(final_text, MATRIX_REPLY_CHUNK_CHARS))`, finish the run `handled` (reason `empty_reply` when there are no chunks) and `finish_run_rows(handled)`.
  - message `cancelled` or `failed` without a turn, or `NotFound`, on a `follow` run: finish `failed`, `session_gone`, and `requeue_run_rows` (the worker starts a new session).
  - turn `failed`, or message `failed`/`cancelled` on a `first` run: finish `failed` (`turn_failed`, `message_failed`, `message_cancelled`), `finish_run_rows(failed)`, and `add_outbound(kind="notice", chunks=["Sorry, the agent could not answer that message."])`.
  - older than `MATRIX_RUN_TIMEOUT_SECONDS`: finish `failed`, `timeout`, rows `failed`, the same notice.
  - still running: refresh `typing(True, 30000)`.
- Then send every `pending` outbound row oldest first with `send_text(room, txn_id, body)`; `mark_sent(event_id)`; `MatrixUnavailable` leaves it pending for the next tick; `MatrixForbidden` marks it `failed`, `forbidden`. After a run's last row is sent or failed, `typing(False)`.
- Once a day (first tick after the previous prune plus 24 h), prune `inbound`, `outbound` and finished `runs` older than `MATRIX_RETENTION_DAYS`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: split keeps every chunk within the limit preferring paragraph then line boundaries, and an empty text gives no chunk [evidence: test:tests/test_tracker.py::test_split_boundaries]
- AC2: a completed turn posts its final text to the room in chunks, finishes the run and its rows handled, and turns typing off [evidence: test:tests/test_tracker.py::test_completed_turn_replies]
- AC3: a crash after sending and before mark_sent re-sends with the same transaction id and the room gets one message [evidence: test:tests/test_tracker.py::test_resend_is_idempotent]
- AC4: a failed turn and a timeout fail the run and post one notice [evidence: test:tests/test_tracker.py::test_failure_and_timeout_notice]
- AC5: a follow run whose session is gone is failed session_gone and its rows go back to new with no notice [evidence: test:tests/test_tracker.py::test_follow_session_gone_requeues]
- AC6: an unavailable homeserver leaves replies pending and a forbidden room marks them failed [evidence: test:tests/test_tracker.py::test_send_errors]
- AC7: typing is refreshed while a run is in progress [evidence: test:tests/test_tracker.py::test_typing_refreshed]
- AC8: rows older than the retention are pruned once a day [evidence: test:tests/test_tracker.py::test_daily_prune]

## Files

- `src/agents_matrix_connector/chunks.py`
- `src/agents_matrix_connector/tracker.py`
- `tests/test_tracker.py`

## Interfaces

- `src/agents_matrix_connector/chunks.py`: `split`.
- `src/agents_matrix_connector/tracker.py`: `Tracker.tick`. Started by mxc-service-entrypoints in the `bot` process.
- Uses `OrchestratorClient.get_message` (`Message.status`, `Turn.status`, `Turn.final_text`), `FakeOrchestrator.complete_turn` / `fail_turn` / the session discard helper in tests.

## Expected outcome

After `FakeOrchestrator.complete_turn(message_id, "Hello")` one tick posts `Hello` to the fake room exactly once.

## Steps

- Red: `tests/test_tracker.py` with the eight tests (fixed clock, seeded runs and rows). Fails on the missing modules.
- Green: write `chunks.py` and `tracker.py`. Run the verify (Docker).

## Notes

- Review focus: replies use the deterministic transaction ids of `add_outbound`; the run and its rows finish in the same transaction that stores the outbound rows.
- Plain text body only, markdown left as written (design D9).
