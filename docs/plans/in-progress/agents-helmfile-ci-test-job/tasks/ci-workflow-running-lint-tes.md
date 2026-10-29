---
title: "CI workflow running lint, tests and check-pins"
status: in-progress
repo: agents-helmfile
value: "A red pin or test can no longer merge unnoticed; main stays green"
files: [.github/workflows/ci.yaml, README.md, MEMORY.md]
verify: mise run lint
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 981792
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# CI workflow running lint, tests and check-pins

## Requirement

User decision (chat 2026-10-28 21:07Z, relayed by mx-34 #270), verbatim: "Yes", accepting: "cct2 adds a CI test job to agents-helmfile after its current work, running the helmfile tests (incl. test_orchestrator_release.py) and check-pins on PRs and main".

Why: agents-helmfile has no CI test job (only GitGuardian), so PR #40 (6548e1f) merged a pin bump while tests/test_orchestrator_release.py still asserted the old tag, turning main red until #42; `mise run apply` caught it only at deploy time.

Scope: a GitHub Actions workflow in agents-helmfile that runs on pull_request and on push to main: `mise run lint`, `mise run test` (the whole suite, including tests/test_orchestrator_release.py) and `mise run check-pins`. Follow the conventions of the sibling repos' workflows (e.g. code/claude-code-wrapper/.github/workflows/build.yaml: actions pinned by full commit sha with a version comment, mise via the same action and pinning, minimal permissions). Repos are public, so check-pins can read check runs with the workflow GITHUB_TOKEN.

Known environment facts: four release tests (`test_release_chart_version_and_needs`, `test_service_token_file_listed`, `test_web_release_chart`, `test_web_release_chart_renders_unique_pull_secrets`, see agents-helmfile MEMORY.md 2026-10-28) run `helmfile template` and need Harbor chart-pull access; agents-helmfile has no repository secrets today (claude-code-wrapper has HARBOR_USERNAME/HARBOR_PASSWORD). The workflow logs in to Harbor with `helm registry login` from HARBOR_USERNAME/HARBOR_PASSWORD secrets when present. Values files are SOPS/PGP-encrypted; determine (by running the suite with an empty GNUPGHOME) whether any test needs decryption, and if so how the workflow handles it, without putting any key in the repo. Never skip or xfail a test to make CI green; if a test cannot run in CI without a secret the user must add, the workflow fails loudly naming the missing secret, and the README documents the user-run step.

## Acceptance conditions

- ac1: A workflow under .github/workflows runs on pull_request and on push to main and executes mise run lint, mise run test and mise run check-pins; every third-party action is pinned by full commit sha with a version comment [evidence: command:grep -nE "pull_request|branches|mise run (lint|test|check-pins)|uses: " .github/workflows/ci.yaml]
- ac2: The Harbor login step reads the HARBOR_USERNAME and HARBOR_PASSWORD secrets and, when either is missing, the job fails with a message naming the missing secrets; the Harbor-dependent tests are never skipped or xfailed [evidence: command:grep -n "HARBOR_USERNAME\|HARBOR_PASSWORD" .github/workflows/ci.yaml]
- ac3: The suite was run once locally with an empty GNUPGHOME and no Harbor login, and the report lists exactly which tests need Harbor and which (if any) need SOPS decryption; the workflow covers each case without committing any key [evidence: judgement:implementer report quotes both runs' summary lines]
- ac4: README.md documents the CI job and the user-run step (add HARBOR_USERNAME and HARBOR_PASSWORD repository secrets for a read-only chart-pull robot), and MEMORY.md records the decision dated 2026-10-29 with the why [evidence: doc-section:README.md#CI]
- ac5: mise run lint passes on the branch [evidence: command:mise run lint]

## Files

- `.github/workflows/ci.yaml`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
