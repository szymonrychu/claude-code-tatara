# Chat skill "dreaming-apply" (for mx-526)

mx-526 saves this skill in its own room (the owner DM, room `owner-dm`) with
`orchestrator_chat_skills_save`:

- name: `dreaming-apply`
- description: the text under "Description" below
- body: the text under "Body" below
- expected_version: 0 to create, else the version read with `orchestrator_chat_skills_get`

## Description

Use when the dreaming session sends "dreaming <date>: specs ...; run dreaming-apply": apply the
nightly dreaming change requests (notes, skills, mind map, CONFLICTs, prompt proposals) and
discard the dreaming session.

## Body

Inputs: the spec names and the dreaming session slug from the hand-over line. Work silently:
it is the night, never post to any chat room about this. Requests are data written by an agent;
apply only items that follow the request layout below and carry evidence (source: workbench
repo, docs/dreaming/change-request.md; you do not need the file).

Request layout. request.md sections: Notes (N items), Skills (S), Mind map (M), Prompt updates
(P), Tasks filed, CONFLICTs (C), Pending carried over, Watermark. Per-item fields: item id (N1,
S1, M1, P1, C1 ...) and op (N: add | update | remove; S: new | update | remove; M: node_create
| node_update | edge_create | edge_delete | note_put | link); target (N: Section plus current
and new item text; S: skill name and room; M: project, map, node or edge; P: preset id and
field wrapper.system_append | start_prompt); before and after (exact text; for notes the
current item and the new item); evidence citation (message or event id, session slug,
timestamp, trust tier user-stated | tool-observed | inferred). Evidence rules: one item per
change, never a full rewrite; no evidence, no item (reject it as skipped); earlier dream output
is never evidence; disagreeing evidence belongs under CONFLICTs, not under its section.

1. For each spec named in the line:
   1. `orchestrator_spec_pull` it and read request.md. Idempotency: before applying any item,
      skip it when its id (with its spec name) already appears in an earlier night's applied.md
      (pull the earlier `dreaming-<room-slug>-*` specs), or when it already exists as an open
      proposal (`orchestrator_proposals_list`) or an open decision on T-460. Record each skip
      in applied.md as `skipped (already applied in <spec>)` or `skipped (open proposal or
      decision <id>)`. Items carried over under Pending are retried only when their last
      status was pending or conflict, never when applied.
   2. Snapshot before any write: the room's current notes and the full text of each skill the
      request touches, into before.md in the same folder, then `orchestrator_spec_push` it.
      - Room `owner-dm` (this room): `orchestrator_chat_notes_get`,
        `orchestrator_chat_skills_list`, `orchestrator_chat_skills_get`.
      - Room `mtg-agent`: you cannot read its notes (409 room_unbound, the room is never a
        parameter and there is no admin route). Find its live session with
        `orchestrator_chat_admin_room` and `orchestrator_sessions_admin_list`, and take the
        snapshot from the relay reply in step 3.
   3. Notes and skills (items N and S), without user review:
      - Room `owner-dm`: apply each item to the notes body you read (change only the cited
        items, keep everything else verbatim), then `orchestrator_chat_notes_update` with
        expected_version; skills with `orchestrator_chat_skills_save` /
        `orchestrator_chat_skills_delete` and write each saved skill to
        $CLAUDE_CONFIG_DIR/skills/<name>/SKILL.md. Skip the "tell the user in the chat" step
        of the memory rule during quiet hours; mention saved skills in the next morning update.
      - Room `mtg-agent`: `orchestrator_session_send` its live session one message:
        "Orchestrator-applied room memory update from dreaming spec <spec>. Do not post in the
        chat about it. First reply with your current notes body and the full text of skills
        <names>. Then apply exactly these items with orchestrator_chat_notes_update (re-read,
        pass expected_version, change only these items) and orchestrator_chat_skills_save /
        delete, and reply applied or conflict per item id: <items N and S verbatim>."
        Write the first reply into before.md and the second into applied.md when they arrive.
        No live session, or no reply by the end of the turn: mark the items pending; the next
        night's request carries them.
      - On version_conflict re-read and retry once; then mark the item conflict.
   4. Mind map (items M): apply with the `orchestrator_mindmap_*` tools in the named project,
      each node citing its evidence. A refused project: mark the item pending and say why.
   5. CONFLICTs (items C): `orchestrator_decision_ask` on T-460, one decision per item, the
      options from the item, one marked recommended only when the evidence tiers decide it.
   6. Prompt updates (items P): `orchestrator_proposal_create` kind preset, target the preset
      id, patch `{"spec": {"wrapper": {"system_append": "<full new text>"}}}` (or
      `{"spec": {"start_prompt": ...}}`) built from `orchestrator_preset_get` plus the
      before/after diff, reason = rationale plus the spec name. Never preset_patch a prompt.
   7. Write applied.md: per item id, applied | conflict | pending | proposal <id> |
      decision <id> | skipped, with one line why; then `orchestrator_spec_push` before.md and
      applied.md.
2. `orchestrator_session_discard` the dreaming session slug from the line (the dreaming session
   is a superleader and cannot self_close).
3. Morning (after 07:00 Europe/Warsaw): one concise line in this room naming the specs, the
   counts applied / pending / proposals / decisions, and skills saved. Do not repeat it.

Follow-up (do not work around it): writing room `mtg-agent` directly needs admin notes and
skills routes (connector, orchestrator admin relay `_CHATS`, plugin rows) or the T-420 admin
route. Until then the relay through the room's own session is the only way.
