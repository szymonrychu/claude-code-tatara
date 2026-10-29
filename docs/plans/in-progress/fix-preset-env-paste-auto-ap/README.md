---
title: "Fix preset .env paste: auto-apply on save, accept secret-named keys"
blockers: []
stage: review
owner: Szymon Richert
repos: [agents-web, agents-helmfile]
created: 2026-10-29
---

# Fix preset .env paste: auto-apply on save, accept secret-named keys

## Project brief

What: Preset form keeps pasted .env values on Create/Save without Apply and stops rejecting TOKEN/PASSWORD-style keys
How: Submit applies a pending paste through the Apply merge (parse errors block it); drop the web-only SECRET_KEY rule from envKeyError; bump and apply the web chart pin
Why: The user cannot enter the agents-helmfile secrets through the UI until this works

## Description

User report (verbatim): "When I try to paste .env and I don't hit "apply", create preset like this, it's not keeping the secret. When I attempt to paste .env and hit apply envs with TOKEN and PASSWORD are flagged as something that doesn't belong to envs."

Two defects in agents-web, both in the preset form (src/presets/PresetForm.tsx, also used to create sessions from presets):
1. Create/Save submits `values.env` only; text left in the open "Paste .env" textbox without Apply is silently dropped.
2. `envKeyError` (src/sessions/sessionSpecForm.ts) rejects keys matching SECRET_KEY (TOKEN, SECRET, PASSWORD, CREDENTIAL, API_KEY, PRIVATE_KEY, ACCESS_KEY) with "Looks like a secret, secrets do not belong in the spec". The orchestrator accepts these keys (spec.py `_env`), so the web rule alone blocks them.

User decisions (relayed by mx-34 #386, 2026-10-29): auto-apply a pending paste on Create, refuse on parse errors, no secret-key check and no warning. Priority: ahead of the rest of slash, so the user can enter the agents-helmfile secrets through the fixed UI.

## Goals

- Create and Save apply a pending (unapplied) .env paste with the same merge as Apply before submitting, so the pasted keys are in the saved spec.
- A pending paste with any parse error blocks the submit: nothing is sent, the line errors show in the paste box.
- Env keys containing TOKEN, SECRET, PASSWORD, CREDENTIAL, API_KEY, PRIVATE_KEY or ACCESS_KEY are accepted with no error and no warning, typed or pasted.
- Deployed: agents-web chart pin bumped in agents-helmfile and applied under the deploy lease.

## Non-goals

- No orchestrator change; its env key rules stay as they are.
- No change to the reserved-name, name-shape or duplicate-key checks.
- No secret storage (Kubernetes Secret backed presets is the separate epic kubernetes-secret-backed-pre).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-29)

fix-preset-env-paste-auto-ap review notes (2026-10-29, cct2-1)
- web-env-paste-fix: implementer 7027bb1 (red 7 failed/44 passed, green 51/51), reviewer clean round 0, pointsActual 3; mise run test 648 passed, lint ok.
- Scope audit: goals 1-3 and AC1-AC7 delivered, no duplicates; goal 4 deploy done below.
- agents-web PR #22 merged ab78d97, main CI passed. agents-helmfile PR #51 (pin ab78d97, commit 1906b61) merged 082bedc.
- Deploy: lease taken, mise run apply -- --selector name=agents-web from 1906b61: lint ok, 290 passed, check-pins ok, agents-web upgraded; rollout ok, image agents-web:ab78d97, live bundle has no secret-key rule; lease deleted, temp kubeconfig/GNUPGHOME/registry login removed.
- Helmfile pin done outside a ticket task: new-task refused the file overlap with hive-decoupling helmfile-deploy-pin; selector-scoped apply left the orchestrator pin untouched.
- noted, not doing now: web RESERVED_KEY lacks ORCH_* that the orchestrator rejects.
