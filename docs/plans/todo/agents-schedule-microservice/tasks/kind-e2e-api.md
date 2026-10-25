---
title: kind e2e api
status: todo
repo: agents-schedule
value: every capability is proven headlessly against a real deployment in kind
files: [scripts/e2e.sh, e2e/values-kind.yaml, e2e/fake-orchestrator.yaml, tests/e2e/__init__.py, tests/e2e/fake_orchestrator.py, tests/e2e/test_e2e_kind.py]
verify: "bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e && uv run ruff check . && uv run ruff format --check ."
depends_on: [chart-ingress-and-test-hook, dockerfile-and-ci, api-docs-and-openapi]
owns: [sched-kind-e2e]
uses: [agents-schedule-chart, agents-schedule-image, agents-schedule-api]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# kind e2e api

## Requirement

Add the API-only kind e2e (design D11; approval A5), modelled on `code/agent-orchestrator/scripts/e2e.sh` and `tests/e2e/test_e2e_kind.py`. Every capability of the API is exercised over HTTP through a port-forward to the api Service; no UI is touched.

- `scripts/e2e.sh`: creates a kind cluster, builds and loads the image, installs a Postgres (the orchestrator e2e's approach), deploys `tests/e2e/fake_orchestrator.py` from a ConfigMap (`e2e/fake-orchestrator.yaml`, python slim image, stdlib http.server), installs the chart with `e2e/values-kind.yaml` (`components.worker.replicas: 2`, `SCHED_TICK_SECONDS: 2`, `SCHED_POLL_SECONDS: 1`), runs `pytest -m e2e tests/e2e`, deletes the cluster on exit.
- The fake orchestrator implements the routes the service calls (`GET /api/v1/presets[/{id}]`, `POST|GET /api/v1/clusters`, `GET|POST /api/v1/clusters/{id}/messages`, `GET /api/v1/messages/{id}`), checks the bearer token, answers 409 on a taken slug, and completes a turn after 2 s unless the prompt contains `HOLD` (stays running) or `FAIL` (turn fails). It exposes `GET /_calls` for assertions.
- `test_e2e_kind.py` covers: create with validation 422s (cron, timezone, unknown preset), list, get, replace, preview, disable and enable, run now -> handled, a `* * * * *` schedule fires within 90 s and is handled, overlap with `HOLD` -> next fire `ignored previous_running`, `FAIL` -> `failed turn_failed`, run lists and get, delete -> 404; with 2 worker replicas each fire time has exactly one run and one create call.
- `mise run test:e2e` (defined by `scaffold-project-and-cli`) runs `bash scripts/e2e.sh`.

## Acceptance conditions

- AC1: the e2e suite collects and the script parses [evidence: command:bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e]
- AC2: the kind e2e passes end to end [evidence: command:mise run test:e2e]
- AC3: the e2e hits every route in openapi.json [evidence: judgement:test_every_route_exercised compares the routes the e2e client recorded with openapi.json paths and passes inside mise run test:e2e]
- AC4: two workers produce exactly one run and one cluster per fire time [evidence: judgement:the e2e asserts one run per (schedule, fire_time) and one create call per run via the fake orchestrator /_calls]

## Files

- `scripts/e2e.sh`
- `e2e/values-kind.yaml`
- `e2e/fake-orchestrator.yaml`
- `tests/e2e/__init__.py`
- `tests/e2e/fake_orchestrator.py`
- `tests/e2e/test_e2e_kind.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
