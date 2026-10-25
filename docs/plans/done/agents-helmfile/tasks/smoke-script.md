---
title: smoke script
status: done
repo: agents-helmfile
value: A repeatable proof that the deployed UI answers and a fresh agent pod lists any-mcp.
files: [scripts/smoke.sh, mise.toml, tests/test_smoke_script.py]
verify: "uv run pytest tests/test_smoke_script.py -q && mise run lint"
depends_on: [orchestrator-release, mise-tasks]
model: ""
review: ""
verified_head: 6b8fa017763c2ea130a9a77556e7e14e88cdfb7e
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 7
actual_tokens: 854683
actual_roles: "impl 5, review 2"
actual_role_tokens: "impl 603822, review 250861"
---

# smoke script

## Requirement

Add `scripts/smoke.sh` and the mise task `smoke` (`bash scripts/smoke.sh`) that proves a deployed orchestrator works end to end. bash, `set -euo pipefail`, shellcheck clean, no secret printed; parameters by env with defaults: `HOST=agents.szymonrichert.pl`, `NAMESPACE=agents`, `SMOKE_TIMEOUT_S=600`.

1. UI: `curl -fsS --max-time 20 https://$HOST/` from the LAN returns HTTP 200 and an HTML body; the API health or `openapi.json` path named by the agent-orchestrator API contract also returns 200.
2. Create a 1-replica cluster through the public API (`POST https://$HOST/api/v1/clusters` with the cluster spec of the API contract: name `smoke-<epoch>`, replicas 1, no special prompt); the body is built with `jq -n`.
3. Poll until the cluster's agent pod exists and is Ready (`kubectl -n $NAMESPACE wait --for=condition=Ready pod -l <cluster label> --timeout=...`), bounded by SMOKE_TIMEOUT_S; on timeout fail with the pod events.
4. `kubectl -n $NAMESPACE exec <pod> -- claude mcp list` output must contain `any-mcp`; otherwise fail printing the mcp list only.
5. Always, on exit (trap): discard the cluster through the API (`DELETE /api/v1/clusters/<id>`, which also removes its PVC) so the smoke leaves nothing behind; an unreachable API on cleanup prints the cluster name to delete manually.

`tests/test_smoke_script.py` (no cluster needed): shellcheck clean; the source has `set -euo pipefail`, a `trap` that issues the DELETE, the `claude mcp list` and `any-mcp` check and `--max-time` on every curl; the script runs against a local fake HTTP server and a fake `kubectl` on PATH (a test double in tmp_path) to prove the happy path exits 0, a missing `any-mcp` in the list exits non-zero, and the cleanup DELETE is sent in both cases.

## Acceptance conditions

- AC1: the happy path against a fake API and fake kubectl exits 0 and deletes the cluster [evidence: command:uv run pytest tests/test_smoke_script.py -q -k happy_path_exits_zero_and_cleans_up]
- AC2: a missing any-mcp in claude mcp list fails the smoke and still cleans up [evidence: command:uv run pytest tests/test_smoke_script.py -q -k missing_any_mcp_fails_and_cleans_up]
- AC3: every curl is bounded and the script has the strict-mode header and the cleanup trap [evidence: command:uv run pytest tests/test_smoke_script.py -q -k script_is_strict_bounded_and_traps]
- AC4: the script is shellcheck clean [evidence: command:shellcheck --severity=error scripts/smoke.sh]
- AC5: mise exposes a smoke task [evidence: command:mise tasks ls | grep -q '^smoke']

## Files

- `scripts/smoke.sh`
- `mise.toml`
- `tests/test_smoke_script.py`

## Interfaces

none

## Expected outcome

`mise run smoke` runs the end-to-end check; its offline tests pass with a fake API and fake kubectl.

## Steps

- Write tests/test_smoke_script.py with the fake server and fake kubectl; run it; expect failures (script missing).
- Write scripts/smoke.sh and the `smoke` mise task.
- Rerun the test, `shellcheck --severity=error scripts/smoke.sh` and `mise run lint`; expect `passed`.

## Notes

The real run happens after the orchestrator applies the namespace; this task only delivers the script and its offline tests. API paths and the cluster label come from the agent-orchestrator API contract (README of code/agent-orchestrator, or its openapi.json).

- 2026-10-23 run agents-helmfile: dependency-failed on orchestrator-release
