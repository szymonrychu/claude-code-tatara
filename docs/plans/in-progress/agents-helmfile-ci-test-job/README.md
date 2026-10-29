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
