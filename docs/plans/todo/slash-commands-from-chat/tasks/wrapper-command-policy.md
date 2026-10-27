---
title: wrapper command policy
status: todo
repo: claude-code-wrapper
value: any command name or a wildcard can be allowed while session-ending commands stay refused
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/commands.py, src/claude_code_wrapper/metrics.py, src/claude_code_wrapper/router.py, src/claude_code_wrapper/api/commands.py, README.md, tests/test_command_registry.py, tests/test_api_commands.py]
verify: "uv run pytest tests/test_command_registry.py tests/test_api_commands.py tests/test_command_vocabulary.py tests/test_readme_config.py tests/test_readme_api.py tests/test_slash_review_fixes.py tests/test_command_runner.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper command policy

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D5, verbatim: "`sessions.commands.deny: list[str]`, default `[exit, quit, clear, resume, branch, fork, login, logout, restart]` (`DEFAULT_COMMAND_DENY` in `config.py`), checked before the allowlists: 403 `command_denied`. `sessions.commands.agent|client` accept names (D2 pattern) or `"*"`; `timeout_seconds` keys are free names or `default`; `CommandsOverride` mirrors `deny`. A gate change to the deny list is an amend of this one default and its pins (user decision 2)."

Design D15, verbatim: "`metrics.py` keeps a fixed label set `METRIC_COMMAND_NAMES` (compact, context, mcp, reload-plugins, reload-skills) and counts every other name as `other`, so arbitrary names cannot grow the label cardinality."

D2 name pattern: `[A-Za-z0-9][A-Za-z0-9:_.-]{0,63}` (full match).

Scope (claude-code-wrapper):
- `config.py`: remove `BUILTIN_COMMAND_NAMES`; add the D2 name pattern as a module constant; `_check_command_names` accepts a name matching the pattern or `"*"`; `_check_command_timeouts` accepts a pattern name or `default`; `CommandsConfig.deny: list[str]` defaulting to `DEFAULT_COMMAND_DENY` (pattern names, no `"*"`); `CommandsOverride.deny: list[str] | None`.
- `commands.py`: `CommandQueue.request` checks, for origins agent and client, `name in cfg.deny` first (`CommandRejected("denied", ...)`), then the allowlist (`"*"` admits every name); origin idle stays compact only. Drop the `assert` that ties `BUILTIN_COMMANDS` to `BUILTIN_COMMAND_NAMES`. `validate_params` and the five-name registry stay in this task (task wrapper-command-args replaces them).
- `router.py`: `request_command` drops its duplicate `validate_params` call before the state check, so the queue's order deny, allowlist, validation holds.
- `metrics.py`: `METRIC_COMMAND_NAMES` as in D15.
- `api/commands.py`: `_REJECT["denied"] = (403, "command_denied")`.
- `README.md`: Configuration reference rows for `sessions.commands.deny` (and the agent/client rows say "names or `*`"), the Errors table row `command_denied`, `### Configuration` of `## Slash commands` mentions the deny list.

Tests no longer accurate (named): `tests/test_command_registry.py::test_unknown_command_name_rejected_at_config` and `::test_unknown_client_and_timeout_key` assert that a name outside the five built-ins is a config error; D5 makes names free-form. They are rewritten to assert that a name outside the D2 pattern (for example `rm -rf`, `-x`, `/clear`) is rejected with its config path, and that `timeout_seconds: {compact: 0}` still fails "must be greater than 0".

## Acceptance conditions

- ac1: agent and client allowlists accept any D2-pattern name and "*", and a name outside the pattern is a config error naming its path (new) [evidence: test:tests/test_command_registry.py::test_command_names_free_form_and_wildcard]
- ac2: `sessions.commands.deny` defaults to exactly exit, quit, clear, resume, branch, fork, login, logout, restart, and a per-session override replaces it (new) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac3: a denied name is refused with code `denied` even when the allowlist is "*" or names it; "*" admits any other name (new) [evidence: test:tests/test_command_registry.py::test_deny_checked_before_allowlist]
- ac4: POST /v1/sessions/{id}/commands {name: exit} with client ["*"] answers 403 `command_denied`, queues nothing and emits no event (new) [evidence: test:tests/test_api_commands.py::test_denied_command_403]
- ac5: with client ["*"] POST /v1/sessions/{id}/commands {name: context} answers 202 (new) [evidence: test:tests/test_api_commands.py::test_wildcard_client_allowlist]
- ac6: the commands metric label stays bounded to the five names plus `other` [evidence: test:tests/test_command_vocabulary.py::test_command_metrics_bounded]
- ac7: every config key, deny included, is documented with its default [evidence: test:tests/test_readme_config.py::test_defaults_match_model]
- ac8: the README Errors table lists command_denied [evidence: command:grep -q '^| `command_denied`' README.md]
- ac9: no BUILTIN_COMMAND_NAMES left in src [evidence: command:! grep -rn BUILTIN_COMMAND_NAMES src]
- ac10: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_api_commands.py tests/test_command_vocabulary.py tests/test_readme_config.py tests/test_readme_api.py tests/test_slash_review_fixes.py tests/test_command_runner.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/commands.py`
- `src/claude_code_wrapper/metrics.py`
- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/api/commands.py`
- `README.md`
- `tests/test_command_registry.py`
- `tests/test_api_commands.py`

## Interfaces

- `claude_code_wrapper.config.DEFAULT_COMMAND_DENY: tuple[str, ...]` (or list): the nine names, the only place the deny list is written.
- `CommandsConfig.deny: list[str]`, `CommandsOverride.deny: list[str] | None`; `agent`, `client`: pattern names or `"*"`.
- `CommandRejected("denied", message)` -> HTTP 403 `command_denied` (`api/commands.py:_REJECT`).
- `metrics.METRIC_COMMAND_NAMES`.

## Expected outcome

A session config can allow any command name or `"*"` for clients and agents; the nine session-ending or account commands are refused 403 `command_denied` before any allowlist; nothing else about running commands changes yet.

## Steps

- Red: write the five new tests (ac1-ac5) and rewrite the two inaccurate config tests; run `uv run pytest tests/test_command_registry.py tests/test_api_commands.py`: the new ones fail (unknown command, no deny key).
- Green: change config.py, commands.py, router.py, metrics.py, api/commands.py, README.md; run the task's verify: passes. Quote the pytest summary line with its counts.

## Notes

- Ruling, pinned by ac3: deny is checked before the allowlist; a name in both deny and the allowlist is denied.
- `CommandsOverride` merges through `commands.effective_commands` (model_copy update): a set `deny` replaces the default, it does not extend it.
- `test_command_vocabulary.py::test_command_metrics_bounded` must stay green unchanged.
- No LSP: find every `BUILTIN_COMMAND_NAMES` use with `grep -rn BUILTIN_COMMAND_NAMES src tests` (config.py, commands.py, metrics.py today).
