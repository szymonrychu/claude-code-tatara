---
title: helm chart ci publish
status: todo
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
- Job `chart-publish`, only on push to main and on `v*` tags, with `needs: [chart, images]`:
  - computes the version with `scripts/chart-version.sh`
  - refuses an existing version: when `helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator --version <v>` succeeds, the job fails with `chart version <v> already published; bump chart/agent-orchestrator/Chart.yaml version`
  - logs in to `harbor.szymonrichert.pl` with HARBOR_USERNAME and HARBOR_PASSWORD
  - runs `helm package chart/agent-orchestrator --version <v> --app-version <sha7>` and `helm push <tgz> oci://harbor.szymonrichert.pl/charts`
- The `images` job (container-images-ci) also runs on `v*` tags, building and pushing nothing new when `<sha7>` exists, so a tagged chart's appVersion image always exists.

README.md gains `## Releasing`: the version scheme, the OCI location, and that a tag must match Chart.yaml's version.

## Acceptance conditions

- AC1: the chart job lints and runs the chart tests on every push and pull request [evidence: test:tests/test_chart_ci.py::test_chart_job_on_every_push]
- AC2: chart-publish runs only on main and v* tags, after the chart and images jobs, and pushes to oci://harbor.szymonrichert.pl/charts [evidence: test:tests/test_chart_ci.py::test_publish_only_main_and_tags_after_images]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
