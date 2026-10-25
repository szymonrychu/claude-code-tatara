---
title: deploy pin scaling
status: in-progress
repo: agents-helmfile
value: the agents namespace runs cluster scaling
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [agent-scale-route, scale-tool-allow, agents-strip-leaving-mark, kind-e2e-scaling, smoke-scale-check]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/cluster-scaling-deploy-pin-scaling/agents-helmfile
branch: cluster-scaling-deploy-pin-scaling
verified_head: ""
run: ""
provides: []
---

# deploy pin scaling

## Requirement

Release and deploy this epic to the agents namespace (design D6; user S1, S2, S3, X2). The orchestrator release is the main build of this epic's merged agent-orchestrator commit: chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`); no any-mcp or wrapper release is needed (the scale tool ships in any-mcp v0.2.0 from hive F1, already pinned). In agents-helmfile: `helmfile.yaml.gotmpl` release `agent-orchestrator` chart version `0.1.0-main.<sha7>`, `values/agent-orchestrator/common.yaml` `image.tag` `<sha7>`, `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` asserts both carry the sha (offline, text read). The sha is filled with `ticket.py amend` once the orchestrator merge lands on main (precedent `docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md`). Then run `mise run diff` (only the orchestrator chart version and image tag change), `mise run apply` and `mise run smoke` (which now includes the scale step) against the expected kube context.

## Acceptance conditions

- AC1: the chart version and image tag agree on the orchestrator sha, read offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the published chart exists for the pinned version [evidence: command:v=$(grep -A3 'name: agent-orchestrator$' helmfile.yaml.gotmpl | sed -n 's/.*version: //p'); helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version "$v"]
- AC3: helmfile apply of the agents namespace succeeds [evidence: command:mise run apply]
- AC4: the live smoke passes, including the scale step [evidence: command:mise run smoke]
- AC5: only the orchestrator chart version and image tag change [evidence: judgement:the task diff and mise run diff output reviewed]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

- Consumes the published chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`).

## Expected outcome

The agents namespace runs this epic's orchestrator and the live smoke, including the scale step, passes.

## Steps

- Update `test_orchestrator_pin_matches_image` to the new sha; run it: fails.
- Change the two pins; run the verify command: passes.
- `mise run diff`: only the orchestrator chart version and image tag change. `mise run apply`, then `mise run smoke`: both exit 0.

## Notes

- Runs after the orchestrator epic branch merges to main; its sha is filled with `ticket.py amend` then (precedent cluster-presets deploy-pin-presets).
- Starts from agents-helmfile main after the hive epic's deploy pin, so the any-mcp v0.2.0 smoke check is already in place.
- `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts and are deselected in the verify, not changed.
- `mise run apply` is guarded by lint, test and the kube-context check (`EXPECTED_KUBE_CONTEXT`).
