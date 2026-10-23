---
title: api allowlist pod gateways
status: done
repo: agents-helmfile
value: LAN users reach the UI while agent pods stay refused
files: [values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest tests/test_orchestrator_release.py -q -p no:cacheprovider && mise run lint"
depends_on: [db-secret-name-from-cnpg, orchestrator-release]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agents-helmfile-api-allowlist-pod-gateways/agents-helmfile
branch: agents-helmfile-api-allowlist-pod-gateways
verified_head: 02b3cc90b1113e4c5b9e1840b2d206e1676c8b1e
run: agents-helmfile
provides: []
acs_for_audit: [AC2]
process_gaps: []
---

# api allowlist pod gateways

## Requirement

Live finding after apply: the API's direct-peer allowlist returns 403 to LAN clients. ingress-nginx is hostNetwork, but on this flannel cluster its connection to the api pod arrives from the node's pod-network gateway address (10.244.N.0 via flannel.1 from another node, 10.244.N.1 via cni0 on the same node), not from a 192.168.1.x node IP (api access log: peer 10.244.0.0). Set ORCH_ALLOWED_CIDRS to each node's podCIDR .0/31: 10.244.0.0/31,10.244.1.0/31,10.244.2.0/31,10.244.3.0/31,10.244.4.0/31 (from kubectl get nodes .spec.podCIDR), which admits host-network traffic (the ingress) while agent pods (.2 and up) stay refused; the ingress whitelist/denylist keeps LAN-only. Values comment documents how the list is derived and that it must be updated when nodes change. Test pins the value shape (five /31s on .0 of 10.244.N.0/24).

## Acceptance conditions

- AC1: ORCH_ALLOWED_CIDRS lists each node pod-network gateway /31 and not the LAN /24 [evidence: test:tests/test_orchestrator_release.py::test_allowed_cidrs_are_node_pod_gateways]
- AC2: from a LAN host, GET https://agents.szymonrichert.pl/api/v1/meta returns 200 after apply [evidence: judgement]

## Files

- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The UI answers 200 from the LAN after apply.

What is true and observable when the task is done.

## Steps

- Red: live 403 from 192.168.1.106; write the value test, see it fail.
- Set the value; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Ruling

- 2026-10-23 accepted: gate-repeat on a parking-wording false positive: common.yaml:22 is the required note that the list tracks the node set; hand-verified on 02b3cc9: tests/test_orchestrator_release.py 9 passed, mise run lint exit 0 (the verifier's 2 ruff errors were on a stale base).

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
