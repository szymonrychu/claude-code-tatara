---
title: webhook ci images
status: todo
repo: agents-webhook
value: every main merge publishes an immutable image and chart that agents-helmfile can pin
files: [.github/workflows/ci.yaml, scripts/chart-version.sh, tests/test_ci.py]
verify: "uv run pytest tests/test_ci.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [webhook-chart-network, webhook-api-e2e]
owns: [agents-webhook-image]
uses: [agents-webhook-chart]
model: ""
estimate: 5
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

# webhook ci images

## Requirement

CI and publishing (design D13, D15). Paths are in code/agents-webhook.

Precondition, checked first: `gh secret list -R szymonrychu/agents-webhook` shows `HARBOR_USERNAME` and `HARBOR_PASSWORD`. If not, set them with `gh secret set` from the same robot account agent-orchestrator uses when the values are available to the agent; otherwise end `blocked`, whoCanClear "user: set HARBOR_USERNAME and HARBOR_PASSWORD on szymonrychu/agents-webhook".

- `.github/workflows/ci.yaml` modelled on agent-orchestrator's: jobs `lint`, `test` (Docker for testcontainers), `chart` (`mise run test:chart`, `helm lint`), `e2e` (`mise run test:e2e`), `images` (docker build, `--help` smoke, push `harbor.szymonrichert.pl/containers/agents-webhook:<sha7>` on main only), `chart-publish` (`0.1.0-main.<sha7>` on main to `oci://harbor.szymonrichert.pl/charts/agents-webhook`), `chart-publish-tag` (`X.Y.Z` on tag `vX.Y.Z`).
- `scripts/chart-version.sh` as agent-orchestrator's.
- `tests/test_ci.py`: the jobs exist; images and chart-publish run only on main; the image name and chart repo are as above; pull requests never push.
- After this epic's agents-webhook PR merges to main (orchestrator), the main run is green and `helm show chart oci://harbor.szymonrichert.pl/charts/agents-webhook --version 0.1.0-main.<sha7>` succeeds; quote it in the task notes.

## Acceptance conditions

- AC1: CI has lint, test, chart, e2e, images and chart-publish jobs, publishing only from main or tags [evidence: command:uv run pytest tests/test_ci.py -q]
- AC2: the published image and chart for the main merge exist in Harbor [evidence: judgement:the task notes quote helm show chart and docker manifest inspect for the main sha]
- AC3: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `tests/test_ci.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
