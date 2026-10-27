---
title: wrapper dialog commands
status: todo
repo: claude-code-wrapper
value: dialog commands sent from the chat are dismissed by ESC inside a bound instead of wedging the session
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/session.py, src/claude_code_wrapper/router.py, tests/fake_claude/fake_claude.py, README.md, tests/test_command_dialogs.py, tests/test_fake_claude_commands.py]
verify: "uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_registry.py tests/test_readme_config.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-command-signals]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper dialog commands

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D7, verbatim: "A `DialogScanner` (a `FatalScanner` over `sessions.commands.dialog_patterns`, default `esc to cancel`, `esc to close`, `esc to clear`, `esc to exit`, `enter to confirm`) is fed the PTY output from the mark. No completion signal and a dialog hit -> wait `dialog_grace_seconds` (2.0, restarted by any PTY output) for a late signal, then ESC; 1.5 s later, if still no `command_output` and the scanner hit again since the ESC, ESC again (budget 3, never two ESCs within 1 s: a double ESC at an empty prompt opens the rewind menu). Output after an ESC -> completed `dismissed`, output = claude's stdout ("Help dialog dismissed"). No output after the budget -> failed `dialog_stuck`. Timeout (`timeout_seconds[name]`, default 60, compact 600) -> ESC, 1.5 s, a second ESC only when a dialog pattern is on screen -> failed `timeout`. Compact is excluded from dialog detection (its own leg). Dialog commands stay allowed: "dismissed" with claude's own message is the honest answer for a chat with no keyboard (user decision 1)."

Design Bounds, verbatim: "dialog: `dialog_grace_seconds` 2.0 s after the first footer hit; ESC budget 3, 1.5 s apart, never two ESCs within 1 s; `dialog_stuck` after the budget." and "worst-case slot hold for a non-promoted command: timeout + 2.0 + 3 x 1.5 = about 67 s (default)."

Scope (claude-code-wrapper): `config.py` (`CommandsConfig.dialog_grace_seconds: float = 2.0` (ge 0), `dialog_patterns: list[str]` with the five defaults; `CommandsOverride` mirrors both), `session.py` (a dialog scanner over the PTY output, reset at the mark, with "hit since" queries; an ESC helper that never sends two ESCs within 1 s), `router.py` (`_await_completion` dialog leg and the conditional second ESC of the timeout leg; result `dismissed`, error `dialog_stuck`), `tests/fake_claude/fake_claude.py` (scenario `commands.<name>.dialog: {footer, dismiss_stdout, escs: 1|2}`: print the footer, write nothing until the given number of ESCs, then the system echo and the stdout; ESC keys already logged to `fake-keys.jsonl` by wrapper-command-signals), `README.md` (config rows; `### Lifecycle` of `## Slash commands` describes dialogs and the bound).

Real samples the fake must match: `/workdir/workdir/.scratchpad/probe-slash/summaries/outA.txt` (/model and /config dialogs: system echo written only after ESC; /config needed two ESCs), outC.txt (/usage dismissed: "Settings dialog dismissed"), the real transcript `/workdir/workdir/.scratchpad/probe-slash/config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl` (/permissions, /theme echoes). Footers seen: "Esc to cancel", "Esc to clear", "Enter to confirm . Esc to cancel" (design Research, probed).

## Acceptance conditions

- ac1: a dialog command (fake dialog, footer "Esc to cancel", escs 1) completes with result dismissed and claude's stdout as output, after exactly one ESC sent at least dialog_grace_seconds after the footer (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_command_dismissed_by_escape]
- ac2: a dialog that needs two ESCs (escs 2) is dismissed with two ESCs at least 1.5 s apart (new) [evidence: test:tests/test_command_dialogs.py::test_config_dialog_needs_two_escapes]
- ac3: a dialog that never closes fails dialog_stuck after 3 ESCs, no two within 1 s, and the session returns to ready (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_stuck_after_esc_budget]
- ac4: a command that only times out with no dialog on screen sends one ESC and fails timeout; with a dialog on screen a second ESC follows (new) [evidence: test:tests/test_command_dialogs.py::test_timeout_second_escape_only_with_dialog]
- ac5: PTY output during the grace restarts it: a slow command printing within 2 s is not ESCed (new) [evidence: test:tests/test_command_dialogs.py::test_grace_restarts_on_output]
- ac6: compact never takes the dialog leg (new) [evidence: test:tests/test_command_dialogs.py::test_compact_excluded_from_dialog_detection]
- ac7: dialog_grace_seconds and dialog_patterns have the D7 defaults and a per-session override (new) [evidence: test:tests/test_command_dialogs.py::test_dialog_config_defaults_and_override]
- ac8: the fake's dialog scenario prints the footer, waits for N ESCs, then writes the system echo and stdout (new) [evidence: test:tests/test_fake_claude_commands.py::test_dialog_scenario]
- ac9: every config key is documented with its default [evidence: test:tests/test_readme_config.py::test_defaults_match_model]
- ac10: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_registry.py tests/test_readme_config.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check .]

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
- Fake scenario `commands.<name>.dialog = {"footer": str, "dismiss_stdout": str, "escs": 1 | 2}`.

## Expected outcome

A dialog command sent from the chat never leaves the session wedged: it is dismissed with claude's own message, or fails `dialog_stuck` or `timeout` inside the D7 bound, and the slot is released.

## Steps

- Red: add `tests/test_command_dialogs.py` (ac1-ac7) and the fake test (ac8); run `uv run pytest tests/test_command_dialogs.py tests/test_fake_claude_commands.py`: they fail.
- Green: config, session, router, fake, README; run the task's verify: passes. Quote the summary line.

## Notes

- Reuse `session.FatalScanner` (escape-, whitespace- and case-insensitive matching across chunks) for the dialog scanner.
- ESC count and spacing are read from `fake-keys.jsonl` (D16), never from `fake-inputs.jsonl`.
- Rulings pinned: never two ESCs within 1 s (ac2, ac3); ESC only while a dialog pattern was seen since the last ESC or at the timeout (ac4); compact excluded (ac6).
- Depends on wrapper-command-signals (class-agnostic `_await_completion`, the key log).
