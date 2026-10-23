---
title: helm chart ci publish
status: in-progress
repo: agent-orchestrator
value: agents-helmfile can pin an immutable published chart version for every main commit and release tag
files: [.github/workflows/ci.yaml, scripts/chart-version.sh, tests/test_chart_ci.py, README.md]
verify: "uv run pytest tests/test_chart_ci.py -q && mise run lint"
depends_on: [helm-chart-rbac-and-ingress, container-images-ci]
owns: []
uses: [helm-render, agent-orchestrator-chart, agent-orchestrator-image]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# helm chart ci publish

## Requirement

Chart CI and publishing to `oci://harbor.szymonrichert.pl/charts` with immutable versions (D17, D28).

`scripts/chart-version.sh <ref_type> <ref_name> <sha>` prints the chart version to publish, reading `version` from `chart/agent-orchestrator/Chart.yaml`:
- `branch main` prints `<version>-main.<sha7>`.
- `tag vX.Y.Z` prints `X.Y.Z` when it equals the Chart.yaml version; otherwise it exits 1 naming both.
- Anything else exits 2 (nothing to publish).

`.github/workflows/ci.yaml`:
- Job `chart`, on every push and pull request:
  - mise installs helm
  - `mise run lint:chart`
  - `uv run pytest tests/test_chart_*.py -q`
- Job `chart-publish`, only on push to main (`needs: [chart, images]`) and on `v*` tags (`needs: [chart]`):
  - computes the version with `scripts/chart-version.sh`
  - refuses an existing version: when `helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version <v>` succeeds, the job fails with `chart version <v> already published; bump chart/agent-orchestrator/Chart.yaml version`
  - logs in to `harbor.szymonrichert.pl` with HARBOR_USERNAME and HARBOR_PASSWORD
  - runs `helm package chart/agent-orchestrator --version <v> --app-version <sha7>` and `helm push <tgz> oci://harbor.szymonrichert.pl/charts`
- On a tag, before packaging, it checks that `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` exists (`regctl image digest`). A tag must point at a commit main CI already built, so a tagged chart's appVersion image always exists. The images job stays main-only (container-images-ci).

README.md gains `## Releasing`: the version scheme, the OCI location, and that a tag must match Chart.yaml's version.

## Acceptance conditions

- AC1: the chart job lints and runs the chart tests on every push and pull request [evidence: test:tests/test_chart_ci.py::test_chart_job_on_every_push]
- AC2: chart-publish runs only on main (after the chart and images jobs) and on v* tags (after the chart job, requiring the sha7 image to exist), and pushes to oci://harbor.szymonrichert.pl/charts [evidence: test:tests/test_chart_ci.py::test_publish_only_main_and_tags_after_images]
- AC3: chart-version.sh prints <version>-main.<sha7> on main and X.Y.Z on a matching tag, and fails on a mismatched tag [evidence: test:tests/test_chart_ci.py::test_chart_version_scheme]
- AC4: the publish job refuses a version that already exists before it pushes [evidence: test:tests/test_chart_ci.py::test_publish_refuses_existing_version]
- AC5: helm package sets the app version to the commit sha7 [evidence: test:tests/test_chart_ci.py::test_package_sets_app_version_sha7]
- AC6: README documents releasing [evidence: doc-section:README.md#Releasing]

## Files

- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `tests/test_chart_ci.py`
- `README.md`

## Interfaces

- `scripts/chart-version.sh <ref_type> <ref_name> <sha>` (stdout: version; exit 1 mismatch, 2 nothing to publish)
- published chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator` (contract `agent-orchestrator-chart`, consumed by agents-helmfile)

## Expected outcome

Every main commit publishes `0.1.0-main.<sha7>`, and a `vX.Y.Z` tag publishes `X.Y.Z`. A version is never pushed twice.

## Steps

- Write tests/test_chart_ci.py with the five named tests. They parse ci.yaml with yaml.safe_load and run `scripts/chart-version.sh` with subprocess against a temp copy of Chart.yaml. Run `uv run pytest tests/test_chart_ci.py -q` and expect failures.
- Write scripts/chart-version.sh, the two CI jobs and the README section.
- Rerun and expect `5 passed`, then run `mise run lint` and `shellcheck scripts/chart-version.sh`.

## Notes

Harbor chart tags are immutable (brief-infra section 1). The same version is rejected, hence the explicit existence check, which gives a clear message instead of a push error.

With Helm 4, `helm registry login` against a Harbor robot can answer 401 without a scope probe. If it does, write the registry config.json directly (field note helm4-harbor-robot-login).

The Harbor robot needs push on the `charts` project as well as `containers`. The orchestrator checks this at origin creation (design Assumptions).
