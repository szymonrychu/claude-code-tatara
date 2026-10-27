---
title: orch ci publish gate
status: todo
repo: agents-orchestrator
value: a red orchestrator main build is never pushed to Harbor or published as a chart
files: [.github/workflows/ci.yaml, tests/test_chart_ci.py, tests/test_images.py, README.md]
verify: "uv run pytest -q tests/test_chart_ci.py tests/test_images.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-e2e-main-failure]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch ci publish gate

## Requirement

Design D9, user decision verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator, web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no override flag. Its tests use fakes like tests/test_smoke_script.py."

Design D9, checked, verbatim: "the e2e job builds and loads its own images (`mise run test:e2e`, `scripts/e2e.sh`); it does not pull the pushed orchestrator image, so `e2e` may stop needing `images`."

This task is the agents-orchestrator part. Goal G8, verbatim: "No red main build is published or deployed: CI publish jobs need e2e/tests, and the agents-helmfile apply refuses pins whose commit checks are not green."

Scope (agents-orchestrator):
- `.github/workflows/ci.yaml`: nothing reaches Harbor (image push or chart push) before `lint`, `test` and `e2e` pass. Either a separate main-only push job that needs `lint`, `test`, `e2e` (and builds or receives the image), or the push step gated in a job that needs them; `e2e` no longer needs `images` when it does not use the pushed image. `chart-publish` and `chart-publish-tag` need `lint`, `test` and `e2e` too (plus the push job for main).
- Tests no longer accurate, to update: `tests/test_chart_ci.py::test_publish_only_main_and_tags_after_images` asserts `needs` exactly `{chart, images}` and `["chart"]`; `tests/test_images.py::test_ci_pushes_orchestrator_image_on_main_only` asserts the push step lives in the `images` job (update only if the push moves).
- README releasing section reflects the gate (`tests/test_chart_ci.py::test_readme_documents_releasing`).

Steps: tests first, seen failing; then the workflow; run the verify.

Notes: depends on orch-e2e-main-failure so the first gated main run is green. Keep the 50MB chunked `regctl image import` (Cloudflare 413).

## Acceptance conditions

- AC1: the image push runs only on main and only after lint, test and e2e passed [evidence: test:tests/test_chart_ci.py::test_image_push_needs_lint_test_e2e]
- AC2: chart-publish and chart-publish-tag need lint, test and e2e [evidence: test:tests/test_chart_ci.py::test_publish_only_main_and_tags_after_images]
- AC3: the e2e job does not need the pushed image [evidence: test:tests/test_chart_ci.py::test_e2e_does_not_need_pushed_image]
- AC4: exactly one image reference is pushed, on main only, in 50MB chunks [evidence: test:tests/test_images.py::test_ci_pushes_orchestrator_image_on_main_only]
- AC5: README documents the gated release [evidence: test:tests/test_chart_ci.py::test_readme_documents_releasing]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `.github/workflows/ci.yaml`
- `tests/test_chart_ci.py`
- `tests/test_images.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
