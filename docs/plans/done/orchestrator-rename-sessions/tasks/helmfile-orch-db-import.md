---
title: helmfile orch db import
status: done
repo: agents-helmfile
value: "the renamed database is declared as a copy of the live one, with the old one untouched"
files: [helmfile.yaml.gotmpl, values/agents-orchestrator-db/common.yaml, values/agents-orchestrator-db/default.secrets.yaml, tests/test_db_release.py]
verify: "uv run pytest -q tests/test_db_release.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: c1f72b5
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 2
actual_tokens: 530612
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 376514, review 154098"
---

# helmfile orch db import

## Requirement

Declare the new orchestrator database release, imported from the old one (design D1, D5; gate Q2; contract `agents-orchestrator-db-release`). Paths are in code/agents-helmfile. The old release `agent-orchestrator-db` and its values stay exactly as they are.

- `helmfile.yaml.gotmpl`: release `agents-orchestrator-db` (chart `cnpg/cluster` 0.9.0, namespace `agents`, `force: false`, timeout 600, labels `purpose: agents`, `application: agents-orchestrator`, the default template).
- `values/agents-orchestrator-db/common.yaml`: same shape as the old db values (postgresql 16, 1 instance, storage 5Gi and WAL 2Gi on rook-ceph, resources, monitoring off) plus `mode: recovery`, `recovery.method: import`, `recovery.database: agents_orchestrator`, `recovery.owner: agents_orchestrator`, `recovery.import.type: microservice`, `recovery.import.databases: [agent_orchestrator]`, `recovery.import.source` host `agent-orchestrator-db-cluster-rw`, port 5432, username `agent_orchestrator`, database `agent_orchestrator`, `sslMode: verify-full`, `passwordSecret` name `agent-orchestrator-db-cluster-app` key `password` (create false), `sslRootCertSecret` name `agent-orchestrator-db-cluster-ca` key `ca.crt`; backups enabled with S3 path `/agents-orchestrator-db/` (same bucket, region, 30d retention, daily 03:00 scheduled backup, `backupOwnerReference: self`). The builder checks every key against `helm show values cnpg/cluster --version 0.9.0` and `helmfile -l name=agents-orchestrator-db template`, and names any key that differs from this list in the task notes.
- `values/agents-orchestrator-db/default.secrets.yaml`: the S3 backup credentials, encrypted with the repo's SOPS rules through the workbench-secrets secret helper skill (never decrypted to the transcript, never committed in plain text); the values are the old db release's backup keys.
- `tests/test_db_release.py` (test first): tests for `agents-orchestrator-db` (`test_new_release_chart_and_labels`, `test_import_from_old_cluster`, `test_new_backups_own_path`, `test_new_db_secrets_encrypted`) next to the unchanged tests of the old release; the hook tests stay.

## Acceptance conditions

- AC1: the new release imports database agent_orchestrator from the old cluster into agents_orchestrator over verified TLS [evidence: test:tests/test_db_release.py::test_import_from_old_cluster]
- AC2: the new database backs up to its own S3 path [evidence: test:tests/test_db_release.py::test_new_backups_own_path]
- AC3: the new secrets file is encrypted and the old release is unchanged [evidence: command:uv run pytest -q tests/test_db_release.py]
- AC4: the release renders with the cnpg chart [evidence: judgement:the task notes quote helmfile -l name=agents-orchestrator-db template showing spec.bootstrap.initdb.import and externalClusters]
- AC5: lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator-db/common.yaml`
- `values/agents-orchestrator-db/default.secrets.yaml`
- `tests/test_db_release.py`

## Interfaces

- Release `agents-orchestrator-db`; CNPG Cluster `agents-orchestrator-db-cluster`; its app Secret `agents-orchestrator-db-cluster-app` (key `uri`) is what helmfile-orch-release-rename wires (contract `agents-orchestrator-db-release`).

## Expected outcome

The new database release is declared as an import of the old one; nothing about the old release changes; nothing is applied here.

## Steps

- Red: write the four new tests in `tests/test_db_release.py`; `uv run pytest -q tests/test_db_release.py` fails.
- Green: add the release, the values and the encrypted secrets file; run `helmfile -f helmfile.yaml.gotmpl -l name=agents-orchestrator-db template` and quote the bootstrap and externalClusters part; the verify passes.

## Notes

- Never apply: deploy-cutover runs the import after the old app is uninstalled (design D7).
- Encrypted files go through the workbench-secrets secret helper skill, never a raw decrypt to the transcript.

- 2026-10-25 done
