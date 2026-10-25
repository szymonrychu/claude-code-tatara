---
title: common settings runtime
status: todo
repo: agents-common
value: "services share one settings base and one singleton worker runtime, so each runs exactly one dispatcher"
files: [src/agents_common/settings.py, src/agents_common/runtime.py, tests/test_settings_runtime.py]
verify: "uv run pytest tests/test_settings_runtime.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-db-helpers]
owns: [agents-common-settings-runtime]
uses: [agents-common-db]
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

# common settings runtime

## Requirement

Settings base and worker runtime of agents-common (design D1). Paths are in code/agents-common.

- `settings.py`: `BaseServiceSettings(BaseSettings)` with fields `database_url`, `http_host` (`0.0.0.0`), `http_port` (8000), `log_level` (`INFO`), `orchestrator_url`, `orchestrator_token` (+ `orchestrator_token_file`: the file's stripped content wins when set), `shutdown_grace_seconds` (20). A subclass sets its own `env_prefix` through `model_config` (agents-webhook uses `WEBHOOK_`). `CsvList` annotated type (comma-separated env to list, blanks dropped). `load_settings(cls)` returns the instance or raises `SettingsError` whose message names every bad variable with its env name (`WEBHOOK_DATABASE_URL: required`), modelled on `code/agent-orchestrator/src/agent_orchestrator/settings.py` L25, L81-82, L155-172. Secret values never appear in `repr` or the error (SecretStr).
- `runtime.py`: `advisory_singleton(pool, key: str, heartbeat_seconds=10)` async context manager that holds a session advisory lock on a dedicated connection, re-checks it on each heartbeat and raises `LostLock` when the connection drops (from `runtime/singleton.py:advisory_singleton` L90); `run_service(main, *, grace_seconds)` runs an async main with SIGTERM and SIGINT handling and a bounded graceful stop (from `runtime/run.py:run_service` L83).
- `tests/test_settings_runtime.py`: prefix handling, `_FILE` precedence, CsvList, every bad variable named in one SettingsError, no secret in repr; only one of two concurrent `advisory_singleton` holders enters, the second enters after the first exits; `run_service` stops main on SIGTERM within the grace period.

## Acceptance conditions

- AC1: a subclass reads its own env prefix, the _FILE secret wins, and every bad variable is named in one error without secret values [evidence: command:uv run pytest tests/test_settings_runtime.py -q -k settings]
- AC2: only one advisory_singleton holder runs at a time and the next takes over after release [evidence: command:uv run pytest tests/test_settings_runtime.py -q -k singleton]
- AC3: run_service stops on SIGTERM within the grace period [evidence: command:uv run pytest tests/test_settings_runtime.py -q -k run_service]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/settings.py`
- `src/agents_common/runtime.py`
- `tests/test_settings_runtime.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
