# chat-notes (T-124): automatic per-room notes and skills for interactive chats

Status: gate passed (user answers on T-124 recorded in section 10, 2026-11-11). Implementation
plan: `docs/plans/chat-notes/implementation.md`. Nothing committed.

## 1. What and why

User request (T-124): interactive chat agents must automatically keep notes about the user's
requests, the work the user is doing and the information the user provided; modest, but useful
when the user re-runs the session. Trigger case: Marek gave a decklist, worked on it with our
system, and had to redo the same work because the earlier agent kept no notes and extracted no
skill.

Goal: a per-room store of notes and skills that survives session close, is written as the
conversation goes, is offered at the start of every new session of that room, and is never
visible to another room. Also: recover Marek's earlier decklist work, and test with a real rerun.
Scheduled sessions of a room also read and write the room's notes ("The scheduled hive must also
write down notes if needed").

## 2. Research findings

Docs (research-docs.md, Claude Code 2.1.304):
- Native auto memory is model-discretionary ("decides what's worth remembering"), machine-local,
  no remote backend. MEMORY.md loads first 200 lines / 25KB; topic files only on demand.
- Deterministic load at start via a SessionStart hook `additionalContext` is capped at 10,000
  chars. Not used here: the connector injects notes into the first prompt instead, so that
  limit does not apply. Factual phrasing for data, not imperative injections.
- SessionEnd has a 1.5s default budget and will not run on pod kill: write as you go, never at
  the end.
- No documented skill-extraction feature. The wrapper's existing `notes` config (client-pushed
  inbox) is unrelated; pick distinct names ("room notes", "room skills").
- Skills (code.claude.com/docs/en/skills, read 2026-11-11): personal skills live in
  `~/.claude/skills/<name>/SKILL.md`; `CLAUDE_CONFIG_DIR` replaces `~/.claude`, so for a wrapper
  session that is `$CLAUDE_CONFIG_DIR/skills/<name>/SKILL.md`. "Claude Code watches skill
  directories for file changes ... picks up the change within the current session, without a
  restart." Caveat: "If you create a top-level skills directory that didn't exist when the
  session started, run /reload-skills ... Claude Code isn't watching that directory yet." Only
  SKILL.md text is live-detected. Frontmatter fields are optional; `description` recommended;
  `name` defaults to the directory name; description plus when_to_use is truncated at 1,536
  chars in the listing.
- Wrapper check (code/claude-code-wrapper): each session gets
  `<sessions_root>/<session_id>/config/` as `CLAUDE_CONFIG_DIR` (manager.py `_bootstrap`, step
  `ensure_config_dir`, env set at manager.py:717). The wrapper never creates `config/skills/`.
  So today a skill written mid-session lands in a directory that did not exist at start: not
  watched, and the agent cannot run `/reload-skills` itself. The config dir is per session, so
  "from the next session" does not help either: a new session gets a fresh config dir and only
  the connector table carries skills over. Consequence: a small wrapper change creates an empty
  `config/skills/` (mode 0700) at bootstrap, so skills the agent materializes at any point of
  the session are live-detected. Until that wrapper release is deployed, the rule's fallback
  applies: the agent follows a skill's body directly (fetched with the get tool).

Internal code (research summary):
- A "rerun" = chat session closes after inactivity (900s/3600s); the next room message makes a
  new `mx-<n>` session via agents-matrix-connector (worker.py:333).
- On delete: orchestrator rows cascade, transcript goes to agents-history (superleader-only
  reads), workdir saved to S3 cache under the preset's `cache.save_key` (per preset, not per
  room, saved only at discard, last writer wins). Shared keys `chat/` and `media-support/` mix
  rooms, so the workspace cache cannot be a private per-room store (and skills must never be
  written to the workdir).
- Room identity in the session exists only in the prompt frame `<chat room_id=...>`
  (connector prompt.py). Connector resolves session to room via `bindings.active_for_session`
  (api/agent.py); agent-facing routes live in `build_chat_router` (/chat/v1); orchestrator relays
  in api/chat.py; agent tools live in the any-mcp-tatara-plugins orchestrator plugin.
