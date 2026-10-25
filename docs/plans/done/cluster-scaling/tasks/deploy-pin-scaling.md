---
title: deploy pin scaling
status: done
repo: agents-helmfile
value: the agents namespace runs cluster scaling
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [agent-scale-route, scale-tool-allow, agents-strip-leaving-mark, kind-e2e-scaling, smoke-scale-check]
model: ""
review: ""
verified_head: "not obtained: the verify script did not run"
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 1
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# deploy pin scaling

## Requirement

Release and deploy this epic to the agents namespace (design D6; user S1, S2, S3, X2). The orchestrator release is the main build of this epic's merged agent-orchestrator commit: chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`); no any-mcp or wrapper release is needed (the scale tool ships in any-mcp v0.2.0 from hive F1, already pinned). In agents-helmfile: `helmfile.yaml.gotmpl` release `agent-orchestrator` chart version `0.1.0-main.<sha7>`, `values/agent-orchestrator/common.yaml` `image.tag` `<sha7>`, `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` asserts both carry the sha (offline, text read). The sha is filled with `ticket.py amend` once the orchestrator merge lands on main (precedent `docs/plans/done/cluster-presets/tasks/deploy-pin-presets.md`). Then run `mise run diff` (only the orchestrator chart version and image tag change), `mise run apply` and `mise run smoke` (which now includes the scale step) against the expected kube context.

## Acceptance conditions

- AC1: the chart version and image tag agree on the orchestrator sha, read offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the published chart exists for the pinned version [evidence: command:v=$(grep -A3 'name: agent-orchestrator$' helmfile.yaml.gotmpl | sed -n 's/.*version: //p'); helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version "$v"]
- AC3: helmfile apply of the agents namespace succeeds [evidence: judgement:the apply output (helm revision and chart) quoted in the task notes; never run apply as AC evidence]
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

## Ruling

- 2026-10-25 accepted: pin landed (ed0233a), PR #17 merged; orchestrator applied helm rev 13 under the user's apply approval; post-apply diff clean; smoke OK incl scale 1->2->1

## Notes

- Runs after the orchestrator epic branch merges to main; its sha is filled with `ticket.py amend` then (precedent cluster-presets deploy-pin-presets).
- Starts from agents-helmfile main after the hive epic's deploy pin, so the any-mcp v0.2.0 smoke check is already in place.
- `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts and are deselected in the verify, not changed.
- `mise run apply` is guarded by lint, test and the kube-context check (`EXPECTED_KUBE_CONTEXT`).

Orchestrator notes (2026-10-25): pin 3b9926d landed on cluster-scaling (ed0233a, rebased onto main 8ff9753), agents-helmfile PR #17 merged. Pre-apply `mise run diff`: only `helm.sh/chart 0.1.0-main.a5b5a75 -> 0.1.0-main.3b9926d` and `app.kubernetes.io/version "a5b5a75" -> "3b9926d"` (live had been rolled back to a5b5a75 by the verifier running AC3's apply at rev 12). `mise run apply`: helm revision 13, chart agent-orchestrator-0.1.0-main.3b9926d deployed. Post-apply diff: `No affected releases`. `mise run smoke` last line: `smoke: OK` (scale 1->2->1, pod-0 uid kept, init scripts succeeded).
