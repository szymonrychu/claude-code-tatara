---
title: wrapper deny list extend
status: done
repo: claude-code-wrapper
value: "commands that install, export, reconfigure or report from the agent's account can no longer be run from chat, and no session override can lift the deny list"
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/commands.py, README.md, config.example.yaml, tests/test_command_registry.py]
verify: "uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-slash-js-whitespace]
model: sonnet
review: ""
verified_head: ea7535f3cee9c180db34f16deb114e306007230c
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 3
actual_tokens: 464021
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 353679, review 110342"
---

# wrapper deny list extend

## Requirement

User decision (2026-10-29 15:26Z/15:29Z), verbatim: "User verbatim 2026-10-29 15:26Z/15:29Z: "Yes" / "all yes" to: (1) extend the wrapper's DEFAULT_COMMAND_DENY with heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory (verify each name/alias against claude 2.1.304 at /usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe; a name that does not exist is reported, not invented); (2) a wrapper session-create override may only extend the deny list, never replace or empty it; (3) keep client ["*"] with the extended deny list. The orchestrator's fake wrapper COMMAND_DENY mirror and docs/examples follow."

Design D5 (amended 2026-10-29), verbatim: "(1) `DEFAULT_COMMAND_DENY` gains heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory. Each name was checked against the claude 2.1.304 binary during planning: all 24 exist (plugins and marketplace are aliases of plugin, routines an alias of schedule; bug is its own command); desktop's alias `app` is not in the list (Open questions Q3). (2) A `POST /v1/sessions` `commands.deny` override only extends the deny list (the effective list is the configured list plus the override's names), never replaces or empties it; `sessions.commands.deny` in the server config keeps its D5 meaning (it sets the list). (3) Clients keep `["*"]` (D11) with the extended list. The orchestrator's fake wrapper `COMMAND_DENY` mirror and the wrapper docs and example configs follow."

Scope (claude-code-wrapper, on the same wrapper branch as wrapper-slash-js-whitespace):
- `src/claude_code_wrapper/config.py`: the 24 names appended to `DEFAULT_COMMAND_DENY` (26 + 24 = 50 names), the comment naming why (claude's own descriptions from the binary).
- `src/claude_code_wrapper/commands.py`: `effective_commands` merges an override's `deny` into the base list (base order kept, then the override's new names, compared case-insensitively); an override `deny: []` or unset leaves the base list. The stored override is reapplied on resume through the same function.
- README.md: the `POST /v1/sessions` `commands` row ("a set `deny` replaces the default list"), the "Slash commands" prose ("a `deny` there replaces the default list") and the `sessions.commands.deny` configuration reference row (default list, "a set value (config or create override) replaces the default list") say the override only extends; the default list is the 50 names.
- `config.example.yaml`: the commented `deny:` line lists the 50 names and says a create override only extends it.
- `tests/test_command_registry.py`. Test no longer accurate (named): `test_deny_list_default_and_override` pins `len(DENY) == 26` and an override `deny: ["exit"]` that replaces the default (`out.deny == ["exit"]`, `/clear` no longer denied); user decision (2) forbids exactly that, so the test is updated to the extend-only rule and the 50-name default.

## Acceptance conditions

- ac1: DEFAULT_COMMAND_DENY holds the 26 earlier names plus heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory (50); an override deny ["exit"] or [] leaves every default name denied, an override ["foo"] adds foo, and CreateSessionRequest still validates the names (updated, named) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac2: with agent and client ["*"], each of the 24 added names is refused denied for both origins, in any letter case ("Plugin", "MARKETPLACE") (new) [evidence: test:tests/test_command_registry.py::test_deny_list_covers_user_extension]
- ac3: a CommandQueue built from effective_commands(CommandsConfig(client=["*"]), CommandsOverride(deny=[])) or CommandsOverride(deny=["exit"]) refuses "clear" and "plugin" as denied, and a session-create request {"commands": {"deny": []}} validates without emptying the effective list (new) [evidence: test:tests/test_command_registry.py::test_create_override_only_extends_deny]
- ac4: config.example.yaml's commented deny list equals DEFAULT_COMMAND_DENY [evidence: test:tests/test_slash_commands_docs.py::test_config_example_documents_command_keys]
- ac5: README no longer says an override replaces the deny list and names the extension rule [evidence: command:! grep -q "a set \`deny\` replaces the default list" README.md && ! grep -q "a \`deny\` there replaces the default" README.md && grep -q "usage-credits" README.md]
- ac6: the named tests and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/commands.py`
- `README.md`
- `config.example.yaml`
- `tests/test_command_registry.py`

## Interfaces

- `claude_code_wrapper.config.DEFAULT_COMMAND_DENY: tuple[str, ...]`: 50 names (26 earlier plus the 24 of user decision 1, in that order).
- `claude_code_wrapper.commands.effective_commands(base, override) -> CommandsConfig`: `deny` = base deny plus the override's names not already in it (case-insensitive); every other field as before (override replaces when set).
- `POST /v1/sessions` `commands.deny`: extends only; `sessions.commands.deny` in the server config still sets the list.

## Expected outcome

`/plugin install ...`, `/memory`, `/export`, `/feedback` and the rest of the 24 are refused 403 `command_denied` for agent and client origins under `["*"]`, and no per-session override can remove a default name.

## Steps

- Red: update `test_deny_list_default_and_override` (named, no longer accurate: it pins replace semantics and 26 names), add `test_deny_list_covers_user_extension` and `test_create_override_only_extends_deny`; run `uv run pytest tests/test_command_registry.py`: they fail.
- Green: extend `DEFAULT_COMMAND_DENY`, change `effective_commands`, update README (the `commands` row of `POST /v1/sessions`, the Slash commands prose, the `sessions.commands.deny` reference row) and `config.example.yaml`; run the task's verify. Quote the summary line.

## Notes

- Name check done at planning (claude 2.1.304 binary): all 24 exist; `plugins` and `marketplace` are aliases of `plugin`, `routines` of `schedule`; `bug` is its own command; `desktop` has the alias `app`, which is not in the user's list (design Open questions Q3; an answer of yes amends this task). If the implementer finds a name missing from the binary, it is reported, not invented.
- `test_config_example_documents_command_keys` compares `config.example.yaml`'s commented deny list with `DEFAULT_COMMAND_DENY`; keep the example line in the same order.
- Builds on wrapper-slash-js-whitespace (same wrapper branch, README touched by both).
- Do not run `tests/test_manager.py` (known local failure `test_shutdown_stops_all`).

- 2026-10-29 done: 51 names: alias app of desktop added, leader-approved under the user's Q1
