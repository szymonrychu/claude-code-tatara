---
title: helmfile orch slice2 pin
status: done
repo: agents-helmfile
value: the orchestrator with the handover_due and leadership_request notes is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-handover-outcome-note]
model: sonnet
review: ""
verified_head: 96b2e5e211be50d7bb2f12d5ce826619b52d5c91
points: 1
expected_minutes: 4
expected_tokens: 634927
points_actual: 1
actual_minutes: 39
actual_tokens: 340130
actual_roles: "impl 38, review 2"
actual_role_tokens: "impl 278372, review 61758"
---

# helmfile orch slice2 pin

## Requirement

Deploy slice 2 of hive-decoupling (user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #34 (tasks orch-handover-due-note, orch-handover-outcome-note; no migration): chart `0.1.0-main.98d3c23` in helmfile.yaml.gotmpl and `image.tag` `98d3c23` in values/agents-orchestrator/common.yaml. Wait until the orchestrator main CI run for 98d3c23 is green including chart-publish before pinning. Keep every other pin unchanged. Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #34 merge sha 98d3c23 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: every pin's main CI is green [evidence: command:mise run check-pins]
- AC3: lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

- Sync to origin/main; wait for the orchestrator main CI run on 98d3c23 to be green including chart-publish (`gh run list -R szymonrychu/agents-orchestrator -b main`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to 98d3c23 and run the verify: the pin tests fail.
- Set the chart version and image tag to 98d3c23, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch hive-decoupling, push, open a PR to main.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done
