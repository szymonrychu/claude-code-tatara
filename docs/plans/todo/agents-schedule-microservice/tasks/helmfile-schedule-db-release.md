---
title: helmfile schedule db release
status: todo
repo: agents-helmfile
value: the schedule service gets its own CNPG database in the agents namespace
files: [helmfile.yaml.gotmpl, values/agents-schedule-db/common.yaml, tests/test_schedule_db_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_db_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [agents-schedule-db-release]
uses: []
model: ""
estimate: 5
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

# helmfile schedule db release

## Requirement

Add release `agents-schedule-db` (design D14; approval A6), the pattern of `agent-orchestrator-db` in `helmfile.yaml.gotmpl`: namespace `agents`, chart `cnpg/cluster` 0.9.0, `force: false`, timeout 600, labels `purpose: agents`, `application: agents-schedule`, values `values/common.yaml` and `values/agents-schedule-db/common.yaml` (one instance, storage as the orchestrator db, initdb database `schedule` owner `schedule`). The CNPG app Secret is `agents-schedule-db-cluster-app` with key `uri`.

## Acceptance conditions

- AC1: the release is declared with the pinned chart and labels [evidence: test:tests/test_schedule_db_release.py::test_release_declared]
- AC2: initdb names the schedule database and owner [evidence: test:tests/test_schedule_db_release.py::test_initdb]
- AC3: helmfile lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule-db/common.yaml`
- `tests/test_schedule_db_release.py`

## Interfaces

- Part `agents-schedule-db-release`: Secret `agents-schedule-db-cluster-app` key `uri` in namespace `agents`.

## Expected outcome

Applying the helmfile creates the schedule database next to the orchestrator's.

## Steps

- Write tests/test_schedule_db_release.py; run: fails.
- Add the release and values; the test passes.
- `mise run lint` clean.

## Notes

- Creating a database is additive; nothing existing changes. Listed at the gate with the apply.
