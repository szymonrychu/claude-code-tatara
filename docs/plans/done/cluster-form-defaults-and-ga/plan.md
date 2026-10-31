---
title: cluster form defaults and gauge tick
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-23
owner: Szymon Richert
rung: 1
---

# cluster form defaults and gauge tick

## What and why

What: Dropdowns for model and effort, defaults prefilled for every cluster field, a correct auto-compact tick
How: Settings and /meta carry model, effort and resource defaults; the form reads them like max attempts; the renderer applies resource defaults; the gauge tick is a radial mark
Why: The form shows empty fields with no hint of what the cluster will get, and the gauge tick is drawn off the ring

User request (2026-10-23): in the cluster form, Model and Effort must be dropdowns, and every other field must show its default when not provided, the way Max attempts is prefilled from /meta defaults (e.g. CPU request). Also the ribbon context gauge's auto-compact tick renders as a skewed rectangle outside the circle (screenshot: grey ring at 3%, white bar top-right); it must be a small radial mark on the ring.

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: Model and Effort are dropdowns fed by /meta (models: claude-opus-5-5 default, claude-sonnet-5-5, claude-haiku-5-5, claude-fable-5-1; efforts: low, medium, high, xhigh, max).
- 1.2: Every form field is prefilled from /meta defaults; cpu request 500m / limit 4 and memory request 1Gi / limit 8Gi are real defaults applied to agent pods when a cluster leaves them empty, all configurable via ORCH_* settings.
- 1.3: The gauge's auto-compact tick sits on the ring at the auto-compact percentage.
- 1.4: Deployed: chart and image bumped in agents-helmfile, applied, smoke OK.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No change to clusters already running until they are edited (existing specs keep their values).

## Design

none recorded in the epic format

## Decisions

none recorded in the epic format

## Open questions

none

## Research

none recorded in the epic format

## Irreversible operations

none

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-23)

Whole-diff review (sonnet reviewer): 3 medium findings, all fixed in run wf_e3cf829b-ffa:
- render-time resource defaults would roll running clusters: moved to write time (2d099ec); goldens identical to origin/main.
- PATCH 422 for stored legacy model/effort and for high request without limit: validate only changed values, guarded fill (2d099ec).
- edit mode blank Model select for null model: default option (34631bd).
Also fixed a pre-existing timing flake in test_at_most_eight_sends_in_flight (3fcbb0b; TDD exception: test-only change, red shown by cap mutation 7/9).
Full suites on 3fcbb0b: test 405 passed; integration 8 passed; chart, lint, lint:chart, fe lint/test/build/check:api, kind e2e all exit 0.
Ruling: user said live session edit is not needed; edit removal belongs to the cluster-presets epic.

### approvals.json

- A: Model and Effort are dropdowns in the cluster form, fed by /meta (models: claude-opus-5-5 default, claude-sonnet-5-5, claude-haiku-5-5, claude-fable-5-1; efforts low..max). [decisions: ] [tasks: meta-form-defaults, form-dropdowns-and-gauge-tic] [status: approved]
- B: Every other form field shows its default when not provided, like Max attempts; cpu 500m/4 and memory 1Gi/8Gi are real defaults applied to agent pods. [decisions: ] [tasks: meta-form-defaults, form-dropdowns-and-gauge-tic] [status: approved]
- C: The ribbon context gauge's auto-compact tick sits on the ring. [decisions: ] [tasks: form-dropdowns-and-gauge-tic] [status: approved]
