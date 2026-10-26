---
title: workspace s3 cache deploy
blockers: [workspace-s3-cache]
stage: review
owner: Szymon Richert
repos: [agents-helmfile, agents-web]
created: 2026-10-25
---

# workspace s3 cache deploy

## Project brief

What: Optional per-preset workspace caching in S3 (deploy half): rook-ceph bucket and wiring in agents-helmfile, preset form in agents-web, pinned builds, apply and smoke. Core in epic workspace-s3-cache.
How: ObjectBucketClaim on rook-ceph in agents-helmfile wired to the orchestrator's generic S3 settings; cache fields in the agents-web preset form; pin builds, apply, live smoke proves restore across sessions.
Why: User request 2026-10-25: S3 based workspace caching like GitLab runner caches, deployed on rook-ceph, generic configuration. Split from workspace-s3-cache so core work can land before deploy.

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