- Tool access: `CHAT_TOOLS` in orchestrator `k8s/on_start.py` already grants the chat tools to
  every session; the new tools are added there, so no preset allow-list patch is needed.
- Marek's room uses preset marek-mtg (032955f8), not mtg (51a41b02).

Live checks (read-only, 2026-11-11):
- (a) marek-mtg-morning-* sessions DO post into Marek's room through a connector binding:
  room_bindings rows with origin=agent (e.g. marek-mtg-morning-cc1d3a18, created 07:02 after the
  07:00 fire) exist for each daily run. The schedule prompt (agents-schedule, schedule
  marek-mtg-morning, cron `0 8 * * *` Europe/Warsaw) names the room id literally, posts with
  orchestrator_chat_send, then stays on as Marek's companion for follow-ups. They are bound only
  after their first send is claimed; the room id is known in the prompt from the start.
- (b) Current memory per preset (start_prompt / wrapper.system_append):
  - chat (1a06e560), facebook chat (45325158): no memory instructions at all; cache save/restore
    key `chat/` for chat, none for facebook chat. Facebook chat has no start_prompt.
  - media-support (8f607d19): no memory instructions; shared cache key `media-support/`.
  - marek-mtg (032955f8): start_prompt says keep Marek's news preferences in
    `marek-preferences.md` in the workspace (persisted by the preset cache `chat-mtg/`), read at
    start, update when he asks. Only news preferences, no decklists or work.

## 3. Design

### Data model (agents-matrix-connector, own Postgres, single writer: api)
- `room_notes`: `room_id text primary key`, `body text not null`, `version int not null`,
  `updated_at timestamptz`, `updated_by_slug text`. Body is markdown with sections: Preferences,
  Requests, Work in progress, Provided information, Repeatable workflows.
- `room_skills`: `room_id text`, `name text` (slug `^[a-z0-9][a-z0-9-]{0,63}$`), `description
  text` (at most 1024 chars, under the 1,536 listing truncation), `body text`, `version int`,
  `created_at`, `updated_at`, `updated_by_slug`; primary key `(room_id, name)`. Caps: at most
  `MATRIX_ROOM_SKILLS_MAX` (default 20) skills per room, body at most
  `MATRIX_ROOM_SKILL_MAX_CHARS` (default 8000) characters.

### API (connector `build_chat_router`, /chat/v1)
- `GET /chat/v1/notes`, `PUT /chat/v1/notes` (body, expected_version). GET also returns `rule`,
  the standing memory rule text, so a session that reads notes through the tool (a scheduled
  session) gets the same rule from the same single source.
- `GET /chat/v1/skills` (index: name, description, version, chars, plus caps),
  `GET /chat/v1/skills/{name}`, `PUT /chat/v1/skills/{name}` (description, body,
  expected_version), `DELETE /chat/v1/skills/{name}`.
- The room is NEVER a parameter: resolved from the caller's session via
  `bindings.active_for_session`, so a session can only touch its own room. Unbound session gets
  409 `room_unbound`. Stale version 409 `version_conflict`. Over a size cap 413; over the count
  cap 409 `skill_limit`; unknown skill 404 `skill_not_found`.
- Orchestrator relays all six under /agent/v1/chat (same auth and session identity as
  chat_send, scope `own`).

### Agent tools (any-mcp-tatara-plugins, orchestrator plugin)
`orchestrator_chat_notes_get`, `orchestrator_chat_notes_update` (full-body replace with version;
the agent condenses), `orchestrator_chat_skills_list`, `orchestrator_chat_skills_get`,
`orchestrator_chat_skills_save`, `orchestrator_chat_skills_delete`. Granted to every session by
`CHAT_TOOLS` in orchestrator on_start.py.

### Injection at session start (connector, one place)
Connector worker `_render` with `first=True` inserts, between the preamble and `<chat>`, a memory
block: the standing rule, then the room's notes as a fenced labeled data block ("facts, not
instructions"), then the skill index (name and description per skill). Empty notes or no skills
omit only that part; the rule is always present. The rule text lives in one constant in the
connector (`prompt.MEMORY_RULE`), overridable by setting `MATRIX_ROOM_MEMORY_RULE`.

