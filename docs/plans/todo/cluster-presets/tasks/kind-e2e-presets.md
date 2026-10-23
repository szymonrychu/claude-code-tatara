---
title: kind e2e presets
status: todo
repo: agent-orchestrator
value: CI proves on a real cluster that presets and preset scheduling work through the public API alone
files: [tests/e2e/test_e2e_kind.py, e2e/values-kind.yaml]
verify: "uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [retire-cluster-patch-route]
owns: []
uses: [orch-presets-api, orch-cluster-create-api]
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

# kind e2e presets

## Requirement

Prove presets end to end through the public API on kind (design D8; headless parity, user Q1 to Q4), in `tests/e2e/test_e2e_kind.py` (marker `e2e`, run by `mise run test:e2e` and the PR CI `e2e` job). Only `/api/v1` over the port-forward is used; kubectl only for the existing pod and label assertions.

- The module `cluster` fixture creates a preset through `POST /presets` (`replicas: 2`, `peers: true`, `env: FAKE_TURN_ENV`) and schedules the shared cluster with `POST /clusters {"preset_id", "slug": SLUG}`; the view carries `preset_id` and `preset_name`; the rest of the module is unchanged.
- Teardown: every test deletes each cluster it creates; check `e2e/values-kind.yaml` and raise `ORCH_MAX_CLUSTERS` there only if needed. The generated-slug cluster is 1 replica.
- The Default preset is never edited in e2e; edit and delete act on the test's own preset or a copy.
- `test_default_preset_listed`: `GET /presets` lists the seeded default, asserts it exists, is `is_default`, and its spec `replicas` is 1.
- `test_preset_edit_and_delete_leave_cluster_unchanged`: after the cluster is ready, `PUT` the preset (`replicas: 1`) and then `POST .../copy`; the cluster's `spec` and `generation` are unchanged and its pod names and pod uids stay the same; then `DELETE` the source preset (204): the cluster's `preset_id` is null, `preset_name` is kept, `spec` and `generation` unchanged. Runs after the round-robin tests so their pods are not disturbed, and deletes the copy at the end.
- `test_schedule_default_preset_generated_slug`: `POST /clusters {"preset_id": <default id>}` is 201 with a slug matching `^default-[a-z]{4}$` and `spec.replicas == 1`; the test discards that cluster at once and waits until its row is gone.
- `test_patch_cluster_retired`: `PATCH /clusters/{id}` answers 405.
- `test_delete_default_preset_refused`: `DELETE /presets/{default id}` is 409 `preset_default`.

## Acceptance conditions

- AC1: the new e2e tests are collected under the e2e marker [evidence: command:uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py]
- AC2: the tests cover preset listing, schedule from a preset with explicit and generated slug, edit, copy and delete leaving the cluster unchanged, the default delete refusal and PATCH 405, through the public API only [evidence: judgement:tests/e2e/test_e2e_kind.py reviewed against the requirement; executed by the PR CI e2e job]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC4: test_default_preset_listed asserts the Default exists, is_default is true and its spec replicas is 1; no e2e test edits the Default [evidence: test:tests/e2e/test_e2e_kind.py::test_default_preset_listed]
- AC5: every cluster an e2e test creates is deleted in that test's teardown [evidence: judgement:tests/e2e/test_e2e_kind.py teardown reviewed; executed by the PR CI e2e job]

## Files

- `tests/e2e/test_e2e_kind.py`
- `e2e/values-kind.yaml` (only if `ORCH_MAX_CLUSTERS` needs raising, ruling 6)

## Interfaces

- Uses `/api/v1/presets` routes (part `orch-presets-api`) and the preset create body (part `orch-cluster-create-api`).
- Existing fixtures `api`, `baseline`, `cluster`, `round_robin` and helpers `wait_for`, `agents_of`, `kubectl` in `tests/e2e/test_e2e_kind.py`.

## Expected outcome

The PR CI e2e job shows on a real kind cluster that presets drive scheduling and that preset changes never touch a running cluster.

## Steps

- Change the `cluster` fixture and add the five tests; run `uv run pytest -q -p no:cacheprovider -m e2e --collect-only tests/e2e/test_e2e_kind.py`: the new tests are listed.
- Run the verify command: passes. The full run happens in CI (no cluster access here).

## Notes

- Order the new tests after the round-robin and before the discard test (the module runs in file order and shares one cluster).
- The generated-slug cluster costs one more reconcile; discard it immediately and wait only for its row to disappear, bounded like the existing discard wait.
- Pod uids come from `kubectl get pods -l agents.szymonrichert.pl/cluster=<SLUG> -o jsonpath`.
- Builder check ruling 6 (2026-10-23): tests delete every cluster they create in teardown; the builder checks e2e/values-kind.yaml and raises ORCH_MAX_CLUSTERS there only if needed; the generated-slug cluster is 1 replica.
- Builder check ruling 7 (2026-10-23): never edit the Default in e2e; edit and delete a copy. test_default_preset_listed asserts the Default exists, is_default, and its spec replicas is 1.

- 2026-10-23 amended: builder check rulings 6, 7: teardown deletes clusters, Default never edited (AC4, AC5 added)
