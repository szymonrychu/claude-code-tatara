---
title: migration 0003 hive
status: done
repo: agent-orchestrator
value: "leadership, locks and pod identity have tables with one writer each"
files: [src/agent_orchestrator/db/migrations/0003_hive.sql, README.md, tests/test_migrations.py]
verify: "uv run pytest tests/test_migrations.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: ""
review: ""
verified_head: 05280b3639caae0730efa9f576e7db19eaa2db98
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: 662742
actual_roles: "impl 4, review 3"
actual_role_tokens: "impl 458939, review 203803"
---

# migration 0003 hive

## Requirement

Foundation part F5. `src/agent_orchestrator/db/migrations/0003_hive.sql`, forward-only, statements idempotent like `0002_presets.sql`:

- `leadership_requests` (queue): `id bigserial pk`, `cluster_id uuid not null references clusters on delete cascade`, `kind text check (kind in ('handover','user'))`, `from_agent_id` and `to_agent_id` nullable references agents, `reason text not null default ''`, `epoch int null`, `status text not null default 'queued' check (status in ('queued','applied','rejected'))`, `reject_reason text null`, `created_at timestamptz not null default now()`, `decided_at timestamptz null`; partial index `(cluster_id, id) where status = 'queued'`. Writers: the api inserts; the dispatcher decides rows only through status-guarded updates (`where status = 'queued'`).
- `cluster_leaders`: `cluster_id uuid pk references clusters on delete cascade`, `agent_id` references agents, `epoch int not null`, `since timestamptz not null`, `reason text not null`, `unready_since timestamptz null`, `feed_cursor bigint not null default 0`, `state_hash text null`, `state_pushed_at timestamptz null`. Writer: the dispatcher only.
- `file_locks`: `cluster_id` references clusters on delete cascade, `path text`, `agent_id` references agents on delete cascade, `claimed_at timestamptz not null default now()`, primary key `(cluster_id, path)`. Writer: the api only.
- `agents.pod_ip text null` (writer: the reconciler, like the rest of `agents`).
- README Architecture writers table (`### Single-writer interpretation`) lists the three tables and the column with their writer (`tests/test_readme_api.py` enforces). Migrations 0004 and later belong to cluster-scaling and agent-init-scripts.
- Interrogate item 3(c): the migration adds no feed history: `cluster_leaders.feed_cursor` keeps `default 0` in the table and the leader-row insert (hive-state-push-loop, `db/leadership.py`) sets it from `coalesce(max(events.id), 0)` of the cluster, so history is never pushed as current activity; the migration backfills nothing into `cluster_leaders`.
- Interrogate item 7: the migration backfills stored cluster specs without `max_replicas` (`update clusters set spec = jsonb_set(spec, '{max_replicas}', spec->'replicas') where spec ? 'replicas' and not spec ? 'max_replicas'`), idempotent, so later in-place replicas edits never change the cap.

## Acceptance conditions

- AC1: after migrate the three tables, their columns and agents.pod_ip exist [evidence: test:tests/test_migrations.py::test_0003_hive_schema]
- AC2: running the migrations twice is a no-op [evidence: test:tests/test_migrations.py::test_0003_idempotent]
- AC3: the check constraints reject an unknown kind or status [evidence: test:tests/test_migrations.py::test_0003_constraints]
- AC4: README lists every new table with its single writer [evidence: command:uv run pytest tests/test_readme_api.py -q]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]
- AC6: a stored spec without max_replicas gets max_replicas equal to replicas after migrate and a rerun changes nothing [evidence: test:tests/test_migrations.py::test_0003_backfills_max_replicas]
- AC7: the migration adds no feed history: cluster_leaders.feed_cursor defaults to 0 and the leader-row insert sets it from max(events.id) [evidence: test:tests/test_migrations.py::test_0003_feed_cursor_default]

## Files

- `src/agent_orchestrator/db/migrations/0003_hive.sql`
- `README.md`
- `tests/test_migrations.py`

## Interfaces

- Owns part `orch-hive-tables` (cross-epic contract): `leadership_requests`, `cluster_leaders`, `file_locks`, `agents.pod_ip` in `db/migrations/0003_hive.sql`.

## Expected outcome

`orch migrate` creates the hive tables; README names their writers.

## Steps

- Red: add the three tests to `tests/test_migrations.py`; run `uv run pytest tests/test_migrations.py -q`: fails.
- Green: write the migration and the README rows; run the verify command: passes.

## Notes

- Runner `db/migrate.py:15-48` (one transaction per file, advisory lock). Use `create table if not exists`, `add column if not exists`.

- 2026-10-24 amended: interrogate verdict 2026-10-24 item 3
