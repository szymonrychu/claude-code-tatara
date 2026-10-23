---
title: deploy pin presets
status: todo
repo: agents-helmfile
value: the live agents namespace runs the presets release
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [fe-presets-page, retire-spec-update-repo, kind-e2e-presets]
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

# deploy pin presets

## Requirement

Pin agents-helmfile to this epic's merged agent-orchestrator build (design D9; precedent `docs/plans/done/cluster-form-defaults-and-ga/tasks/deploy-pin-d5a7738.md`; web-ui-cluster-tabs-with-fil task deploy-pin set the current pins).

The value is the short sha (7 hex) of this epic's agent-orchestrator main merge; the orchestrator supplies it by amending this requirement (`ticket.py amend`) after the PR merges; until then this task reports `blocked` with `whoCanClear: orchestrator (merge the agent-orchestrator PR of cluster-presets)`.

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.<orch sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<orch sha7>`. The wrapper image pins, `ORCH_ALLOWED_ORIGINS` and the ingress settings stay as they are.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` asserts the chart version and the image tag both carry `<orch sha7>`, reading `helmfile.yaml.gotmpl` as text (no `helmfile build`, so it runs without pulling charts).
- Nothing else changes. `scripts/smoke.sh` keeps its raw spec create (Q2). `helmfile apply` and `mise run smoke` are run by the user after the epic.

## Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator sha and the test runs offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: only the orchestrator chart version and image tag change; the wrapper pins and ORCH_ALLOWED_ORIGINS stay [evidence: judgement:the task diff reviewed against the requirement]
- AC3: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster" && uv run ruff check . && uv run ruff format --check .]

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
