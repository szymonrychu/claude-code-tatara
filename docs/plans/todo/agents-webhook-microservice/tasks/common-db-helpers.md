---
title: common db helpers
status: todo
repo: agents-common
value: "both trigger services get one tested pool, migrator, guarded-transition and test-DB layer instead of copies"
files: [src/agents_common/db/__init__.py, src/agents_common/db/pool.py, src/agents_common/db/migrate.py, src/agents_common/db/queue.py, src/agents_common/testing.py, tests/conftest.py, tests/test_db.py, pyproject.toml]
verify: "uv run pytest tests/test_db.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-scaffold]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common db helpers

## Requirement

The database layer of agents-common (design D1), copied from agent-orchestrator's proven code and generalised. Paths are in code/agents-common.

- `db/pool.py`: `open_pool(url, min_size=1, max_size=10) -> AsyncConnectionPool`, `notify(conn, channel, payload="")`, `listen(url, channel)` async iterator that reconnects after a dropped connection (from `code/agent-orchestrator/src/agent_orchestrator/db/pool.py`).
- `db/migrate.py`: `run_migrations(url, package: str) -> list[str]` applies forward-only `NNNN_*.sql` files found in `<package>/migrations/` in order, records them in a `schema_migrations` table, under a Postgres advisory lock keyed on the package name, and returns the applied names; an edited applied file raises `MigrationError` (checksum) (from `db/migrate.py:run_migrations`).
- `db/queue.py`: `transition(conn, table, row_id, frm, to, **fields) -> bool` runs `UPDATE <table> SET status=%s, ... WHERE id=%s AND status=%s` and returns whether one row changed (from `db/queue.py:_transition`); `claim(conn, sql, params)` helper that runs a caller-supplied `SELECT ... FOR UPDATE SKIP LOCKED` inside the caller's transaction. Table and column names are validated identifiers (`^[a-z_][a-z0-9_]*$`), never interpolated user input.
- `db/__init__.py` re-exports the above.
- `testing.py`: a pytest plugin (`pytest11` entry point in pyproject) with fixtures `pg_url` (one testcontainers `postgres:18-alpine` per session) and `migrated_db(package)` factory that migrates a template database once and clones it per test (from `code/agent-orchestrator/tests/conftest.py` L27-56).
- `tests/test_db.py` with a throwaway migrations package under `tests/`: migrations apply once and in order under concurrency (two concurrent `run_migrations` calls apply each file once); an edited applied file raises; `transition` changes a row only from the expected status and returns False otherwise; two concurrent claims with SKIP LOCKED never return the same row; `listen` receives a `notify`.

## Acceptance conditions

- AC1: migrations are forward-only, ordered, applied once under concurrency, and an edited applied file is refused [evidence: command:uv run pytest tests/test_db.py -q -k migrat]
- AC2: transition changes a row only from the expected status [evidence: command:uv run pytest tests/test_db.py -q -k transition]
- AC3: concurrent SKIP LOCKED claims never return the same row [evidence: command:uv run pytest tests/test_db.py -q -k claim]
- AC4: notify reaches listen [evidence: command:uv run pytest tests/test_db.py -q -k listen]
- AC5: the testing plugin is registered as a pytest11 entry point [evidence: command:grep -q "pytest11" pyproject.toml]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/db/__init__.py`
- `src/agents_common/db/pool.py`
- `src/agents_common/db/migrate.py`
- `src/agents_common/db/queue.py`
- `src/agents_common/testing.py`
- `tests/conftest.py`
- `tests/test_db.py`
- `pyproject.toml`

## Interfaces

- Owns part `agents-common-db`: `agents_common.db.{open_pool, notify, listen, run_migrations, MigrationError, transition, claim}` and the pytest plugin `agents_common.testing` (`pg_url`, `migrated_db`).

## Expected outcome

Any service can migrate its own `migrations/` package, change queue rows only through guarded updates and test against a migrated template DB.

## Steps

- Red: write `tests/test_db.py`; run `uv run pytest tests/test_db.py -q`: import errors.
- Green: port the modules from agent-orchestrator, generalise table and package names; tests pass.
- Run the verify command.

## Notes

- Sources: `code/agent-orchestrator/src/agent_orchestrator/db/{pool,migrate,queue}.py`, `tests/conftest.py`. Keep their behaviour; do not add an ORM (do-not-build).
- Docker is needed for testcontainers; the 2026-10-25 local baseline had Postgres readiness failures, CI is the fallback.
