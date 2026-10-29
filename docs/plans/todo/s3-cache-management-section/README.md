---
title: S3 cache management section
blockers: [Decouple S3 session cache from presets, Live session transcript backup, hive decoupling]
stage: build
owner: ""
repos: [agents-orchestrator, agents-web, agents-helmfile]
created: 2026-10-29
---

# S3 cache management section

## Project brief

What: Dedicated agents-web section for S3 cache management, beside presets, sessions and webhooks, backed by an orchestrator HTTP API
How: the reconciler (sole S3 credential holder) keeps a bucket inventory table and runs single-object deletes queued through a status-guarded request table; the orchestrator api serves a classified, paged list and delete requests on the web port only; agents-web adds a Cache section with a quota gauge and a typed-name confirm
Why: User request 2026-10-29 04:52Z via mx-34 #343: dedicated section (as presets, sessions, webhooks) for s3 cache management

## Description

User request (2026-10-29 04:52Z via mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

Today nothing lists, inspects or deletes S3 cache objects: the only S3 call is presigning for the reconciler's save and restore Jobs, the database knows only live sessions' objects, and objects of discarded sessions, old `preset-*` and `sessions/<slug>` copies left by decouple-s3-session-cache-fr, and smoke objects show up only in a bucket listing. The bucket has a quota (100G, 100000 objects) and no versioning, and a corrupt archive is "fixed by deleting the object" (orchestrator MEMORY D11) with no tool to do it. This epic adds a Cache section beside Sessions and Presets: every object with its kind, class (in use by which session, named by a preset, legacy copy, saved, other), size and age, a quota gauge, and a single-object delete the orchestrator refuses for objects a session still uses or that changed since listing. Bulk deletion of old copies stays in the unqueued clean-up-old-s3-session-cach epic, which reuses this delete path. Architecture: `.scratchpad/s3-section/architecture.md`; design: design.md.

## Goals

- G1: agents-web has a Cache section in the orchestrator menu (beside Sessions and Presets) listing every object under the cache prefix with object name, kind (workspace or transcripts), class, size and last modified, filterable by class and searchable by name, paged.
- G2: each object's class is current on every view: `in_use` (with the session slugs), `preset` (with the preset name), `legacy` (old `preset-*` copy, with how many live sessions copied it), `saved` or `other`; the object list itself is at most `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` old (default 900), shows when it was listed, and a Refresh lists again at once.
- G3: a user deletes one object after typing its name; the orchestrator's reconciler refuses an object pinned by any session row (live, starting or discarding) or rewritten since it was listed, and the outcome (done, refused with reason, failed with reason) is shown.
- G4: S3 credentials stay on the reconciler only; the new routes are on the web port only (not the agent or service ports).
- G5: a quota gauge shows bytes and objects against the bucket quota set in agents-helmfile; released and deployed, and proven live by listing the bucket and deleting one disposable object.

## Non-goals

- Bulk or multi-select deletion, and automatic deletion of old copies (the clean-up-old-s3-session-cach epic).
- Overwriting, uploading, downloading or renaming objects from the UI.
- An MCP tool or service-port access for cache management.
- Bucket versioning, lifecycle rules or quota changes.
- Changes to claude-code-wrapper, any-mcp-tatara-plugins or agents-common.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
