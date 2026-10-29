---
title: Decouple S3 session cache from presets
blockers: [hive decoupling, slash commands from chat]
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

Today a session created from a cache-enabled preset without a key gets `preset-<16 hex of sha256(preset id)>`, so every session of a preset shares one workspace archive, and the Claude transcripts sit at `sessions/<slug>`. This epic makes the preset's `cache.key` a Jinja2 template (sandboxed, expressions only), rendered once at session create with the preset name, preset id, session slug and creating service; empty means the default `<preset>-<session>`. One rendered name per session names both S3 objects: `<prefix><name>.tar.zst` (workspace) and `<prefix>sessions/<name>.tar.zst` (transcripts). The reconciler, the only holder of the S3 credentials, copies the objects of every session that existed before the change to its new name (server-side CopyObject, never overwriting, never moving or deleting) and repoints the session, so a session discarded and recreated with the same slug from the same preset restores its workspace and transcripts. agents-web edits the template on a preset and names the effective cache name in the discard dialog. Design: design.md. Blocked by the in-progress epics hive decoupling and slash commands from chat, which change the same orchestrator and web files (README, MEMORY, openapi.json, pyproject.toml, spec.py, the vendored schema).

## Goals

- G1: A preset's `cache.key` is a Jinja2 cache name template; a session created from it stores the rendered name, and an empty template renders the default `<preset>-<session>` that always fits the key rule.
- G2: Templates are checked at preset save (422 on an unsafe or invalid template, or a trial render that breaks the key rule) and rendered in a restricted Jinja2 sandbox; a raw-spec key is rendered with the session variables only.
- G3: One cache name per session names both its workspace archive and its Claude transcripts object, pinned in `status.cache` (`key`, `object`, `sessions_object`) at the first restore.
- G4: No preset-id-derived key remains: `default_cache_key`, the reserved `preset-` prefix and the copy rule are removed, and presets that stored their own derived key get the default.
- G5: The caches of sessions that existed before this epic (workspace and transcripts) are copied server-side to their new names, never moved, deleted or overwritten, and each session is repointed so its next save and a session recreated from the same preset with the same slug use the new name.
- G6: agents-web edits the cache name template on a preset (the default shown from `/meta`) and the discard dialog names the effective cache name and when it is restored.

## Non-goals

- The S3 cache management section in agents-web and any orchestrator list, inspect or delete API over cache objects (sibling epic s3-cache-management-section).
- Deleting, moving or expiring old `preset-*` or `sessions/<slug>` objects, bucket lifecycle rules, or a quota change.
- A per-session template override at session create or in the new session dialog.
- Changes to agents-helmfile, agents-webhook, agents-schedule, agents-matrix-connector, agents-common or claude-code-wrapper.
- Retiring the migration code once no pre-epic session remains.
- Cache name uniqueness enforcement or locking (shared names keep last-writer-wins, design D4 of workspace-s3-cache).
- The live-session transcript backup trigger (cct2 queue item 4).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
