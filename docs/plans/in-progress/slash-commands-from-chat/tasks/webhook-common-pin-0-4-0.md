---
title: webhook common pin 0.4.0
status: todo
repo: agents-webhook
value: "a webhook preset whose prompt is a slash command finishes by the command's outcome instead of timing out"
files: [pyproject.toml, uv.lock, README.md, tests/test_worker.py]
verify: "uv run --frozen pytest tests/test_worker.py && mise run lint"
depends_on: [common-release-0-4-0]
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

# webhook common pin 0.4.0

## Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; [...]), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "7. `common-release-0-4-0` (a minor release), then two pin tasks:
   - `webhook-common-pin-0-4-0`: `pyproject.toml` (2 lines), `uv.lock`, test `tests/test_worker.py::test_command_prompt_run_handled`.
   - `schedule-common-pin-0-4-0`: `pyproject.toml`, `uv.lock`, test `tests/test_tracker.py::test_command_prompt_run_handled`."

Design D20, verbatim: "agents-webhook and agents-schedule move their pins to v0.4.0 and pin a slash preset prompt run that ends handled."

Needs the agents-common v0.4.0 tag on origin (common-release-0-4-0 ac3, pushed by the orchestrator session after mx-34's confirmation).

Scope (agents-webhook, branch from origin `main`): `pyproject.toml` (agents-common v0.3.0 to v0.4.0 in every line that pins it: 2), `uv.lock`, `tests/test_worker.py` (a run whose prompt is slash text is tracked by the command outcome), README.md (the run reasons table gains `command_<error>` and `command_cancelled`, both `failed`).

## Acceptance conditions

- ac1: the service pins agents-common v0.4.0 in every pinning line and uv.lock, and Message carries command [evidence: command:test "$(grep -c 'agents-common@v0.4.0' pyproject.toml)" = 2 && ! grep -q 'agents-common@v0.3.0' pyproject.toml && grep -q 'agents-common?rev=v0.4.0#' uv.lock && ! grep -q 'rev=v0.3.0' uv.lock && uv run --frozen python -c "from agents_common.orchestrator import Message; assert 'command' in Message.model_fields"]
- ac2: (Docker) a run whose prompt is "/review-pr 12" ends handled when the fake orchestrator completes the command (fake.complete_command), with no timeout (new) [evidence: test:tests/test_worker.py::test_command_prompt_run_handled]
- ac3: (Docker) a run whose command fails unknown_command ends failed with reason command_unknown_command, and a cancelled one with command_cancelled (new) [evidence: test:tests/test_worker.py::test_command_prompt_run_failed_reason]
- ac4: README's reason table names command_cancelled and command_<error> [evidence: command:grep -q "command_cancelled" README.md && grep -q "command_<error>" README.md]
- ac5: the named tests and lint pass [evidence: command:uv run --frozen pytest tests/test_worker.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `tests/test_worker.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
