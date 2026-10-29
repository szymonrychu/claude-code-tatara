---
title: helmfile orch flaky fix pin
status: in-progress
repo: agents-helmfile
value: the orchestrator with the push-after-decision flaky-test fix is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-flaky-push-after-decisi]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 632059
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile orch flaky fix pin

## Requirement

Deploy the flaky-test fix alone (mx-34 #430, relaying cct2: "Tatara should deploy be554bb on its own"; user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #37 (task orch-flaky-push-after-decisi, fix fe2c623; no migration): chart `0.1.0-main.be554bb` in helmfile.yaml.gotmpl and `image.tag` `be554bb` in values/agents-orchestrator/common.yaml, replacing df2b80e. Wait until the orchestrator main CI run for be554bb is green including chart-publish before pinning. Keep every other pin unchanged (plugins v0.4.0, agent image, connector, web). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #37 merge sha be554bb [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
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

- Sync to origin/main; wait for the orchestrator main CI run on be554bb to be green including chart-publish (`gh run list -R szymonrychu/agents-orchestrator -b main`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to be554bb and run the verify: the pin tests fail.
- Set the chart version and image tag to be554bb, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch orch-flaky-fix-pin (from origin/main; PR #53 holds branch hive-decoupling), push, open a PR to main.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress
