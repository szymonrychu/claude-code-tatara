---
title: deploy schedule
status: todo
repo: agents-helmfile
value: the agents namespace runs the schedule service and the UI with its Schedules entry
files: [helmfile.yaml.gotmpl, values/agents-schedule/common.yaml, values/agents-web/common.yaml, tests/test_schedule_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_release.py tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [release-v0-1-0, helmfile-schedule-release, schedule-service-token, web-config-schedules-backend, smoke-schedule-check, web-schedules-menu-entry]
owns: []
uses: [agents-schedule-release, agents-schedule-release-values, agents-web-schedules-config, agents-web-chart, agents-web-image]
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

# deploy schedule

## Requirement

Release and deploy this epic (design D14; approval A6). Pin release `agents-schedule` to chart `0.1.0` and `image.tag` to the sha7 of tag v0.1.0; pin the agents-web release to the main build that contains this epic's UI (chart `0.1.0-main.<sha7>` and image `<sha7>`, contracts `agents-web-chart` and `agents-web-image`). tests assert each chart version and image tag agree on their sha (offline, text read). Then run `bash scripts/bootstrap-secrets.sh` (schedule token), `mise run diff` (only the new releases and the agents-web pin change), `mise run apply` and `mise run smoke` against the expected kube context.

## Acceptance conditions

- AC1: the schedule chart and image pins agree on the v0.1.0 sha [evidence: test:tests/test_schedule_release.py::test_schedule_pin_matches_release]
- AC2: the agents-web chart and image pins agree on one sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: helmfile apply of the agents namespace succeeds [evidence: command:mise run apply]
- AC4: the live smoke passes, including the schedule step [evidence: command:mise run smoke]
- AC5: the diff shows only the new schedule releases and the agents-web pin [evidence: judgement:the task diff and mise run diff output reviewed]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_schedule_release.py`
- `tests/test_web_release.py`

## Interfaces

- Consumes chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` 0.1.0 and image `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` (contracts `agents-schedule-chart`, `agents-schedule-image`), and the agents-web main build.

## Expected outcome

The schedule service and the UI with its Schedules entry run live and the smoke is green.

## Steps

- Update the pin tests to the new shas; they fail.
- Change the pins; the verify passes.
- `bash scripts/bootstrap-secrets.sh`, `mise run diff`, `mise run apply`, `mise run smoke`: each exits 0.

## Notes

- Runs after the agents-schedule and agents-web merges reach main; the shas are filled with `ticket.py amend` then (precedent `docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md`, frontend-decoupling `deploy-pin-web`).
- `mise run apply` is guarded by lint, test and the kube-context check (`EXPECTED_KUBE_CONTEXT`).
- The orchestrator already runs the agents-webhook-microservice build with the service port; this task does not touch the orchestrator release.
