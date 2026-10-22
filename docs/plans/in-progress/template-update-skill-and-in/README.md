---
title: Template update skill and init docs cleanup
blockers: []
stage: build
owner: Szymon Richert
repos: [workbench]
created: 2026-10-22
---

# Template update skill and init docs cleanup

## Project brief

What: init removes all template-specific docs; a new skill updates an existing workbench from the template without the template's own docs
How: extend the init engine's template-history cleanup; add a tested engine command plus a skill that fetches the template, merges tooling and keeps instance-owned docs
Why: new workbenches must not inherit the template's plans, records and memory, and pulling template updates today is a manual merge with conflicts

## Description

The template repo (this workbench) carries its own development docs: epic plans and records under docs/plans, the contracts file, research briefs, and its own MEMORY.md and ROADMAP.md entries. These stay in the template repo (the user decided not to gitignore them). Two things follow for projects made from the template:

- Initial setup (`init:new`, `init:adopt`) removes every template-specific doc, so a new workbench starts with empty plan folders, no template research, and fresh MEMORY.md and ROADMAP.md. init already clears docs/plans phases, docs/research and facts.md; anything left behind (for example docs/plans/contracts.json) is cleaned too.
- A new skill refreshes an existing workbench instance from the template: it pulls the template's tooling and rules changes and never brings the template's own docs back. Today this is a manual `git merge template/main` plus hand-resolved conflicts plus `mise run init:refresh` (README "Pulling template updates").

## Goals

- init leaves no template-specific doc in a new or adopted workbench: docs/plans holds only empty phase folders, no docs/research, no contracts or facts files, MEMORY.md and ROADMAP.md are fresh.
- One skill, run in an initialised workbench, updates it from the template in one tested engine command through mise: template tooling, plugins, rules and generated blocks arrive; template plans, records, research, contracts, MEMORY.md and ROADMAP.md entries never arrive; the user's own docs and AGENTS.md answers stay intact; it ends in one commit with lint green.
- README "Pulling template updates" points at the skill instead of the manual merge.

## Non-goals

- Gitignoring docs/plans in the template (the user decided against it).
- Changes to the personal plugin at ~/Documents/claude-infra-plugin.
- Pushing anything; the update skill commits locally only.

## Time

Estimate: 53 min | Actual: 0 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
