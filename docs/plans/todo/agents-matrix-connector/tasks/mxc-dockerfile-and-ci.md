---
title: mxc dockerfile and ci
status: todo
repo: agents-matrix-connector
value: main builds publish the connector image and chart to Harbor
files: [Dockerfile, .dockerignore, .github/workflows/ci.yaml, scripts/chart-version.sh, tests/test_ci.py]
verify: "uv run --frozen pytest tests/test_ci.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-service-entrypoints]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc dockerfile and ci

## Requirement

Image and CI of the connector (design D1, D13; contracts `agents-matrix-connector-image`, `agents-matrix-connector-chart`). Paths are in code/agents-matrix-connector.

- `Dockerfile` as agents-webhook's: `python:3.12-slim-bookworm`, uv from `ghcr.io/astral-sh/uv`, `uv sync --frozen --no-dev`, non-root `USER 1000`, `ENTRYPOINT ["agents-matrix-connector"]`, no default subcommand.
- `.dockerignore` excluding `.git`, `.venv`, `tests`, caches.
- `.github/workflows/ci.yaml` as agents-webhook's: on pull request and push to main run lint and the test suite (Docker available for testcontainers), `helm lint` of the chart; on push to main build and push `harbor.szymonrichert.pl/containers/agents-matrix-connector:<sha7>` and package and push the chart to `oci://harbor.szymonrichert.pl/charts/agents-matrix-connector` with version `0.1.0-main.<sha7>` (from `scripts/chart-version.sh`), using repo secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD`.
- `scripts/chart-version.sh` as agents-webhook's.
- `tests/test_ci.py`: the workflow builds the image with that name and tag, pushes the chart with that version, runs lint and tests on pull requests, and reads only the two Harbor secrets; the Dockerfile runs as user 1000 with the console-script entrypoint.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: main pushes the image harbor.szymonrichert.pl/containers/agents-matrix-connector:<sha7> and the chart 0.1.0-main.<sha7> [evidence: test:tests/test_ci.py::test_main_publishes_image_and_chart]
- AC2: pull requests run lint, tests and helm lint, and only the Harbor secrets are read [evidence: test:tests/test_ci.py::test_pr_checks_and_secrets]
- AC3: the image runs as user 1000 with the agents-matrix-connector entrypoint [evidence: test:tests/test_ci.py::test_dockerfile_user_and_entrypoint]
- AC4: the chart version script prints 0.1.0-main.<sha7> on main [evidence: command:bash scripts/chart-version.sh | grep -Eq '^0\.1\.0-main\.[0-9a-f]{7}$']

## Files

- `Dockerfile`
- `.dockerignore`
- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `tests/test_ci.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
