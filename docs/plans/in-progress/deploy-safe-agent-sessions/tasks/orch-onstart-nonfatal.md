---
title: orch onstart nonfatal
status: done
repo: agents-orchestrator
value: a failed plugin install no longer keeps an agent pod from starting
files: [src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/k8s/on_start.py, tests/test_render.py, tests/test_on_start.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, MEMORY.md]
verify: "uv run pytest -q tests/test_render.py tests/test_on_start.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: 289be85a6859eb7a923fd98ce8feb045ceafefcc
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: 2
actual_minutes: 20
actual_tokens: 820107
actual_roles: "impl 4, review 16"
actual_role_tokens: "impl 609387, review 210720"
---

# orch onstart nonfatal

## Requirement

Design D6, user decision verbatim: "onStart plugin install: stays blocking (tools ready before sessions resume) but with on_error allow, and the on_start.py script logs and swallows an install failure (never exits non-zero for it, never exit 2); a failed install leaves the pod Ready."

Design D6 (my call), verbatim: "Both installs are covered: the any-mcp package install (then `.ref` is not written, so the next start retries) and `any-mcp plugins install`; the trailing `any-mcp --help` check is skipped after a failed install. Each failure prints one line to stderr naming the step."

Goal G5, verbatim: "A failed any-mcp plugin install in onStart is logged and leaves the agent pod Ready."

Scope (agents-orchestrator):
- `k8s/render.py`: the onStart hook stays `blocking: True` with `on_error: "allow"`.
- `k8s/on_start.py` `render_on_start`: the pip install and `plugins install` failures are logged to stderr (one line naming the step) and swallowed; the script exits 0 for them and never exits 2; `.ref` is written only after a successful package install; `--help` runs only after a successful install. Other failures (writing the config) keep failing as today.
- Tests no longer accurate, to update: `tests/test_render.py::test_on_start_hook_and_startup_probe` asserts `on_error: deny`; the golden files `tests/golden/session_single.yaml` and `tests/golden/session_two_peers.yaml` are regenerated with `UPDATE_GOLDEN=1` (the rendered hook changes).
- New script tests in `tests/test_on_start.py` run the rendered script with fake `python3`/`pip`/`any-mcp` on PATH (pattern of `tests/test_render.py::test_on_start_script_installs_once_and_writes_json_config`).

Steps: tests first, seen failing; then the change; regenerate goldens; run the verify.

Notes: the wrapper denies on an exit 2 regardless of on_error (`hooks.py:407-409`), so exit 2 must never escape. The config hash changes, so agent pods roll under the replacer of task orch-rollout-replacer (same release). MEMORY.md dated entry.

## Acceptance conditions

- AC1: the onStart hook is blocking with on_error allow [evidence: test:tests/test_render.py::test_on_start_hook_and_startup_probe]
- AC2: a failing plugins install is logged naming the step and the script exits 0 [evidence: test:tests/test_on_start.py::test_plugin_install_failure_logged_and_exits_zero]
- AC3: a failing any-mcp package install is logged, exits 0, writes no .ref and skips the --help check [evidence: test:tests/test_on_start.py::test_any_mcp_install_failure_logged_and_retried_next_start]
- AC4: an install tool exiting 2 never makes the script exit 2 or non-zero [evidence: test:tests/test_on_start.py::test_install_exit_two_never_propagates]
- AC5: the golden renders are regenerated [evidence: command:uv run pytest -q tests/test_render.py -k golden]
- AC6: MEMORY.md records the decision [evidence: command:grep -q "on_error allow" MEMORY.md]
- AC7: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_render.py`
- `tests/test_on_start.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_render.py tests/test_on_start.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_render.py tests/test_on_start.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done
