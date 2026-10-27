---
title: wrapper command args
status: in-progress
repo: claude-code-wrapper
value: any slash command with free one-line args can be queued through the API and the ccw tool
files: [src/claude_code_wrapper/commands.py, src/claude_code_wrapper/router.py, src/claude_code_wrapper/api/commands.py, src/claude_code_wrapper/mcp_server.py, README.md, tests/test_command_registry.py, tests/test_slash_review_fixes.py, tests/test_mcp_server.py, tests/test_api_commands.py, tests/test_command_runner.py, tests/test_auto_compact.py, tests/test_mcp_injection.py]
verify: "uv run pytest tests/test_command_registry.py tests/test_slash_review_fixes.py tests/test_mcp_server.py tests/test_api_commands.py tests/test_command_runner.py tests/test_auto_compact.py tests/test_mcp_injection.py tests/test_command_vocabulary.py tests/test_fake_claude_mcp.py tests/test_readme_api.py tests/test_slash_commands_docs.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-command-policy]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 14
expected_tokens: 3155191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper command args

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D4, verbatim: "`commands.py`: `validate(name, args)` (name by the D2 name pattern, an empty name refused `invalid_command`; args by the D2 args rule: newlines and tabs allowed, `\r\n` normalised, at most `MAX_COMMAND_ARGS` 20000 characters, no other control character), `render(name, args)` = `f"/{name} {args}".rstrip()`, `CommandRecord.args: str` (default ""). `BUILTIN_COMMANDS`, `validate_params` and `params_schema` are removed. `--force` among the args of `reload-plugins` needs `allow_force` (`force_not_allowed`). `POST /v1/sessions/{id}/commands` takes `{name, args: str = ""}`. The ccw MCP tool `command` takes `{name, args?}` (name: an enum of the agent allowlist, or a plain string when the allowlist holds `"*"`). The onCommand hook payload and `command_*` event records carry `args` as a string. Auto-compact queues `compact` with args = `auto_compact.instructions`. Ruling (my call): a queued duplicate coalesces only when name and args are identical, so `/model a` and `/model b` both queue. The line is typed as one bracketed paste and one CR (`Session.send_command`, `pty.send_prompt`), so a second line of multi-line args that starts with `/` is part of the first command's args, never a command of its own (the probe: a paste "/x\n\n<!-- ccw turn: id -->" ran /x with the rest as args)."

Design D2, verbatim (the args part): "Args are at most `MAX_COMMAND_ARGS` 20000 characters (my call: webhook prompt templates render issue bodies and the default event block) and may hold newlines and tabs; `\r\n` is normalised to `\n`; any other control character (ESC included, so args cannot end the bracketed paste the line is typed in) and U+2028/U+2029 are refused 422 `invalid_command`, and the message fails visibly with that code (D10)." D2 name pattern: `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap.

Interrogate item 8 (interrogate.md), verbatim: "Multi-line slash text and existing callers (C). agents-common runs.py:151 posts `text\n\nmarker`; a preset prompt starting with `/` used to run and would now fail `invalid_command`. Strip the ccw marker before classifying and accept multi-line args (pasted) up to a cap; test the marker-suffixed case." Interrogate item 2, verbatim (the name part): "Mirror the binary: name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap."

Design D18, verbatim: "wrapper-command-args touches 12 files (4 source, README, 7 test files), over the 8-file guideline: removing `validate_params` and `params_schema` and changing `CommandRecord.args` to a string breaks every caller (router, API, MCP server) and the tests that pass params dicts in the same commit; there is no green intermediate without a compatibility shim (rule 4)."

User decision (gate brief): "Replace the five structured command params (compact.instructions, reload-plugins.force, mcp.action/server) with free-text `args` everywhere, including the ccw MCP `command` tool and the example configs, with no compatibility shim" (example configs: task wrapper-command-docs).

Scope (claude-code-wrapper):
- `commands.py`: `validate(name, args) -> str` (the normalised, stripped args; `CommandRejected("invalid_command", ...)` for an empty name, a name outside the D2 pattern, or args breaking the D2 args rule; `force_not_allowed` for `reload-plugins` args holding the token `--force` without `allow_force`); `MAX_COMMAND_ARGS = 20000`; `render(name, args)`; `CommandRecord.args: str = ""`; `CommandQueue.request(name, args: str, *, origin, turn_id)`; coalescing only for an identical queued (name, args) pair (ruling); remove `BUILTIN_COMMANDS`, `validate_params`, `params_schema`, `SERVER_NAME`.
- `router.py`: `request_command(name, args: str = "", *, origin)`; `_auto_compact_due` passes `cfg.instructions`; the onCommand payload carries `"args": record.args`; the runner types `render(record.name, record.args)` through `Session.send_command` (one paste, one CR).
- `api/commands.py`: `CommandRequest {name: str, args: str = ""}` (`extra="forbid"`); a non-string `args` is 422.
- `mcp_server.py`: tool `command` input schema `{name: string (enum of the agent allowlist, plain string when it holds "*"), args?: string}`, `additionalProperties: false`; `_call` accepts exactly `name` and optional string `args`, an extra key lists "allowed: name, args".
- `README.md`: `### The ccw command tool`, `### Commands endpoint` (body `{name, args}`, multi-line args up to 20000 characters), the onCommand payload and the command record (`args` string).

