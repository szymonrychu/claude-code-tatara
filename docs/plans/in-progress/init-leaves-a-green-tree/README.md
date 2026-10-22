---
title: Init leaves a green tree
blockers: []
stage: build
owner: Szymon Richert
repos: [workbench]
created: 2026-10-22
---

# Init leaves a green tree

## Project brief

What: Fix the six init defects in FEEDBACK.md so init and component add leave lint and test green
How: Project-owned personal allow file written by init, gitlink-free secrets scan, all-LICENSE holder rewrite, a template pytest marker skipped after init, skill text fixes
Why: Every new workbench currently starts red, which blocks the TDD and boy-scout flow from the first commit

## Description

Initialising claude-code-tatara from the template (init:adopt of a GitHub repo) broke the
template's own promise that init leaves a clean tree with `mise run lint` and `mise run test`
green. Six issues are recorded in ~/Documents/FEEDBACK.md: the personal lint trips on the
project's own name and on the owner in .gitmodules, the secrets lint scans submodule checkouts,
--license-holder rewrites only the root LICENSE, template-only self-tests fail in every
initialised workbench, and the init skill misdescribes local-bare and the --path move.

## Goals

- An init (new or adopt) and every component add leave `mise run lint` and `mise run test` green, proven by an e2e test whose project name and owner collide with a denylisted hash.
- lint:personal accepts the project's own vocabulary through a project-owned allow file that the shipped denylist tests and template-update never touch.
- lint:secrets scans the metarepo's own files only, never a gitlink's checkout, with no gitleaks allowlist.
- --license-holder (or its git-author default) lands in the root LICENSE and every plugins/*/LICENSE.
- Template-only self-tests skip in an initialised workbench and still run in the template.
- The init and component-add skills state the local-bare limits and the --path move.

## Non-goals

- No change to the shipped denylist terms or hashes.
- No secret scanning inside component repos (each component scans itself).
- No push of the template or of claude-code-tatara.

## Time

Estimate: 54 agent-min | Critical path: 39 min | Expected wall at P=1.5: 1.3 h (k=2.0) | Actual: 0 min | Remaining estimate: 16 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
