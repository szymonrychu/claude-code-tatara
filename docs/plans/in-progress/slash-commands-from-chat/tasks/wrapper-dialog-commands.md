---
title: wrapper dialog commands
status: done
repo: claude-code-wrapper
value: dialog commands sent from the chat are dismissed by ESC inside a bound instead of wedging the session
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/session.py, src/claude_code_wrapper/router.py, tests/fake_claude/fake_claude.py, README.md, tests/test_command_dialogs.py, tests/test_fake_claude_commands.py]
verify: "uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_registry.py tests/test_readme_config.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-command-signals]
model: opus
review: ""
verified_head: 24ccb08f4951172e55a940f320dde143ae2c5275
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: 5
actual_minutes: 55
actual_tokens: 11619840
actual_roles: "impl 50, review 5"
actual_role_tokens: "impl 11358635, review 261205"
---

# wrapper dialog commands

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D7, verbatim: "A `DialogScanner` (a `FatalScanner` over `sessions.commands.dialog_patterns`, default `esc to cancel`, `esc to close`, `esc to clear`, `esc to exit`, `enter to confirm`) is fed the PTY output from the mark. No completion signal and a dialog hit -> wait `dialog_grace_seconds` (2.0, restarted by any PTY output) for a late signal, then ESC; 1.5 s later, if still no `command_output` and the scanner hit again since the ESC, ESC again (budget 3, never two ESCs within 1 s: a double ESC at an empty prompt opens the rewind menu). Output after an ESC -> completed `dismissed`, output = claude's stdout ("Help dialog dismissed"). No output after the budget -> failed `dialog_stuck`. Timeout (`timeout_seconds[name]`, default 60, compact 600) -> ESC, 1.5 s, a second ESC only when a dialog pattern is on screen -> failed `timeout`. Compact is excluded from dialog detection (its own leg). One deadline per command (my call, interrogate item 7): `timeout_seconds[name]` counts from the runner taking the command and is spent by the quiet wait, typing, the completion wait and the dialog leg together (today `wait_quiet` and the completion wait each spend a full `timeout`, about 2x the stated bound). A dialog left open (my call, interrogate item 6): when a command ends `dialog_stuck`, or `timeout` with a dialog pattern still on screen after the last ESC, claude is restarted through the existing relaunch path (`Session._recover`: `_boot(resume=True)`, the same pinned claude session id) before the slot is released, so the next turn never lands in an open dialog (a paste into an open dialog acts on it, probe outA). This wrapper-initiated restart does not count against `max_restarts` (my call: three stuck dialogs must not kill a session), emits the usual restart event, and a failed relaunch takes the crash path's outcome (dead). Dialog commands stay allowed: "dismissed" with claude's own message is the honest answer for a chat with no keyboard (user decision 1)."

Design Bounds, verbatim: "one deadline per command (my call, interrogate item 7): `timeout_seconds[name]` (`default` 60 s, `compact` 600 s; operators may add names), counted from the runner taking the command and spent by the quiet wait (`quiet_seconds` 1.5 s), typing, the completion wait and the dialog leg together; "screen never settled" fails `timeout` at that deadline.", "dialog: `dialog_grace_seconds` 2.0 s after the first footer hit; ESC budget 3, 1.5 s apart, never two ESCs within 1 s; `dialog_stuck` after the budget; all inside the deadline.", "at the deadline: ESC, 1.5 s, a second ESC only with a dialog pattern on screen -> `timeout`.", "dialog still open after `dialog_stuck` or `timeout` (my call, interrogate item 6): one claude relaunch with `--resume` before the slot is released, bounded by `boot.timeout_seconds` (60 s); it does not count against `max_restarts`." and "worst-case slot hold for a non-promoted command: timeout + 1.5 s = about 62 s (default), plus one relaunch of at most `boot.timeout_seconds` 60 s when a dialog stays open."

Interrogate item 6 (interrogate.md), verbatim: "Dialog left open after the ESC budget (C). On `dialog_stuck` or `timeout` with a dialog still on screen, restart claude through the existing restart path before releasing the slot; AC."

Interrogate item 7, verbatim: "One deadline per command (C). wait_quiet plus _await_completion each spend `timeout`, so the real bound is about 2x the stated one; use one deadline and pin it."

Scope (claude-code-wrapper): `config.py` (`CommandsConfig.dialog_grace_seconds: float = 2.0` (ge 0), `dialog_patterns: list[str]` with the five defaults; `CommandsOverride` mirrors both), `session.py` (a dialog scanner over the PTY output, reset at the mark, with "hit since" and "on screen now" queries; an ESC helper that never sends two ESCs within 1 s; a wrapper-initiated restart of claude through the relaunch path with `--resume` that leaves `restarts` unchanged), `router.py` (`_run_command` computes one deadline and passes the remaining time to `wait_quiet` and `_await_completion`; `_await_completion` dialog leg and the conditional second ESC of the timeout leg; result `dismissed`, error `dialog_stuck`; the restart before `end_command` when a dialog is still on screen), `tests/fake_claude/fake_claude.py` (scenario `commands.<name>.dialog: {footer, dismiss_stdout, escs: 1|2|"never"}`: print the footer, write nothing until the given number of ESCs, then the system echo and the stdout; "never" keeps the footer on screen; ESC keys already logged to `fake-keys.jsonl` by wrapper-command-signals), `README.md` (config rows; `### Lifecycle` of `## Slash commands` describes dialogs, the restart and the bound).

