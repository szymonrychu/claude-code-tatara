---
title: wrapper command docs
status: in-progress
repo: claude-code-wrapper
value: operators read in the README and example configs what any slash command does and how long it can hold a session
files: [README.md, config.example.yaml, src/claude_code_wrapper/data/config.example.yaml, src/claude_code_wrapper/data/examples/workbench.config.yaml, tests/test_slash_commands_docs.py]
verify: "uv run pytest tests/test_slash_commands_docs.py tests/test_readme_api.py tests/test_readme_config.py tests/test_examples.py tests/test_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-commands-after-stop]
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

# wrapper command docs

## Requirement

Design D17, verbatim: "README `## Slash commands` (tool, endpoint, lifecycle, configuration, limits) describes any name, args, the deny list, the classes and bounds; the Limits paragraph "the five names above are the whole set" goes. `data/examples/workbench.config.yaml` sets `client: ["*"]`; tatara and magic-trainer keep their agent lists. `config.example.yaml` documents `deny`, `dialog_grace_seconds`, `dialog_patterns`."

User decision (gate brief): "Replace the five structured command params [...] with free-text `args` everywhere, including the ccw MCP `command` tool and the example configs, with no compatibility shim".

Scope (claude-code-wrapper): `README.md` `## Slash commands` (all six subsections, Limits rewritten: what runs, the deny list, dialog and prompt classes, the bounds of design Bounds), `config.example.yaml` and `src/claude_code_wrapper/data/config.example.yaml` (commented `commands:` block with `deny`, `dialog_grace_seconds`, `dialog_patterns`), `src/claude_code_wrapper/data/examples/workbench.config.yaml` (`client: ["*"]`, its comment), `tests/test_slash_commands_docs.py`.

Tests no longer accurate (named): `tests/test_slash_commands_docs.py::test_workbench_example_enables_commands` pins the client list to the five built-ins (`ALL_COMMANDS`); the example now allows `"*"`. `::test_config_example_documents_command_keys` gains the three new keys.

## Acceptance conditions

- ac1: README Slash commands keeps its six subsections and names the deny list, dialog dismissal, prompt commands as turns and the bounds (updated) [evidence: test:tests/test_slash_commands_docs.py::test_readme_slash_commands_content]
- ac2: the five-name Limits sentence is gone [evidence: command:! grep -q "the five names above are the whole set" README.md]
- ac3: the example config documents deny, dialog_grace_seconds and dialog_patterns with the model defaults (updated) [evidence: test:tests/test_slash_commands_docs.py::test_config_example_documents_command_keys]
- ac4: the workbench example allows client ["*"] (updated) [evidence: test:tests/test_slash_commands_docs.py::test_workbench_example_enables_commands]
- ac5: every example config still validates [evidence: command:uv run pytest tests/test_examples.py tests/test_config.py]
- ac6: targeted suites and lint pass [evidence: command:uv run pytest tests/test_slash_commands_docs.py tests/test_readme_api.py tests/test_readme_config.py tests/test_examples.py tests/test_config.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `README.md`
- `config.example.yaml`
- `src/claude_code_wrapper/data/config.example.yaml`
- `src/claude_code_wrapper/data/examples/workbench.config.yaml`
- `tests/test_slash_commands_docs.py`

## Interfaces

None beyond the documented config keys (`sessions.commands.deny`, `dialog_grace_seconds`, `dialog_patterns`, agent/client names or `"*"`).

## Expected outcome

An operator reading the README or the example configs learns that any command except the deny list runs, how each class completes and the worst-case hold.

## Steps

- Red: update the docs tests (ac1, ac3, ac4); run `uv run pytest tests/test_slash_commands_docs.py`: they fail.
- Green: README and the example configs; run the task's verify: passes. Quote the summary line.

## Notes

- Doc and config edit with test pins; the docs tests are written first.
- `config.example.yaml` at the repo root and `src/claude_code_wrapper/data/config.example.yaml`: check whether one is a copy of the other (`test_config_example_documents_command_keys` reads the root one) and keep both consistent.
- Depends on wrapper-commands-after-stop (every behaviour the docs describe has landed).
