---
title: entrypoints and singleton
status: done
repo: agent-orchestrator
value: "Makes the four services and migrate runnable as separate processes, with singletons that fail over and clean shutdown."
files: [src/agent_orchestrator/runtime/__init__.py, src/agent_orchestrator/runtime/singleton.py, src/agent_orchestrator/runtime/run.py, src/agent_orchestrator/cli.py, tests/test_entrypoints.py, README.md]
verify: "uv run pytest tests/test_entrypoints.py -q && mise run lint"
depends_on: [api-clusters-and-agents, api-events-and-streams, check-jobs, dispatcher-loop, ingester, reconciler-loop, scaffold-repo-and-cli, settings-model]
owns: []
uses: [orch-cli, settings, kube-api, api-app]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-entrypoints-and-singleton/agent-orchestrator
branch: agent-orchestrator-entrypoints-and-singleton
verified_head: fab4fae6cc277775265e4d5531d51d482ee56762
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# entrypoints and singleton

## Requirement

Entrypoints (D1, D20).

Commands registered with `cli.register`:
- `orch migrate`: runs migrations and exits 0.
- `orch api`: uvicorn `create_app` on `settings.http_host:http_port`, with `proxy_headers=False` and no forwarded-allow-ips so the direct peer is what the source allowlist sees (D22); the uvicorn config comes from `build_uvicorn_config(settings)`.
- `orch dispatcher`: runs the dispatcher.
- `orch ingester`: runs the ingester inside `advisory_singleton(dsn, "ingester")`.
- `orch reconciler`: runs the reconciler inside `advisory_singleton(dsn, "reconciler")` with `LightkubeApi`.

`runtime/singleton.py`:
- `advisory_singleton(dsn, name, *, heartbeat_seconds, tcp_user_timeout_seconds)` holds a session-level `pg_advisory_lock` on a dedicated connection, blocking until it is acquired, so a second replica waits as a hot standby (D20, D25).
- The lock connection is opened with libpq keepalives (`keepalives=1`, short `keepalives_idle`, `keepalives_interval`, `keepalives_count`) and `tcp_user_timeout = tcp_user_timeout_seconds * 1000`, so a half-open connection is detected by the kernel instead of hanging.
- A heartbeat runs every `settings.lock_heartbeat_seconds`: it checks on the lock connection that the advisory lock is still held by this backend. A failed, timed-out or negative heartbeat sets the stop event and the process exits 3, letting Kubernetes restart it rather than run without the lock. The same happens when the connection drops.

`runtime/run.py`:
- SIGTERM and SIGINT set a stop event; loops finish their iteration.
- Streams and the pool close within `settings.shutdown_grace_seconds`, and the exit code is 0.
- Logs are JSON lines on stdout at `settings.log_level`.

README.md gains `## Commands`: each command, what it runs, which settings it needs, and how many replicas it allows, plus the singleton failover behaviour (keepalives, heartbeat, exit 3).

## Acceptance conditions

- AC1: orch migrate applies the schema and exits 0 [evidence: test:tests/test_entrypoints.py::test_migrate_command_applies_schema]
- AC2: a second singleton waits until the first releases the lock [evidence: test:tests/test_entrypoints.py::test_singleton_second_waits_until_first_releases]
- AC3: losing the lock connection stops the holder with exit 3 [evidence: test:tests/test_entrypoints.py::test_singleton_lost_connection_stops_holder]
- AC4: SIGTERM stops a running loop cleanly with exit 0 [evidence: test:tests/test_entrypoints.py::test_sigterm_stops_loop_cleanly]
- AC5: orch --help lists api, dispatcher, ingester, reconciler and migrate [evidence: test:tests/test_entrypoints.py::test_cli_registers_all_commands]
- AC6: orch api serves /healthz [evidence: test:tests/test_entrypoints.py::test_api_command_serves_healthz]
- AC7: README documents the commands [evidence: doc-section:README.md#Commands]
- AC8: a lock holder whose connection silently stops (a TCP proxy that drops all traffic) exits 3 within tcp_user_timeout plus one heartbeat [evidence: test:tests/test_entrypoints.py::test_singleton_blackholed_connection_exits_3]
- AC9: the heartbeat detects a lock lost without a connection error (pg_terminate_backend of the holder is not required) and stops the holder [evidence: test:tests/test_entrypoints.py::test_singleton_heartbeat_detects_lost_lock]
- AC10: build_uvicorn_config disables proxy headers so X-Forwarded-For cannot spoof the peer [evidence: test:tests/test_entrypoints.py::test_api_uvicorn_config_ignores_proxy_headers]

## Files

- `src/agent_orchestrator/runtime/__init__.py`
- `src/agent_orchestrator/runtime/singleton.py`
- `src/agent_orchestrator/runtime/run.py`
- `src/agent_orchestrator/cli.py`
- `tests/test_entrypoints.py`
- `README.md`

## Interfaces

- `agent_orchestrator.runtime.singleton:advisory_singleton(dsn, name, *, heartbeat_seconds, tcp_user_timeout_seconds)` (async context manager)
- `agent_orchestrator.runtime.run:build_uvicorn_config(settings) -> uvicorn.Config`
- `agent_orchestrator.runtime.run:run_service(coro_factory, settings) -> int`

## Expected outcome

`orch api|dispatcher|ingester|reconciler|migrate` run as the Deployments of this repo's chart (helm-chart-deployments).

## Steps

- Write tests/test_entrypoints.py with the nine named tests; drive SIGTERM through a subprocess `uv run orch dispatcher` with ORCH_DATABASE_URL pointing at the test container; run it; expect failures.
- Implement runtime/ and register the commands in cli.py.
- Rerun `uv run pytest tests/test_entrypoints.py -q`; expect `9 passed`; run `mise run lint`.

## Notes

Advisory lock keys: a stable 64-bit hash of the name. The api process gets no Kubernetes client (D1). Contract agent-orchestrator-settings-env: this repo's chart sets these commands and env (consumed by agents-helmfile).

- 2026-10-23 run agent-orchestrator: dependency-failed on ingester, dispatcher-loop, check-jobs

- 2026-10-23 run agent-orchestrator: dependency-failed on check-jobs, dispatcher-loop, reconciler-loop

- 2026-10-23 run agent-orchestrator: dependency-failed on check-jobs, reconciler-loop