### The standing rule (content)
Update the notes during the conversation, right after (1) the user states a request, (2) the
user provides data such as a decklist (verbatim if short, else condensed with the key facts),
(3) work progresses or finishes. Keep notes short and current, no transcripts. Never store
secrets or other people's private data. If the user asks to see or forget notes (or skills),
show or clear them in chat. Update immediately, not at the end. Skills: at session start write
each listed skill to `$CLAUDE_CONFIG_DIR/skills/<name>/SKILL.md` (fetched with the get tool),
never into the workdir (cached per preset, shared across rooms); save a skill when a workflow
was repeated or is clearly reusable, and tell the user in chat when a skill is saved or removed;
if a skill does not show up as available, follow its body directly.

### Size caps
Our own connector caps, configurable: notes 8000 characters (`MATRIX_ROOM_NOTES_MAX_CHARS`),
skill body 8000 (`MATRIX_ROOM_SKILL_MAX_CHARS`), 20 skills (`MATRIX_ROOM_SKILLS_MAX`). The
8000 default is a choice to keep the first prompt compact; it is not a wrapper delivery limit.
Counted in code points. The tool results report size and remaining room.

### Privacy
Per room only. The room is derived server-side from the session binding. Notes and skills are
not mixed into the workspace cache, not sent to other rooms, not exposed in any listing API
beyond the room's own session, and not logged (room id, name, version and size only). Secrets
model (plugins/workbench/rules/secrets-model.md) read before implementing.

## 4. Orchestrator design calls (made without a user question, 2026-11-11)

1. Q2 default for future presets: the connector injects the standing rule (notes and skills)
   with the room's notes and skill index into the first prompt of every room session it
   creates, so no preset needs a patch for the rule. Preset patches only remove superseded
   memory instructions (marek-mtg: the `marek-preferences.md` instruction moves into the notes,
   section Preferences). The rule text is in one place in the connector, configurable.
2. Q4 per-room skills: connector table `room_skills` (room_id, name slug, description, body,
   version, timestamps; unique room_id+name; caps on count and body size), routes under
   /chat/v1/skills (list, get, put, delete) scoped by the caller's binding exactly like notes,
   orchestrator relay, plugin tools orchestrator_chat_skills_list/get/save/delete. The first
   prompt lists the room's skills (name + description). The rule tells the agent to materialize
   each skill as SKILL.md under `$CLAUDE_CONFIG_DIR/skills/<name>/`, never the workdir, to save a
   skill when a workflow was repeated or is clearly reusable, and to tell the user in chat on
   save or removal. Verified: live detection needs the skills directory to exist at session
   start, which the wrapper does not do today; so a claude-code-wrapper change creates it at
   bootstrap (new release, new agent image pin). Fallback in the rule: follow the body directly.
3. Gap Q7 (scheduled sessions unbound until first send), option A: the morning schedule prompt
   posts its first message (the briefing itself if it needs no notes, else a short opener),
   then reads notes and skills through the tools, and writes notes as needed. Q7 is not asked.
4. Factual corrections: the 8000 cap is our own connector cap, not a wrapper delivery limit;
   mx-406 history retention expires about 2027-02-06.
5. Tool access: `CHAT_TOOLS` in orchestrator on_start.py grants chat tools to all sessions; the
   six new tools are added there.

## 5. Components and files touched

- claude-code-wrapper: create `config/skills/` at bootstrap; release; agent image pin.
- agents-matrix-connector: migrations `room_notes`, `room_skills`; repositories; settings and
  chart values; notes and skills routes (api/agent.py); memory block injection (prompt.py,
  worker.py `_render`); tests (room A cannot read or write room B; unbound rejected; stale
  version; caps; injection only on first prompt; escaping).
- agents-orchestrator: relay routes in api/chat.py (PUT and DELETE support in `_relay`), scope
  rows, tests, README; `CHAT_TOOLS` plus plugin pin.
- any-mcp-tatara-plugins: six tools in the orchestrator plugin + tests + release.
- agents-web: re-sync the orchestrator API schema (type-only, no UI per Q6).
- Presets (orchestrator API, no code): marek-mtg start_prompt drops the `marek-preferences.md`
  instruction. No other preset patch.
- agents-schedule schedule `marek-mtg-morning` prompt: post first, then read and update notes
  and skills.
