# Schedule "dreaming-nightly": prompt

Schedule fields: name `dreaming-nightly`, cron `0 3 * * *`, timezone `Europe/Warsaw`, preset
"dreaming", enabled after one green run, no then_schedule_ids. The preset's
`reuse_running_agent` stays off so each night is a fresh session.

The prompt is a Jinja template rendered by agents-schedule (sandboxed, StrictUndefined). The
variables it may read are `schedule_name`, `fired_at` (ISO 8601 in the schedule's timezone),
`preset` (the preset id), `now` (ISO 8601, UTC) and `previous_schedule`, `previous_status`,
`previous_session_slug`, `previous_result` (empty unless chained). Check the rendering with
orchestrator_schedule_preview before saving.

Copy the text between the two lines below as the schedule prompt.

---

Dreaming run {{ schedule_name }} for {{ fired_at[:10] }} (fired {{ fired_at }}). Follow your
start prompt: run the probe, read the watermarks of rooms owner-dm and mtg-agent, fan out the
subagents, apply notes, mind map changes and skills, write one spec per room with changes named
dreaming-<room-slug>-{{ fired_at[:10] }}, file tasks, then send the owner-dm session the one
hand-over line and call self_close. If nothing changed since the watermarks, send only the line
with "nothing since watermark". Internal sources only; never post to a chat room.
