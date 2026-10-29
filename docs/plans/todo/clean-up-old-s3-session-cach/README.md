---
title: Clean up old S3 session cache copies
blockers: [decouple-s3-session-cache-fr]
stage: build
owner: ""
repos: [agents-orchestrator]
created: 2026-10-29
---

# Clean up old S3 session cache copies

## Project brief

What: Remove the old preset-derived S3 cache objects that decouple-s3-session-cache-fr copied to the new per-session names, once the rotation is verified
How: Unqueued: planned only when the user queues it; deletes only objects proven copied and superseded, after verification
Why: User 2026-10-29 06:50Z via mx-34 #355, verbatim: "Migration copies, but there is a follow-up epic to cleanup them"

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
