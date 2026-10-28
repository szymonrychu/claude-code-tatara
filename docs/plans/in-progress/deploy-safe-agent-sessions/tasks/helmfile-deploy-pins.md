---
title: helmfile deploy pins
status: in-progress
repo: agents-helmfile
value: the release that keeps sessions alive is pinned for deploy
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"
depends_on: [wrapper-patch-release, orch-onstart-nonfatal, orch-sessions-backup-restore, orch-api-session-safety, orch-ci-publish-gate, orch-e2e-rollout-mid-turn, web-discard-backup-notice, web-agent-unavailable-banner, web-ci-publish-gate, helmfile-pin-check, helmfile-smoke-continuity, orch-rollout-dispatch-reserv, orch-sessions-save-unconverg, orch-security-hardening, web-review-fixes]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile deploy pins

## Requirement

Design D13, user decision verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned release tags are pre-approved."

Goal G10, verbatim: "Released and deployed: wrapper release tag, orchestrator and web pins, agents-helmfile bump, apply and smoke green, with a live check that the deploy did not roll a busy agent."

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<orchestrator merge sha7>`; agents-web chart `0.1.0-main.<agents-web merge sha7>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<orchestrator sha7>`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:0.3.2` (a release tag: Harbor prunes sha7 tags).
- `values/agents-web/common.yaml`: `image.tag` `<agents-web sha7>`.
- Tests: `tests/test_orchestrator_release.py` and `tests/test_web_release.py` keep the pins in agreement.
- `mise run check-pins` (task helmfile-pin-check) passes on the new pins: their main CI runs are green.

The shas are filled in by `ticket.py amend` when the orchestrator and agents-web PRs merge.

Notes: `tests/test_orchestrator_release.py` holds `test_values_dir_moved`; it must pass so the apply is not stopped by a stale test (retro). Chart-pull tests blocked by a container network policy may be deselected locally (precedent); they run unblocked before the apply.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on the wrapper release [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC4: the agent image is the 0.3.2 release [evidence: command:grep -q "claude-code-wrapper:0.3.2" values/agents-orchestrator/common.yaml]
- AC5: every pin's main CI is green [evidence: command:mise run check-pins]
- AC6: the release test files and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
