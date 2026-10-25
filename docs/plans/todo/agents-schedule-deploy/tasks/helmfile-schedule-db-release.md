---
title: helmfile schedule db release
status: todo
repo: agents-helmfile
value: the schedule service gets its own CNPG database in the agents namespace
files: [helmfile.yaml.gotmpl, values/agents-schedule-db/common.yaml, tests/test_schedule_db_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_db_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
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

# helmfile schedule db release

## Requirement

Add release `agents-schedule-db` (design D14; approval A6), the pattern of `agents-orchestrator-db` in `helmfile.yaml.gotmpl`: namespace `agents`, chart `cnpg/cluster` 0.9.0, `force: false`, timeout 600, labels `purpose: agents`, `application: agents-schedule`, values `values/common.yaml` and `values/agents-schedule-db/common.yaml` (one instance, storage as the orchestrator db, initdb database `schedule` owner `schedule`). The CNPG app Secret is `agents-schedule-db-cluster-app` with key `uri`.

## Acceptance conditions

- AC1: the release is declared with the pinned chart and labels [evidence: test:tests/test_schedule_db_release.py::test_release_declared]
- AC2: initdb names the schedule database and owner [evidence: test:tests/test_schedule_db_release.py::test_initdb]
- AC3: helmfile lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule-db/common.yaml`
- `tests/test_schedule_db_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