Tests no longer accurate (named), because D4 removes structured params: `tests/test_command_registry.py` (`test_validate_params`, `test_render_command_lines`, `test_params_schema_lists_allowed_commands`, `test_unknown_param_rejected_naming_allowed`, `test_force_and_instruction_limits`, and every `request(name, {...})` call), `tests/test_slash_review_fixes.py` (pins `validate_params`, `params_schema`, `BUILTIN_COMMANDS`; its still-valid invariants - control characters, length cap, smuggled `/exit` never run as its own command, flat tool schema - are rewritten against `validate(name, args)`, the one-paste typing and the new tool schema; a newline is no longer a refused control character, ESC still is), `tests/test_mcp_server.py` (`params` argument and `params_schema`), `tests/test_api_commands.py` (`args` objects in `test_post_command_bad_args_422`, `test_post_command_queue_full_429`), `tests/test_command_runner.py` (params dicts in `request_command` calls and the onCommandComplete `args` dict), `tests/test_auto_compact.py` (`rec["args"] == {"instructions": ...}`), `tests/test_mcp_injection.py` (`SELF` tool arguments with `params`).

## Acceptance conditions

- ac1: validate accepts any D2-pattern name ("_x", a 100-character name) with args that span lines and hold tabs, normalises "\r\n" to "\n", and rejects an empty name, a name holding "." or "/", ESC, U+2028 and args over 20000 characters as invalid_command (new) [evidence: test:tests/test_command_registry.py::test_validate_name_and_args]
- ac2: render(name, args) is "/name args" with no trailing space for empty args, multi-line args kept (new) [evidence: test:tests/test_command_registry.py::test_render_name_and_args]
- ac3: reload-plugins args holding --force are refused force_not_allowed unless allow_force (new) [evidence: test:tests/test_command_registry.py::test_force_needs_allow_force]
- ac4: only an identical queued (name, args) pair coalesces; the same name with other args queues a second record (new) [evidence: test:tests/test_command_registry.py::test_coalesce_identical_name_and_args]
- ac5: args holding a newline plus /exit are typed inside the one paste with one CR (the fake records one input and /exit never runs on its own); args holding ESC (the paste end "\x1b[201~") are refused invalid_command and nothing is typed (updated) [evidence: test:tests/test_slash_review_fixes.py::test_args_smuggling_never_typed]
- ac6: POST /commands {name, args} answers 202 with a record whose args is the string (updated) [evidence: test:tests/test_api_commands.py::test_post_command_returns_202_record]
- ac7: POST /commands with an object as args answers 422; with an empty name answers 422 invalid_command (new) [evidence: test:tests/test_api_commands.py::test_post_command_args_must_be_string]
- ac8: tools/list gives the command tool the {name, args} schema: an enum of the agent allowlist, a plain string with "*" (new) [evidence: test:tests/test_mcp_server.py::test_tools_list_schema_name_and_args]
- ac9: tools/call queues the command with its args string (updated) [evidence: test:tests/test_mcp_server.py::test_tools_call_queues_command]
- ac10: a command with args is typed as "/mcp reconnect github" (updated) [evidence: test:tests/test_command_runner.py::test_other_commands_complete_with_output]
- ac11: multi-line args are typed as one paste and one CR, "/compact keep\nthe plan" (new) [evidence: test:tests/test_command_runner.py::test_multiline_args_typed_as_one_paste]
- ac12: onCommandComplete receives the record with args as a string (updated) [evidence: test:tests/test_command_runner.py::test_on_command_complete_fired_with_record]
- ac13: idle auto-compact queues compact with args = the instructions string (updated) [evidence: test:tests/test_auto_compact.py::test_auto_compact_fires_after_idle]
- ac14: the agent self-compact e2e still runs through the ccw tool with args (updated) [evidence: test:tests/test_mcp_injection.py::test_agent_self_compact_same_turn_e2e]
- ac15: the removed registry symbols are gone from src and tests [evidence: command:! grep -rnE "validate_params|params_schema|BUILTIN_COMMANDS" src tests]
- ac16: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_slash_review_fixes.py tests/test_mcp_server.py tests/test_api_commands.py tests/test_command_runner.py tests/test_auto_compact.py tests/test_mcp_injection.py tests/test_command_vocabulary.py tests/test_fake_claude_mcp.py tests/test_readme_api.py tests/test_slash_commands_docs.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/commands.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/api/commands.py`
- `src/claude_code_wrapper/mcp_server.py`
- `README.md`
- `tests/test_command_registry.py`
- `tests/test_slash_review_fixes.py`
- `tests/test_mcp_server.py`
- `tests/test_api_commands.py`
- `tests/test_command_runner.py`
- `tests/test_auto_compact.py`
- `tests/test_mcp_injection.py`

## Interfaces

- `commands.validate(name: str, args: str, *, allow_force: bool) -> str`, `commands.render(name: str, args: str = "") -> str`.
- `CommandRecord.args: str`; `CommandQueue.request(name, args, *, origin, turn_id)`.
- `SessionRouter.request_command(name: str, args: str = "", *, origin) -> CommandRecord`.
- HTTP `POST /v1/sessions/{id}/commands` body `{"name": str, "args": str = ""}`; response the record (`id`, `name`, `args`, `origin`, `state`, ...).
- ccw MCP tool `command` arguments `{"name": str, "args"?: str}`.

## Expected outcome

Any allowed command name with free args (multi-line, up to 20000 characters) can be queued through the API and the ccw tool; the typed line is `/name args` in one paste; structured params are gone everywhere in src and tests.

## Steps

- Red: rewrite the named inaccurate tests and add the new ones (ac1-ac5, ac7, ac8); run `uv run pytest tests/test_command_registry.py tests/test_slash_review_fixes.py tests/test_mcp_server.py`: they fail (old signatures).
- Green: change commands.py, router.py, api/commands.py, mcp_server.py, README.md together (one commit: no intermediate is green); run the task's verify: passes. Quote the summary line.

## Notes

- Ruling, pinned by ac4: coalescing matches (name, args), so `/model a` and `/model b` both queue.
- Ruling, pinned by ac3: only `reload-plugins` checks `--force` (as today); the token check splits args on whitespace.
- The fake claude still knows only its five names in this task: tests of arbitrary names that need completion come in wrapper-command-signals; use the five names here.
- Depends on wrapper-command-policy (deny list, wildcard, the name pattern constant in config.py).
- Sizing exception D18: 12 files, opus.

- 2026-10-27 amended: interrogate items 8 and 2 (multi-line args up to MAX_COMMAND_ARGS 20000 typed as one paste, ESC still refused; empty name invalid_command; claude's name regex), design D2 and D4 revised
