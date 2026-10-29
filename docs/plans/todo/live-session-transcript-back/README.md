---
title: Live session transcript backup
blockers: [Decouple S3 session cache from presets]
stage: build
owner: ""
repos: [agents-orchestrator, agents-web, agents-helmfile]
created: 2026-10-29
---

# Live session transcript backup

## Project brief

What: The reconciler periodically backs up each live session's Claude transcripts to its S3 transcripts object, not only at discard.
How: A per-session live backup step in the reconciler with its own status record and Job name, reusing the cache save Job and the decouple epic's pinned transcripts object; archive reads tolerate live files; API and discard dialog show the latest backup.
Why: mx-34 #234: 'The user lost sessions in the incident, so a live backup is worth having.' (cct2 queue item 4)

## Description

Request (mx-34 #234, 2026-10-28, relaying the user's priorities): "The live-session backup trigger: yes, take it after the paste-.env bug, as a small start-development epic. The user lost sessions in the incident, so a live backup is worth having." and "The ingester row stuck at status='sent' after its turn failed: file it as a small bug inside that same backup epic, no separate queue slot." Origin (mx-34 #232): "there's no backup trigger for a live session (last_transcripts_backup=null)".

Today the orchestrator writes a session's Claude transcripts to S3 only when the session is discarded (`reconciler/loop.py:_discard`, one-shot `sessions_save`), so a live session has no off-cluster copy: claude-code-tatara had none during the 2026-10-28 incident. The transcripts live on the session PVC, which survives pod rolls but not a lost volume or a discard that fails before its save. This epic adds a periodic live backup run by the reconciler: for each converged live session whose conversation changed since its last backup, a backup Job tars the transcripts from the ReadWriteMany PVC beside the running pods and overwrites the session's transcripts object, the same object the discard save writes and a recreated session restores. The discard save stays the final word. It builds on decouple-s3-session-cache-fr (per-session cache names, the pinned `status.cache.sessions_object` and the copy migration); the sent-row item was investigated and is not an orchestrator defect (`.scratchpad/live-backup/sent-row-root-cause.md`), so it is closed by a gate question, not a task. Design: design.md.

## Goals

- G1: every converged live session whose conversation changed since its last backup gets its Claude transcripts saved to its S3 transcripts object at least every `ORCH_SESSIONS_BACKUP_INTERVAL_SECONDS` (default 1800), by a reconciler-run Job, without stopping or pausing its pods.
- G2: a live backup never corrupts or blocks the discard: a running backup Job is removed before the discard's final save, the final save is never skipped because a live backup exists, and a failed or partial live backup leaves the previous object intact.
- G3: a live backup taken while files are appended or atomically replaced succeeds and restores into a session that resumes (no torn final JSONL line, no failure on a replaced file).
- G4: the API's `last_transcripts_backup` and the discard dialog show the latest successful backup, live or final, and the live backup state is visible in `status.cache`.
- G5: released and deployed (orchestrator image, web image, helmfile pins), and proven live: a running session's transcripts object appears in S3 with a recent `last_transcripts_backup`.

## Non-goals

- Live backup of the workspace archive (workdir): its objects are large and may be shared across sessions; the workspace keeps its discard-time save.
- Versioned or timestamped backup objects, retention or lifecycle rules; one object per cache name, overwritten.
- An on-demand "back up now" button, API route or MCP tool.
- Backups gated before pod rolls (the PVC survives rolls).
- A new message status or any change to message/turn linking (the sent-row item is closed as by design).
- Changes to claude-code-wrapper, any-mcp-tatara-plugins or agents-common.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
