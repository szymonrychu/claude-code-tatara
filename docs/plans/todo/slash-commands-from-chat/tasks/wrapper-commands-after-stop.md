---
title: wrapper commands after stop
status: todo
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

Design D9, verbatim: "The orchestrator dispatches a command even to a busy agent (D10); the wrapper queues it and runs it at the running turn's Stop (Claude Code itself holds commands typed while it responds until the turn ends: parity). When every pending command has origin `client`, `_stop_gate` lets the Stop complete the turn normally (`turn_completed`, final text intact) and the idle runner starts after the turn completed; no `continue_prompt`, no `turn_resumed`. Agent-origin commands keep the same-turn resume. This behaviour is isolated in task wrapper-commands-after-stop, so a gate change (for example interrupt and run now) is an amend of that one task (user decision 2)."

Scope (claude-code-wrapper): `router.py` (`_stop_gate` client-only leg returns None; after the completed turn's `turn_completed` the idle runner starts the queued client commands), `README.md` (`### Lifecycle`: client commands sent during a turn run after it completes, agent commands resume the same turn).

Tests no longer accurate (named): `tests/test_api_commands.py::test_client_command_during_turn_resumes_turn` pins a same-turn resume with the continue prompt for a client command; D9 changes it, so it becomes `test_client_command_during_turn_runs_after_turn_completes`. In `tests/test_command_turn_resume.py` the tests that use origin `client` only to exercise the same-turn resume (`test_command_runs_at_stop_and_turn_resumes`, `test_interrupt_cancels_queued_and_running`, `test_crash_mid_command_follows_k12`, `test_turn_max_seconds_counts_through_command`, `test_usage_accumulates_across_command`, `test_deferred_reason_and_resumed_cause`) switch to origin `agent`, which keeps that behaviour; `test_onstop_block_keeps_command_queued`, `test_background_defer_keeps_command_queued`, `test_interrupt_before_stop_cancels_queued` and the mixed-origin `test_continue_prompt_lists_results_with_same_marker` stay as they are.

## Acceptance conditions

- ac1: a client command queued during a turn runs after the turn completed: turn_completed with the turn's final_text, then command_started and command_completed, no turn_resumed, no continue prompt typed, all inputs typed while idle (new) [evidence: test:tests/test_command_turn_resume.py::test_client_only_commands_run_after_turn_completes_without_continue_prompt]
- ac2: an agent command queued during a turn still runs at the Stop and resumes the same turn with the continue prompt (new) [evidence: test:tests/test_command_turn_resume.py::test_agent_commands_still_resume_same_turn]
- ac3: through the API, POST /commands during a turn answers 202 queued with the turn_id and completes after the turn (renamed from test_client_command_during_turn_resumes_turn) [evidence: test:tests/test_api_commands.py::test_client_command_during_turn_runs_after_turn_completes]
- ac4: an interrupted turn cancels its queued client commands (ruling, unchanged pin) [evidence: test:tests/test_command_turn_resume.py::test_interrupt_before_stop_cancels_queued]
- ac5: a mixed agent and client queue resumes the turn once with every result listed [evidence: test:tests/test_command_turn_resume.py::test_continue_prompt_lists_results_with_same_marker]
- ac6: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_turn_resume.py tests/test_api_commands.py tests/test_stop_gate.py tests/test_command_runner.py tests/test_command_prompt_turn.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_command_turn_resume.py`
- `tests/test_api_commands.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
