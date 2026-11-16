# request.md layout

Each night the dreaming lead writes one spec per room with changes,
`dreaming-<room-slug>-<YYYY-MM-DD>`, and its document `request.md` follows this layout. Dreaming applies the
Notes, Skills and Mind map items itself; the owner-dm session keeps the CONFLICTs and Prompt
updates with the skill "dreaming-apply" (apply-skill.md).

Rules for every item:

- One item per change. Never a full rewrite of the notes body.
- Every item has an id (`N1`, `S1`, `M1`, `P1`, `C1` ...) and evidence: message or event id,
  session slug and timestamp, with the trust tier (user-stated, tool-observed, inferred).
- No evidence, no item. Earlier dream output is never evidence.
- When evidence disagrees, the item goes under CONFLICTs, not under its section.
- Plain ASCII; no secrets, tokens or personal data of people outside the room.

## Template

```markdown
# Dreaming request: <room-slug> <YYYY-MM-DD>

Room: <room-slug> (<room_id>), preset <preset name> (<preset id>)
Sessions read: <slug> (<from> - <to>), ...
Previous spec: <dreaming-<room-slug>-<date> or none>

## Notes

Section names follow the room memory rule: Preferences, Requests, Work in progress,
Provided information, Repeatable workflows.

### N1 add | update | remove
- Section: <section>
- Current item: "<exact current text>" (update and remove only)
- New item: "<exact new text>" (add and update only)
- Evidence: <session slug> event <id> <timestamp> (<tier>); ...
- Why: <one line>
- Status: applied | conflict | pending (<reason>)

## Skills

### S1 new | update | remove: <skill-name>
- Room: <room-slug>
- Description: <when to use it, at most 1024 characters>
- Evidence: <the 3 or more sessions where the workflow ran and worked, with ids>
- Why: <one line>
- Status: applied (edited in place at <project>/skills/<name>, saved with backup_save) | pending
- Body (full text, at most 8000 characters):

    <skill body: the steps with their inputs>

## Mind map

### M1 node_create | node_update | edge_create | edge_delete | note_put | link
- Project: <project slug>, map: <map slug>
- Target: <node id or new node title>
- Change: <fields and values, or edge from <node> to <node> with its kind>
- Evidence: <citations>
- Why: <one line>
- Status: applied | pending (<reason>)

## Prompt updates

### P1 <preset name> (<preset id>)
- Field: wrapper.system_append | start_prompt
- Before:

    <exact current lines>

- After:

    <exact new lines>

- Rationale: <the observed failures or successes this fixes>
- Evidence: <citations>

## Tasks filed

- T-<n>: <title> (methodology | tooling), evidence <citations>

## CONFLICTs

### C1 <short subject>
- Side A: "<claim>" (<citation>, <tier>)
- Side B: "<claim>" (<citation>, <tier>)
- Affects: <N/S/M/P item or current note text>
- Question for the owner: <one line, with the options>

## Pending carried over

Items from earlier applied.md files still marked pending, repeated with their old ids.

- <old spec>/<item id>: <one line>

## Watermark

- Room: <room-slug>
- Last processed: <session slug> event <id> at <timestamp>; history record <id> at <timestamp>
- Written: <timestamp of this run>
```

Write the Watermark section last, only after every subagent finished. A partial run leaves it
as the previous night's value and says "partial: <reason>".
