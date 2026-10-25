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

Interfaces: uses `orch-cluster-config-api`.

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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
