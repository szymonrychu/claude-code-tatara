---
title: smoke web ui
status: in-progress
repo: agents-helmfile
value: "the live smoke proves the UI, its config and the path routing"
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md, mise.toml]
verify: "uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_mise_tasks.py && uv run ruff check . && uv run ruff format --check . && shellcheck --severity=error scripts/smoke.sh"
depends_on: [web-chart-config-ingress]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# smoke web ui

## Requirement

The smoke checks the UI on the agents-web release and the path routing of the host (design D2, D8). Paths are in code/agents-helmfile.

- `scripts/smoke.sh` step 1 is split:
  - UI: without `HOST`, port-forward `svc/${WEB_RELEASE:-agents-web}` port 8080 to `127.0.0.1:${SMOKE_WEB_LOCAL_PORT:-18080}` (killed by the existing trap); `GET /` answers HTML and `GET /config.json` is JSON listing a backend `orchestrator` with `basePath` `/api/v1`. With `HOST` set, both go to `https://$HOST`.
  - API: `GET /api/v1/openapi.json` through the api port-forward as today.
  - Ingress routing, in the existing ingress query: for host `lab.szymonrichert.pl` the path `/` routes to Service `agents-web` and the path `/api` to Service `agent-orchestrator`; any other mapping fails naming it. No Ingress at all still passes (existing test).
- `tests/test_smoke_script.py`: the fake server and fake kubectl cover the web port-forward; new tests: the happy path checks the web UI and config, a non-HTML web root fails, a config without `orchestrator` fails, `/` routed to the api Service fails, `/api` missing fails. Every existing test keeps passing.
- `README.md` and the `smoke` task description in `mise.toml`: the UI is checked on agents-web.

## Acceptance conditions

- AC1: the smoke checks the UI and its config on the agents-web Service [evidence: test:tests/test_smoke_script.py::test_ui_checked_on_web_service]
- AC2: a config without the orchestrator backend fails the smoke [evidence: test:tests/test_smoke_script.py::test_web_config_without_orchestrator_fails]
- AC3: the root path routed to the api fails the smoke [evidence: test:tests/test_smoke_script.py::test_root_path_routed_to_api_fails]
- AC4: a missing /api path fails the smoke [evidence: test:tests/test_smoke_script.py::test_api_path_missing_fails]
- AC5: the script stays strict, bounded and shellcheck clean and every smoke test passes [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_mise_tasks.py && shellcheck --severity=error scripts/smoke.sh]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`
- `mise.toml`

## Interfaces

- Uses `web-chart` (Service `agents-web`, port 8080), `backends-config` (`config.json`) and `url-layout` (`/` to agents-web, `/api` to agent-orchestrator).

## Expected outcome

`mise run smoke` proves the split: UI from agents-web, API from the orchestrator, and the host's path routing.

## Steps

- Red: the new tests in `tests/test_smoke_script.py`; `uv run pytest -q tests/test_smoke_script.py` fails.
- Green: edit `scripts/smoke.sh`, README, `mise.toml` description.
- Run the AC5 command: pass.

## Notes

- Keep the script's existing guarantees: `set -euo pipefail`, bounded curls, trap cleanup of both port-forwards (`test_script_is_strict_bounded_and_traps`).
- This smoke runs live only after deploy-pin-web; before that the host still routes `/` to the api.
