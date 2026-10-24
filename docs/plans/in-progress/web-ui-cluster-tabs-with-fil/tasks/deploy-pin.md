---
title: deploy pin
status: in-progress
repo: agents-helmfile
value: "the live agents namespace runs the tabs, files and terminal release with the UI origin allowed"
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [kind-e2e-workspace, fe-terminal-panel, fe-agents-strip]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-deploy-pin/agents-helmfile
branch: web-ui-cluster-tabs-with-fil-deploy-pin
verified_head: ""
run: web-ui-cluster-tabs-with-fil
provides: []
acs_for_audit: []
process_gaps: []
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
- AC4: the release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

- Consumes the cross-epic contract `orch-allowed-origins` (`ORCH_ALLOWED_ORIGINS`) and the published chart `0.1.0-main.<sha7>` and images `agent-orchestrator:<sha7>`, `claude-code-wrapper:<sha7>`.

## Expected outcome

`helmfile diff` shows only the chart version, the two image pins and the new origin setting for agent-orchestrator.

## Steps

- Write or update the three tests in `tests/test_orchestrator_release.py` for the new values; run `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: fails.
- Change the pins and add the setting; run the verify command: passes.

## Notes

- Check the chart and images exist before pinning when credentials allow (`helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`); the precedent run blocked on a transient Harbor 403 in chart publish.
- Apply and smoke are not this task's verify: no cluster access in this container, and the user runs them.
- Builder check ruling 10: Accepted that only configured origins work; the orchestrator README and chart README document ORCH_ALLOWED_ORIGINS with http://localhost:5173 as the dev example; the helmfile sets only the ingress origin.

- 2026-10-24 run web-ui-cluster-tabs-with-fil: dependency-failed on kind-e2e-workspace
