---
title: agents-helmfile CI test job
blockers: []
stage: review
owner: Szymon Richert
repos: [agents-helmfile]
created: 2026-10-29
---

# agents-helmfile CI test job

## Project brief

What: A GitHub Actions job running lint, the helmfile tests and check-pins on PRs and main.
How: One workflow following the sibling repos' pinned-action conventions; Harbor login from repo secrets; README and MEMORY updated.
Why: Main went red after pin PR #40 because no CI ran the tests; user approved the job (2026-10-28 21:07Z).

## Description



## Goals

- A GitHub Actions job in agents-helmfile runs `mise run lint`, the whole `mise run test` suite (incl. tests/test_orchestrator_release.py) and `mise run check-pins` on every pull request and on push to main (user, 2026-10-28 21:07Z via mx-34 #270: "Yes").
- Missing repository secrets fail the job loudly by name; no test is skipped or xfailed to get green.

## Non-goals

- Branch protection or required checks (repository settings stay with the user).
- Deciding where the SOPS key lives: open user decision (mx-34 #349); the PR merges only after it and the Harbor secrets are settled, so main never goes red.


## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-29)

agents-helmfile-ci-test-job review notes (2026-10-29, cct2-1)
- Task ci-workflow-running-lint-tes: implementer 08fa9f3, reviewer clean round 0 (verify mise run lint EXIT=0), pointsActual 3. First implementer attempt died with the cct2-1 pod roll (no commits); re-run from 52b6893.
- Scope audit: every AC landed; gap README Goals/Non-goals empty -> filled (698111a3).
- Full suite on 08fa9f3 with SOPS key and Harbor login (regcred, standing approval): 290 passed in 468.75s; lint ok.
- Without keys: 18 failed / 272 passed, all SOPS decryption (prepare hook on raw/regcred.pre.secrets.yaml).
- Security review by reviewer: pull_request only, contents: read, no secret echo, temp GNUPGHOME. Open user decision: SOPS key as repo secret (mx-34 #349); Harbor secrets to be added by the user (#348).
- PR szymonrychu/agents-helmfile#48 opened, held unmerged until secrets are settled (main stays green).
