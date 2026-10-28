---
title: helmfile-pin-check-attempts
status: todo
repo: agents-helmfile
value: a harmless re-run of a published build never blocks a deploy
files: [scripts/check_pins.py, tests/test_check_pins.py, tests/fixtures, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_check_pins.py"
depends_on: [helmfile-pin-check]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 556633
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile-pin-check-attempts

## Requirement

`mise run check-pins` (scripts/check_pins.py, task helmfile-pin-check) refuses two live, correctly published pins: agents-webhook 838ba1f (run 40223858394) and agents-schedule 0.1.0 = tag v0.1.0 = 6cfa955 (run 40233933676). In both runs attempt 1 succeeded on 2026-10-25 (chart and images published); a manual re-run (attempt 2, 2026-10-28 05:31) failed only because the chart-publish guard refuses to re-push an already published chart version ("chart version ... already published"). check_pins.py reads only the latest attempt, so the pin is refused although its build was green and published (evidence: .scratchpad/session-loss/check-pins-refusal.md). Rule fix (my call, option b): a gated job counts as green when it succeeded in any attempt of the same workflow run for the pinned commit; a job that never succeeded in any attempt still refuses the pin. Use the GitHub API's per-attempt jobs (`/repos/{o}/{r}/actions/runs/{id}/attempts/{n}/jobs`) or equivalent; test first with fixtures (an attempt-1-green, attempt-2-red run is accepted; a run red in every attempt is refused). Record the rule in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: a pin whose gated job succeeded in an earlier attempt and failed in the latest attempt is accepted [evidence: test:tests/test_check_pins.py::test_earlier_green_attempt_accepts_pin]
- AC2: a pin whose gated job failed in every attempt is refused [evidence: test:tests/test_check_pins.py::test_red_in_every_attempt_refuses_pin]
- AC3: check-pins passes on the live and new pins [evidence: command:mise run check-pins]
- AC4: MEMORY.md records the attempt rule [evidence: command:grep -q "earlier attempt" MEMORY.md]

## Files

- `scripts/check_pins.py`
- `tests/test_check_pins.py`
- `tests/fixtures`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
