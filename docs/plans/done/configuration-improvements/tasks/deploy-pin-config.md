---
title: deploy pin config
status: done
repo: agents-helmfile
value: the agents namespace runs the configuration improvements
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_agents_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_agents_web_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [kind-e2e-config, web-clusters-page, smoke-config-check]
model: ""
review: ""
verified_head: a128670
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 1
actual_tokens: 193721
actual_roles: impl 1
actual_role_tokens: impl 193721
---

# deploy pin config

## Requirement

Release and deploy this epic to the agents namespace (design D10; approval A7). The releases are the main builds of this epic's merged commits: the orchestrator chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` `0.1.0-main.<sha7>` with image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (contracts `agent-orchestrator-chart`, `agent-orchestrator-image`), and the agents-web chart and image published by agents-web CI on main (as frontend-decoupling defines them). No wrapper or any-mcp release (wrapper 0.2.0 already implements every setting). In agents-helmfile: `helmfile.yaml.gotmpl` pins both chart versions; `values/agent-orchestrator/common.yaml` and `values/agents-web/common.yaml` pin the image tags; `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` and `tests/test_agents_web_release.py::test_agents_web_pin_matches_image` assert each chart version and image tag carry the same sha (offline, text read). The shas are filled with `ticket.py amend` once the merges land on main. Then run `mise run diff` (only the two chart versions and image tags change), `mise run apply` and `mise run smoke` (which now includes the config step) against the expected kube context.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the merged sha, read offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the agents-web chart version and image tag agree on the merged sha, read offline [evidence: test:tests/test_agents_web_release.py::test_agents_web_pin_matches_image]
- AC3: the published orchestrator chart exists for the pinned version [evidence: command:v=$(grep -A3 'name: agent-orchestrator$' helmfile.yaml.gotmpl | sed -n 's/.*version: //p'); helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version "$v"]
- AC4: helmfile apply of the agents namespace succeeds [evidence: judgement:the apply output (helm revision and chart) quoted in the task notes; never run apply as AC evidence]
- AC5: the live smoke passes, including the config step [evidence: command:mise run smoke]
- AC6: only the two chart versions and image tags change [evidence: judgement:the task diff and mise run diff output reviewed]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_agents_web_release.py`

## Interfaces

Uses the shared parts listed in the frontmatter `uses`; builds no new interface.

## Expected outcome

The agents namespace runs this epic's orchestrator and agents-web builds, and the live smoke, including the config step, passes.

## Steps

- Update the two pin tests to the merged shas; run them: fail.
- Change the pins; run the verify command: passes.
- `mise run diff`: only the two chart versions and image tags change. `mise run apply`, then `mise run smoke`: both exit 0.

## Notes

The agents-web values and release test file names follow frontend-decoupling's deploy task; amend if they differ (design D12). `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster` pull charts and are deselected in the verify. `mise run apply` is guarded by lint, test and the kube-context check.

Orchestrator notes (2026-10-25; the orchestrator runs live applies): pins e3b2f3c + 7a1654e (agents-web tag quoted; all-digit 1343836 rendered as 1.343836e+06). Pre-apply `mise run diff`, every non-label line: 8x orchestrator image a4be86b -> 60cb11c, agents-web image cedcbbc -> 1343836, checksum/settings (derived), Secret content suppressed (label bump); affected releases agent-orchestrator and agents-web. `mise run apply`: agents-web 0.1.0-main.1343836 and agent-orchestrator 0.1.0-main.60cb11c deployed. Post-apply diff: `No affected releases`. `mise run smoke` last line `smoke: OK` (includes the config check). MEMORY line: agents-helmfile PR #20.

- 2026-10-25 done
