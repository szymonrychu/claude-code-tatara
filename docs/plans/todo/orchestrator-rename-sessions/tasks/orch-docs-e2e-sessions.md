---
title: orch docs e2e sessions
status: todo
repo: agents-orchestrator
value: "the orchestrator's docs and e2e say session and agents-orchestrator, and a guard keeps it so"
files: [README.md, AGENTS.md, CLAUDE.md, MEMORY.md, chart/agents-orchestrator/, examples/, e2e/, scripts/e2e.sh, tests/]
verify: "uv run pytest -q tests/test_nomenclature.py tests/test_project_name.py tests/test_readme_api.py && mise run lint:chart && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-agent-api-sessions]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch docs e2e sessions

## Requirement

Finish the rename in the orchestrator's docs, chart comments and e2e, and guard the whole repo (design D1, D2, D10, D12; user decision: cluster is renamed session throughout (API, UI, docs)). Paths are in code/agents-orchestrator.

- `README.md` (all prose), `AGENTS.md`, `CLAUDE.md`, `chart/agents-orchestrator/README.md`, `chart/agents-orchestrator/values.yaml` and template comments ("per-session tokens", "session Secrets"), `examples/bench.yaml`, `e2e/agent-test.config.yaml`, `scripts/e2e.sh` messages, `tests/e2e/`: session for the unit, agents-orchestrator for the project; Kubernetes, CNPG and kind clusters keep their word.
- `MEMORY.md`: dated 2026-10-25 lines: renamed to agents-orchestrator and cluster to session (D1, D2), wrapper session id is `wrapper_session_id` (D3), no aliases; earlier dated lines keep their history.
- `tests/test_nomenclature.py` and `tests/test_project_name.py`: guard every tracked file of the repo (`git ls-files`), allowlisting only the D12 Kubernetes/CNPG/kind phrases and the dated-history files (MEMORY.md, ROADMAP.md, CHANGELOG.md, docs/plans/).
- The kind e2e passes on the renamed chart, images, routes and labels: `mise run test:e2e`.

## Acceptance conditions

- AC1: no tracked file names the unit cluster or the project agent-orchestrator outside the allowlist and dated history [evidence: command:uv run pytest -q tests/test_nomenclature.py tests/test_project_name.py]
- AC2: MEMORY.md records the rename decisions [evidence: command:grep -q 'wrapper_session_id' MEMORY.md && grep -q 'agents-orchestrator' MEMORY.md]
- AC3: the kind e2e passes on the renamed chart, routes and labels [evidence: command:mise run test:e2e]
- AC4: README and openapi stay in sync and lint passes [evidence: command:uv run pytest -q tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check . && mise run lint:chart]

## Files

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `MEMORY.md`
- `chart/agents-orchestrator/`
- `examples/`
- `e2e/`
- `scripts/e2e.sh`
- `tests/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
