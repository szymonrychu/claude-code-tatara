---
title: images test precision
status: done
repo: agent-orchestrator
value: the full suite and the integration task run green out of the box
files: [tests/test_images.py, mise.toml, README.md]
verify: "uv run pytest tests/test_images.py -q && mise run lint"
depends_on: [ambiguous-send-verifier, bench-cli, container-images-ci, discard-hook-and-export, discard-quiesce-before-expor, entrypoints-and-singleton, helm-chart-ci-publish, helm-chart-config-postgres, helm-chart-rbac-and-ingress, helm-chart-scaffold, ingress-node-denylist, kind-e2e, readme-api-and-openapi, reconciler-loop, scaffold-repo-and-cli, settings-model]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-images-test-precision/agent-orchestrator
branch: agent-orchestrator-images-test-precision
verified_head: a27c8c3b791cecc2e1867f61800098e14e51b4eb
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# images test precision

## Requirement

Full-suite failure: tests/test_images.py::test_no_derived_agent_image asserts the string claude-code-wrapper never appears in .github/workflows/ci.yaml, but the kind e2e job legitimately pulls the wrapper image. Make the test assert what the decision means: no Dockerfile in the repo builds FROM the wrapper image and CI builds and pushes no agent image (no containers/agent-orchestrator-agent tag), while allowing the e2e job's wrapper references. Also: mise run test:integration fails with KeyError when ORCH_TEST_WRAPPER_IMAGE is unset; make the task build e2e/agent-test.Dockerfile (tag agent-orchestrator-agent-test:e2e, as scripts/e2e.sh does) when the variable is unset and export it, and document it in README.

## Acceptance conditions

- AC1: the derived-image rule is asserted precisely and passes with the e2e job present [evidence: test:tests/test_images.py::test_no_derived_agent_image]
- AC2: mise run test:integration works with ORCH_TEST_WRAPPER_IMAGE unset [evidence: command:env -u ORCH_TEST_WRAPPER_IMAGE mise run test:integration]

## Files

- `tests/test_images.py`
- `mise.toml`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The full suite and integration task are green out of the box.

What is true and observable when the task is done.

## Steps

- Red already seen in the epic full suite (test_no_derived_agent_image) and integration KeyError.
- Fix the test and the mise task; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
