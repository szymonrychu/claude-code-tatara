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

Design D2, verbatim: "Slash text is: after leading whitespace, `/` then a name matching `[A-Za-z0-9][A-Za-z0-9:_.-]{0,63}`, then whitespace or the end of the text. The name is that token; the args are the rest, stripped. The orchestrator classifies with this rule (no single-line condition) and the wrapper's turn guard (D3) refuses with the same rule, so a text that claude would parse as a command can never be typed as a turn. A multi-line or over-long args text is still kind `command`; the wrapper rejects it 422 `invalid_command` (args must be one line, at most 2000 characters, no control characters), and the message fails visibly with that code (D10). Text such as `/workdir/foo is broken` or `/ is root` is prose (the name stops at `/` or is empty)."

Scope (agents-orchestrator): new module `src/agents_orchestrator/slash.py` with `parse`, and `tests/test_slash.py`. Pure, no database.

## Acceptance conditions

- ac1: parse returns (name, args) for "/reload-plugins", "  /compact keep the plan", "/workbench:start-development x", "/model sonnet" and a multi-line "/x a\nb" (args kept raw after stripping) (new) [evidence: test:tests/test_slash.py::test_parse_slash_commands]
- ac2: parse returns None for prose, "/workdir/foo is broken", "/ is root", "//x", a name over 64 characters and text where the slash is not first (new) [evidence: test:tests/test_slash.py::test_parse_leaves_prose]
- ac3: the test file and lint pass without a database [evidence: command:uv run --frozen pytest tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/slash.py`
- `tests/test_slash.py`

## Interfaces

- `agents_orchestrator.slash.parse(text: str) -> tuple[str, str] | None`: `(name, args)`; `name` without the slash.

## Expected outcome

One function decides, for both message routes, whether a text is a slash command, with the same rule the wrapper's turn guard uses.

## Steps

- Red: write `tests/test_slash.py` (ac1, ac2); run `uv run --frozen pytest tests/test_slash.py`: import error.
- Green: write `slash.py`; run the task's verify: passes. Quote the summary line.

## Notes

- Keep the case table identical to the wrapper's guard tests in task wrapper-slash-turn-guard (`test_slash_rule_leaves_paths_and_prose`), so the two sides cannot drift (retro proposal of generic-any-mcp-with-git-and: one shared parity table).
- Docker-free: runs in this container.
