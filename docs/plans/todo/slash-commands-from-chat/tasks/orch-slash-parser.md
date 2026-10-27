---
title: orch slash parser
status: todo
repo: agents-orchestrator
value: one rule decides for chat and superleader messages whether a text is a slash command
files: [src/agents_orchestrator/slash.py, tests/test_slash.py]
verify: "uv run --frozen pytest tests/test_slash.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch slash parser

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards." Goal G2, verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Design D1, verbatim (the parser part): "[both routes] call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`."

Design D2, verbatim: "Slash text mirrors Claude Code's own parser (claude 2.1.304 binary, interrogate item 2). After leading whitespace the text starts with `/`. A trailing agents-common run marker (`<!-- agents-<kind>:<id> -->`, `agents_common.runs.marker`, posted as `text\n\nmarker` by `runs.py:_post_once`) is removed first (interrogate item 8). The name is the text after the `/` up to the first whitespace (space, tab or newline); the args are the rest, stripped, and may span lines. The text is a command when the name is empty (`/`, `/ is root`: claude answers "Commands are in the form `/command [args]`" and calls no model; the wrapper refuses an empty name 422 `invalid_command`) or matches `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, with no length cap (`/tmp`, `/_x`, a 100-character name: claude runs it or answers "Unknown command", again with no model call, so a bare `/tmp` fails `unknown_command`). A name with any other character is prose (`/workdir/foo is broken`, `/etc/hosts`, `//x`, `/notes.txt`): claude sends it to the model as a prompt. The orchestrator classifies with this rule and the wrapper's turn guard (D3) refuses with the same rule, both pinned by one shared case table, so a text that claude would parse as a command can never be typed as a turn. The path-like prose leg is confirmed by a real-binary probe in task wrapper-command-signals; a result that contradicts this rule is reported back and amends both parser tasks, never worked around."

Interrogate item 2 (interrogate.md), verbatim: "Classification must match Claude Code's own parser (B, critical). D2 types `/`, `/ is root`, `/_x` and names over 64 chars as turns; claude runs no model call for them, so no Stop and the session hangs. Mirror the binary: name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap. Fix wrapper-slash-turn-guard ac3 and orch-slash-parser ac2. Path-like prose (`/workdir/foo is broken`) must be pinned either way after a probe."

Interrogate item 8, verbatim: "Multi-line slash text and existing callers (C). agents-common runs.py:151 posts `text\n\nmarker`; a preset prompt starting with `/` used to run and would now fail `invalid_command`. Strip the ccw marker before classifying and accept multi-line args (pasted) up to a cap; test the marker-suffixed case."

User decision (builder check), verbatim: "a bare '/word' message such as '/tmp' is a command that fails unknown_command, while '/etc/hosts'-like paths stay prose (per the parser rule of item 2, after the probe)."

Scope (agents-orchestrator): new module `src/agents_orchestrator/slash.py` with `parse`, and `tests/test_slash.py`. Pure, no database. `parse` returns `("", args)` for an empty name (the wrapper refuses it `invalid_command`, D10 fails the message with that code); it never rejects on args length (the wrapper's `MAX_COMMAND_ARGS` applies). The marker pattern is written in `slash.py` with a comment naming `agents_common.runs.marker` as its source (the orchestrator does not depend on agents-common).

## Acceptance conditions

- ac1: parse returns (name, args) for "/reload-plugins", "  /compact keep the plan", "/workbench:start-development x", "/model sonnet", "/_x", "/tmp", a 100-character name and a multi-line "/x a\nb" (args "a\nb") (new) [evidence: test:tests/test_slash.py::test_parse_slash_commands]
- ac2: parse returns ("", "") for "/" and ("", "is root") for "/ is root" (empty name: a command the wrapper refuses invalid_command) (new) [evidence: test:tests/test_slash.py::test_parse_empty_name_is_command]
- ac3: parse returns None for prose, "/workdir/foo is broken", "/etc/hosts", "//x", "/notes.txt" and text where the slash is not first ("see /compact") (new) [evidence: test:tests/test_slash.py::test_parse_leaves_prose]
- ac4: a trailing agents-common run marker is removed before classifying: "/review-pr 12\n\n<!-- agents-webhook:42 -->" gives ("review-pr", "12") and "/compact\n\n<!-- agents-schedule:7 -->" gives ("compact", ""); a marker-like comment that is not trailing stays in the args (new) [evidence: test:tests/test_slash.py::test_parse_strips_trailing_run_marker]
- ac5: the test file and lint pass without a database [evidence: command:uv run --frozen pytest tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/slash.py`
- `tests/test_slash.py`

## Interfaces

- `agents_orchestrator.slash.parse(text: str) -> tuple[str, str] | None`: `(name, args)`; `name` without the slash, `""` for an empty name; args with a trailing run marker removed, newlines kept.

## Expected outcome

One function decides, for both message routes, whether a text is a slash command, with the same rule the wrapper's turn guard uses.

## Steps

- Red: write `tests/test_slash.py` (ac1-ac4); run `uv run --frozen pytest tests/test_slash.py`: import error.
- Green: write `slash.py`; run the task's verify: passes. Quote the summary line.

## Notes

- Keep the case table identical to the wrapper's guard tests in task wrapper-slash-turn-guard (`test_slash_rule_matches_claude_parser`, `test_slash_rule_leaves_paths_and_prose`), so the two sides cannot drift (retro proposal of generic-any-mcp-with-git-and: one shared parity table).
- Docker-free: runs in this container.

- 2026-10-27 amended: interrogate items 2 and 8 (parser mirrors claude: empty name is a command, name regex with no length cap, paths stay prose; trailing run marker stripped, multi-line args), builder check (/tmp is a command), design D2 revised
