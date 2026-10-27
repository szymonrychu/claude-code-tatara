---
title: wrapper commands after stop
status: in-progress
repo: claude-code-wrapper
value: "a command sent while the agent works runs after that turn, with no fabricated continue prompt"
files: [src/claude_code_wrapper/router.py, README.md, tests/test_command_turn_resume.py, tests/test_api_commands.py]
verify: "uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py tests/test_stop_gate.py tests/test_command_runner.py tests/test_command_prompt_turn.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-prompt-command-turn]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper commands after stop

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards." User request, verbatim: "Allow these commands to be run from chat window at any moment."

Design D9, verbatim: "The orchestrator dispatches a command even to a busy agent (D10); the wrapper queues it and runs it at the running turn's Stop (Claude Code itself holds commands typed while it responds until the turn ends: parity). When every pending command has origin `client`, `_stop_gate` lets the Stop complete the turn normally (`turn_completed`, final text intact) and the idle runner starts after the turn completed; no `continue_prompt`, no `turn_resumed`. Agent-origin commands keep the same-turn resume. Slot handover (my call, interrogate item 4): the router takes the slot for the queued client commands (`_start_idle_runner`, `Session.begin_command`) synchronously right after `session.complete` and before any await (onTurnComplete, the callback), so a `POST /turns` right after `turn_completed` gets 409 `busy` until the queued commands drained; prose can no longer take the slot ahead of them. This behaviour is isolated in task wrapper-commands-after-stop, so a gate change (for example interrupt and run now) is an amend of that one task (user decision 2)."

Interrogate item 4 (interrogate.md), verbatim: "Slot handover at Stop (B, C; A judged it no-hang). The idle runner starts after the awaited onTurnComplete hooks, so prose can take the slot before queued commands. Take the slot for queued commands at Stop before any await; AC: a POST /turns right after turn_completed gets 409 until the commands drain."

User decision, verbatim: "Keep [...] the mid-turn behaviour isolated in one task." and "Do not change the two gate questions' defaults (deny list exists; mid-turn commands accepted at once and run at the turn's Stop)".

Scope (claude-code-wrapper): `router.py` (`_stop_gate` client-only leg returns None; in `_on_stop`, right after `session.complete` returns the completed record and before `_after_turn` is awaited, `_start_idle_runner` takes the slot for the queued client commands), `README.md` (`### Lifecycle`: client commands sent during a turn run after it completes, before any new turn; agent commands resume the same turn).

Tests no longer accurate (named): `tests/test_api_commands.py::test_client_command_during_turn_resumes_turn` pins a same-turn resume with the continue prompt for a client command; D9 changes it, so it becomes `test_client_command_during_turn_runs_after_turn_completes`. In `tests/test_command_turn_resume.py` the tests that use origin `client` only to exercise the same-turn resume (`test_command_runs_at_stop_and_turn_resumes`, `test_interrupt_cancels_queued_and_running`, `test_crash_mid_command_follows_k12`, `test_turn_max_seconds_counts_through_command`, `test_usage_accumulates_across_command`, `test_deferred_reason_and_resumed_cause`) switch to origin `agent`, which keeps that behaviour; `test_onstop_block_keeps_command_queued`, `test_background_defer_keeps_command_queued`, `test_interrupt_before_stop_cancels_queued` and the mixed-origin `test_continue_prompt_lists_results_with_same_marker` stay as they are.

## Acceptance conditions

- ac1: a client command queued during a turn runs after the turn completed: turn_completed with the turn's final_text, then command_started and command_completed, no turn_resumed, no continue prompt typed, all inputs typed while idle (new) [evidence: test:tests/test_command_turn_resume.py::test_client_only_commands_run_after_turn_completes_without_continue_prompt]
- ac2: an agent command queued during a turn still runs at the Stop and resumes the same turn with the continue prompt (new) [evidence: test:tests/test_command_turn_resume.py::test_agent_commands_still_resume_same_turn]
- ac3: through the API, POST /commands during a turn answers 202 queued with the turn_id and completes after the turn (renamed from test_client_command_during_turn_resumes_turn) [evidence: test:tests/test_api_commands.py::test_client_command_during_turn_runs_after_turn_completes]
- ac4: slot handover: with a slow onTurnComplete hook and client commands queued, a POST /turns sent right after turn_completed answers 409 busy until the queued commands completed, then 202; the session never shows ready between turn_completed and the first command_started (new) [evidence: test:tests/test_api_commands.py::test_turn_refused_until_queued_client_commands_drain]
- ac5: an interrupted turn cancels its queued client commands (ruling, unchanged pin) [evidence: test:tests/test_command_turn_resume.py::test_interrupt_before_stop_cancels_queued]
- ac6: a mixed agent and client queue resumes the turn once with every result listed [evidence: test:tests/test_command_turn_resume.py::test_continue_prompt_lists_results_with_same_marker]
- ac7: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py tests/test_stop_gate.py tests/test_command_runner.py tests/test_command_prompt_turn.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_command_turn_resume.py`
- `tests/test_api_commands.py`

## Interfaces

- No API change: `POST /v1/sessions/{id}/commands` during a turn answers 202 `queued` with `turn_id`, as today.

## Expected outcome

A command a user sends while the agent works waits for that turn's Stop; the turn completes untouched and the command then runs on the idle session. No fabricated "continue" prompt appears for a human-sent command.

## Steps

- Red: add ac1, ac2 and ac4, rename and rewrite the API test (ac3), switch the named resume tests to origin agent; run `uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py`: ac1, ac3 and ac4 fail.
- Green: change `_stop_gate` and the post-completion runner start, README; run the task's verify: passes. Quote the summary line.

## Notes

- Ruling, pinned by ac5: an interrupted or failed turn cancels its queued client commands (today's behaviour, kept).
- Ruling, pinned by ac4: the slot is taken for queued client commands synchronously after `session.complete`, before `_after_turn` is awaited (`begin_command` is synchronous; no await in between).
- A gate change of the mid-turn behaviour amends only this task (user decision 2).
- Depends on wrapper-prompt-command-turn (sequenced: router.py).

- 2026-10-27 amended: interrogate item 4 (take the slot for queued client commands at Stop before any await; POST /turns gets 409 until they drain), design D9 revised; gate default kept (run at the turn's Stop)
