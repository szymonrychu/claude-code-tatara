---
title: deploy schedule
status: todo
repo: agents-helmfile
value: the agents namespace runs the schedule service and the UI with its Schedules entry
files: [helmfile.yaml.gotmpl, values/agents-schedule/common.yaml, values/agents-web/common.yaml, tests/test_schedule_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_release.py tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-schedule-release, schedule-service-token, web-config-schedules-backend, smoke-schedule-check, web-schedules-menu-entry]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 678580
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# deploy schedule

## Requirement

Release and deploy this epic (design D14; approval A6). Pin release `agents-schedule` to chart `0.1.0` and `image.tag` to the sha7 of tag v0.1.0; pin the agents-web release to the main build that contains this epic's UI (chart `0.1.0-main.<sha7>` and image `<sha7>`, contracts `agents-web-chart` and `agents-web-image`). tests assert each chart version and image tag agree on their sha (offline, text read). Then run `bash scripts/bootstrap-secrets.sh` (schedule token), `mise run diff` (only the new releases and the agents-web pin change), `mise run apply` and `mise run smoke` against the expected kube context.

## Acceptance conditions

- AC1: the schedule chart and image pins agree on the v0.1.0 sha [evidence: test:tests/test_schedule_release.py::test_schedule_pin_matches_release]
- AC2: the agents-web chart and image pins agree on one sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC3: helmfile apply of the agents namespace succeeds [evidence: judgement:the apply output (helm revision and chart) quoted in the task notes; never run apply as AC evidence]
- AC4: the live smoke passes, including the schedule step [evidence: command:mise run smoke]
- AC5: the diff shows only the new schedule releases and the agents-web pin [evidence: judgement:the task diff and mise run diff output reviewed]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_schedule_release.py`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
