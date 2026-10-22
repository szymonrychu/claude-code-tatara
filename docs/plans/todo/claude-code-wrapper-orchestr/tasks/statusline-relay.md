---
title: Statusline relay
status: todo
repo: claude-code-wrapper
value: Wrapper receives real context-window usage from Claude Code
files: [src/claude_code_wrapper/cli.py, src/claude_code_wrapper/statusline.py, src/claude_code_wrapper/internal_api.py, src/claude_code_wrapper/bootstrap/settings.py, src/claude_code_wrapper/router.py, README.md, tests/test_statusline_relay.py]
verify: "uv run pytest tests/test_statusline_relay.py tests/test_readme_api.py -q && mise run lint"
depends_on: [history-before-seq-and-types]
owns: [wrapper-statusline-callback]
uses: []
model: ""
estimate: 44
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Statusline relay

## Requirement

Statusline relay, the source of context-window usage. (1) A new CLI subcommand `ccw statusline` (cli.py, logic in a new statusline.py) reads the Claude Code statusLine JSON from stdin, posts it to the loopback internal API route `POST /internal/statusline` (internal_api.py, session identified as the hook relay identifies it), then runs the user-configured statusLine command (the original `claude.settings.statusLine`, preserved as a chained command) feeding it the same stdin and prints its stdout; with no chained command it prints nothing. A failure to post never fails the statusline (best effort, bounded timeout). (2) bootstrap/settings.py renders `statusLine: {type: command, command: "ccw statusline"}` into each session's settings and moves any user `claude.settings.statusLine` command into the chain config the relay reads. (3) The route validates the payload and hands `context_window.{used_percentage, context_window_size, current_usage}` and `model` to a router callback `on_statusline(payload)` that stores the latest values; surfacing them is task statusline-context-surface. README.md documents the subcommand, the route being internal, and the chaining behaviour; test_readme_config enforces any config key.

## Acceptance conditions

- AC1: ccw statusline posts the stdin JSON to /internal/statusline [evidence: test:tests/test_statusline_relay.py::test_cli_posts_stdin_to_internal_route]
- AC2: it runs the chained user statusLine and prints its stdout [evidence: test:tests/test_statusline_relay.py::test_chained_command_output_is_printed]
- AC3: an unreachable internal API does not fail the statusline [evidence: test:tests/test_statusline_relay.py::test_post_failure_is_best_effort]
- AC4: settings bootstrap installs ccw statusline and preserves a user statusLine as the chain [evidence: test:tests/test_statusline_relay.py::test_settings_install_and_chain]
- AC5: the internal route validates the payload and calls the router callback [evidence: test:tests/test_statusline_relay.py::test_internal_route_validates_and_dispatches]
- AC6: README documents the relay [evidence: test:tests/test_readme_api.py::test_every_internal_route_documented]

## Files

- `src/claude_code_wrapper/cli.py`
- `src/claude_code_wrapper/statusline.py`
- `src/claude_code_wrapper/internal_api.py`
- `src/claude_code_wrapper/bootstrap/settings.py`
- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_statusline_relay.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
