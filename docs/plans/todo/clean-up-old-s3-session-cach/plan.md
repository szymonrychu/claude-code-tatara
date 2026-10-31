---
title: Clean up old S3 session cache copies
repos: [agents-orchestrator]
created: 2026-10-29
owner: ""
rung: ""
---

# Clean up old S3 session cache copies

## What and why

What: Remove the old preset-derived S3 cache objects that decouple-s3-session-cache-fr copied to the new per-session names, once the rotation is verified
How: Unqueued: planned only when the user queues it; deletes only objects proven copied and superseded, after verification
Why: User 2026-10-29 06:50Z via mx-34 #355, verbatim: "Migration copies, but there is a follow-up epic to cleanup them"

## Scope ladder

### Rung 1: agreed scope (migrated)

none recorded in the epic format

## Agreed scope

not agreed yet

## Non-goals

none recorded in the epic format

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
