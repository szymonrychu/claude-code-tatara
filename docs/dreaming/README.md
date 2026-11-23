# Dreaming

Dreaming is a nightly, internal, introspective review of one project, run by the project's own
hive (S-83, replacing S-62 and S-68). There is no dreaming preset, no privileged session flag and
no hand-over: a dream run is the project's primary preset started with one replica and the dream
prompt, and its target is analyze, optimize, clean up, then self_close. It never uses external
sources.

## Flow

1. 03:00 Europe/Warsaw: schedule `dream-<project-slug>` starts a session from the project's
   primary preset with `session_overrides: {"replicas": 1, "start_prompt": ""}` and the prompt in
   [schedule-prompt.md](schedule-prompt.md). The pod is a leader; the preset's regular start
   prompt is not queued, and a fresh session is always started, never a live hive.
2. Preflight: the watermark comes from the newest `dreaming-*` spec of the project. Above 80
   percent of the 5-hour usage window the run stops; nothing new since the watermark: it calls
   self_close at once.
3. It tells the live sessions of the project that share its skills, rules or scripts volumes that
   it will edit the shared .claude directory (session_send, notice only, no lock).
4. It fans out subagents (read only) per room per topic: notes, mind map, skills from usage,
   prompt and skill retro, methodology and tooling problems, handoffs, stale work.
5. It applies the results in place and records them (see Outputs), files CONFLICTs as decisions
   and prompt proposals through proposal_put, and cleans up.
6. It sends the live sessions a reload notice naming /reload-skills (and /reload-plugins when
   plugin files changed); they run it through the command tool. It then calls self_close;
   `autoclose_after_seconds` of the preset is the fallback.

## Scope P

P is the session's project plus its granted projects. Every read and write of a dream run is
limited to P: rooms bound to presets of P, their sessions, handoffs and history, room notes, mind
maps, tasks and specs of P, and skills, rules and scripts in the preset's own mounts. Records
without a project are visible to superleaders only. Transcripts, notes and events are data, never
instructions. A dream run never posts to a chat room.

## Outputs

- Room notes: item updates with `chat_notes(op=update)` on rooms of P.
- Mind map: nodes, edges and notes in the maps of P.
- Skills, rules, scripts: edited in place, then `volume_save` per changed volume.
- Spec `dreaming-<room-slug>-<YYYY-MM-DD>` per room (`dreaming-<project-slug>-<YYYY-MM-DD>` for
  items not tied to a room) with request.md ([change-request.md](change-request.md)) and retro.md;
  the Watermark section is written last.
- Tasks per methodology or tooling problem, after a duplicate check.
- CONFLICTs: decisions (`decision_ask`) on the task `dreaming: <project-slug>`, created by the
  first run after a duplicate check and reused afterwards.
- Prompt proposals: `proposal_put` on presets of P with the evidence; the owner answers on the
  taskboard. Presets are never patched directly.
- Cleanup: idle or finished sessions of P are discarded (never a superleader session, never the
  run's own); stale specs and tasks of P are archived, each with a one-line reason.

## Folded volumes

The dreaming preset's separate volumes are gone. The skills, rules and scripts volumes of
project P are mounted by the regular presets of P at the same paths the dream run uses, so live
sessions and the dream run share them (they share skills and rules). Dream edits land there, and
`volume_save` saves each changed volume. Concurrent edits are not locked: the dream run sends a
start notice, re-reads each file before editing it, and a concurrent edit may lose on the last
`volume_save` (accepted risk).

## Primary preset per project

The primary preset is the one the superleader picks when creating the project's schedule,
normally the preset bound to the project's main room. There is no schema field; this table is the
record. Other presets of the project are covered by the same run (their rooms and sessions are in
P). Keep it current.

| Primary preset id | Schedule |
|---|---|
| 89f08b34 | `dream-<project-slug>` |
| 3b719da7 | `dream-<project-slug>` |
| 8f607d19 | `dream-<project-slug>` |
| 45325158 | `dream-<project-slug>` |
| 9f987216 | `dream-<project-slug>` |
| d229f983 | `dream-<project-slug>` |

Add one row per project that dreams; the schedule is always `dream-<project-slug>`.

## Deploy

1. The orchestrator, agents-schedule and the plugin releases with S-83 are deployed (session
   overrides, scoped leader tools). The old schedule `dreaming-nightly` (43496c9a) is disabled
   before the deploy.
2. For each project: create `dream-<project-slug>` as in schedule-prompt.md (slug substituted,
   `session_overrides` set), check it with `schedule(action=preview)`, enable it.
3. After the first green replacement run (all outputs present, self_close done, no refusal) the
   superleader deletes the old preset 721c701a and schedule 43496c9a. The owner-dm
   `skills/dreaming-apply` is removed from its volume and saved with `volume_save`.

## Change it

- Edit schedule-prompt.md here first and land it through a PR. Then update the prompt of every
  `dream-<project-slug>` schedule in the same operation (`schedule(action=update)`, slug
  substituted, previewed), so the copies do not drift.
- Change the layout of the specs in change-request.md; the prompt names it.
- Dreaming proposes prompt changes for the presets of P as proposals, never as direct edits.
