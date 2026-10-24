---
title: main agent only tools
status: todo
repo: claude-code-wrapper
value: a subagent cannot hand leadership away or scale the cluster
files: [src/claude_code_wrapper/config.py, src/claude_code_wrapper/router.py, README.md, tests/test_main_agent_only_tools.py]
verify: "uv run pytest tests/test_main_agent_only_tools.py tests/test_readme_config.py tests/test_config.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [wrapper-main-agent-only-tools]
uses: []
model: ""
estimate: 6
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

# main agent only tools

## Requirement

Foundation part F2 (D2 main-agent gating). New wrapper config key `claude.main_agent_only_tools: list[str]` (fnmatch globs, default `[]`). The PreToolUse gate in `router.py` denies a tool whose name matches any glob when the hook payload carries `agent_id` (a subagent), next to the existing `mcp__ccw__*` check (`router.py:611-614`), with the same deny shape and a reason naming the main-agent-only rule. Main-agent calls pass; non-matching tools and the default `[]` change nothing. The orchestrator renders `["mcp__any-mcp__orchestrator_*"]`, so a leader's subagent cannot hand leadership away or scale the cluster.

README: the key in the config reference (enforced by `tests/test_readme_config.py`) and one sentence in the trust model section.

## Acceptance conditions

- AC1: a subagent call of a tool matching a configured glob is denied in PreToolUse [evidence: test:tests/test_main_agent_only_tools.py::test_subagent_call_denied]
- AC2: the main agent's call of the same tool is allowed [evidence: test:tests/test_main_agent_only_tools.py::test_main_agent_allowed]
- AC3: with the default empty list, and for non-matching tools, the gate behaves as before [evidence: test:tests/test_main_agent_only_tools.py::test_default_empty_changes_nothing]
- AC4: the key validates as a list of strings and is documented in the README config reference [evidence: command:uv run pytest tests/test_readme_config.py tests/test_config.py -q]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/config.py`
- `src/claude_code_wrapper/router.py`
- `README.md`
- `tests/test_main_agent_only_tools.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
