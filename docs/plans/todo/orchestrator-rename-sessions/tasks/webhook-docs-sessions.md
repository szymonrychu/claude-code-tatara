---
title: webhook docs sessions
status: todo
repo: agents-webhook
value: "agents-webhook's docs and chart say session and agents-orchestrator, guarded"
files: [README.md, AGENTS.md, MEMORY.md, chart/agents-webhook/values.yaml, chart/agents-webhook/ci/lint-values.yaml, tests/test_nomenclature.py]
verify: "uv run pytest -q tests/test_nomenclature.py tests/test_readme_config.py tests/test_readme_api.py tests/test_chart_workloads.py tests/test_chart_network.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-worker-sessions]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook docs sessions

## Requirement

Finish the rename in agents-webhook's docs and chart and guard the whole repo (design D1, D2, D12). Paths are in code/agents-webhook.

- `README.md`, `AGENTS.md`: session for the unit, agents-orchestrator for the orchestrator (`WEBHOOK_ORCHESTRATOR_URL` is "the agents-orchestrator base URL").
- `chart/agents-webhook/values.yaml` comments (the agents-orchestrator the worker and api talk to) and `chart/agents-webhook/ci/lint-values.yaml` (`url: http://agents-orchestrator.agents.svc`).
- `MEMORY.md`: a dated 2026-10-25 line: run columns are session_id/session_slug (migration 0005), agents-common v0.3.0, no aliases.
- New `tests/test_nomenclature.py` (D12): every tracked file, allowlisting only the Kubernetes/CNPG/kind phrases and dated history, has no `/cluster/i` naming the unit and no `agent[-_]orchestrator`.

## Acceptance conditions

- AC1: no tracked file names the unit cluster or the project agent-orchestrator outside the allowlist and dated history [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC2: the README config docs stay pinned [evidence: command:uv run pytest -q tests/test_readme_config.py tests/test_readme_api.py]
- AC3: the chart lints and renders [evidence: command:uv run pytest -q tests/test_chart_workloads.py tests/test_chart_network.py && helm lint chart/agents-webhook -f chart/agents-webhook/ci/lint-values.yaml]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `README.md`
- `AGENTS.md`
- `MEMORY.md`
- `chart/agents-webhook/values.yaml`
- `chart/agents-webhook/ci/lint-values.yaml`
- `tests/test_nomenclature.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
