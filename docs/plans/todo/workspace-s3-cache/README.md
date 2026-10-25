---
title: workspace s3 cache
blockers: [orchestrator-rename-sessions]
stage: build
owner: ""
repos: [agent-orchestrator, agents-web, agents-helmfile]
created: 2026-10-25
---

# workspace s3 cache

## Project brief

What: Optional per-preset workspace caching in S3, like GitLab runner caches: when a session starts its workspace archive is downloaded from S3 and unpacked; when it ends the workspace is archived and uploaded back under the same name. The cache key is a user-supplied slug or by default a pseudorandom preset-derived string. Generic S3 configuration, deployed with rook-ceph S3.
How: 
Why: User request 2026-10-25: 'S3 based workspace caching similar to caching in gitlab runners- when cluster/session starts, workspace is getting downloaded from S3, when it ends it's getting uploaded back to S3 (use zip or something to prepare archive, reuse the same name). Deploy using rook-ceph s3, but configuration must be generic and not assume anything about infra system will run on. Caching is an optional feature, preset coupled with preset. Optionally user can provide cache slug, by default it's pseudorandom (preset derived) string.'

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
