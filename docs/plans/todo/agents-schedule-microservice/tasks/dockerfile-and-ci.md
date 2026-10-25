---
title: dockerfile and ci
status: todo
repo: agents-schedule
value: "every main commit is linted, tested and published as an image and chart"
files: [Dockerfile, .dockerignore, .github/workflows/ci.yaml, scripts/chart-version.sh, tests/test_ci_workflow.py]
verify: "uv run --frozen pytest tests/test_ci_workflow.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [service-entrypoints]
owns: [agents-schedule-image]
uses: [sched-entrypoints, agents-schedule-repo]
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

# dockerfile and ci

## Requirement

Add the image and CI (design D13; approvals A1, A6), modelled on `code/agent-orchestrator/Dockerfile` and `.github/workflows/ci.yaml`:

- Dockerfile: `python:<agents-common minor>-slim`, uv sync from the lock (no dev group), `USER 1000`, entrypoint `sched`; no node stage.
- ci.yaml on pull requests and push to main and tags `v*`: jobs `lint` (`mise run lint`), `test` (`mise run test`, Docker available for testcontainers), `images` (docker build, `docker run --rm <image> --help` smoke, push `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` on main with secrets `HARBOR_USERNAME`/`HARBOR_PASSWORD`, regctl chunked push as the orchestrator does), `chart` (`mise run lint:chart` and `mise run test:chart`), `e2e` (`mise run test:e2e`, kind), `chart-publish` (`<version>-main.<sha7>` on main via `scripts/chart-version.sh`), `chart-publish-tag` (`X.Y.Z` on tag `vX.Y.Z`) to `oci://harbor.szymonrichert.pl/charts/agents-schedule`.
- `tests/test_ci_workflow.py` parses ci.yaml and asserts the jobs, triggers, image name and chart repo, and that `scripts/chart-version.sh` prints `<chart version>-main.<sha7>` for a sha.

## Acceptance conditions

- AC1: the workflow has every job, trigger and publish target [evidence: test:tests/test_ci_workflow.py::test_workflow_jobs_and_targets]
- AC2: chart-version.sh prints the main build version [evidence: test:tests/test_ci_workflow.py::test_chart_version_script]
- AC3: the image builds and its entrypoint answers --help [evidence: command:docker build -t agents-schedule:ci . && docker run --rm agents-schedule:ci --help]
- AC4: the image runs as uid 1000 without a dev dependency [evidence: command:test "$(docker run --rm --entrypoint id agents-schedule:ci -u)" = 1000 && ! docker run --rm --entrypoint python agents-schedule:ci -c 'import pytest']

## Files

- `Dockerfile`
- `.dockerignore`
- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `tests/test_ci_workflow.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
