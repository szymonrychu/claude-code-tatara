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



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
