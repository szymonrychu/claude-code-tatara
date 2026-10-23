---
title: deploy pin d5a7738
status: done
repo: agents-helmfile
value: the live agents namespace runs the merged form fix
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest -q -p no:cacheprovider && mise run lint"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/cluster-form-defaults-and-ga-deploy-pin-d5a7738/agents-helmfile
branch: cluster-form-defaults-and-ga-deploy-pin-d5a7738
verified_head: 7329bc8d44d83b96616485336f273d94f8744ea4
run: cluster-form-defaults-and-ga
provides: []
acs_for_audit: []
process_gaps: []
---

# deploy pin d5a7738

## Requirement

Deploy agent-orchestrator main d5a7738 (PR #3 merge): set helmfile.yaml.gotmpl release agent-orchestrator chart version to 0.1.0-main.d5a7738 and values/agent-orchestrator/common.yaml image tag to d5a7738. Nothing else changes. Pin the new version in a test so a stale pin is caught (the test asserts the chart version and image tag agree on the same sha7).

## Acceptance conditions

- AC1: chart version and image tag both point at d5a7738 and agree [evidence: command:uv run pytest -q -p no:cacheprovider && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

`helmfile diff` would show only the image tag and chart version change for agent-orchestrator.

## Steps

- Add a test in tests/test_orchestrator_release.py asserting chart version 0.1.0-main.d5a7738 and image tag d5a7738; run `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: fails.
- Change the two pins; rerun the verify command: passes.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
