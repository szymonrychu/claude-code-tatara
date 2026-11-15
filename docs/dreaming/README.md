# Dreaming

Dreaming is a nightly, internal, introspective review of two chat rooms (spec S-62, task
T-460). A scheduled session reads what happened since the last run (chat history, session
events, handoffs, room notes and skills, mind maps, presets) and writes change requests. The
orchestrator session mx-526 applies them. Dreaming never uses external sources and never edits
anything itself.

## Flow

1. 03:00 Europe/Warsaw: schedule `dreaming-nightly` starts a session from the preset
   "dreaming" with the prompt in [schedule-prompt.md](schedule-prompt.md).
2. The session (the lead, framed by [preset-system-append.md](preset-system-append.md)) reads
   the watermark of each room from the previous night's spec, checks the usage window, and
   fans out subagents in parallel per room and topic. It never reads history itself.
3. Per room with changes it creates spec `dreaming-<room-slug>-<YYYY-MM-DD>` with request.md
   (layout: [change-request.md](change-request.md)) and retro.md, and files tasks for
   methodology and tooling problems.
4. It sends mx-526 one line naming the specs and its own slug. Nothing new since the watermark:
   the line says so and no spec is made.
5. mx-526 runs the chat skill "dreaming-apply" ([apply-skill.md](apply-skill.md)): snapshot
   to before.md, apply notes, skills and mind map changes, raise CONFLICTs as decisions, turn
   prompt updates into preset proposals, record applied.md, push, and discard the dreaming
   session.

Rooms in scope: `owner-dm` (the owner DM, preset "facebook chat", session mx-526) and
`mtg-agent` (the "MTG agent" group, preset c3b66e54 mtg-research-group). Every other room is
excluded.

## Decisions (T-460)

| Id | Decision |
|---|---|
| #723 | Only rooms `owner-dm` and `mtg-agent`, with the priorities listed in preset-system-append.md. |
| Q1 B | A new preset "dreaming", copied from "facebook chat" by the user, session_messaging on; the dream frame is its system_append. |
| Q2 | Dreaming sends change requests through specs; the orchestrator (mx-526) applies them. Dreaming never edits rooms, notes, skills, mind maps or presets. |
| Q3 C | Notes, mind map and skills are applied by mx-526 without user review; preset prompt changes go through proposal_create for the user. |
| Q4 A | 03:00 Europe/Warsaw every night, no gating; the run ends at once when nothing changed since the watermark. |
| Q5 | One spec per room per night, plus tasks for methodology and tooling problems. |
| Q6 A | History from live sessions' events and messages plus history_* for discarded sessions, until T-420. |
| Q7 B | Live from the first night, no dry run. |
| m1106 | Scope: notes consistency and generalisation, mind map dedup, skills from what worked, prompt and skill retros, methodology and tooling problems, handoffs; very deep, parallel subagents; internal only. |

## Deploy

1. The user copies preset "facebook chat" to "dreaming" (web UI, or `orchestrator_preset_copy`
   by a superleader followed by the user's edit) and sets:
   - `session_messaging: true` (human-only flag): the session needs the admin read tools;
   - `superleader_manageable: true`, so mx-526 can create the schedule and discard the run;
   - `wrapper.system_append`: the text of preset-system-append.md;
   - `autoclose_after_seconds: 10800`: the fallback close, since a superleader cannot
     self_close;
   - `reuse_running_agent` off; model and effort at the strongest tier.
2. mx-526 (or the user in the web UI) creates schedule `dreaming-nightly` as described in
   schedule-prompt.md, after checking it with `orchestrator_schedule_preview`.
3. mx-526 saves the chat skill `dreaming-apply` with `orchestrator_chat_skills_save` from
   apply-skill.md.
4. The first night is live (Q7 B). The checks of the first runs are todo items on T-460.

## Change it

- Edit the file here first, land it through a PR, then copy the new text to its target: the
  preset system_append through a preset proposal (the preset is privileged), the schedule prompt
  with `orchestrator_schedule_update`, the apply skill with `orchestrator_chat_skills_save`.
- Rooms and their priorities live in preset-system-append.md and apply-skill.md; change both.
- Dreaming itself proposes prompt changes for the room presets as P items; those reach the user
  as proposals, never as direct edits.

## Planned move to T-420

When `orchestrator_chat_history` (T-420, S-60) exists, the history topic subagents read room
history with it instead of session_events, session_messages and history_*. When an admin route
for room notes and skills exists, mx-526 writes room `mtg-agent` directly instead of relaying
through that room's session. Both are text changes in preset-system-append.md and
apply-skill.md.
