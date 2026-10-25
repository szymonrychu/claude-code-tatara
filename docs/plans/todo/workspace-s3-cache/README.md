---
title: workspace s3 cache
blockers: [orchestrator-rename-sessions, webhook-event-filters]
stage: build
owner: ""
repos: [agents-orchestrator, agents-web, agents-helmfile]
created: 2026-10-25
---

# workspace s3 cache

## Project brief

What: Optional per-preset workspace caching in S3, like GitLab runner caches: when a session starts its workspace archive is downloaded from S3 and unpacked; when it ends the workspace is archived and uploaded back under the same name. The cache key is a user-supplied slug or by default a pseudorandom preset-derived string. Generic S3 configuration, deployed with rook-ceph S3.
How: the reconciler runs a restore Job before init and a save Job during the discard; each Job gets one presigned URL, so S3 credentials stay in the reconciler; tar.zst archive per key; generic S3 settings, rook-ceph ObjectBucketClaim in agents-helmfile.
Why: User request 2026-10-25: 'S3 based workspace caching similar to caching in gitlab runners- when cluster/session starts, workspace is getting downloaded from S3, when it ends it's getting uploaded back to S3 (use zip or something to prepare archive, reuse the same name). Deploy using rook-ceph s3, but configuration must be generic and not assume anything about infra system will run on. Caching is an optional feature, preset coupled with preset. Optionally user can provide cache slug, by default it's pseudorandom (preset derived) string.'

## Description

Runs after orchestrator-rename-sessions (agents-orchestrator, sessions). A preset (or a session spec)
sets `cache {key?, exclude?}`; the session spec gets the user's key or a pseudorandom key derived from
the preset id. The reconciler restores `<prefix><key>.tar.zst` into the workdir with a Job before init
and the Claude sessions, and at session end stops the agent pods and saves the workdir with a second
Job under the same name before the PVC is deleted. S3 credentials stay in the reconciler, which gives
each Job one presigned URL. Generic S3 settings in agents-orchestrator; the rook-ceph bucket
(ObjectBucketClaim) and its wiring in agents-helmfile; the preset form in agents-web. Design:
design.md.

## Goals

- G1: A preset (and a session spec) can enable the workspace cache; it is off unless set.
- G2: The cache key is the user-supplied slug, or by default a pseudorandom string derived from the preset id.
- G3: At session start the archive is downloaded and unpacked into the workdir before init scripts and Claude sessions run; a missing object is a miss.
- G4: At session end the workdir is archived and uploaded under the same object name before the PVC is deleted, on every path through the discard.
- G5: No S3 credential reaches an agent pod or a Job pod.
- G6: S3 configuration is generic; nothing in agents-orchestrator assumes rook-ceph.
- G7: agents-helmfile provisions the bucket on rook-ceph and wires it in; agents-web exposes the cache in the preset form.
- G8: The live smoke proves a value written in one session is restored in the next.

## Non-goals

- Caching outside the session workdir; periodic or mid-session saves; saving on pod crash or node loss.
- A cache delete, list or eviction API, and bucket lifecycle rules.
- Locking between concurrent sessions sharing a key (last writer wins).
- Cache status in the web session views; any claude-code-wrapper change.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
