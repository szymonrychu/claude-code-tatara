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

Verdict: pass (2026-10-26)

Epic review of workspace-s3-cache-deploy, 2026-10-26.
- Every task was reviewed alone, with fix rounds:
  - the quota unit is 100G (rook's documented form);
  - the presign proofs moved to a one-off probe;
  - discovered: RGW rejects an unsigned Content-Type on presigned PUT, fixed by cache-put-signs-content-type (agents-orchestrator ea1fac7).
- Security review: no medium-or-higher findings.
  - The OBC Secret is used only by the reconciler.
  - The user quota is enforced: 100G / 100000 objects.
  - rgw is ClusterIP only.
  - No new NetworkPolicy gap (the namespace has none).
- Live:
  - agents-orchestrator 0.1.0-main.ea1fac7, agents-web 0.1.0-main.d81b219, OBC Bound.
  - Probe: 403 (PUT URL used for GET), 404 (missing key).
  - Post-apply diff "No affected releases"; smoke OK with a cache round trip.
- Merged: agents-web #11 (d81b219), agents-orchestrator #19 (ea1fac7), agents-helmfile #25 (2d65d0a). helmfile `mise run test`: 165 passed.
