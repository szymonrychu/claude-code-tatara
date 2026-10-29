---
title: CI secret hardening for all tests
status: todo
repo: agents-helmfile
value: "CI runs every test, including SOPS decryption, without exposing the key or decrypted values in a public repo"
files: [.github/workflows/ci.yaml, README.md, MEMORY.md]
verify: "mise run lint && mise run test"
depends_on: [ci-workflow-running-lint-tes]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# CI secret hardening for all tests

## Requirement

User decision 2026-10-29 06:50Z via mx-34 #355, verbatim: "Tell me the repo, I will update the secrets. I already put private gov key into Gitlab repo secrets / In general pipeline is meant to run all changes eventually (CI/CD)." mx-34's reading, relayed with it: CI runs ALL tests, including the 18 SOPS-decrypting ones, and the pipeline is meant to grow into CI/CD; harden it because szymonrychu/agents-helmfile is public: never use pull_request_target; give secrets only to push and same-repo PR runs, never forks; never print decrypted values; delete the key from the runner after use.

Scope (agents-helmfile, .github/workflows/ci.yaml from 08fa9f3 plus README.md and MEMORY.md):
- The job that receives HARBOR_USERNAME, HARBOR_PASSWORD and SOPS_PGP_PRIVATE_KEY runs only for push, workflow_dispatch and pull_request whose head repo is this repository (job-level `if` on `github.event.pull_request.head.repo.full_name == github.repository`). A fork PR gets a separate secret-free job that runs lint only and states in its log that the full suite runs after a maintainer merges or re-pushes from a same-repo branch. No `pull_request_target` anywhere.
- Secret cleanup: an `if: always()` final step kills the gpg-agent (`gpgconf --kill gpg-agent`), removes the temporary GNUPGHOME, and runs `helm registry logout` on the Harbor host, even when an earlier step failed.
- No decrypted value reaches the log: determine (by reading the tests, .hook.sh and the helmfile prepare hooks) every place decrypted material can be printed (pytest assertion diffs and captured output of `helmfile template`, hook stderr, `set -x`), and close each one, for example pytest run with output capture not shown on failure for the decrypting tests, and any rendered Secret data never echoed. Never weaken or skip a test; if a test's failure message would print a decrypted value, say which and propose the fix as a question instead of changing the test.
- Determine whether `helmfile template` in CI runs the prepare hook in .hook.sh (lines 60-75) that pipes decrypted files into kubectl; in CI there is no cluster and nothing may be applied. Report what happens and make sure CI never touches a cluster.
- README section CI and MEMORY.md (dated 2026-10-29, with the why) record the trust model: which events get secrets, the cleanup, the no-print rule.

## Acceptance conditions

- ac1: no `pull_request_target` in any workflow, and the secret-receiving job has a job-level `if` limiting pull_request runs to head repo == this repository [evidence: command:! grep -rn pull_request_target .github && grep -n "head.repo.full_name == github.repository" .github/workflows/ci.yaml]
- ac2: a fork PR runs a secret-free lint job; no `secrets.` reference appears in it [evidence: judgement:reviewer reads the fork job in ci.yaml]
- ac3: a final `if: always()` step kills gpg-agent, removes GNUPGHOME and logs out of Harbor [evidence: command:grep -n "always()" .github/workflows/ci.yaml && grep -n "gpgconf --kill gpg-agent" .github/workflows/ci.yaml && grep -n "registry logout" .github/workflows/ci.yaml]
- ac4: every path that could print decrypted values is listed in the report and closed in the workflow or confirmed safe, with no test skipped, xfailed or weakened [evidence: judgement:implementer report lists each path and its handling]
- ac5: CI never applies to or contacts a cluster; the report states what the prepare hook does under `helmfile template` in CI [evidence: judgement:implementer report and ci.yaml]
- ac6: README section CI and MEMORY.md (2026-10-29) document the trust model [evidence: doc-section:README.md#CI]
- ac7: lint and the full suite pass locally with the SOPS key and Harbor login available, quoting the summary line [evidence: command:mise run lint && mise run test]

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
