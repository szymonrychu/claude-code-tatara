---
title: helmfile-orch-chat-fix-pin
status: todo
repo: agents-helmfile
value: the fixed orchestrator chart is the one applied
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py"
depends_on: [orch-chat-env-scope]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 551464
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile-orch-chat-fix-pin

## Requirement

Pin the agents-orchestrator release to the merge commit of task orch-chat-env-scope (chart `0.1.0-main.<sha7>` in helmfile.yaml.gotmpl and `image.tag` `<sha7>` in values/agents-orchestrator/common.yaml; the orchestrator session fills the sha with `ticket.py amend` after the orchestrator PR merges and its main CI is green). The previous pin 37edd58 with chat enabled crash-looped every migrate init container (live apply 2026-10-28 21:32Z, rolled back). Keep every other pin unchanged, including the agent image. Update tests/test_orchestrator_release.py to the new pin. `mise run check-pins` must pass. Never run an apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orch-chat-env-scope merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
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

- Sync the tree to origin/main (`git merge --ff-only origin/main`), then change the orchestrator pin assertions in tests/test_orchestrator_release.py to 6b467b7 and run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: the pin tests fail.
- Set the chart version and image tag to 6b467b7, rerun: pass (Harbor-401 template tests may be deselected locally, name them).
- `mise run check-pins`: every pin ok. `mise run lint`: clean.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
