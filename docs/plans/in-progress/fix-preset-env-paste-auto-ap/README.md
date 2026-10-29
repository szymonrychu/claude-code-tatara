---
title: "Fix preset .env paste: auto-apply on save, accept secret-named keys"
blockers: []
stage: build
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
