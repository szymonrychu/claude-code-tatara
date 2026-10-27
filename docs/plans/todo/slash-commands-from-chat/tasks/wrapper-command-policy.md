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

Design D5, verbatim: "`sessions.commands.deny: list[str]`, default (my call, interrogate item 5) `[exit, quit, clear, reset, new, resume, continue, branch, fork, cd, background, bg, teleport, tp, stop, remote-control, rc, restart, update, login, logout, upgrade, setup-bedrock, setup-vertex, web-setup, design-login]` (`DEFAULT_COMMAND_DENY` in `config.py`), matched case-insensitively (`/EXIT`, `/Clear` are denied), checked before the allowlists: 403 `command_denied`. Aliases are listed by name from claude's own alias table (binary grep, 2026-10-27: clear `reset`, `new`; resume `continue`; exit `quit`; restart `update`; background `bg`; teleport `tp`; remote-control `rc`), each pinned by a test, so the list stays one config value with no alias resolver. `sessions.commands.agent|client` accept names (D2 pattern) or `"*"`; `timeout_seconds` keys are free names or `default`; `CommandsOverride` mirrors `deny`. A gate change to the deny list is an amend of this one default and its pins (user decision 2)." The per-name reasons are design.md D5's table.

Interrogate item 5 (interrogate.md), verbatim: "Deny list misses aliases and session-moving commands (B, C). Add `reset`, `new` (clear), `continue` (resume), `update` (restart), `cd`; match case-insensitively; resolve aliases from claude's table, pin each with a test. Review the rest of cmdtable.txt (`background`, `teleport`, `stop`, `session`, `remote-control`, `upgrade`) and record each as denied or allowed with the reason."

User decision, verbatim: "Keep the deny list as one config value".

Design D15, verbatim: "`metrics.py` keeps a fixed label set `METRIC_COMMAND_NAMES` (compact, context, mcp, reload-plugins, reload-skills) and counts every other name as `other`, so arbitrary names cannot grow the label cardinality."

D2 name pattern (design D2, interrogate item 2): `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$` (full match, no length cap).

Scope (claude-code-wrapper):
- `config.py`: remove `BUILTIN_COMMAND_NAMES`; add the D2 name pattern as a module constant; `_check_command_names` accepts a name matching the pattern or `"*"`; `_check_command_timeouts` accepts a pattern name or `default`; `CommandsConfig.deny: list[str]` defaulting to `DEFAULT_COMMAND_DENY` (the 26 names above, pattern names, no `"*"`); `CommandsOverride.deny: list[str] | None`.
- `commands.py`: `CommandQueue.request` checks, for origins agent and client, the name lowercased against the lowercased deny list first (`CommandRejected("denied", ...)`), then the allowlist (`"*"` admits every name); origin idle stays compact only. Drop the `assert` that ties `BUILTIN_COMMANDS` to `BUILTIN_COMMAND_NAMES`. `validate_params` and the five-name registry stay in this task (task wrapper-command-args replaces them).
- `router.py`: `request_command` drops its duplicate `validate_params` call before the state check, so the queue's order deny, allowlist, validation holds.
- `metrics.py`: `METRIC_COMMAND_NAMES` as in D15.
- `api/commands.py`: `_REJECT["denied"] = (403, "command_denied")`.
- `README.md`: Configuration reference rows for `sessions.commands.deny` (the default list, case-insensitive matching; the agent/client rows say "names or `*`"), the Errors table row `command_denied`, `### Configuration` of `## Slash commands` mentions the deny list.

Tests no longer accurate (named): `tests/test_command_registry.py::test_unknown_command_name_rejected_at_config` and `::test_unknown_client_and_timeout_key` assert that a name outside the five built-ins is a config error; D5 makes names free-form. They are rewritten to assert that a name outside the D2 pattern (for example `rm -rf`, `-x`, `/clear`, `notes.txt`) is rejected with its config path, and that `timeout_seconds: {compact: 0}` still fails "must be greater than 0".

## Acceptance conditions

