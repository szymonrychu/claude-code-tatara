---
title: helmfile orch cleanup pin
status: done
repo: agents-helmfile
value: the orchestrator without dead feed code and with one compaction helper is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-feed-dead-code-and-comp]
model: sonnet
review: ""
verified_head: eafa60b4027f81680c8e1204d9686eed90719b59
points: 1
expected_minutes: 4
expected_tokens: 632059
points_actual: 1
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile orch cleanup pin

## Requirement

Deploy the scope-audit cleanup alone (mx-34 #461 go-ahead; user rule 2026-10-28: deploy small and often). Pin agents-orchestrator to the merge commit of PR #38 (task orch-feed-dead-code-and-comp; no migration): chart `0.1.0-main.2d6d722` in helmfile.yaml.gotmpl and `image.tag` `2d6d722` in values/agents-orchestrator/common.yaml, replacing be554bb. Wait until the orchestrator main CI run for 2d6d722 is green including chart-publish before pinning. Keep every other pin unchanged (plugins v0.4.0, agent image, connector, web). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #38 merge sha 2d6d722 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
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

- Sync to origin/main (4e29e70 or newer); wait for the orchestrator main CI run on 2d6d722 to be green including chart-publish (`gh run watch <id> -R szymonrychu/agents-orchestrator --exit-status`).
- Change the orchestrator pin assertions in tests/test_orchestrator_release.py to 2d6d722 and run the verify: the pin tests fail.
- Set the chart version and image tag to 2d6d722, rerun: pass. `mise run check-pins` ok, `mise run lint` clean. Commit on branch orch-cleanup-pin from origin/main, push, open a PR to main.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 in-progress

- 2026-10-29 done: PR #55 review pass, merged; orch CI 40915663717 green

- 2026-10-29 actuals: no agent records
