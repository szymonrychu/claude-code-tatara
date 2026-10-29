---
title: wrapper deny list extend
status: todo
repo: claude-code-wrapper
value: "commands that install, export, reconfigure or report from the agent's account can no longer be run from chat, and no session override can lift the deny list"
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/commands.py, README.md, config.example.yaml, tests/test_command_registry.py]
verify: "uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-slash-js-whitespace]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
