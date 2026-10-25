---
title: ci image checks and worker test flake
status: todo
repo: agents-schedule
value: "the image's non-root and no-dev-deps guarantees are checked on every PR, and the suite does not flake"
files: [.github/workflows/ci.yaml, tests/test_ci_workflow.py, tests/test_entrypoints.py]
verify: "uv run --frozen pytest tests/test_ci_workflow.py tests/test_entrypoints.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [epic-review-fixes]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 671138
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# ci image checks and worker test flake

## Requirement

Close two gaps found while verifying the epic (dockerfile-and-ci AC4, the full suite).

- The CI `images` job, after the existing `--help` smoke step and before any push, also asserts the image runs as uid 1000 and carries no dev dependency: `test "$(docker run --rm --entrypoint id agents-schedule:ci -u)" = 1000` and `! docker run --rm --entrypoint python agents-schedule:ci -c 'import pytest'`, so dockerfile-and-ci AC4 is checked on every PR, not only by hand.
- `tests/test_entrypoints.py::test_single_worker_fires` is deterministic: today it uses an every-minute schedule and a fixed sleep, so it fires twice when the run crosses a minute boundary (seen as `assert 2 == 1` in a full-suite run). Make the expected fire count independent of wall-clock minute boundaries (for example a schedule armed so exactly one fire time falls in the observed window, or asserting one run per fire_time and one lock holder) while still proving that a second worker never fires.

## Acceptance conditions

- AC1: the images job asserts uid 1000 and no pytest in the image before any push [evidence: test:tests/test_ci_workflow.py::test_images_job_checks_uid_and_no_dev_deps]
- AC2: the single-worker test passes regardless of minute boundaries [evidence: test:tests/test_entrypoints.py::test_single_worker_fires]

## Files

- `.github/workflows/ci.yaml`
- `tests/test_ci_workflow.py`
- `tests/test_entrypoints.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
