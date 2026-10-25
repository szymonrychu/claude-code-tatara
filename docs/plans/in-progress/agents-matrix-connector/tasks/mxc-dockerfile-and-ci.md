---
title: mxc dockerfile and ci
status: done
repo: agents-matrix-connector
value: main builds publish the connector image and chart to Harbor
files: [Dockerfile, .dockerignore, .github/workflows/ci.yaml, scripts/chart-version.sh, tests/test_ci.py]
verify: "uv run --frozen pytest tests/test_ci.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-service-entrypoints]
model: sonnet
review: ""
verified_head: 433e8736a1d65e1fd79790b14a3179a717f4c45e
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: 2
actual_minutes: 2
actual_tokens: 368146
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 205772, review 162374"
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

- `harbor.szymonrichert.pl/containers/agents-matrix-connector:<sha7>` (contract `agents-matrix-connector-image`) and `oci://harbor.szymonrichert.pl/charts/agents-matrix-connector` `0.1.0-main.<sha7>` (contract `agents-matrix-connector-chart`), consumed by helmfile-matrix-releases.

## Expected outcome

After this epic's connector PR merges, main CI publishes the image and the chart to Harbor.

## Steps

- Red: `tests/test_ci.py` with the three tests parsing the workflow YAML and the Dockerfile. Fails: no files.
- Green: write the four files, copying agents-webhook's shape. Run the verify.

## Notes

- Copy `code/agents-webhook/.github/workflows/ci.yaml`, `Dockerfile`, `scripts/chart-version.sh` and `tests/test_ci.py`, renaming; keep their action pins.
- The Harbor secrets are set on the repo by orchestrator step O1.

- 2026-10-25 done
