# Dreaming

Dreaming is a nightly, internal, introspective review of two chat rooms (spec S-62, task
T-460; backups and in-place skills: spec S-68). A scheduled session reads what happened since
the last run (chat history, discarded-session history, handoffs, room notes, mind maps,
presets), applies room notes, mind map changes and skills itself, and hands the rest (CONFLICT
decisions and prompt proposals) to the owner-dm session. Dreaming never uses external sources.

## Flow

1. 03:00 Europe/Warsaw: schedule `dreaming-nightly` starts a session from the preset
   "dreaming" with the prompt in [schedule-prompt.md](schedule-prompt.md).
2. The session (the lead, framed by [preset-system-append.md](preset-system-append.md)) runs a
   mandatory probe (one subagent calls one read tool; on refusal it stops and files nothing),
   reads each room's watermark, checks the usage window, and fans out subagents in parallel per
   room and topic. Subagents read the read tools directly; the lead may do small
   lookups itself.
3. It applies what it found in place: room notes with `orchestrator_chat_admin_notes_update`
   (only for rooms whose bound preset project is granted), mind map updates, and skills, rules
   and scripts edited as its own files in the mounted project directories, then
   `orchestrator_backup_save`. It also records a spec `dreaming-<room-slug>-<YYYY-MM-DD>` per
   room (request.md layout: [change-request.md](change-request.md), retro.md) and files tasks
   for methodology and tooling problems.
4. It hands over by one `orchestrator_session_send` to the owner-dm session, found at run time
   (see "Hand-over"). Nothing new since the watermark: the line says so and no spec is made.
5. The owner-dm session runs the skill "dreaming-apply" ([apply-skill.md](apply-skill.md)): it
   keeps only CONFLICT decisions and prompt proposals.
6. The dreaming session ends with `orchestrator_self_close`; `autoclose_after_seconds: 10800`
   is the fallback.

Rooms in scope: `owner-dm` (the owner DM) and `mtg-agent` (the "MTG agent" group). Every other
room is excluded. Sessions are found by the room's preset id from `chat_admin_rooms`, never by
session name or slug.

## Backups and skills (S-68)

- The dreaming preset has backup and restore entries (mode both, workspace root) for
  `<P>/skills`, `<P>/rules` and `<P>/scripts` of each room project P, or prepares those
  repositories with initScripts and commits and pushes. Dreaming edits them normally, as if the
  skills were its own, then calls `orchestrator_backup_save`. No `dreaming/<P>` staging
  directory and no copy step.
- Discarding the dreaming session saves its entries too (saves happen at discard and through
  `orchestrator_backup_save` only; a later save wins and the earlier one stays as a version,
  no merge). Live entries reach the room sessions, which pick the new skills up with a
  reload.
- `orchestrator_backups_copy` is the generic copy of a backup between names (user,
  superleader, retrospective); dreaming's method does not use it.
- Agents of every session call `orchestrator_backup_save` after creating or changing a skill,
  rule or script.

## Hand-over

The owner-dm session is found at run time: `orchestrator_chat_admin_rooms` -> the `owner-dm`
room -> `binding.slug` -> `orchestrator_session_get` (must be live and a superleader) ->
`orchestrator_session_send`. This is the one exception to the no-send rule. Fallback when no
live session exists or the send is refused: a comment on T-460. A refused probe goes in the
same line, and the watermark is kept.

## Retrospective flag

The preset has the `retrospective` flag (not superleader). It grants the read set over
histories, handoffs, chats, presets and backups, `orchestrator_backups_copy`, the scoped room
notes update, mind map, spec and task writes in granted projects, and `orchestrator_self_close`.
Subagents of every session may call read-only orchestrator tools; writes stay with the main
agent. Handoffs are readable through `orchestrator_handoffs_list` / `orchestrator_handoff_get`
and as agents-history records of kind handoff (`history_records`, `kind=handoff`).

Known limit (F17): `max_replicas` stays 1; there is no member-pod read path.

## Run rules

- Size first: a reader's records above 1 MB are split into consecutive ranges and merged in
  order.
- Notes come from `orchestrator_chat_admin_notes_get`; the first-prompt copy is a cross-check.
- The watermark advances only at the end of a fully green run. The first run covers everything
  since 2026-11-08T23:25Z.
- The first morning update after 07:00 Europe/Warsaw carries a digest of the skills applied.

## Decisions

| Id | Decision |
|---|---|
| #723 | Only rooms `owner-dm` and `mtg-agent`, with the priorities listed in preset-system-append.md. |
| Q1 B | A preset "dreaming" copied from "facebook chat", plus the `retrospective` flag; the dream frame is its system_append. |
| 765 | Saves at discard and through `orchestrator_backup_save` only. |
| 766 | Later save wins, the earlier is kept as a version, no merge. |
| 767 | Explicit backup entries only, no built-in entries. |
| 768 | Dreaming mounts the backup and restore paths (for example dedicated for skills), or uses initScripts to prepare repositories, then commits and pushes skills updates; it edits them normally as if skills are its own. |
| 769 | Retrospective flag only (not superleader); `self_close` at the end. |
| 770 | Subagents read directly; no member-pod path; `max_replicas` stays 1. |
| 771 | Handoffs readable through the handoff tools and agents-history handoff records. |
| 774 | Agents call `orchestrator_backup_save` after creating or changing a skill, rule or script. |
| 775 | Notes update only for rooms whose bound preset project is granted. |
| Q4 A | 03:00 Europe/Warsaw every night; the run ends at once when nothing changed since the watermark. |
| Q5 | One spec per room per night, plus tasks for methodology and tooling problems. |
| m1106 | Scope: notes consistency and generalisation, mind map dedup, skills from what worked, prompt and skill retros, methodology and tooling problems, handoffs; very deep, parallel subagents; internal only. |

## Deploy

1. The preset "dreaming" is a copy of "facebook chat" with: `retrospective: true`,
   `session_messaging` as needed for the admin read tools, `wrapper.system_append` from
   preset-system-append.md, `autoclose_after_seconds: 10800`, `reuse_running_agent` off, model
   and effort at the strongest tier, and `backup` entries (workspace, mode both) for the
   `skills`, `rules` and `scripts` paths of each room project.
2. The schedule `dreaming-nightly` is created as in schedule-prompt.md, checked with
   `orchestrator_schedule_preview`. It is re-enabled after one green run.
3. The apply skill lives in the owner-dm project as `<owner-dm project>/skills/dreaming-apply/SKILL.md`
   and is saved with `orchestrator_backup_save`.

## Change it

- Edit the file here first, land it through a PR, then copy the new text to its target: the
  preset system_append through a preset proposal (the preset is privileged), the schedule prompt
  with `orchestrator_schedule_update`, the apply skill into the owner-dm project skills path
  followed by `orchestrator_backup_save`.
- Rooms and their priorities live in preset-system-append.md and apply-skill.md; change both.
- Dreaming proposes prompt changes for the room presets as P items; those reach the user as
  proposals, never as direct edits.
