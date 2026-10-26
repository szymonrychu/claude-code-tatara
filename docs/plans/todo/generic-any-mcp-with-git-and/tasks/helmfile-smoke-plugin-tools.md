---
title: helmfile smoke plugin tools
status: todo
repo: agents-helmfile
value: smoke proves sessions get the orchestrator tools from the plugins repo and extra sources install
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint"
depends_on: [helmfile-deploy-pin]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile smoke plugin tools

## Requirement

Goal G6 (epic README), verbatim: "Deployed through agents-helmfile; agent sessions still get the orchestrator tools." Goal G4, verbatim: "... accepts a list of extra plugin sources per preset and session, installed in agent pods." Orchestrator design call, verbatim: "smoke proves a session lists orchestrator tools from the plugins repo." Design D11, verbatim: "Smoke proves, in the smoke session's pod, that the `any-mcp-tatara-orchestrator` distribution is installed, the rendered config's orchestrator entry names the plugins repo at the pinned ref, and `any-mcp --list-tools` lists `orchestrator_sessions_list`; and that a session created with `any_mcp_sources: ["git::https://github.com/szymonrychu/any-mcp//examples/petstore?ref=v0.5.0"]` lists `petstore_` tools (petstore is a packaged plugin that loads with an empty config). Live steps run by the orchestrator (Rollout)." Retro (matrix-read-receipts, agents-matrix-connector-depl): live proof is an orchestrator-run step, so this task writes and offline-tests the steps; the orchestrator runs `mise run smoke` after the apply (design Rollout R5).

Scope (agents-helmfile `scripts/smoke.sh`, in the style of its existing steps, same parameters):
- Plugin tools step, in the existing smoke session's pod after the any-mcp version check: `kubectl exec <pod> -c ccw -- /opt/any-mcp/bin/pip show any-mcp-tatara-orchestrator` succeeds; `/opt/any-mcp/etc/any-mcp.yaml` in the pod contains `any-mcp-tatara-plugins//orchestration/orchestrator?ref=<ORCH_ANY_MCP_PLUGINS_REF>` (read from the orchestrator values like `ORCH_ANY_MCP_REF`); `/opt/any-mcp/bin/any-mcp --config /opt/any-mcp/etc/any-mcp.yaml --list-tools` in the pod lists `orchestrator_sessions_list`.
- Extra source step: a session `smoke-src-<ts>` created with a raw spec (`replicas: 1`, `any_mcp_sources: ["git::https://github.com/szymonrychu/any-mcp//examples/petstore?ref=v<any-mcp version>"]`) gets a Ready pod whose `--list-tools` lists a tool starting with `petstore_`.
- The cleanup trap deletes `smoke-src-<ts>` on every exit.
- The header comment and `README.md` (`mise run smoke` paragraph) describe both steps; never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.
- `tests/test_smoke_script.py`: tests for both steps with the existing fake kubectl and curl harness.

## Acceptance conditions

- ac1: the plugin tools step passes when pip show finds any-mcp-tatara-orchestrator, the pod config names the plugins repo source at ORCH_ANY_MCP_PLUGINS_REF and list-tools lists orchestrator_sessions_list, and fails smoke naming the check when any of these does not hold [evidence: test:tests/test_smoke_script.py::test_orchestrator_plugin_from_plugins_repo]
- ac2: the extra source step creates its session with the petstore source at the pinned any-mcp tag, passes when that pod lists a petstore_ tool, and fails smoke naming the check otherwise [evidence: test:tests/test_smoke_script.py::test_extra_plugin_source_step]
- ac3: the trap deletes the extra source session on success and on a failure [evidence: test:tests/test_smoke_script.py::test_plugin_source_session_cleaned_up]
- ac4: the new steps never print the agent token or any other secret [evidence: test:tests/test_smoke_script.py::test_plugin_steps_print_no_token]
- ac5: the smoke script tests and the nomenclature and hygiene guards pass [evidence: command:uv run --frozen pytest -q tests/test_smoke_script.py tests/test_nomenclature.py tests/test_repo_hygiene.py]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
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
