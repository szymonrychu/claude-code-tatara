---
title: render wrapper settings
status: todo
repo: agent-orchestrator
value: "agents run with the user's hooks, idle auto-compact and other wrapper settings, with credentials safe from interpolation"
files: [src/agent_orchestrator/k8s/render.py, tests/test_render.py, README.md, MEMORY.md]
verify: "uv run --frozen pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-config-fields]
owns: []
uses: [orch-spec-config-fields, orch-render-hash-invariant]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# render wrapper settings

## Requirement

Render `spec.wrapper` into the claude-code-wrapper config (design D2, D3; approvals A1, A2). In `src/agent_orchestrator/k8s/render.py:_ccw_config`:

- Reserved entries stay first and cannot be removed: user `hooks.onStart` actions are appended after the rendered `sh /etc/ccw/on-start.sh` entry; user `hooks.onAgentToolCall` actions are appended after `_lock_check_hook()` when it is rendered; every other user hook event becomes its own list; `claude.permissions.deny` is `EnterPlanMode, ExitPlanMode, AskUserQuestion` followed by the user denies not already listed; `claude.permissions.allow` is the user allow list; user `mcp_servers` are added beside `any-mcp`; `prompts.system_append` is `ASK_IN_WRITING_PROMPT`, a blank line, then the user text.
- Mapping: `auto_compact` to `sessions.auto_compact`, `turn_stall_seconds`, `max_restarts`, `restart_continue_prompt` to `sessions.*`, `agent_commands` to `sessions.commands.agent`, `turn_max_seconds` to `limits.turn_max_seconds`, `plugins` to `plugins`. The rendered `sessions` keys `max_sessions`, `resume_on_start`, `idle_timeout_seconds` and `ask_user_question` stay as today.
- Escaping (user decision): every string value that comes from `spec.wrapper` (lists and nested values included, mapping keys excluded because the wrapper never interpolates keys) has each `$` replaced by `$$`, so `claude_code_wrapper.interpolation.interpolate` yields the user's literal text and a command hook's shell still sees `$VAR` at run time. Rendered orchestrator values (`${CCW_AUTH_TOKEN}`, the lock-check headers) are not escaped.
- A spec without `wrapper` renders exactly the config it renders today.

README.md: under `## Security` add `### Hooks and credentials`: command hooks run `sh -c` in the agent pod with the wrapper's full environment (`CLAUDE_CODE_OAUTH_TOKEN`, `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `ORCH_AGENT_TOKEN`); whoever edits a preset can already run code through terminals and init scripts; a webhook `secret` and headers are stored in the spec in plain text and returned by the API; `${VAR}` interpolation is disabled for every user value. MEMORY.md: a dated entry for the escaping rule and the reserved-first order, with the why.

Interfaces: uses part `orch-spec-config-fields`; keeps contract `orch-render-hash-invariant` (the new fields are create-time, so the config hash changes only with the spec).

Steps: red, add the five tests to `tests/test_render.py` (the escaping test calls the wrapper's `interpolate` with an env holding `CLAUDE_CODE_OAUTH_TOKEN=secret` and asserts the literal `${CLAUDE_CODE_OAUTH_TOKEN}` text comes back); green, implement in `_ccw_config` with one recursive escape helper over the user subtree; run the verify command.

Notes: the existing `test_rendered_ccw_config_validates` shows how to load the rendered YAML with the wrapper's `load_config`; extend that pattern for a full wrapper block. Highest-risk surface: credentials. Keep the helper pure.

## Acceptance conditions

- AC1: reserved entries survive and stay first: the on-start hook, the lock-check hook, the three built-in denies, the any-mcp server and the ASK_IN_WRITING prompt, with user entries after them [evidence: test:tests/test_render.py::test_wrapper_settings_keep_reserved_entries]
- AC2: a ${CLAUDE_CODE_OAUTH_TOKEN} placed in a webhook url, a header, a command run, auto-compact instructions and system_append renders escaped and interpolates back to the literal text [evidence: test:tests/test_render.py::test_user_strings_escaped_against_interpolation]
- AC3: every wrapper settings key lands at its wrapper config path [evidence: test:tests/test_render.py::test_wrapper_settings_mapped]
- AC4: a config rendered from a full wrapper block loads with the wrapper's own load_config [evidence: test:tests/test_render.py::test_rendered_wrapper_settings_validate]
- AC5: a spec without a wrapper block renders the same config as before [evidence: test:tests/test_render.py::test_no_wrapper_block_renders_unchanged]
- AC6: README documents the hook credential exposure [evidence: doc-section:README.md#Hooks and credentials]
- AC7: MEMORY.md has a dated entry for the escaping rule and the reserved-first order [evidence: judgement:MEMORY.md entry reviewed]
- AC8: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
