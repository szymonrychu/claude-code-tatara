---
title: webhook template memory cap
status: todo
repo: agents-webhook
value: a hostile prompt template cannot OOM the webhook pods
files: [src/agents_webhook/prompt.py, src/agents_webhook/settings.py, chart/agents-webhook/values.yaml, chart/agents-webhook/templates/_config.tpl, tests/test_prompt.py, tests/test_chart_workloads.py, README.md]
verify: "uv run pytest tests/test_prompt.py tests/test_chart_workloads.py -o addopts= -q && uv run ruff check ."
depends_on: [webhook-api-source-allowlist]
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 9
expected_tokens: 538938
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook template memory cap

## Requirement

Epic security review 2026-10-25: in agents-webhook prompt.py the sandbox bounds only `*` and `**`. Filters such as `"x"|center(10**9)`, `|indent(10**9)` and `|wordwrap(10**9)` still allocate unbounded memory in the forkserver render child. The 2 s timeout does not cap RAM, so a template preview by an SSO user, or a stored prompt_template rendered by the worker, can OOM the api or worker pod.

Cap the render child's address space with `resource.setrlimit(RLIMIT_AS, ...)` inside the child before rendering. Expose the limit as a setting (`WEBHOOK_TEMPLATE_MEMORY_MB`, default 256) and a chart value. A child that hits the limit (MemoryError or abnormal exit) must yield the existing `template_error` reason or preview error, never crash the parent.

Also give the chart non-empty default `resources` (requests and memory limits) for api, ingest and worker, sized from the live pods' usage (read-only `kubectl top pod -n agents`), so a runaway render cannot take the node. Document both.

## Acceptance conditions

- AC1: a template that allocates past the cap yields template_error and the parent survives [evidence: test:tests/test_prompt.py::test_render_memory_cap_yields_template_error]
- AC2: the chart sets default memory limits for api, ingest and worker and renders WEBHOOK_TEMPLATE_MEMORY_MB [evidence: test:tests/test_chart_workloads.py::test_default_resources_and_template_memory]
- AC3: the suite and lint pass [evidence: command:mise run test && mise run lint]

## Files

- `src/agents_webhook/prompt.py`
- `src/agents_webhook/settings.py`
- `chart/agents-webhook/values.yaml`
- `chart/agents-webhook/templates/_config.tpl`
- `tests/test_prompt.py`
- `tests/test_chart_workloads.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
