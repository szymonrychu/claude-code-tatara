---
title: webhook docs sessions
status: done
repo: agents-webhook
value: "agents-webhook's docs and chart say session and agents-orchestrator, guarded"
files: [README.md, AGENTS.md, MEMORY.md, chart/agents-webhook/values.yaml, chart/agents-webhook/ci/lint-values.yaml, tests/test_nomenclature.py]
verify: "uv run pytest -q tests/test_nomenclature.py tests/test_readme_config.py tests/test_readme_api.py tests/test_chart_workloads.py tests/test_chart_network.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-worker-sessions]
model: opus
review: ""
verified_head: 8e579ba
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: 2
actual_minutes: 5
actual_tokens: 1099459
actual_roles: "impl 4, review 1"
actual_role_tokens: "impl 819730, review 279729"
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

- None new.

## Expected outcome

Every tracked agents-webhook file passes the guard; MEMORY.md records the rename.

## Steps

- Red: write `tests/test_nomenclature.py` over all tracked files; it fails on docs and chart.
- Green: rewrite README, AGENTS.md, chart comments and lint values, add the MEMORY.md line; the verify passes.

## Notes

- Allowlist only Kubernetes/CNPG phrases (`db-cluster`, `cluster-issuer`, `in-cluster`, `cluster node IPs`) and dated history, each with a comment.

- 2026-10-25 done
