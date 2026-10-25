---
title: hibernate old orch db
status: in-progress
repo: agents-helmfile
value: the pre-rename database is kept as a reversible cold copy instead of being deleted
files: [values/agent-orchestrator-db/common.yaml, tests/test_db_release.py, MEMORY.md]
verify: "uv run pytest -q tests/test_db_release.py && mise run lint && mise run diff && mise run smoke"
depends_on: [deploy-cutover]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# hibernate old orch db

## Requirement

Hibernate the old orchestrator database instead of deleting it (design D6; gate Q3; constraint: prefer a design that never deletes live data). Paths are in code/agents-helmfile.

- `values/agent-orchestrator-db/common.yaml`: `cluster.annotations: {cnpg.io/hibernation: "on"}` and the scheduled backups removed (`backups.scheduledBackups: []`, existing S3 backups untouched); a comment: kept hibernated as the pre-rename copy, delete only on a user decision; remove the annotation to wake it.
- `tests/test_db_release.py` (test first): `test_old_db_hibernated` (the annotation is set and no scheduled backup is declared for the old cluster); the old release stays declared and installed.
- Apply (orchestrator): `mise run apply -- --selector name=agent-orchestrator-db`. Implementer: `kubectl -n agents get pods -l cnpg.io/cluster=agent-orchestrator-db-cluster` lists none, `kubectl -n agents get pvc agent-orchestrator-db-cluster-1 agent-orchestrator-db-cluster-1-wal` both Bound, `mise run diff` shows no drift, `mise run smoke` still exits 0.
- `MEMORY.md`: a dated line: old database hibernated (PVCs and S3 backups kept), how to wake it.

## Acceptance conditions

- AC1: the old cluster is declared hibernated with no scheduled backups [evidence: test:tests/test_db_release.py::test_old_db_hibernated]
- AC2: the old PVCs are still bound and no old database pod runs [evidence: judgement:the task notes quote the kubectl get pods and get pvc output]
- AC3: no drift and the smoke still passes [evidence: command:mise run diff && mise run smoke]
- AC4: MEMORY.md records the hibernation [evidence: command:grep -q 'hibernat' MEMORY.md]

## Files

- `values/agent-orchestrator-db/common.yaml`
- `tests/test_db_release.py`
- `MEMORY.md`

## Interfaces

- Old release `agent-orchestrator-db` values: `cluster.annotations`, `backups.scheduledBackups`.

## Expected outcome

The old CNPG cluster runs no pods, keeps its PVCs and S3 backups, and can be woken by removing one annotation.

## Steps

- Red: write `test_old_db_hibernated`; it fails.
- Green: the values change; the verify's pytest and lint pass; the orchestrator applies the selector; the implementer quotes pods and PVCs, then `mise run diff` and `mise run smoke`.

## Notes

- Deleting the old cluster is out of scope (design D6, Non-goals).
- Check with `helm show values cnpg/cluster --version 0.9.0` that `cluster.annotations` reaches the Cluster metadata; if not, end `blocked` with the chart's key list.
