---
title: wrapper merge guards
status: todo
repo: claude-code-wrapper
value: a mid-turn paste never answers a dialog and a flood of messages cannot pile up in one turn
files: [src/claude_code_wrapper/session.py, src/claude_code_wrapper/pty_proc.py, src/claude_code_wrapper/ring.py, src/claude_code_wrapper/config.py, README.md, tests/test_turn_merge_guards.py, tests/test_pty_proc.py]
verify: "uv run pytest tests/test_turn_merge_guards.py tests/test_turn_merge.py tests/test_pty_proc.py tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-immediate-turn-merge, wrapper-paste-hygiene]
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

# wrapper merge guards

## Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "message should get through PTY immediately and let either Claude Code or even agent queue them internally."

Goal G5 (README), verbatim: "slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open."

Design D4 (caps), verbatim: "the turn already holds `sessions.merge.max_unconfirmed` unconfirmed pastes (default 4) or `sessions.merge.max_per_turn` merged pastes (default 32) (429 `merge_queue_full`) (my call, the numbers mirror the command queue's `MAX_QUEUED` 4 and Claude Code's own queue bounds)."

Design D4 (dialog guard, interrogate 5), verbatim: "`dialog_open` (interrogate 5): the wrapper reads a named "current screen" source in which a dialog footer that was dismissed no longer matches (a byte tail alone does not qualify); the default patterns must match the permission, AskUserQuestion and MCP elicitation footers probe P6 captured; the check runs before the paste and again under the PTY lock just before the CR; a dialog seen at the second check withholds the CR, clears the unsent text with the key P6 recorded as safe and refuses 409 `dialog_open` with the entry removed. The dialog guard and the caps are task wrapper-merge-guards; the rest of D4 is wrapper-immediate-turn-merge."

Design D4 (order, interrogate 7), verbatim: "the onTurn hook first, then every refusal re-checked and the merge entry appended to the running record and persisted synchronously, then the paste; a paste that fails (`PtyClosed`) removes the entry. A Stop during the paste delay therefore already sees the pending merge (D6), and concurrent merges cannot pass the cap."

Design anti-goals, verbatim: "Text pasted while a slash command runs, while the turn is in its command phase or while a dialog is on screen (a CR answers a dialog, probe outA of the slash epic)." "An unbounded number of pastes into one turn (flood): capped, 429 (D4)."

Scope (claude-code-wrapper): `session.py` (`dialog_open` and cap checks inside `Session.merge`, the pre-CR re-check), `pty_proc.py` (`send_prompt` takes a check run under its lock before the CR), `ring.py` (the current-screen source, if the builder builds it there), `config.py` (`sessions.merge.max_unconfirmed`, `sessions.merge.max_per_turn`, dialog defaults extended to the captured footers), `README.md` (screen source, codes, configuration), `tests/test_turn_merge_guards.py` (new), `tests/test_pty_proc.py`.

## Acceptance conditions

- ac1: with a dialog footer on the current screen, POST /turns immediate while a turn runs answers 409 dialog_open and nothing is typed (new) [evidence: test:tests/test_turn_merge_guards.py::test_dialog_on_screen_refuses_merge]
- ac2: the default dialog patterns match every dialog block of tests/fixtures/screens/midturn-dialogs.txt captured by probe P6 (permission, AskUserQuestion, MCP elicitation) (new) [evidence: test:tests/test_turn_merge_guards.py::test_default_patterns_match_captured_dialog_footers]
- ac3: once the captured dismissal output has followed a footer, the dismissed footer no longer refuses and the merge is accepted (new) [evidence: test:tests/test_turn_merge_guards.py::test_dismissed_dialog_does_not_refuse_merge]
- ac4: a dialog that appears between the paste and the CR withholds the CR, writes the clear key P6 recorded, removes the merge entry from the record and answers 409 dialog_open (new) [evidence: test:tests/test_turn_merge_guards.py::test_dialog_between_paste_and_cr_withholds_the_cr]
- ac5: send_prompt runs its check under the PTY lock after the paste delay and before the CR, and writes no CR when the check refuses (new) [evidence: test:tests/test_pty_proc.py::test_send_prompt_checks_before_the_cr]
- ac6: with max_unconfirmed unconfirmed pastes the next merge is 429 merge_queue_full and writes nothing; once one is absorbed a new paste is accepted; past max_per_turn merges the next is 429 merge_queue_full (new) [evidence: test:tests/test_turn_merge_guards.py::test_unconfirmed_and_per_turn_caps]
- ac7: concurrent merge requests never leave more than max_unconfirmed unconfirmed entries on the record, the surplus answered 429 merge_queue_full (new) [evidence: test:tests/test_turn_merge_guards.py::test_concurrent_merges_respect_the_cap]
- ac8: README names the current-screen source, dialog_open, merge_queue_full and sessions.merge.max_unconfirmed and max_per_turn, and the README and config guards pass [evidence: command:grep -q 'dialog_open' README.md && grep -q 'merge_queue_full' README.md && grep -q 'max_unconfirmed' README.md && uv run pytest tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py]
- ac9: targeted suites and lint pass [evidence: command:uv run pytest tests/test_turn_merge_guards.py tests/test_turn_merge.py tests/test_pty_proc.py tests/test_readme_config.py tests/test_readme_api.py tests/test_config.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/pty_proc.py`
- `src/claude_code_wrapper/ring.py`
- `src/claude_code_wrapper/config.py`
- `README.md`
- `tests/test_turn_merge_guards.py`
- `tests/test_pty_proc.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
