---
title: ingress node denylist
status: todo
repo: agent-orchestrator
value: agent pods cannot reach the API through the ingress
files: [chart/agent-orchestrator/values.yaml, chart/agent-orchestrator/templates/ingress.yaml, tests/test_chart_rbac_ingress.py, README.md]
verify: "uv run pytest tests/test_chart_rbac_ingress.py -q && mise run lint && mise run lint:chart"
depends_on: [ambiguous-send-verifier, bench-cli, container-images-ci, discard-hook-and-export, entrypoints-and-singleton, helm-chart-ci-publish, helm-chart-config-postgres, helm-chart-deployments, helm-chart-rbac-and-ingress, helm-chart-scaffold, readme-api-and-openapi, reconciler-loop, scaffold-repo-and-cli, settings-model]
owns: []
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

# ingress node denylist

## Requirement

Panel finding (high, sonnet+opus): an agent pod can call the ingress hostname; flannel ipMasq SNATs pod-to-LAN traffic to the node IP, ingress-nginx (hostNetwork) admits it under whitelist-source-range 192.168.1.0/24 and proxies to the api from a node IP inside ORCH_ALLOWED_CIDRS, so the direct-peer allowlist (api/allowlist.py) cannot tell a pod from a LAN client. Add chart value ingress.denySourceRanges (list) rendered as nginx.ingress.kubernetes.io/denylist-source-range when non-empty (and ingress.allowSourceRanges rendered as whitelist-source-range), both empty by default (no homelab defaults). README Security section documents the boundary: legit traffic always arrives from node IPs at the api, so the ingress must deny the cluster node IPs (pods egress SNATed as node IPs) and allow the LAN; a process on a node itself is denied too.

## Acceptance conditions

- AC1: denySourceRanges renders the denylist annotation and allowSourceRanges the whitelist annotation; neither renders when empty [evidence: test:tests/test_chart_rbac_ingress.py::test_ingress_source_ranges_render]
- AC2: README Security documents the SNAT boundary and the node-IP denylist [evidence: doc-section:README.md#Security]

## Files

- `chart/agent-orchestrator/values.yaml`
- `chart/agent-orchestrator/templates/ingress.yaml`
- `tests/test_chart_rbac_ingress.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
