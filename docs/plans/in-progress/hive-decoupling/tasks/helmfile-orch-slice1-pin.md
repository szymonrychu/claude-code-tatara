---
title: helmfile orch slice1 pin
status: done
repo: agents-helmfile
value: the orchestrator without the member feed and with the activity route is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-drop-feed-cursor]
model: sonnet
review: ""
verified_head: 0db3588ac99980f84c4366c75c3cc54dbd3418c3
points: 1
expected_minutes: 4
expected_tokens: 634927
points_actual: 1
actual_minutes: 41
actual_tokens: 749152
actual_roles: "impl 40, review 2"
actual_role_tokens: "impl 687076, review 62076"
---

# helmfile orch slice1 pin

## Requirement

Deploy slice 1 of hive-decoupling (user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #33 (tasks orch-activity-route, orch-hive-feed-removal, orch-drop-feed-cursor; migration 0011_drop_feed_cursor): chart `0.1.0-main.342cad8` in helmfile.yaml.gotmpl and `image.tag` `342cad8` in values/agents-orchestrator/common.yaml. Wait until the orchestrator main CI run for 342cad8 is green including chart-publish before pinning. Keep every other pin unchanged. Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #33 merge sha 342cad8 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
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

- Sync to origin/main; wait for the orchestrator main CI run on 342cad8 to be green including chart-publish (`gh run list -R szymonrychu/agents-orchestrator -b main`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to 342cad8 and run the verify: the pin tests fail.
- Set the chart version and image tag to 342cad8, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch hive-decoupling-slice1-pin, push, open a PR to main.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done
