---
title: Paste .env contents into the preset env editor
blockers: []
stage: build
owner: Szymon Richert
repos: [agents-web]
created: 2026-10-26
---

# Paste .env contents into the preset env editor

## Project brief

What: A Paste .env textbox in the agents-web preset form env editor that fills the env rows from pasted .env text
How: A pure dotenv parser module plus a toggleable textbox with Apply/Cancel in PresetForm, merging into the existing rows and reusing their validation
Why: Adding many env vars row by row is slow; pasting an existing .env file is the natural workflow

## Description

The preset form in agents-web (src/presets/PresetForm.tsx, also used to create sessions from presets) edits `spec.env` one key/value row at a time through "Add env". Setting many variables means a click and two text fields per variable. This epic adds a "Paste .env" textbox to that editor: the user pastes .env file contents, applies them, and the rows are filled from the parsed lines. The existing per-row editor and its key validation (envKeyError: name shape, secret-looking keys, reserved names, duplicates) stay as they are and judge the pasted keys like typed ones.

## Goals

- A pure .env parser (new module src/sessions/dotenv.ts) turning pasted text into ordered key/value pairs or per-line errors.
- A "Paste .env" control in the preset form env editor: a multiline textbox plus Apply that merges parsed pairs into the env rows (an existing key's value is replaced in place, new keys are appended in paste order), then closes and clears the textbox.
- A paste with any unparseable line applies nothing and shows the offending line numbers.

## Non-goals

- No change to the orchestrator API, spec validation or the per-row editor's validation rules.
- No export of rows back to .env text, no file upload.
- No multi-line values (a quoted value spanning lines is reported as an error line).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
