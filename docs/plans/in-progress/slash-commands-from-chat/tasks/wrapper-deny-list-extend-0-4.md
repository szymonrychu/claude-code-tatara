---
title: wrapper deny list extend 0.4.2
status: done
repo: claude-code-wrapper
value: "chat users can no longer reach the agent account's cloud features or rewrite the session's tool and permission settings"
files: [src/claude_code_wrapper/config.py, README.md, config.example.yaml, tests/test_command_registry.py]
verify: "uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: 24c2ce95dd865251a3200ece14c47416bc7872a0
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: 2
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper deny list extend 0.4.2

## Requirement

User decision PENDING (mx-34 #471 Q1-3, recommended yes to all; tatara #473 confirmed the version v0.4.2). The leader amends this paragraph with the user verbatim answer before the merge; nothing merges or is tagged before it. Questions, verbatim: "1) Deny the account or cloud group too? That means wrapper v0.4.2 (patch, after v0.4.1) before the slash deploy, about 1 h of agent time. Recommended: yes. 2) Also deny mcp, permissions, config and hooks in v0.4.2? Recommended: yes, so that chat cannot rewrite the session's tool and permission settings. 3) Bump the version to wrapper v0.4.2? Live is 0.3.3, v0.4.1 is tagged but not deployed, and v0.4.2 would replace it in the same deploy. Recommended: yes, pending tatara's confirmation."

Security re-review (.scratchpad/slash-fix-phase5/security.md), verbatim: "MEDIUM wrapper config.py:499: still allowed by client [\"*\"] and reaching account/cloud: privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, session (alias remote). Names confirmed present in claude 2.1.304 binary by cct2-1. Local-settings commands also allowed: mcp, permissions/allowed-tools, config/settings, hooks."

Name check (cct2-1, claude 2.1.304 binary): privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, mcp and hooks are commands; session has alias remote; permissions has alias allowed-tools; config has alias settings. None is in the current 51-name DEFAULT_COMMAND_DENY.

Scope (claude-code-wrapper, new branch slash-deny-v042 from origin/main eed2c3c):
- `src/claude_code_wrapper/config.py`: append the 13 names privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, session, remote, mcp, permissions, allowed-tools, config, settings, hooks to `DEFAULT_COMMAND_DENY` (51 + 13 = 64), with the comment naming why (account/cloud reach; session tool and permission settings).
- README.md: the default deny list documented as the 64 names.
- `config.example.yaml`: the commented `deny:` line lists the 64 names in the same order.
- `tests/test_command_registry.py`: `test_deny_list_default_and_override` pins 51 names and is no longer accurate (named): update it to 64; add a test that each of the 13 is refused denied for agent and client origins in any letter case.

## Acceptance conditions

- ac1: DEFAULT_COMMAND_DENY holds the 51 earlier names plus privacy-settings, ultraplan, ultrareview, autofix-pr, cloud-plugins, session, remote, mcp, permissions, allowed-tools, config, settings, hooks (64), override still extend-only (updated, named) [evidence: test:tests/test_command_registry.py::test_deny_list_default_and_override]
- ac2: with agent and client ["*"], each of the 13 added names is refused denied for both origins in any letter case ("Ultrareview", "MCP") (new) [evidence: test:tests/test_command_registry.py::test_deny_list_covers_account_and_settings]
- ac3: config.example.yaml's commented deny list equals DEFAULT_COMMAND_DENY [evidence: test:tests/test_slash_commands_docs.py::test_config_example_documents_command_keys]
- ac4: README names the added commands [evidence: command:grep -q "ultrareview" README.md && grep -q "allowed-tools" README.md]
- ac5: the named tests and lint pass [evidence: command:uv run pytest tests/test_command_registry.py tests/test_slash_commands_docs.py tests/test_config.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/config.py`
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

- 2026-10-29 done

- 2026-10-29 actuals: no agent records
