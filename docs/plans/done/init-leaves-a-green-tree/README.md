---
title: Init leaves a green tree
blockers: []
stage: review
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

Estimate: 59 agent-min | Critical path: 44 min | Expected wall at P=1.5: 1.5 h (k=2.0) | Actual: 0 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-23)

Whole-diff review (sonnet reviewer): every acceptance condition A-E met, no correctness defects.
Acted on: e2e runtime in the default suite (heavy tests now behind the slow marker and `mise run e2e`, CI job e2e); license-missing refusal regression restored; discovered during the tatara update: refresh now writes the allow file (template-update of a pre-fix workbench works, verified on claude-code-tatara a9dc548); CI workflow test pins the e2e job.
Dropped: unchecked `git ls-files -sz` in lint/secrets (a failure only yields a false positive, never a hidden leak; reviewer recommended no change).
Scope audit (scope-auditor): every approval item and FEEDBACK.md section 1-6 landed.
Rulings: template-marker-skip gate-repeat false positive (skipif is the deliverable); e2e-init-green verifier timeout, hand-verified 7 passed in 2867s; ruff-e501 no change needed (landed in ce694a7).
