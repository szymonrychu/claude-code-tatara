---
title: smoke config check
status: todo
repo: agents-helmfile
value: the live smoke proves the new configuration on the deployed orchestrator
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [config-cluster-views]
owns: []
uses: [orch-cluster-config-api]
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

# smoke config check

## Requirement

Extend the live smoke to prove the new configuration on the deployed orchestrator (design D9; approvals A6, A7). In `scripts/smoke.sh` the smoke cluster spec adds `wrapper {auto_compact {idle_seconds: 1800}, hooks {onTurnComplete: [{type: command, run: "true"}]}}`, `leader_lease_seconds: 3600` (the smoke cluster is a hive through `max_replicas: 2`) and `autoclose_after_seconds: 3600`; after create it reads the cluster view and fails with a named message unless the spec echoes the three fields and `closes_at` equals `created_at` plus 3600 s; once a leader exists, `leader_since` is set. Cleanup stays in the existing trap, so the autoclose never fires during a smoke. `tests/test_smoke_script.py`: the fake API serves the new fields; a happy-path test and a test where the view lacks `closes_at` (named failure, cleanup runs). README smoke section names the config step.

## Acceptance conditions

- AC1: the happy path creates the cluster with the new fields, checks the spec echo, closes_at and leader_since, exits 0 and cleans up [evidence: test:tests/test_smoke_script.py::test_config_fields_checked]
- AC2: a view without closes_at fails with a named message and cleans up [evidence: test:tests/test_smoke_script.py::test_config_view_mismatch_fails]
- AC3: the script stays strict, bounded and shellcheck clean [evidence: test:tests/test_smoke_script.py::test_script_is_shellcheck_clean]
- AC4: lint passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

Uses `orch-cluster-config-api`.

## Expected outcome

`mise run smoke` creates its cluster with the new fields and fails with a named message when the view does not reflect them.

## Steps

- Red: add `test_config_fields_checked` and `test_config_view_mismatch_fails` to `tests/test_smoke_script.py` with the fake API serving the new fields; `uv run --frozen pytest -q tests/test_smoke_script.py`: fails.
- Green: extend `scripts/smoke.sh`; run the verify command and `mise run lint`: pass.

## Notes

Decisions are in design.md; nothing beyond the requirement.
