---
title: plugin advice threshold floor
status: todo
repo: any-mcp-tatara-plugins
value: "the plugin's handover advice never says 0% or a negative percent"
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/tests/test_orchestrator_plugin.py]
verify: "uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint"
depends_on: [plugins-release-0-4-0]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 632059
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugin advice threshold floor

## Requirement

Phase 5 review finding (Act on), README G3 verbatim: "the `hive_state` hint and the plugin advice always use the effective threshold". The effective threshold is `max(compact - HANDOVER_MARGIN_PCT, 1)` (agents-orchestrator dispatcher/hive.py:handover_threshold, HANDOVER_MARGIN_PCT 15). The orchestrator plugin (orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, the `me` tool description) renders `{cfg.auto_compact_pct - 15}%` with no floor, so a session with `auto_compact_pct` 1..15 (valid: spec Field ge=1) is advised 0% or a negative number. Make the advice use `max(auto_compact_pct - 15, 1)`, with the margin named once in the plugin as a constant whose comment points to the orchestrator's HANDOVER_MARGIN_PCT. Release it as plugin patch 0.5.1 on top of cct2's v0.5.0 (bump the orchestrator plugin version the way commit 3dfd403 did for 0.5.0). The git tag v0.5.1 is pushed by the supervisor after merge. No deploy in this task: the plugins ref pin rides with cct2's slash deploy.

## Acceptance conditions

- ac1: auto_compact_pct 10 renders the advice "passes 1%" and 80 renders "passes 65%" [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_handover_advice_uses_the_floored_threshold]
- ac2: the orchestrator plugin version is 0.5.1 [evidence: judgement:reviewer reads the version files changed as in 3dfd403]
- ac3: plugin tests and lint pass [evidence: command:uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Branch `plugin-advice-floor` from fresh origin/main (dfa0355, v0.5.0).
- Add test_handover_advice_uses_the_floored_threshold (auto_compact_pct 10 -> "passes 1%", 80 -> "passes 65%"); run the verify: red on the 10 case.
- Floor the advice with a named margin constant; rerun: green. Bump the orchestrator plugin version to 0.5.1 as 3dfd403 did. Commit, push, open a PR to main. Known pod-only failure: tests/test_source_install (git 2.39 --end-of-options), also red on origin/main; quote it, do not fix it.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
