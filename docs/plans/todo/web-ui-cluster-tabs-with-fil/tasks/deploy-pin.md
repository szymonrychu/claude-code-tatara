---
title: deploy pin
status: todo
repo: agents-helmfile
value: "the live agents namespace runs the tabs, files and terminal release with the UI origin allowed"
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && mise run lint"
depends_on: [kind-e2e-workspace, fe-terminal-panel, fe-agents-strip]
owns: []
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

# deploy pin

## Requirement

Pin agents-helmfile to this epic's merged agent-orchestrator and claude-code-wrapper builds and allow the UI origin (design D9; precedent `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`).

The values are the short shas (7 hex) of the agent-orchestrator main merge and the claude-code-wrapper main merge of this epic; the orchestrator supplies them by amending this requirement (`ticket.py amend`) after both PRs merge; until then this task reports `blocked` with `whoCanClear: orchestrator (merge the agent-orchestrator and claude-code-wrapper PRs)`.

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.<orch sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<orch sha7>`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:<wrapper sha7>`; `env.ORCH_ALLOWED_ORIGINS: https://agents.szymonrichert.pl`; the ingress timeouts stay 3600 (already set).
- `tests/test_orchestrator_release.py`: the chart version and image tag agree on the orchestrator sha; `agentImage` and `ORCH_AGENT_IMAGES` agree on the wrapper sha; `ORCH_ALLOWED_ORIGINS` lists the ingress host with https.
- Nothing else changes. `helmfile apply` and `mise run smoke` are run by the user after the epic.

## Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on the wrapper sha [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: ORCH_ALLOWED_ORIGINS allows exactly the https ingress host [evidence: test:tests/test_orchestrator_release.py::test_allowed_origins_is_ingress_host]
- AC4: the release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
