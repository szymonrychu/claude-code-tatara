---
title: db release
status: in-progress
repo: agents-helmfile
value: A backed-up Postgres for the orchestrator in namespace agents.
files: [helmfile.yaml.gotmpl, values/agent-orchestrator-db/common.yaml, tests/test_db_release.py]
verify: "uv run pytest tests/test_db_release.py -q && mise run lint"
depends_on: [secrets-bootstrap]
owns: []
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

# db release

## Requirement

Add release `agent-orchestrator-db` to `helmfile.yaml.gotmpl`: chart `cnpg/cluster` version 0.9.0, namespace `agents`, `force: false` (helm --force would delete and recreate the Cluster CR and is incompatible with Helm 4 server-side apply), timeout 600, labels `purpose: agents`, `application: agent-orchestrator`, `<<: *default`.

`values/agent-orchestrator-db/common.yaml`, sized like the infrastructure `helmfiles/ai/values/buzz-database/common.yaml`: `version.postgresql: "16"`, `cluster` with `enablePDB: false`, `instances: 1`, storage 5Gi on `rook-ceph`, walStorage enabled 2Gi on `rook-ceph`, resources (requests 100m/256Mi, limits 1000m/1Gi), `monitoring.enabled: false`, `initdb` database `agent_orchestrator` owner `agent_orchestrator` (CNPG generates the `agent-orchestrator-db-app` Secret with keys `uri`, `host`, `port`, `dbname`, `user`, `password`; the orchestrator release reads that Secret). Backups copied from the infrastructure helmfile's `helmfiles/media/values/jellystat-database/common.yaml` (the databases in the ai bucket have backups disabled; jellystat and home-assistant are the ones with `backups.enabled: true`): `backups.enabled: true`, `provider: s3`, `s3.region: eu-central-1`, `s3.bucket: database-backup-szymonrychu`, `s3.path: /agent-orchestrator-db/`, `retentionPolicy: "30d"`, `scheduledBackups` daily at `0 0 3 * * *` with `backupOwnerReference: self` and `method: barmanObjectStore`; accessKey and secretKey come from the encrypted file made by secrets-bootstrap.

`tests/test_db_release.py` asserts on `helmfile_build()` and `layered_values('agent-orchestrator-db')`: chart, version, namespace, `force: false`, the initdb names, storage classes, backups enabled with the path `/agent-orchestrator-db/` (never another application's path), and that the layered plain values contain no accessKey or secretKey.

## Acceptance conditions

- AC1: the release uses cnpg/cluster 0.9.0 in namespace agents with force false [evidence: command:uv run pytest tests/test_db_release.py -q -k release_chart_namespace_and_force]
- AC2: initdb creates database and owner agent_orchestrator [evidence: command:uv run pytest tests/test_db_release.py -q -k initdb_names]
- AC3: backups are enabled to the agent-orchestrator-db path with a daily schedule and 30d retention [evidence: command:uv run pytest tests/test_db_release.py -q -k backups_enabled_with_own_path]
- AC4: plain values carry no S3 credentials [evidence: command:uv run pytest tests/test_db_release.py -q -k no_credentials_in_plain_values]
- AC5: helmfile build still succeeds with the release [evidence: command:mise exec -- helmfile -f helmfile.yaml.gotmpl build >/dev/null]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator-db/common.yaml`
- `tests/test_db_release.py`

## Interfaces

Provides CNPG Secret `agent-orchestrator-db-app` (keys uri, host, port, dbname, user, password) to orchestrator-release.

## Expected outcome

`helmfile build` lists release agent-orchestrator-db with the CNPG values and backups to its own S3 path.

## Steps

- Write tests/test_db_release.py; run it; expect failures.
- Add the release to helmfile.yaml.gotmpl and write values/agent-orchestrator-db/common.yaml.
- Rerun the test, then `mise exec -- helmfile -f helmfile.yaml.gotmpl build`; expect `passed`.

## Notes

Template: ~/Documents/infrastructure/code/helmfile helmfiles/ai/values/buzz-database/common.yaml and helmfiles/media/values/jellystat-database/common.yaml. The app Secret name is CNPG's `<release>-app`.