Real samples the fake must match: `/workdir/workdir/.scratchpad/probe-slash/summaries/outA.txt` (/model and /config dialogs: system echo written only after ESC; /config needed two ESCs; a paste into an open dialog acted on it), outC.txt (/usage dismissed: "Settings dialog dismissed"), the real transcript `/workdir/workdir/.scratchpad/probe-slash/config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl` (/permissions, /theme echoes). Footers seen: "Esc to cancel", "Esc to clear", "Enter to confirm . Esc to cancel" (design Research, probed).

## Acceptance conditions

- ac1: a dialog command (fake dialog, footer "Esc to cancel", escs 1) completes with result dismissed and claude's stdout as output, after exactly one ESC sent at least dialog_grace_seconds after the footer (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_command_dismissed_by_escape]
- ac2: a dialog that needs two ESCs (escs 2) is dismissed with two ESCs at least 1.5 s apart (new) [evidence: test:tests/test_command_dialogs.py::test_config_dialog_needs_two_escapes]
- ac3: a dialog that never closes fails dialog_stuck after 3 ESCs, no two within 1 s (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_stuck_after_esc_budget]
- ac4: after dialog_stuck, and after a timeout with the dialog still on screen, claude is relaunched with --resume before the slot is released: the fake is spawned again with the same session id, the session returns to ready, a following prose turn is typed into the fresh prompt (never into the dialog) and restarts is unchanged (new) [evidence: test:tests/test_command_dialogs.py::test_open_dialog_restarts_claude_before_release]
- ac5: a command that only times out with no dialog on screen sends one ESC, fails timeout and does not restart claude; with a dialog on screen a second ESC follows (new) [evidence: test:tests/test_command_dialogs.py::test_timeout_second_escape_only_with_dialog]
- ac6: one deadline: a command whose screen keeps changing for most of timeout_seconds and then never completes fails timeout within timeout_seconds plus 2 s of the runner taking it, not after a second full timeout (new) [evidence: test:tests/test_command_dialogs.py::test_one_deadline_covers_quiet_wait_and_completion]
- ac7: PTY output during the grace restarts it: a slow command printing within 2 s is not ESCed (new) [evidence: test:tests/test_command_dialogs.py::test_grace_restarts_on_output]
- ac8: compact never takes the dialog leg (new) [evidence: test:tests/test_command_dialogs.py::test_compact_excluded_from_dialog_detection]
- ac9: dialog_grace_seconds and dialog_patterns have the D7 defaults and a per-session override (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_config_defaults_and_override]
- ac10: the fake's dialog scenario prints the footer, waits for N ESCs (or never closes), then writes the system echo and stdout (new) [evidence: test:tests/test_fake_claude_commands.py::test_dialog_scenario]
- ac11: every config key is documented with its default [evidence: test:tests/test_readme_config.py::test_defaults_match_model]
- ac12: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_registry.py tests/test_readme_config.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/router.py`
- `tests/fake_claude/fake_claude.py`
- `README.md`
- `tests/test_command_dialogs.py`
- `tests/test_fake_claude_commands.py`

## Interfaces

- `CommandsConfig.dialog_grace_seconds: float = 2.0`, `CommandsConfig.dialog_patterns: list[str]`; mirrored in `CommandsOverride`.
- Results and errors: `result = "dismissed"`, `error = "dialog_stuck"`.
- A session method for a wrapper-initiated restart of claude through the relaunch path (`_boot(resume=True)`), leaving `Session.restarts` unchanged (for example `Session.restart_for_dialog() -> None`).
- One deadline: `_run_command` passes `deadline - now` to `wait_quiet` and `_await_completion`.
- Fake scenario `commands.<name>.dialog = {"footer": str, "dismiss_stdout": str, "escs": 1 | 2}`.

## Expected outcome

A dialog command sent from the chat never leaves the session wedged: it is dismissed with claude's own message, or fails `dialog_stuck` or `timeout` inside the D7 bound, and the slot is released.

## Steps

- Red: add `tests/test_command_dialogs.py` (ac1-ac9) and the fake test (ac10); run `uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py`: they fail.
- Green: config, session, router, fake, README; run the task's verify: passes. Quote the summary line.

## Notes

- Reuse `session.FatalScanner` (escape-, whitespace- and case-insensitive matching across chunks) for the dialog scanner.
- ESC count and spacing are read from `fake-keys.jsonl` (D16), never from `fake-inputs.jsonl`.
- Rulings pinned: never two ESCs within 1 s (ac2, ac3); ESC only while a dialog pattern was seen since the last ESC or at the timeout (ac5); compact excluded (ac8); restart only with a dialog still on screen and without spending `max_restarts` (ac4, ac5); one deadline (ac6).
- Reuse the crash relaunch path (`Session._on_exit` and `_recover`); do not add a second boot path.
- Depends on wrapper-command-signals (class-agnostic `_await_completion`, the key log).

- 2026-10-27 amended: interrogate items 6 (restart claude with --resume before releasing the slot when a dialog stays open) and 7 (one deadline per command), design D7 and Bounds revised

- 2026-10-29 done
