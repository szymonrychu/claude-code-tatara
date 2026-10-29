---
title: helmfile-orch-untrusted-pin
status: done
repo: agents-helmfile
value: the orchestrator that keeps trigger sessions off the chat is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-chat-untrusted-sessions]
model: sonnet
review: ""
verified_head: 5f0956b6214c710fc3d4bae47692a646c0bc99d4
points: 1
expected_minutes: 4
expected_tokens: 637069
points_actual: 1
actual_minutes: 3
actual_tokens: 191085
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 146403, review 44682"
---

# helmfile-orch-untrusted-pin

## Requirement

Pin agents-orchestrator to the merge commit of PR #32 (task orch-chat-untrusted-sessions; migration 0009 created_by_service): chart `0.1.0-main.a9f936f` in helmfile.yaml.gotmpl and `image.tag` `a9f936f` in values/agents-orchestrator/common.yaml. Merge commit a9f936f; main CI run 40796228385 green incl chart-publish. Keep every other pin unchanged (connector c98c501, web 6ea3457, agent image 0.3.3). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the PR #32 merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
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

- Sync to origin/main, change the orchestrator pin assertions in tests/test_orchestrator_release.py to a9f936f and run the verify: the pin tests fail.
- Set the chart version and image tag to a9f936f, rerun: pass. `mise run check-pins` ok, `mise run lint` clean.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 amended: fill merged sha a9f936f

- 2026-10-29 done