- ac1: agent and client allowlists accept any D2-pattern name ("_x", a 100-character name) and "*", and a name outside the pattern ("rm -rf", "-x", "/clear", "notes.txt") is a config error naming its path (new) [evidence: test:tests/test_command_registry.py::test_command_names_free_form_and_wildcard]
- ac2: sessions.commands.deny defaults to exactly the 26 names of design D5, and a per-session override replaces it (new) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac3: each alias of claude's table is denied by name: reset and new (clear), continue (resume), quit (exit), update (restart), bg (background), tp (teleport), rc (remote-control), and cd, stop, upgrade, setup-bedrock, setup-vertex, web-setup, design-login are denied; session and its alias remote are allowed (new) [evidence: test:tests/test_command_registry.py::test_deny_list_covers_aliases_and_session_moving_commands]
- ac4: the deny match is case-insensitive: EXIT, Clear and Reset are denied with code denied (new) [evidence: test:tests/test_command_registry.py::test_deny_is_case_insensitive]
- ac5: a denied name is refused with code denied even when the allowlist is "*" or names it; "*" admits any other name (new) [evidence: test:tests/test_command_registry.py::test_deny_checked_before_allowlist]
- ac6: POST /v1/sessions/{id}/commands {name: exit} and {name: Reset} with client ["*"] answer 403 command_denied, queue nothing and emit no event (new) [evidence: test:tests/test_api_commands.py::test_denied_command_403]
- ac7: with client ["*"] POST /v1/sessions/{id}/commands {name: context} answers 202 (new) [evidence: test:tests/test_api_commands.py::test_wildcard_client_allowlist]
- ac8: the commands metric label stays bounded to the five names plus other [evidence: test:tests/test_command_vocabulary.py::test_command_metrics_bounded]
- ac9: every config key, deny included, is documented with its default [evidence: test:tests/test_readme_config.py::test_defaults_match_model]
- ac10: the README Errors table lists command_denied [evidence: command:grep -q '^| `command_denied`' README.md]
- ac11: no BUILTIN_COMMAND_NAMES left in src, and the deny names are written only in config.py [evidence: command:! grep -rn BUILTIN_COMMAND_NAMES src && test "$(grep -rln '"remote-control"' src)" = "src/claude_code_wrapper/config.py"]
- ac12: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_api_commands.py tests/test_command_vocabulary.py tests/test_readme_config.py tests/test_readme_api.py tests/test_slash_review_fixes.py tests/test_command_runner.py && uv run ruff check . && uv run ruff format --check .]

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

- `claude_code_wrapper.config.DEFAULT_COMMAND_DENY: tuple[str, ...]` (or list): the 26 names of design D5, the only place the deny list is written.
- `CommandsConfig.deny: list[str]`, `CommandsOverride.deny: list[str] | None`; `agent`, `client`: pattern names or `"*"`.
- `CommandRejected("denied", message)` -> HTTP 403 `command_denied` (`api/commands.py:_REJECT`).
- `metrics.METRIC_COMMAND_NAMES`.

## Expected outcome

A session config can allow any command name or `"*"` for clients and agents; the session-ending, session-moving, account and credential commands of design D5, under any alias or letter case, are refused 403 `command_denied` before any allowlist; nothing else about running commands changes yet.

## Steps

- Red: write the seven new tests (ac1-ac7) and rewrite the two inaccurate config tests; run `uv run pytest tests/test_command_registry.py tests/test_api_commands.py`: the new ones fail (unknown command, no deny key).
- Green: change config.py, commands.py, router.py, metrics.py, api/commands.py, README.md; run the task's verify: passes. Quote the pytest summary line with its counts.

## Notes

- Ruling, pinned by ac5: deny is checked before the allowlist; a name in both deny and the allowlist is denied.
- Ruling, pinned by ac3 and ac4: aliases are listed by name (no alias resolver) and matched case-insensitively.
- `CommandsOverride` merges through `commands.effective_commands` (model_copy update): a set `deny` replaces the default, it does not extend it.
- `test_command_vocabulary.py::test_command_metrics_bounded` must stay green unchanged.
- No LSP: find every `BUILTIN_COMMAND_NAMES` use with `grep -rn BUILTIN_COMMAND_NAMES src tests` (config.py, commands.py, metrics.py today).

- 2026-10-27 amended: interrogate item 5 (aliases reset, new, continue, update, quit, bg, tp, rc; cd and the reviewed session-moving and account commands; case-insensitive; one config value) and item 2 (D2 name pattern), design D5 revised