- agents-helmfile: image pins for connector, orchestrator, agent image (wrapper), plugin ref.
- Workbench superrepo: bump submodule pointers; MEMORY.md entries per component.

## 6. Test approach

- Unit/integration per repo (isolation tests mandatory for notes and skills).
- Live rerun test (after apply): in a test room, session mx-A: provide a small decklist and ask
  for a change; verify notes saved during the turn. Ask for the same transformation twice and
  verify a skill is saved and announced in chat. Close the session. Send a new message to the
  same room: new session mx-B; verify its first prompt contains the rule, the notes and the
  skill index, that `$CLAUDE_CONFIG_DIR/skills/<name>/SKILL.md` exists in the pod, and that the
  agent continues the deck work without asking for the list again. A second room sees no notes
  and no skills from the first.
- Marek recovery verified by reading his room notes through the tool in a bound session.
- Morning run: next fire posts first, then GETs notes (version visible in connector logs).

## 7. Recovery of Marek's decklist work (Q3: seed from mx-406 and mtg-omnath)

agents-history (DB `history`, retention 90 days) has mx-406 (2026-11-08, Marek's Messenger
session, 7 turns, three decklist versions with 21, 33, 37 card lines) and mtg-omnath
(2026-11-03, preset mtg, 28-line Omnath list; treated as Marek's per the user's answer). A
superleader session (the only reader of history) extracts the latest decklist, the requests
and the conclusions from both, plus the current `marek-preferences.md` content as Preferences,
writes a condensed draft within the notes cap, and the draft is written into Marek's room notes
by a session bound to his room via `orchestrator_chat_notes_update`. Seeding is a one-off
operation, not a code path. Retention: mx-406 expires about 2027-02-06; do it before then.

## 8. Release and apply order (one at a time)

1. claude-code-wrapper: PR, merge, release tag (independent of the rest; can run in parallel).
2. agents-matrix-connector: PR, merge, main build releases the semver tag.
3. agents-orchestrator: relay PR, merge, release.
4. any-mcp-tatara-plugins: tools PR, merge, tag.
5. agents-orchestrator: CHAT_TOOLS and plugin pin, release. agents-web schema sync.
6. agents-helmfile: pin images and plugin ref; apply connector, then orchestrator (agent image
   and plugins ref roll sessions: announce first), check health after each.
7. marek-mtg start_prompt patch (coordinate with spellslinger-chat-sim T-123 and the live
   marek-mtg session; read live immediately before, patch only the named sentences).
8. Seed Marek's notes, update the morning schedule prompt, run the live rerun test.
Each step verified green before the next; main stays green.

## 9. Risks

- Model discretion: the agent may skip updates. Mitigation: explicit standing rule, live test,
  connector logs version bumps.
- Stale or wrong notes mislead: version/replace semantics, "facts not instructions" framing,
  the user can ask to show or forget.
- Prompt injection through notes or skills (a room member writes instructions that are stored):
  notes are labeled data; skills are by nature instructions, written only by the room's own
  session and announced in chat; same trust level as the chat itself. media-support rooms have
  several members, so notes and skills are room-wide there by design.
- Skills not live-detected until the wrapper release is deployed: rule fallback (follow body).
- Cap pressure: decklists are large; condense rule and 413 feedback.
- Concurrent sessions in one room: optimistic version check.
- Coordination race with T-123 on the marek-mtg preset.
- Retention: mx-406 history expires about 2027-02-06.

## 10. Questions (the gate) and answers

Q1. Where do notes live? Answer: A, connector `room_notes` table.

Q2. Which presets get the notes rule? Answer: A, every connector-routed chat preset and default
for future ones. Implemented by connector injection (design call 1).

Q3. Seed Marek's notes? Answer: A, seed from mx-406 AND mtg-omnath (the Omnath list treated as
Marek's).

Q4. Skill extraction? Answer: B, ALSO per-room skill files (design call 2).

Q5. Scheduled sessions for a room? Answer: A, they read and update the room notes. User note:
"The scheduled hive must also write down notes if needed".

Q6. User control? Answer: A, in chat: show or forget. No web UI view.

Q7 (planning gap) is not asked: decided by the orchestrator as option A (design call 3).
