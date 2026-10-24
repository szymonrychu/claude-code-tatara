---
title: deploy pin
status: done
repo: agents-helmfile
value: "the live agents namespace runs the tabs, files and terminal release with the UI origin allowed"
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "mise x -- uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k 'not release_chart_version_and_needs and not db_secret_matches_rendered_cnpg_cluster' && uv run ruff check . && uv run ruff format --check ."
depends_on: [kind-e2e-workspace, fe-terminal-panel, fe-agents-strip]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: 4
actual_roles: "impl 1, verify 1, review 1, fix 1, false-finding 1"
review: ""
worktree: /home/user/claude-code-tatara/.claude/worktrees/web-ui-cluster-tabs-with-fil-deploy-pin/agents-helmfile
branch: "current worktree branch (head feec968)"
verified_head: feec968aa0c2574aebb25c3ca63e8ae0d1fb973a
run: web-ui-cluster-tabs-with-fil
provides: []
acs_for_audit: []
process_gaps: []
---

# deploy pin

## Requirement

Pin agents-helmfile to this epic's merged agent-orchestrator and claude-code-wrapper builds and allow the UI origin (design D9; precedent `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`).

The values: agent-orchestrator main merge `f1baa5b` (szymonrychu/agent-orchestrator#4, full `f1baa5ba4abbf968aff4694f6bbd7bae92eaf7a4`) and claude-code-wrapper main merge `1ced775` (szymonrychu/claude-code-wrapper#2).

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.f1baa5b`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `f1baa5b`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:1ced775`; `env.ORCH_ALLOWED_ORIGINS: https://agents.szymonrichert.pl`; the ingress timeouts stay 3600 (already set).
- `tests/test_orchestrator_release.py`: the chart version and image tag agree on the orchestrator sha; `agentImage` and `ORCH_AGENT_IMAGES` agree on the wrapper sha; `ORCH_ALLOWED_ORIGINS` lists the ingress host with https.
- Nothing else changes. `helmfile apply` and `mise run smoke` are run by the user after the epic.

- The old `test_orchestrator_pin_is_d5a7738` is replaced by the sha-agreement tests. `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts from harbor.szymonrichert.pl and cloudnative-pg.github.io, which this container's network policy blocks; they are deselected in this task's verify and run in CI and locally.

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

## Ruling

- 2026-10-24 accepted: AC4 failures are the two chart-pull tests blocked by this container's network policy (harbor, cloudnative-pg); diff is exactly the pin; PR CI runs the full suite

## Notes

- Check the chart and images exist before pinning when credentials allow (`helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version 0.1.0-main.<sha7>`); the precedent run blocked on a transient Harbor 403 in chart publish.
- Apply and smoke are not this task's verify: no cluster access in this container, and the user runs them.
- Builder check ruling 10: Accepted that only configured origins work; the orchestrator README and chart README document ORCH_ALLOWED_ORIGINS with http://localhost:5173 as the dev example; the helmfile sets only the ingress origin.

- 2026-10-24 run web-ui-cluster-tabs-with-fil: dependency-failed on kind-e2e-workspace

- 2026-10-24 amended: orchestrator PR #4 merged as f1baa5b; wrapper 1ced775
