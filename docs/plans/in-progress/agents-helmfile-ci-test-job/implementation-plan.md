# agents-helmfile CI test job implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: CI workflow running lint, tests and check-pins

- Status: done
- Files: `.github/workflows/ci.yaml`, `README.md`, `MEMORY.md`
- Verify: `mise run lint`
- Verified head: 08fa9f3bfb99b080912299146932d8d0937b1c87

#### Requirement

User decision (chat 2026-10-28 21:07Z, relayed by mx-34 #270), verbatim: "Yes", accepting: "cct2 adds a CI test job to agents-helmfile after its current work, running the helmfile tests (incl. test_orchestrator_release.py) and check-pins on PRs and main".

Why: agents-helmfile has no CI test job (only GitGuardian), so PR #40 (6548e1f) merged a pin bump while tests/test_orchestrator_release.py still asserted the old tag, turning main red until #42; `mise run apply` caught it only at deploy time.

Scope: a GitHub Actions workflow in agents-helmfile that runs on pull_request and on push to main: `mise run lint`, `mise run test` (the whole suite, including tests/test_orchestrator_release.py) and `mise run check-pins`. Follow the conventions of the sibling repos' workflows (e.g. code/claude-code-wrapper/.github/workflows/build.yaml: actions pinned by full commit sha with a version comment, mise via the same action and pinning, minimal permissions). Repos are public, so check-pins can read check runs with the workflow GITHUB_TOKEN.

Known environment facts: four release tests (`test_release_chart_version_and_needs`, `test_service_token_file_listed`, `test_web_release_chart`, `test_web_release_chart_renders_unique_pull_secrets`, see agents-helmfile MEMORY.md 2026-10-28) run `helmfile template` and need Harbor chart-pull access; agents-helmfile has no repository secrets today (claude-code-wrapper has HARBOR_USERNAME/HARBOR_PASSWORD). The workflow logs in to Harbor with `helm registry login` from HARBOR_USERNAME/HARBOR_PASSWORD secrets when present. Values files are SOPS/PGP-encrypted; determine (by running the suite with an empty GNUPGHOME) whether any test needs decryption, and if so how the workflow handles it, without putting any key in the repo. Never skip or xfail a test to make CI green; if a test cannot run in CI without a secret the user must add, the workflow fails loudly naming the missing secret, and the README documents the user-run step.

#### Acceptance conditions

- ac1: A workflow under .github/workflows runs on pull_request and on push to main and executes mise run lint, mise run test and mise run check-pins; every third-party action is pinned by full commit sha with a version comment [evidence: command:grep -nE "pull_request|branches|mise run (lint|test|check-pins)|uses: " .github/workflows/ci.yaml]
- ac2: The Harbor login step reads the HARBOR_USERNAME and HARBOR_PASSWORD secrets and, when either is missing, the job fails with a message naming the missing secrets; the Harbor-dependent tests are never skipped or xfailed [evidence: command:grep -n "HARBOR_USERNAME\|HARBOR_PASSWORD" .github/workflows/ci.yaml]
- ac3: The suite was run once locally with an empty GNUPGHOME and no Harbor login, and the report lists exactly which tests need Harbor and which (if any) need SOPS decryption; the workflow covers each case without committing any key [evidence: judgement:implementer report quotes both runs' summary lines]
- ac4: README.md documents the CI job and the user-run step (add HARBOR_USERNAME and HARBOR_PASSWORD repository secrets for a read-only chart-pull robot), and MEMORY.md records the decision dated 2026-10-29 with the why [evidence: doc-section:README.md#CI]
- ac5: mise run lint passes on the branch [evidence: command:mise run lint]

#### Files

- `.github/workflows/ci.yaml`
- `README.md`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

### S2: CI secret hardening for all tests

- Status: done
- Files: `.github/workflows/ci.yaml`, `README.md`, `MEMORY.md`
- Verify: `mise run lint && mise run test`
- Verified head: 77979dfa9db4f741c3530998e3007063c3f3653d

#### Requirement

User decision 2026-10-29 06:50Z via mx-34 #355, verbatim: "Tell me the repo, I will update the secrets. I already put private gov key into Gitlab repo secrets / In general pipeline is meant to run all changes eventually (CI/CD)." mx-34's reading, relayed with it: CI runs ALL tests, including the 18 SOPS-decrypting ones, and the pipeline is meant to grow into CI/CD; harden it because szymonrychu/agents-helmfile is public: never use pull_request_target; give secrets only to push and same-repo PR runs, never forks; never print decrypted values; delete the key from the runner after use.

Scope (agents-helmfile, .github/workflows/ci.yaml from 08fa9f3 plus README.md and MEMORY.md):
- The job that receives HARBOR_USERNAME, HARBOR_PASSWORD and SOPS_PGP_PRIVATE_KEY runs only for push, workflow_dispatch and pull_request whose head repo is this repository (job-level `if` on `github.event.pull_request.head.repo.full_name == github.repository`). A fork PR gets a separate secret-free job that runs lint only and states in its log that the full suite runs after a maintainer merges or re-pushes from a same-repo branch. No `pull_request_target` anywhere.
- Secret cleanup: an `if: always()` final step kills the gpg-agent (`gpgconf --kill gpg-agent`), removes the temporary GNUPGHOME, and runs `helm registry logout` on the Harbor host, even when an earlier step failed.
- No decrypted value reaches the log: determine (by reading the tests, .hook.sh and the helmfile prepare hooks) every place decrypted material can be printed (pytest assertion diffs and captured output of `helmfile template`, hook stderr, `set -x`), and close each one, for example pytest run with output capture not shown on failure for the decrypting tests, and any rendered Secret data never echoed. Never weaken or skip a test; if a test's failure message would print a decrypted value, say which and propose the fix as a question instead of changing the test.
- Determine whether `helmfile template` in CI runs the prepare hook in .hook.sh (lines 60-75) that pipes decrypted files into kubectl; in CI there is no cluster and nothing may be applied. Report what happens and make sure CI never touches a cluster.
- README section CI and MEMORY.md (dated 2026-10-29, with the why) record the trust model: which events get secrets, the cleanup, the no-print rule.

#### Acceptance conditions

- ac1: no `pull_request_target` in any workflow, and the secret-receiving job has a job-level `if` limiting pull_request runs to head repo == this repository [evidence: command:! grep -rn pull_request_target .github && grep -n "head.repo.full_name == github.repository" .github/workflows/ci.yaml]
- ac2: a fork PR runs a secret-free lint job; no `secrets.` reference appears in it [evidence: judgement:reviewer reads the fork job in ci.yaml]
- ac3: a final `if: always()` step kills gpg-agent, removes GNUPGHOME and logs out of Harbor [evidence: command:grep -n "always()" .github/workflows/ci.yaml && grep -n "gpgconf --kill gpg-agent" .github/workflows/ci.yaml && grep -n "registry logout" .github/workflows/ci.yaml]
- ac4: every path that could print decrypted values is listed in the report and closed in the workflow or confirmed safe, with no test skipped, xfailed or weakened [evidence: judgement:implementer report lists each path and its handling]
- ac5: CI never applies to or contacts a cluster; the report states what the prepare hook does under `helmfile template` in CI [evidence: judgement:implementer report and ci.yaml]
- ac6: README section CI and MEMORY.md (2026-10-29) document the trust model [evidence: doc-section:README.md#CI]
- ac7: lint and the full suite pass locally with the SOPS key and Harbor login available, quoting the summary line [evidence: command:mise run lint && mise run test]

#### Files

- `.github/workflows/ci.yaml`
- `README.md`
- `MEMORY.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
