---
title: agent port listener
status: todo
repo: agent-orchestrator
value: agent pods get their own orchestrator port while the public API stays closed to them
files: [src/agent_orchestrator/cli.py, src/agent_orchestrator/api/allowlist.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/settings.py, tests/test_agent_port.py, README.md]
verify: "uv run pytest tests/test_agent_port.py tests/test_cli.py tests/test_entrypoints.py tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [orch-agent-port]
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

# agent port listener

## Requirement

Foundation part F4, listener (D1). `orch api` listens on two sockets from one uvicorn server, `Server.serve(sockets=[main, agent])` (uvicorn 0.54 creates one asyncio server per socket for the same app): the existing `ORCH_HTTP_PORT` and new `ORCH_AGENT_PORT`.

- Settings: `agent_port: int = 8001` (`ORCH_AGENT_PORT`) and `agent_api_url: str | None = None` (`ORCH_AGENT_API_URL`, the URL agent pods use, set by the chart to the agents Service). Both in the README settings table.
- A port gate middleware branches on `scope["server"][1]`: on the agent port only `/agent/v1/*`, `/healthz` and `/readyz` are served and the `SourceAllowlist` is skipped there (auth is the cluster token plus the pod IP, task agent-api-me); any other path on the agent port is 404 `not_found`; `/agent/v1/*` on the main port is 404 `not_found`. The gate is tested with a stub `/agent/v1` route in the test app.
- Main-port behaviour is unchanged: the allowlist still refuses non-allowed sources, and e2e `test_in_cluster_pod_refused_by_allowlist` stays true verbatim.
- README `## Security`: "agent pods reach `/agent/v1` on the agents Service only, with the cluster token and from their own pod IP."

## Acceptance conditions

- AC1: orch api binds both the HTTP port and the agent port with one server [evidence: test:tests/test_agent_port.py::test_two_sockets_bound]
- AC2: on the agent port only /agent/v1, /healthz and /readyz are served, everything else is 404, and the source allowlist is skipped there [evidence: test:tests/test_agent_port.py::test_agent_port_serves_only_agent_paths]
- AC3: /agent/v1 on the main port is 404 and the main port still enforces the allowlist [evidence: test:tests/test_agent_port.py::test_main_port_unchanged]
- AC4: settings agent_port defaults to 8001 and agent_api_url to None, both read from ORCH_ env [evidence: test:tests/test_agent_port.py::test_agent_settings]
- AC5: README Security states the agent path rule [evidence: command:grep -q "/agent/v1" README.md]
- AC6: existing cli and entrypoint tests and lint pass [evidence: command:uv run pytest tests/test_cli.py tests/test_entrypoints.py tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/cli.py`
- `src/agent_orchestrator/api/allowlist.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/settings.py`
- `tests/test_agent_port.py`
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
