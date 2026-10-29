---
title: wrapper command signals
status: in-progress
repo: claude-code-wrapper
value: "local and unknown commands complete on the real echo shapes, so /reload-plugins from a client completes and frees the slot"
files: [src/claude_code_wrapper/transcript.py, src/claude_code_wrapper/router.py, tests/fake_claude/fake_claude.py, tests/test_transcript_commands.py, tests/test_command_signals.py, tests/test_fake_claude_commands.py, tests/test_command_runner.py, MEMORY.md]
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
2. a `command_unknown` (new transcript event from a `system` line of subtype `informational` "Unknown command: /x", also in the suggestion form "Unknown command: /x. Did you mean /y?" that the binary writes for a near miss, interrogate item 11) -> failed `unknown_command` at once, no ESC.
Real-binary probe (user decision, my call on placement): task wrapper-command-signals settles, in a throwaway dir under `/workdir/workdir/.scratchpad/probe-slash` and recorded in the wrapper's `MEMORY.md`, whether local commands never fire UserPromptSubmit and how claude treats path-like prose such as `/workdir/foo is broken` (D2); a result that contradicts the design is reported back, not worked around.
Transcript fix: a `system/local_command` body starting with `<command-name>` is a `CommandInvoked` (today a `CommandOutput` with empty stdout, so /context, /model and every dialog command on the real binary never match). The fake claude writes the real echo shapes: user echo for reload-plugins, compact, mcp, model with an arg; system echo for context; informational line for an unknown name."

Interrogate item 11 (interrogate.md), verbatim: "Unknown command with suggestion (B). Claude writes "Unknown command: /x. Did you mean /y?"; pin it in wrapper-command-signals so a typo fails fast instead of waiting the full timeout."

User decision (probes), verbatim: "the owning tasks (prompt-command turn, command signals) get a requirement to settle by a real-binary probe in a throwaway dir under /workdir/workdir/.scratchpad/probe-slash, recorded in the component MEMORY.md, whether Stop fires after a promoted prompt-command turn, whether plugin commands fire UserPromptSubmit, whether local commands never fire it, and how claude treats path-like prose such as '/workdir/foo is broken'; a probe result that contradicts the design is reported back, not worked around."
This task's probe facts (design D6): whether local commands (for example /reload-plugins, /context) never fire UserPromptSubmit, and how claude treats path-like prose such as '/workdir/foo is broken' and '/etc/hosts' (prose to the model, design D2), with '/nonexistent' (Unknown command) and '/tmp' (an existing path: sent to the model, design D2 as amended 2026-10-29) and '/ is root' (the "Commands are in the form" message) as the contrast cases. The probe runs the real binary (`/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe`) in a new throwaway directory under `/workdir/workdir/.scratchpad/probe-slash` (never a session workdir, never a test), and each fact is recorded as a dated entry tagged `(slash-commands-from-chat) probe` in the wrapper's `MEMORY.md` (the repo has none yet: this task creates it), with the observed result and the raw evidence path. A fact the probe cannot settle (for example a step that needs a model call and there are no credentials) is recorded as "not settled: <why>" and returned to the orchestrator as a question. A result that contradicts design D2 or D6 is reported back and not worked around.

Design D16, verbatim: "ESC keys the fake receives are appended to `$CLAUDE_CONFIG_DIR/fake-keys.jsonl` (`{"key": "esc", "ts"}`), not to `fake-inputs.jsonl`, so the existing pins that every input was typed while idle (`tests/test_command_turn_resume.py`, `tests/test_fake_claude_commands.py::test_esc_not_recorded_as_busy`) stay accurate, and dialog tests can count and space ESCs."

Scope (claude-code-wrapper): `transcript.py` (`_system_events`: `<command-name>` body -> `CommandInvoked`; subtype `informational` with "Unknown command: /x", with or without ". Did you mean /y?", -> new `CommandUnknown(name)`; other informational lines yield nothing), `router.py` (`_on_transcript_events` publishes `command_unknown`; `_await_completion` legs 1 and 2), `tests/fake_claude/fake_claude.py` (echo style per command and scenario key `commands.<name>.echo: system|user`, `echo_name` for an alias, any name listed under scenario `commands` is known, an unknown name writes the two informational lines, `suggest` for the suggestion form, ESC keys logged to `fake-keys.jsonl`, docstring updated), `MEMORY.md` (new, the probe entries).

