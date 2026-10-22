---
title: Statusline relay
status: done
repo: claude-code-wrapper
value: Wrapper receives real context-window usage from Claude Code
files: [src/claude_code_wrapper/cli.py, src/claude_code_wrapper/statusline.py, src/claude_code_wrapper/internal_api.py, src/claude_code_wrapper/bootstrap/settings.py, src/claude_code_wrapper/router.py, README.md, tests/test_statusline_relay.py]
verify: "uv run pytest tests/test_statusline_relay.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [history-before-seq-and-types]
owns: [wrapper-statusline-callback]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/claude-code-wrapper-orchestr-statusline-relay/claude-code-wrapper
branch: claude-code-wrapper-orchestr-statusline-relay
verified_head: 8fa8c5f8e53c17685750536ccacf4435f2715684
run: claude-code-wrapper-orchestr
provides: [wrapper-statusline-callback]
acs_for_audit: []
process_gaps: []
fork_point: e6c6e4be81099264628a95b4e3d26e8d443c7991
---

# Statusline relay

## Requirement

Statusline relay, the source of context-window usage. (1) A new CLI subcommand `ccw statusline` (cli.py main at cli.py:94, logic in a new statusline.py) reads the Claude Code statusLine JSON from stdin, posts it to the loopback internal API route `POST /internal/statusline` (internal_api.py beside `/internal/hooks/{event}` at internal_api.py:72, session identified as the hook relay identifies it, hook_relay.py:136), then runs the chained command and feeds it the same stdin and prints its stdout; with no chained command it prints nothing. A failure to post never fails the statusline (best effort, bounded timeout). (2) bootstrap/settings.py renders the session settings in this order: relay hooks (settings.py:99-107), permissions, the `claude.settings` overlay merge (settings.py:134-143), and then, new, the statusLine step: the chained command is the `statusLine.command` present in the document after the overlay merge, i.e. the user's `claude.settings.statusLine` as rendered at settings.py:134; the step replaces `doc["statusLine"]` with `{type: command, command: "ccw statusline"}`, writes the original command (and its padding/refreshInterval are kept on the replacement) to the chain config file the relay reads, and then the file is written (settings.py:145). Re-rendering is idempotent: if the document's statusLine already is `ccw statusline` the chain config is left as is, never chained to itself. (3) The route validates the payload and hands `context_window.{used_percentage, context_window_size, current_usage}` and `model` to a router callback `on_statusline(payload)` that stores the latest values; surfacing them is task context-in-snapshot-and-sse. README.md documents the subcommand, the route being internal, and the chaining behaviour; test_readme_config enforces any config key.

## Acceptance conditions

- AC1: ccw statusline posts the stdin JSON to /internal/statusline [evidence: test:tests/test_statusline_relay.py::test_cli_posts_stdin_to_internal_route]
- AC2: it runs the chained user statusLine and prints its stdout [evidence: test:tests/test_statusline_relay.py::test_chained_command_output_is_printed]
- AC3: an unreachable internal API does not fail the statusline [evidence: test:tests/test_statusline_relay.py::test_post_failure_is_best_effort]
- AC4: settings bootstrap installs ccw statusline and preserves a user statusLine as the chain [evidence: test:tests/test_statusline_relay.py::test_settings_install_and_chain]
- AC5: the internal route validates the payload and calls the router callback [evidence: test:tests/test_statusline_relay.py::test_internal_route_validates_and_dispatches]
- AC6: README documents the relay [evidence: test:tests/test_readme_api.py::test_every_internal_route_documented]
- AC7: the chained command is the user's claude.settings.statusLine as rendered after the overlay merge, and re-rendering is idempotent (never chains itself) [evidence: test:tests/test_statusline_relay.py::test_chain_taken_after_overlay_and_idempotent]

## Files

- `src/claude_code_wrapper/cli.py`
- `src/claude_code_wrapper/statusline.py`
- `src/claude_code_wrapper/internal_api.py`
- `src/claude_code_wrapper/bootstrap/settings.py`
- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_statusline_relay.py`

## Interfaces

cli.py: ccw statusline; internal_api.py: POST /internal/statusline; router.py: on_statusline(payload). Contract wrapper-statusline-callback.

## Expected outcome

A session's Claude Code runs ccw statusline; the wrapper receives context_window values at /internal/statusline and the user's own statusLine output is unchanged.

## Steps

- Write tests/test_statusline_relay.py (CLI with a stub internal server, chain command, settings render); run it and see it fail.
- Add statusline.py and the ccw statusline subcommand in cli.py, the internal route, the settings.py install and chain, the router on_statusline callback; update README.md.
- Run `uv run pytest tests/test_statusline_relay.py tests/test_readme_api.py tests/test_readme_config.py -q && uv run ruff check . && uv run ruff format --check .`.

## Notes

Follow hook_relay.py for how the CLI finds the internal API and session id. Best effort post with a short timeout. Statusline JSON fields: context_window.used_percentage, context_window_size, current_usage (code.claude.com/docs/en/statusline); null before the first assistant message and after /compact.

- 2026-10-23 run claude-code-wrapper-orchestr: dependency-failed on history-before-seq-and-types
