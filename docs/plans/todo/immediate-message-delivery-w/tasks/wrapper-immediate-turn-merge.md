---
title: wrapper immediate turn merge
status: todo
repo: claude-code-wrapper
value: a message sent to a busy agent reaches it mid-turn at once instead of waiting for the turn to end
files: [src/claude_code_wrapper/api/turns.py, src/claude_code_wrapper/router.py, src/claude_code_wrapper/session.py, src/claude_code_wrapper/turns.py, src/claude_code_wrapper/config.py, README.md, tests/test_turn_merge.py, tests/test_api_turns.py]
verify: "uv run pytest tests/test_turn_merge.py tests/test_api_turns.py tests/test_submit_busy_first.py tests/test_stop_gate.py tests/test_session_turns.py tests/test_user_message_event.py tests/test_command_turn_resume.py tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-merge-marker-parse, wrapper-fake-claude-queue]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 16
expected_tokens: 3197775
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper immediate turn merge

## Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "Improvement idea to messaging system- currently the messages wait for too long. Ask agents to queue another epic- message should get through PTY immediately and let either Claude Code or even agent queue them internally." Scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goals G1, G3 and G5 (README), verbatim: "a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle." "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)." "slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open."

Design D1 (wrapper part), verbatim: "`idle` is exactly today's behaviour: it waits for an idle leader and the wrapper refuses it with 409 `busy` while a turn runs. The wrapper default is `immediate` too (Q8), and the orchestrator always sends the field explicitly."

Design D2, verbatim: "The wrapper writes the message with its existing `PtyProcess.send_prompt` (bracketed paste, then CR after `boot.submit_delay_seconds`, under the PTY lock, so no other writer interleaves)."

Design D3, verbatim: "When a turn runs, an `immediate` message is pasted as `<text>\n\n<!-- ccw turn: <running turn id> -->\n<!-- ccw merge: <merge id> -->`, the running turn's marker (the `continue_turn` / `_with_marker` convention) plus a new per-paste merge marker. The wrapper answers 202 `{turn_id: <running turn id>, state: "running", merged: true, merge_id}`. Several messages then share one turn and its `final_text`; the orchestrator links each to that turn (`messages.turn_id`). A test pins that a mid-turn paste never carries another turn id in its turn marker. A session that is ready takes an `immediate` message as a normal new turn, as today (`merged: false`). A turn of any origin (client, agent, peer) can absorb a merge (my call)."

Design D4, verbatim: "No new endpoint: `TurnRequest.priority`. While a turn runs, an `immediate` message is refused, and nothing is pasted, when: the turn is in its command phase or a slash command is running or queued for the Stop (409 `command_active`); the slash epic's `DialogScanner` patterns match the current screen (409 `dialog_open`); an interrupt of the turn is in flight (409 `interrupting`); the turn already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or `sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) (my call, the numbers mirror the command queue's `MAX_QUEUED` 4 and Claude Code's own queue bounds). `idle` while busy stays 409 `busy`; booting and dead stay 503. The onTurn hook fires for a merge too, with `merge_into: <turn id>` in its payload; a deny is 403 `vetoed`; its annotations shallow-merge into the turn's (my call). `files` are written as for a turn; a merge's `callbackUrl` is kept on its merge entry and receives the turn's terminal event (my call). Events: `user_message` at paste time (turn_id of the running turn, `merged: true`), `turn_merged {turn_id, merge_id, origin, metadata}` at paste time, `turn_merge_absorbed {turn_id, merge_id}` when the transcript shows the paste."

Design D5 (record and router part), verbatim: "`TurnRecord.merged: list[MergedPrompt]`, `MergedPrompt {merge_id, origin, metadata, callback_url, pasted_at, absorbed_at}` (persisted with the record, served by `GET /turns/{id}`). [...] The router sets `absorbed_at` once (first sighting) and emits `turn_merge_absorbed`. A merge marker never moves `_last_marker` by itself: the turn marker on the same line names the running turn."

Design D8 (wrapper part), verbatim: "Immediate prose is never pasted while a command runs or waits for the Stop (D4 `command_active`), and the slash epic's slot handover at Stop keeps queued client commands ahead of prose."

