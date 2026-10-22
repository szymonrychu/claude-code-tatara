---
title: entrypoints and singleton
status: todo
repo: agent-orchestrator
value: "Makes the four services and migrate runnable as separate processes, with singletons that fail over and clean shutdown."
files: [src/agent_orchestrator/runtime/__init__.py, src/agent_orchestrator/runtime/singleton.py, src/agent_orchestrator/runtime/run.py, src/agent_orchestrator/cli.py, tests/test_entrypoints.py, README.md]
verify: "uv run pytest tests/test_entrypoints.py -q && mise run lint"
depends_on: [ingester, dispatcher-loop, check-jobs, api-events-and-streams]
owns: []
uses: [orch-cli, settings, kube-api, api-app]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# entrypoints and singleton

## Requirement

Entrypoints (D1, D20).

Commands registered with `cli.register`:
- `orch migrate`: runs migrations and exits 0.
- `orch api`: uvicorn `create_app` on `settings.http_host:http_port`.
- `orch dispatcher`: runs the dispatcher.
- `orch ingester`: runs the ingester inside `advisory_singleton(dsn, "ingester")`.
- `orch reconciler`: runs the reconciler inside `advisory_singleton(dsn, "reconciler")` with `LightkubeApi`.

`runtime/singleton.py`:
- `advisory_singleton(dsn, name)` holds a session-level `pg_advisory_lock` on a dedicated connection, blocking until it is acquired, so a second replica waits as a hot standby.
- If that connection drops, it sets the stop event and the process exits 3, letting Kubernetes restart it rather than run without the lock.

`runtime/run.py`:
- SIGTERM and SIGINT set a stop event; loops finish their iteration.
- Streams and the pool close within `settings.shutdown_grace_seconds`, and the exit code is 0.
- Logs are JSON lines on stdout at `settings.log_level`.

README.md gains `## Commands`: each command, what it runs, which settings it needs, and how many replicas it allows.

## Acceptance conditions

- AC1: orch migrate applies the schema and exits 0 [evidence: test:tests/test_entrypoints.py::test_migrate_command_applies_schema]
- AC2: a second singleton waits until the first releases the lock [evidence: test:tests/test_entrypoints.py::test_singleton_second_waits_until_first_releases]
- AC3: losing the lock connection stops the holder with exit 3 [evidence: test:tests/test_entrypoints.py::test_singleton_lost_connection_stops_holder]
- AC4: SIGTERM stops a running loop cleanly with exit 0 [evidence: test:tests/test_entrypoints.py::test_sigterm_stops_loop_cleanly]
- AC5: orch --help lists api, dispatcher, ingester, reconciler and migrate [evidence: test:tests/test_entrypoints.py::test_cli_registers_all_commands]
- AC6: orch api serves /healthz [evidence: test:tests/test_entrypoints.py::test_api_command_serves_healthz]
- AC7: README documents the commands [evidence: doc-section:README.md#Commands]

## Files

- `src/agent_orchestrator/runtime/__init__.py`
- `src/agent_orchestrator/runtime/singleton.py`
- `src/agent_orchestrator/runtime/run.py`
- `src/agent_orchestrator/cli.py`
- `tests/test_entrypoints.py`
- `README.md`

## Interfaces

- `agent_orchestrator.runtime.singleton:advisory_singleton(dsn, name)` (async context manager)
- `agent_orchestrator.runtime.run:run_service(coro_factory, settings) -> int`

## Expected outcome

`orch api|dispatcher|ingester|reconciler|migrate` run as the Deployments of the deploy epic.

## Steps

- Write tests/test_entrypoints.py with the six named tests; drive SIGTERM through a subprocess `uv run orch dispatcher` with ORCH_DATABASE_URL pointing at the test container; run it; expect failures.
- Implement runtime/ and register the commands in cli.py.
- Rerun `uv run pytest tests/test_entrypoints.py -q`; expect `6 passed`; run `mise run lint`.

## Notes

Advisory lock keys: a stable 64-bit hash of the name. The api process gets no Kubernetes client (D1). Contract agent-orchestrator-settings-env: the deploy epic's chart sets these commands and env.
