---
title: be review fixes
status: done
repo: agent-orchestrator
value: the api refuses oversized WebSocket frames before buffering them
files: [src/agent_orchestrator/cli.py, tests/test_cli.py, src/agent_orchestrator/db/agents.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_cli.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [fake-wrapper-workdir-regress, kind-e2e-workspace]
owns: []
uses: []
model: sonnet
estimate: 5
estimate_by: formula
actual: 1
actual_roles: "impl 1, verify 1, land 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-be-review-fixes/agent-orchestrator
branch: web-ui-cluster-tabs-with-fil-be-review-fixes
verified_head: 96a6aa1d10d29c69eacfa805f6f2555f5d279cba
run: web-ui-cluster-tabs-with-fil
provides: []
acs_for_audit: []
process_gaps: []
---

# be review fixes

## Requirement

Close the epic and security review findings on the backend (2026-10-24).

1. Frame cap at the server: build_uvicorn_config in src/agent_orchestrator/cli.py passes `ws_max_size=65536` (the wrapper's terminal frame cap; the UI already splits input into 64 KiB frames) so a client cannot make the api buffer 16 MiB frames before the relay forwards them.
2. Stale comment: src/agent_orchestrator/db/agents.py module docstring no longer says "the ribbon shows"; it names the cluster tabs and agents strip.

## Acceptance conditions

- AC1: build_uvicorn_config sets ws_max_size to 65536 [evidence: test:tests/test_cli.py::test_uvicorn_config_caps_websocket_frames]
- AC2: no source comment refers to the retired ribbon [evidence: command:! grep -rn "ribbon shows" src/agent_orchestrator]

## Files

- `src/agent_orchestrator/cli.py`
- `tests/test_cli.py`
- `src/agent_orchestrator/db/agents.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

uvicorn refuses WebSocket frames above 64 KiB; no comment names the retired ribbon.

## Steps

- Write the AC tests and run the verify command: they fail.
- Implement the requirement.
- Run the verify command: all pass.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
