---
title: kind e2e api
status: todo
repo: agents-schedule
value: every capability is proven headlessly against a real deployment in kind
files: [scripts/e2e.sh, e2e/values-kind.yaml, e2e/fake-orchestrator.yaml, tests/e2e/__init__.py, tests/e2e/test_e2e_kind.py]
verify: "bash -n scripts/e2e.sh && uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e && uv run ruff check . && uv run ruff format --check ."
depends_on: [chart-ingress-and-test-hook, dockerfile-and-ci, api-docs-and-openapi]
owns: [sched-kind-e2e]
uses: [agents-schedule-chart, agents-schedule-image, agents-schedule-api, agents-common-lib]
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

- `scripts/e2e.sh`: creates a kind cluster, builds and loads the image, installs a Postgres (the orchestrator e2e's approach), deploys the agents-common fake orchestrator (contract `agents-common-lib`, a Starlette app) from the agents-schedule image with `uvicorn agents_common.fake_orchestrator:app` (`e2e/fake-orchestrator.yaml`), installs the chart with `e2e/values-kind.yaml` (`components.worker.replicas: 2`, `SCHED_TICK_SECONDS: 2`, `SCHED_POLL_SECONDS: 1`), runs `pytest -m e2e tests/e2e`, deletes the cluster on exit.
- `test_e2e_kind.py` covers: create with validation 422s (cron, timezone, unknown preset), list, get, replace, preview, disable and enable, run now -> handled, a `* * * * *` schedule fires within 90 s and is handled, an overlapping fire while a turn is held running -> `ignored previous_running`, a failed turn -> `failed turn_failed`, run lists and get, delete -> 404; with 2 worker replicas each fire time has exactly one run and one cluster create. Turn outcomes are steered through the fake's own controls.
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
- `tests/e2e/test_e2e_kind.py`

## Interfaces

- `mise run test:e2e` (part `sched-kind-e2e`); CI job `e2e` runs it.

## Expected outcome

A headless e2e in kind proves create, validate, preview, fire, overlap, failure, run now, history and delete.

## Steps

- Write test_e2e_kind.py and the fake orchestrator; `uv run --frozen pytest tests/e2e/test_e2e_kind.py --collect-only -q -m e2e` collects.
- Write e2e.sh and the values; `mise run test:e2e`: all e2e tests pass.
- Lint clean.

## Notes

- `test_every_route_exercised` compares the routes hit (recorded by the test client wrapper) with `openapi.json` paths; it runs inside the e2e session.
- do-not-build: a second fake orchestrator; agents-common ships one. If it cannot hold a turn running or fail one, that is a gap in `agents-common-lib`: report it as `discovered` against agents-common and cover those two cases in tests/test_dispatcher.py and tests/test_tracker.py only.
- Real orchestrator coverage is the live smoke (`smoke-schedule-check`).
