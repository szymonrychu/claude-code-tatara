---
title: orch default continue prompt
status: done
repo: agents-orchestrator
value: agents continue an interrupted turn after a restart without per-preset setup
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/k8s/render.py, tests/test_render.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, README.md]
verify: "uv run pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-onstart-nonfatal]
model: opus
review: ""
verified_head: 6982b3be4ba76d42889e6254d69086055de58f1e
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: 2
actual_minutes: 19
actual_tokens: 1172307
actual_roles: "impl 3, review 16"
actual_role_tokens: "impl 857088, review 315219"
---

# orch default continue prompt

## Requirement

Design D5, user decision verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next patch, 0.3.2) and pyproject version fixed to match."

This task is the orchestrator part: "the orchestrator renders a default restart_continue_prompt (render.py:130)". Design D5 (my call), verbatim: "The default prompt is an orchestrator setting `ORCH_DEFAULT_RESTART_CONTINUE_PROMPT` (default "Claude was restarted. Continue the task where you left off.", the wrapper's own example text), overridden by `spec.wrapper.restart_continue_prompt`."

Goal G4, verbatim: "A wrapper session resumed after a shutdown that interrupted a turn continues that turn with the continue prompt, and the orchestrator renders a default continue prompt."

Scope (agents-orchestrator):
- `settings.py`: `default_restart_continue_prompt: str` with the default above.
- `k8s/render.py` `_ccw_config`: `sessions.restart_continue_prompt` is always rendered, from the spec when set, else the setting.
- Tests no longer accurate, to update: `tests/test_render.py::test_no_wrapper_block_renders_unchanged` (its `sessions` dict gains the default prompt); goldens regenerated with `UPDATE_GOLDEN=1`.
- README settings table: `ORCH_DEFAULT_RESTART_CONTINUE_PROMPT`.

Steps: tests first, seen failing; then the change; regenerate goldens; run the verify.

Notes: the rendered config is validated against the pinned wrapper in `tests/test_render.py`; `restart_continue_prompt` is an existing wrapper key (`config.py:582`). `tests/test_settings.py` is not touched (in-progress epic slash-commands-from-chat owns it).

## Acceptance conditions

- AC1: a session with no wrapper block renders the default restart_continue_prompt [evidence: test:tests/test_render.py::test_default_restart_continue_prompt_rendered]
- AC2: spec.wrapper.restart_continue_prompt overrides the default [evidence: test:tests/test_render.py::test_spec_restart_continue_prompt_overrides_default]
- AC3: the no-wrapper-block render lists the default prompt in sessions [evidence: test:tests/test_render.py::test_no_wrapper_block_renders_unchanged]
- AC4: the golden renders are regenerated [evidence: command:uv run pytest -q tests/test_render.py -k golden]
- AC5: README documents the setting [evidence: command:grep -q "ORCH_DEFAULT_RESTART_CONTINUE_PROMPT" README.md]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_render.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done
