---
title: helmfile-orch-untrusted-pin
status: todo
repo: agents-helmfile
value: the orchestrator that keeps trigger sessions off the chat is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-chat-untrusted-sessions]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 637069
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile-orch-untrusted-pin

## Requirement

Pin agents-orchestrator to the merge commit of PR #32 (task orch-chat-untrusted-sessions; migration 0009 created_by_service): chart `0.1.0-main.<sha7>` in helmfile.yaml.gotmpl and `image.tag` `<sha7>` in values/agents-orchestrator/common.yaml. The orchestrator session fills the sha with `ticket.py amend` once the PR merges and its main CI is green. Keep every other pin unchanged (connector c98c501, web 6ea3457, agent image 0.3.3). Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

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

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
