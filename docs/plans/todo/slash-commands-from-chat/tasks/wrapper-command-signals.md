---
title: wrapper command signals
status: todo
repo: claude-code-wrapper
value: "local and unknown commands complete on the real echo shapes, so /reload-plugins from a client completes and frees the slot"
files: [src/claude_code_wrapper/transcript.py, src/claude_code_wrapper/router.py, tests/fake_claude/fake_claude.py, tests/test_transcript_commands.py, tests/test_command_signals.py, tests/test_fake_claude_commands.py, tests/test_command_runner.py]
verify: "uv run pytest tests/test_transcript_commands.py tests/test_transcript.py tests/test_command_signals.py tests/test_fake_claude_commands.py tests/test_fake_claude.py tests/test_command_runner.py tests/test_command_turn_resume.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-slash-turn-guard]
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

# wrapper command signals

## Requirement

Goal G3 (README), verbatim: "Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it." Goal G1, verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D6, verbatim: "The runner keeps: wait quiet (`quiet_seconds` 1.5) -> onCommand -> mark -> type the line (no marker) -> await. `_await_completion` becomes class-agnostic, first signal after the mark wins:
1. a `command_output` after any `command_invoked` (claude echoes the resolved alias: /cost echoes /usage) -> completed, `output` = stdout; stderr only -> failed `command_error`; compact keeps its PostCompact / compact_boundary / failure-pattern leg; reload-plugins keeps `skipped_cache`.
2. a `command_unknown` (new transcript event from a `system` line of subtype `informational` "Unknown command: /x") -> failed `unknown_command` at once, no ESC.
Transcript fix: a `system/local_command` body starting with `<command-name>` is a `CommandInvoked` (today a `CommandOutput` with empty stdout, so /context, /model and every dialog command on the real binary never match). The fake claude writes the real echo shapes: user echo for reload-plugins, compact, mcp, model with an arg; system echo for context; informational line for an unknown name."

Design D16, verbatim: "ESC keys the fake receives are appended to `$CLAUDE_CONFIG_DIR/fake-keys.jsonl` (`{"key": "esc", "ts"}`), not to `fake-inputs.jsonl`, so the existing pins that every input was typed while idle (`tests/test_command_turn_resume.py`, `tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy`) stay accurate, and dialog tests can count and space ESCs."

Scope (claude-code-wrapper): `transcript.py` (`_system_events`: `<command-name>` body -> `CommandInvoked`; subtype `informational` with "Unknown command: /x" -> new `CommandUnknown(name)`; other informational lines yield nothing), `router.py` (`_on_transcript_events` publishes `command_unknown`; `_await_completion` legs 1 and 2), `tests/fake_claude/fake_claude.py` (echo style per command and scenario key `commands.<name>.echo: system|user`, `echo_name` for an alias, any name listed under scenario `commands` is known, an unknown name writes the two informational lines, ESC keys logged to `fake-keys.jsonl`, docstring updated).

Real samples the fake must match (retro proposal: cite captured real output): `/workdir/workdir/.scratchpad/probe-slash/summaries/outC.txt` lines 15-16 (`type=system sub=informational` "Unknown command: /nonexistent" and "Args from unknown skill: some args"), lines 71-73 (`/context`: system echo, system stdout, isMeta user table), outC.txt line 32 (`/cost` echoes `/usage`); the surviving real transcript `/workdir/workdir/.scratchpad/probe-slash/config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl` (system `local_command` echoes of /context, /permissions, /theme; user echo of /exit).

Tests no longer accurate (named): `tests/test_fake_claude_commands.py::test_unknown_command` asserts that an unknown name writes no transcript line; real claude writes `system/informational` lines (outC.txt:15-16), so it asserts those lines instead. If `tests/test_transcript_commands.py::test_other_system_lines_yield_nothing` or `::test_other_system_lines_ignored` use an informational "Unknown command" line, they change to another informational text.

## Acceptance conditions

- ac1: a system local_command line whose body starts with <command-name> parses as CommandInvoked with name and args (new) [evidence: test:tests/test_transcript_commands.py::test_system_command_echo_is_command_invoked]
- ac2: a system informational "Unknown command: /x" line parses as CommandUnknown(name "x"); an "Args from unknown skill" line and other informational lines yield nothing (new) [evidence: test:tests/test_transcript_commands.py::test_informational_unknown_command]
- ac3: the user-echo shape still parses as CommandInvoked [evidence: test:tests/test_transcript_commands.py::test_command_echo_is_command_invoked]
- ac4: command_unknown is published on the signal bus for the main chain only (new) [evidence: test:tests/test_command_signals.py::test_unknown_command_publishes_signal]
- ac5: regression pin: with client ["*"], POST /commands {name: reload-plugins} on the fake with the real shape (user echo, system stdout) ends command_completed with output "Reloaded: ..." and a POST /turns within 5 s answers 202 (new) [evidence: test:tests/test_command_runner.py::test_reload_plugins_from_client_completes_and_frees_slot]
- ac6: /context with the system echo completes with its stdout (new) [evidence: test:tests/test_command_runner.py::test_context_with_system_echo_completes]
- ac7: an unknown name fails unknown_command within 5 s, no ESC in fake-keys.jsonl, session ready (new) [evidence: test:tests/test_command_runner.py::test_unknown_command_fails_fast_without_esc]
- ac8: /cost whose echo names /usage completes (new) [evidence: test:tests/test_command_runner.py::test_alias_echo_completes]
- ac9: the fake writes user or system echoes per command and logs ESC keys to fake-keys.jsonl only (new) [evidence: test:tests/test_fake_claude_commands.py::test_echo_styles_and_key_log]
- ac10: the fake writes the two informational lines for an unknown name (updated) [evidence: test:tests/test_fake_claude_commands.py::test_unknown_command]
- ac11: targeted suites and lint pass [evidence: command:uv run pytest tests/test_transcript_commands.py tests/test_transcript.py tests/test_command_signals.py tests/test_fake_claude_commands.py tests/test_fake_claude.py tests/test_command_runner.py tests/test_command_turn_resume.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/transcript.py`
- `src/claude_code_wrapper/router.py`
- `tests/fake_claude/fake_claude.py`
- `tests/test_transcript_commands.py`
- `tests/test_command_signals.py`
- `tests/test_fake_claude_commands.py`
- `tests/test_command_runner.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
