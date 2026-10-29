---
title: Decouple S3 session cache from presets
blockers: []
stage: build
owner: ""
repos: [agents-orchestrator, agents-web]
created: 2026-10-29
---

# Decouple S3 session cache from presets

## Project brief

What: Session S3 cache named by a per-session Jinja2 template (default <preset>-<sessionname>) instead of the preset-derived key; existing sessions' caches copied to the new names so everything works after rotation
How: start-development full path; copy-only migration (never move or delete); planned after paste-.env and immediate delivery in the cct2 queue
Why: User request 2026-10-29 04:52Z via mx-34 #343: decouple s3 cache from preset, Jinja2 backup name template defaulting to preset-sessionname, copy caches of existing sessions

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
