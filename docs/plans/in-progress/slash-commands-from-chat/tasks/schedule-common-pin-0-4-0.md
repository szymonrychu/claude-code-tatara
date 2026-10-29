---
title: schedule common pin 0.4.0
status: done
repo: agents-schedule
value: "a scheduled preset whose prompt is a slash command finishes by the command's outcome instead of timing out"
files: [pyproject.toml, uv.lock, README.md, tests/test_tracker.py]
verify: "uv run --frozen pytest tests/test_tracker.py && mise run lint"
depends_on: [common-release-0-4-0]
model: sonnet
review: ""
verified_head: 25601bb3620d83fadd41772b883dd07af790755f
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 5
actual_tokens: 455183
actual_roles: "impl 2, review 3"
actual_role_tokens: "impl 322472, review 132711"
---

# schedule common pin 0.4.0

## Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; [...]), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "7. `common-release-0-4-0` (a minor release), then two pin tasks:
   - `webhook-common-pin-0-4-0`: `pyproject.toml` (2 lines), `uv.lock`, test `tests/test_worker.py::test_command_prompt_run_handled`.
   - `schedule-common-pin-0-4-0`: `pyproject.toml`, `uv.lock`, test `tests/test_tracker.py::test_command_prompt_run_handled`."

Design D20, verbatim: "agents-webhook and agents-schedule move their pins to v0.4.0 and pin a slash preset prompt run that ends handled."

Needs the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session after mx-34's confirmation).

Scope (agents-schedule, branch from origin `main`): `pyproject.toml` (agents-common v0.3.0 to v0.4.0 in every line that pins it: 1), `uv.lock`, `tests/test_tracker.py` (a run whose prompt is slash text is tracked by the command outcome), README.md (the run reasons table gains `command_<error>` and `command_cancelled`, both `failed`).

## Acceptance conditions

- ac1: the service pins agents-common v0.4.0 in every pinning line and uv.lock, and Message carries command [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 1 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && grep -q 'agents-common?rev=v0.4.0#' uv.lock && ! grep -q 'rev=v0.3.0' uv.lock && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'command' in Message.model_fields"]
- ac2: (Docker) a run whose prompt is "/review-pr 12" ends handled when the fake orchestrator completes the command (fake.complete_command), with no timeout (new) [evidence: test:tests/test_tracker.py::test_command_prompt_run_handled]
- ac3: (Docker) a run whose command fails unknown_command ends failed with reason command_unknown_command, and a cancelled one with command_cancelled (new) [evidence: test:tests/test_tracker.py::test_command_prompt_run_failed_reason]
- ac4: README's reason table names command_cancelled and command_<error> [evidence: command:grep -q "command_cancelled" README.md && grep -q "command_<error>" README.md]
- ac5: the named tests and lint pass [evidence: command:uv run --frozen pytest tests/test_tracker.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_tracker.py`

## Interfaces

- `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0` in every line of `pyproject.toml` that pins it; `uv.lock` resolved to the v0.4.0 tag.
- Uses `agents_common.fake_orchestrator.FakeOrchestrator.complete_command` and `fail_command` in `tests/test_tracker.py`.

## Expected outcome

A agents-schedule run whose prompt is slash text finishes `handled` when its command completes and `failed` with `command_<error>` or `command_cancelled` when it does not, instead of `timeout`.

## Steps

- Confirm the v0.4.0 tag on origin (`git ls-remote --tags https://github.com/szymonrychu/agents-common v0.4.0`).
- Red: write `test_command_prompt_run_handled` and `test_command_prompt_run_failed_reason` in `tests/test_tracker.py` against the v0.3.0 pin; they fail (no `complete_command`).
- Green: move the pin, `uv lock`, README reason rows; run the task's verify (Docker for the database tests). Quote the summary line.

## Notes

- The run tracking itself is agents-common's `runs.track` (common-command-outcome); this task only pins it and proves it end to end in the service.
- Dependency bump: the TDD exception covers the pin values; the new tests are the behaviour guard.

- 2026-10-29 done