Scope (claude-code-wrapper): `api/turns.py` (`TurnRequest.priority`, response `merged`, `merge_id`, the new refusal codes), `router.py` (`submit_turn(priority=...)`, the merge leg, onTurn `merge_into`, events, `merge_marker` handling in `_on_transcript_events`, callback delivery to merge entries), `session.py` (`Session.merge`: refusal checks, marker text, paste under the existing lock, record update), `turns.py` (`MergedPrompt`, `TurnRecord.merged`), `config.py` (`sessions.merge.max_unconfirmed`, `sessions.merge.max_per_turn`), `README.md` (API, events, configuration), `tests/test_turn_merge.py` (new); the MEMORY.md entry on the merge model is written by task wrapper-merge-stop-gate. Tests no longer accurate (named): `tests/test_api_turns.py::test_submit_busy_409_and_booting_503` keeps its 409 for a body with `priority: "idle"`; its stub router's `submit_turn` gains the `priority` parameter; this file is changed only for that.

## Acceptance conditions

- ac1: POST /turns with priority immediate, and with no priority, while a turn runs answers 202 {turn_id of the running turn, state running, merged true, merge_id}; exactly one paste reaches the fake (new) [evidence: test:tests/test_turn_merge.py::test_immediate_while_busy_merges_into_running_turn]
- ac2: wedge pin: the pasted text ends with the running turn's turn marker and the merge marker, and no turn marker written while that turn runs names any other turn id (new) [evidence: test:tests/test_turn_merge.py::test_midturn_paste_never_carries_a_new_turn_marker]
- ac3: priority idle while busy answers 409 busy and nothing is typed (new) [evidence: test:tests/test_turn_merge.py::test_idle_while_busy_is_409_busy]
- ac4: priority immediate on a ready session starts a normal new turn: 202 merged false, turn_started emitted (new) [evidence: test:tests/test_turn_merge.py::test_immediate_on_ready_session_starts_a_turn]
- ac5: refusals write nothing to the PTY: 409 command_active while a slash command runs, while one is queued for the Stop and while the turn is in its command phase; 409 dialog_open while a dialog footer pattern is on screen; 409 interrupting while an interrupt is in flight (new) [evidence: test:tests/test_turn_merge.py::test_refusals_while_busy_write_nothing]
- ac6: caps: with max_unconfirmed unconfirmed pastes the next is 429 merge_queue_full; once one is absorbed a new paste is accepted; past max_per_turn merges the next is 429 merge_queue_full (new) [evidence: test:tests/test_turn_merge.py::test_unconfirmed_and_per_turn_caps]
- ac7: GET /turns/{id} lists the merge entries with pasted_at; with the fake in queue mode absorbed_at is set when the transcript shows the merge marker and turn_merge_absorbed is emitted once; _last_marker stays the running turn's id (new) [evidence: test:tests/test_turn_merge.py::test_merge_absorbed_from_transcript]
- ac8: at paste time user_message (turn_id of the running turn, merged true) and turn_merged {turn_id, merge_id, origin, metadata} are emitted, and no turn_started (new) [evidence: test:tests/test_turn_merge.py::test_merge_events]
- ac9: onTurn fires for a merge with merge_into; a deny answers 403 vetoed and nothing is typed; allow annotations merge into the turn's annotations (new) [evidence: test:tests/test_turn_merge.py::test_on_turn_on_merge]
- ac10: with the fake in queue mode a message merged during a tool step ends with the running turn: one turn_completed whose final_text answers after the injection, the session ready afterwards, the merge's callbackUrl receiving the terminal event (new) [evidence: test:tests/test_turn_merge.py::test_merged_message_completes_with_running_turn]
- ac11: limits.max_prompt_bytes and the 16 KiB metadata cap apply to a merge (413 too_large) (new) [evidence: test:tests/test_turn_merge.py::test_merge_size_limits]
- ac12: the stub-based API test keeps 409 busy for an idle body (renamed body only, named) [evidence: test:tests/test_api_turns.py::test_submit_busy_409_and_booting_503]
- ac13: README documents priority, merged, merge_id, the refusal codes, the merge events and sessions.merge.*, and the config and API README guards stay green [evidence: command:uv run pytest tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py]
- ac14: targeted suites and lint pass [evidence: command:uv run pytest tests/test_turn_merge.py tests/test_api_turns.py tests/test_submit_busy_first.py tests/test_stop_gate.py tests/test_session_turns.py tests/test_user_message_event.py tests/test_command_turn_resume.py tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/api/turns.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/turns.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_turn_merge.py`
- `tests/test_api_turns.py`

## Interfaces

- `api/turns.py:TurnRequest.priority: Literal["immediate", "idle"] = "immediate"`. Response 202: `{"turn_id", "state", "merged": bool, "merge_id": str | None}`. Refusals: 409 `busy` (idle while busy), 409 `command_active`, 409 `dialog_open`, 409 `interrupting`, 429 `merge_queue_full`, 503 `booting` / `dead`, 403 `vetoed`, 413 `too_large`.
- `router.SessionRouter.submit_turn(text, *, files=None, callback_url=None, origin="client", metadata=None, priority: Literal["immediate", "idle"] = "idle") -> TurnRecord | MergeResult`: the router's own default stays `idle` so internal callers (peer inbox, tests) keep today's behaviour; the API passes the body's value. The builder picks the return shape (for example a `MergeResult(record, merge_id)`), documented in the docstring.
- `session.Session.merge(text, *, origin, metadata, callback_url) -> MergedPrompt`: raises `TurnRejected("busy" | "command_active" | "dialog_open" | "interrupting" | "merge_queue_full" | "booting" | "dead")`; pastes `self._with_marker(text, running)` plus `\n<!-- ccw merge: <merge_id> -->` through `pty.send_prompt`, appends the entry to `running.merged`, persists.
- `turns.MergedPrompt(BaseModel)`: `merge_id: str`, `origin: Origin`, `metadata: dict`, `callback_url: str | None` (alias `callbackUrl`), `pasted_at: str`, `absorbed_at: str | None = None`. `TurnRecord.merged: list[MergedPrompt] = []`.
- `config.py`: `sessions.merge.max_unconfirmed: int = 4`, `sessions.merge.max_per_turn: int = 32` (task wrapper-merge-stop-gate adds `settle_seconds`).
- Events: `user_message` gains `merged: true` on the merge leg; new `turn_merged`, `turn_merge_absorbed`.

## Expected outcome

A message posted to a busy session is pasted into the running turn at once, joins it and is answered by its final text; the session cannot wedge on the marker; commands, dialogs and interrupts are never disturbed by a paste; a flood is refused with 429.

## Steps

- Read `api/turns.py`, `router.py` (`submit_turn`, `_submit_turn`, `_on_transcript_events`, `_after_turn`, `_deliver`), `session.py` (`check_submittable`, `submit`, `continue_turn`, `_with_marker`, `command_active`, `_commands_turn`, `_interrupting`), `turns.py`, `config.py`, the slash epic's `DialogScanner` and command queue in `commands.py` / `router.py`, `tests/test_api_turns.py`, `tests/test_submit_busy_first.py`, `tests/test_stop_gate.py`, `tests/conftest.py`, the fake's queue mode and `docs/claude-midturn-input.md` in one pass.
- Red: write `tests/test_turn_merge.py` with every test named ac1 to ac11 (fake claude in `"midturn_input": "queue"` where absorption is needed) and change the stub signature in `tests/test_api_turns.py`; run `uv run pytest tests/test_turn_merge.py tests/test_api_turns.py`; expect the new tests to fail.
- Green: implement the field, the merge leg, the refusals, the record, the events, the absorption handling and README; run the task's verify; expect all passed. Quote the summary line.

## Notes

- The anti-goal this task pins: never `new_turn_id()` on the merge leg; the turn marker is always the running record's (`_with_marker`).
- `check_submittable` stays the idle-path gate; the merge leg has its own checks in `Session.merge`, all synchronous before the paste (no await between the checks and the slot-free write except the PTY lock).
- `dialog_open`: read the current screen with the slash epic's `DialogScanner` patterns (`sessions.commands.dialog_patterns`); the builder chooses ring tail or screen snapshot.
- Per-task security check (retro, recurring): this route sends text into a running agent on a caller's behalf; check the size caps, the 429 cap, the onTurn veto and that no metadata or text reaches a log line beyond today's redaction.
- If the probe's consequences table contradicts D3, D4 or D5, the orchestrator amends this task before it starts; do not work around a contradiction here.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: files capped at 8: the MEMORY.md entry moves to wrapper-merge-stop-gate