Real samples the fake must match (retro proposal: cite captured real output): `/workdir/workdir/.scratchpad/probe-slash/summaries/outC.txt` lines 15-16 (`type=system sub=informational` "Unknown command: /nonexistent" and "Args from unknown skill: some args"), lines 71-73 (`/context`: system echo, system stdout, isMeta user table), outC.txt line 32 (`/cost` echoes `/usage`); the surviving real transcript `/workdir/workdir/.scratchpad/probe-slash/config/projects/-workdir-workdir--scratchpad-probe-slash-work/64b31430-13c7-48b0-ba54-c6c432f345db.jsonl` (system `local_command` echoes of /context, /permissions, /theme; user echo of /exit); the binary's format string `Unknown command: /${Be}. Did you mean` (interrogate lead check).

Tests no longer accurate (named): `tests/test_fake_claude_commands.py::test_unknown_command` asserts that an unknown name writes no transcript line; real claude writes `system/informational` lines (outC.txt:15-16), so it asserts those lines instead. If `tests/test_transcript_commands.py::test_other_system_lines_yield_nothing` or `::test_other_system_lines_ignored` use an informational "Unknown command" line, they change to another informational text.

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): claude-code-wrapper `main` is now at `v0.3.3`, which adds a transcript fix in `src/claude_code_wrapper/transcript.py` (`parse_line` reads an `attachment` line through the new `_attachment_events`: a `queued_command` attachment's prompt is a prompt event, other attachment types yield nothing; pinned in `tests/test_transcript.py`). This task also edits `transcript.py`, so the epic's wrapper branch `slash-commands-from-chat` is rebased onto wrapper `main` (`v0.3.3`) before this task's commits, and this task keeps the `queued_command` attachment handling and its tests intact next to its own `_system_events` changes. This epic's wrapper release stays 0.4.0 (task wrapper-release-0-4-0).

## Acceptance conditions

- ac1: a system local_command line whose body starts with <command-name> parses as CommandInvoked with name and args (new) [evidence: test:tests/test_transcript_commands.py::test_system_command_echo_is_command_invoked]
- ac2: a system informational "Unknown command: /x" line parses as CommandUnknown(name "x"); an "Args from unknown skill" line and other informational lines yield nothing (new) [evidence: test:tests/test_transcript_commands.py::test_informational_unknown_command]
- ac3: the suggestion form "Unknown command: /comapct. Did you mean /compact?" parses as CommandUnknown(name "comapct") (new) [evidence: test:tests/test_transcript_commands.py::test_informational_unknown_command_with_suggestion]
- ac4: the user-echo shape still parses as CommandInvoked [evidence: test:tests/test_transcript_commands.py::test_command_echo_is_command_invoked]
- ac5: command_unknown is published on the signal bus for the main chain only (new) [evidence: test:tests/test_command_signals.py::test_unknown_command_publishes_signal]
- ac6: regression pin: with client ["*"], POST /commands {name: reload-plugins} on the fake with the real shape (user echo, system stdout) ends command_completed with output "Reloaded: ..." and a POST /turns within 5 s answers 202 (new) [evidence: test:tests/test_command_runner.py::test_reload_plugins_from_client_completes_and_frees_slot]
- ac7: /context with the system echo completes with its stdout (new) [evidence: test:tests/test_command_runner.py::test_context_with_system_echo_completes]
- ac8: an unknown name ("nonexistent", the real sample outC.txt:15) fails unknown_command within 5 s, no ESC in fake-keys.jsonl, session ready (new) [evidence: test:tests/test_command_runner.py::test_unknown_command_fails_fast_without_esc]
- ac9: a typo answered with the suggestion form fails unknown_command within 5 s, not at the timeout, and sends no ESC (new) [evidence: test:tests/test_command_runner.py::test_unknown_command_with_suggestion_fails_fast]
- ac10: /cost whose echo names /usage completes (new) [evidence: test:tests/test_command_runner.py::test_alias_echo_completes]
- ac11: the fake writes user or system echoes per command and logs ESC keys to fake-keys.jsonl only (new) [evidence: test:tests/test_fake_claude_commands.py::test_echo_styles_and_key_log]
- ac12: the fake writes the two informational lines for an unknown name, and the suggestion form when the scenario sets suggest (updated) [evidence: test:tests/test_fake_claude_commands.py::test_unknown_command]
- ac13: MEMORY.md records the real-binary probe of this task: whether local commands fire UserPromptSubmit and how path-like prose, /tmp and "/ is root" are treated, each with its observed result or "not settled" [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -q "UserPromptSubmit" && grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -q "/workdir/foo is broken"]
- ac14: targeted suites and lint pass [evidence: command:uv run pytest tests/test_transcript_commands.py tests/test_transcript.py tests/test_command_signals.py tests/test_fake_claude_commands.py tests/test_fake_claude.py tests/test_command_runner.py tests/test_command_turn_resume.py && uv run ruff check . && uv run ruff format --check .]
- ac15: the branch is rebased onto wrapper main v0.3.3 and its queued_command attachment parsing still holds (updated) [evidence: command:git merge-base --is-ancestor v0.3.3 HEAD && uv run pytest tests/test_transcript.py -k "queued_command or other_attachment_types"]

## Files

- `src/claude_code_wrapper/transcript.py`
- `src/claude_code_wrapper/router.py`
- `tests/fake_claude/fake_claude.py`
- `tests/test_transcript_commands.py`
- `tests/test_command_signals.py`
- `tests/test_fake_claude_commands.py`
- `tests/test_command_runner.py`
- `MEMORY.md` (new)

## Interfaces

- `transcript.CommandUnknown(_Event)` with `name: str`; part of the `Event` union; parsed from "Unknown command: /x" with or without ". Did you mean /y?".
- SignalBus kind `command_unknown` `{name}`.
- `_await_completion(record, mark, timeout)` returns `("failed", None, "unknown_command", None)` on `command_unknown`.
- Fake claude scenario: `commands.<name>: {echo: "system"|"user", echo_name, stdout, as_user, delay_seconds, hang}`; `$CLAUDE_CONFIG_DIR/fake-keys.jsonl` lines `{"key": "esc", "ts": ...}`.

## Expected outcome

Every local command on the real echo shapes completes with its stdout, an unknown command fails at once, and the reported `/reload-plugins` sent through the command path completes and frees the slot.

## Steps

- Probe first (real binary, throwaway dir under `/workdir/workdir/.scratchpad/probe-slash`, never a test): local commands and UserPromptSubmit (a hooks log as in the first probe), `/workdir/foo is broken`, `/etc/hosts`, `/tmp`, `/ is root`; write the dated `(slash-commands-from-chat) probe` entries in a new `MEMORY.md` (ac13). A result that contradicts design D2 or D6, or a fact the probe cannot settle, is returned to the orchestrator as a question before going on.
- Red: add the parser, signal, runner and fake tests (ac1-ac3, ac5-ac11) and update test_unknown_command; run `uv run pytest tests/test_transcript_commands.py tests/test_command_signals.py tests/test_command_runner.py tests/test_fake_claude_commands.py`: they fail.
- Green: change transcript.py, router.py and the fake; run the task's verify: passes. Quote the summary line.

## Notes

- Completion matches any `command_invoked` after the mark, never the typed name (aliases).
- Ruling, pinned by ac8 and ac9: an unknown command, the suggestion form included, sends no ESC.
- The probe is never a test: tests keep using the fake claude (repo CLAUDE.md).
- The reviewer checks the fake's echo and informational lines against the cited real samples (retro proposal).
- Depends on wrapper-slash-turn-guard (sequenced: both touch router.py).

- 2026-10-27 amended: interrogate item 11 (suggestion form 'Unknown command: /x. Did you mean /y?' fails fast), user decision on the Noted items (real-binary probe of local commands and UserPromptSubmit and of path-like prose, recorded in MEMORY.md, contradictions reported back), builder check (/tmp fails unknown_command), design D6 revised

- 2026-10-29 amended: wrapper main is at v0.3.3 with a queued_command attachment fix in transcript.py, which this task also edits: the wrapper branch rebases onto main and keeps that fix (ac15); release stays 0.4.0

- 2026-10-29 amended: fable ruling 2026-10-29 on the wrapper-command-signals probe: claude sends a bare name that exists on disk (/tmp) to the model; D2 rule unchanged, ac8 uses nonexistent, D8 promotion pins the prose case
