---
title: db secret name from cnpg
status: todo
repo: agents-helmfile
value: the orchestrator connects to the database CNPG actually created
files: [values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py, scripts/smoke.sh, README.md]
verify: "uv run pytest tests/test_orchestrator_release.py tests/test_db_release.py -q -p no:cacheprovider && mise run lint"
depends_on: [mise-tasks, orchestrator-release, smoke-script]
owns: []
uses: []
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

# db secret name from cnpg

## Requirement

Live apply failed: the orchestrator Deployments reference secret agent-orchestrator-db-app (values/agent-orchestrator/common.yaml database.existingSecret), but the cnpg/cluster chart names the cluster agent-orchestrator-db-cluster, so CNPG creates agent-orchestrator-db-cluster-app; pods failed with 'secret "agent-orchestrator-db-app" not found' and the release rolled back. Point every reference to the real secret name, and replace the hardcoded-name assertion with a test that renders the agent-orchestrator-db release (helmfile template) and derives the app secret name from the rendered CNPG Cluster's metadata.name + '-app', then asserts the orchestrator release references exactly that name. Update the smoke script and README if they name the secret.

## Acceptance conditions

- AC1: the orchestrator release references the secret derived from the rendered CNPG Cluster name [evidence: test:tests/test_orchestrator_release.py::test_db_secret_matches_rendered_cnpg_cluster]
- AC2: no file references agent-orchestrator-db-app [evidence: command:! git grep -n 'agent-orchestrator-db-app' -- ':!docs']

## Files

- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`
- `scripts/smoke.sh`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The orchestrator release starts against the CNPG database on the live cluster.

What is true and observable when the task is done.

## Steps

- Red: write the render-derived test, see it fail on the wrong name.
- Fix the references; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
