---
title: hive docs memory
status: todo
repo: agent-orchestrator
value: the hive rules and the reasons behind them are written down where the next builder looks
files: [README.md, MEMORY.md]
verify: "uv run pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [render-hive-gating, plugin-config-merge, leader-routing, hive-state-push-loop, file-locks-api, views-leader-stream]
owns: [orch-spec-runtime-mutable]
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

# hive docs memory

## Requirement

Docs for the rules this epic owns. README:
- `## API` Versioning: "`spec.replicas` and `spec.init_scripts` are the only spec fields that change in place (no generation bump, no pod roll); PATCH stays 405." (foundation D4; the writes land in cluster-scaling and agent-init-scripts.)
- `### Hive` overview: hive derived from `max_replicas > 1`, alone clusters, leader and epoch, leader-only routing, handover only plus the user override, hive_state and feed notes, advisory locks, tool gating fixed at render from cap and static.

MEMORY.md entries dated 2026-10-24, each with the why: agent-to-orchestrator path (second socket of `orch api`, per-cluster token, pod IP binding) and the alternatives rejected; tool visibility fixed at render from `max_replicas` and `static`; peer seeds from the cap; D4 amends the 2026-10-23 immutability entry; `api/agent.py` may import `tokens` (import pin widened); feed and hive_state pushes run in the dispatcher, not the ingester; `LEADER_GRACE_SECONDS` and `PUSH_INTERVAL_SECONDS` are module constants.
Doc edit: the TDD exception for a doc edit applies.

## Acceptance conditions

- AC1: README has the Hive section [evidence: doc-section:README.md#Hive]
- AC2: README Versioning names spec.replicas and spec.init_scripts as the only in-place fields [evidence: command:grep -q "spec.init_scripts" README.md && grep -q "PATCH stays 405" README.md]
- AC3: MEMORY.md has the dated entries for the agent path, tool gating, seeds and the immutability amendment [evidence: command:grep -q "2026-10-24" MEMORY.md && grep -qi "agent port" MEMORY.md && grep -qi "seed" MEMORY.md]
- AC4: README contract tests pass [evidence: command:uv run pytest tests/test_readme_api.py -q]

## Files

- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
