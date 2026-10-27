# interrogate: slash-commands-from-chat (design and plan, 2026-10-27)

Scope: README.md, design.md, tasks/*.md of this epic, against the code they change (claude-code-wrapper,
agents-orchestrator, agents-web, any-mcp-tatara-plugins) and the probes in .scratchpad/probe-slash/.
Panel: A fable, B opus, C sonnet, identical prompt. Lead checks: api/agent.py:412 condition read; claude binary
strings `aliases:["reset","new"]`, `aliases:["continue"]`, `name:"cd"`, `Unknown command: /${Be}. Did you mean`,
`Commands are in the form` confirmed by grep on /usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe.

## Act on

1. Non-superleader to superleader command execution (A, B, C). D7 admits any leader sending to a superleader
   (api/agent.py:412), so with the change a plain worker session runs unframed commands on a superleader. The user
   asked for "user and superleader". Store `kind='command'` only when the sender's session has
   `session_messaging`; otherwise the text stays a framed turn. AC with a worker-to-superleader test.
2. Classification must match Claude Code's own parser (B, critical). D2 types `/`, `/ is root`, `/_x` and names
   over 64 chars as turns; claude runs no model call for them, so no Stop and the session hangs. Mirror the binary:
   name = text up to the first whitespace, empty name is `invalid_command` (claude: "Commands are in the form
   `/command [args]`"), unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap. Fix wrapper-slash-turn-guard
   ac3 and orch-slash-parser ac2. Path-like prose (`/workdir/foo is broken`) must be pinned either way after a probe.
3. Per-session ordering of commands and prose (B, C). Commands write no `last_dispatched_at`, so two commands, or a
   command and later prose, of one session can be claimed concurrently and arrive out of order. Hold a session's later
   messages while one of its command rows is `dispatching`; pin in test_queue_leader_routing.
4. Slot handover at Stop (B, C; A judged it no-hang). The idle runner starts after the awaited onTurnComplete hooks, so
   prose can take the slot before queued commands. Take the slot for queued commands at Stop before any await; AC: a
   POST /turns right after turn_completed gets 409 until the commands drain.
5. Deny list misses aliases and session-moving commands (B, C). Add `reset`, `new` (clear), `continue` (resume),
   `update` (restart), `cd`; match case-insensitively; resolve aliases from claude's table, pin each with a test.
   Review the rest of cmdtable.txt (`background`, `teleport`, `stop`, `session`, `remote-control`, `upgrade`) and
   record each as denied or allowed with the reason.
6. Dialog left open after the ESC budget (C). On `dialog_stuck` or `timeout` with a dialog still on screen, restart
   claude through the existing restart path before releasing the slot; AC.
7. One deadline per command (C). wait_quiet plus _await_completion each spend `timeout`, so the real bound is about
   2x the stated one; use one deadline and pin it.
8. Multi-line slash text and existing callers (C). agents-common runs.py:151 posts `text\n\nmarker`; a preset prompt
   starting with `/` used to run and would now fail `invalid_command`. Strip the ccw marker before classifying and
   accept multi-line args (pasted) up to a cap; test the marker-suffixed case.
9. Hop guard for promoted prompt commands (B, C). A command message stores no `turn_id`, so sends from its promoted
   turn restart at hop 1 and bypass session_message_max_hops. Set messages.turn_id on `command_completed` with
   `result=turn` through a status-guarded update by the single writer.
10. Held-turn interrupt (B). When the held turn continues as a prompt-command turn, `_commands_turn` is not cleared
    (session.py:702-703, 1128-1131), so an interrupt ends the record without ESC. Release the hold through a session
    API; AC that an interrupt on that turn sends ESC.
11. Unknown command with suggestion (B). Claude writes "Unknown command: /x. Did you mean /y?"; pin it in
    wrapper-command-signals so a typo fails fast instead of waiting the full timeout.
12. Kind e2e case placed before the render change (A). The e2e job runs on every PR and agents get
    `client: ["*"]` only in orch-render-client-commands, so the pin PR would be red with 403. Move the e2e case and its
    AC to orch-render-client-commands.
13. AC evidence that already passes today (A): orch-dispatch-commands ac10 grep matches MEMORY.md:41; web-sync-message-kind
    ac3 grep matches the current source pin. Replace with assertions specific to the new state.

## Consider

- D9 "parity with the terminal": claude's docs run some commands immediately even mid-turn (/status, /tasks, /usage),
  so deferral to Stop is only partly parity. Goes to the user with the at-any-moment question.

## Noted

- Not verifiable here, settle by probe in the owning tasks: Stop fires after a promoted prompt-command turn; plugin
  commands fire UserPromptSubmit; local commands never fire UserPromptSubmit.
- Orchestrator Postgres ACs, the contract leg and the kind e2e run only in CI (no Docker here).

## Dismissed

- Allowing /plugin, /add-dir, /permissions: the user asked for any command.
- 409 dead requeue with backoff: parity with today's _map_submit.
- Superleader outcome feedback: not in the requirement; asked at the gate.

Agreement: all three converged on the superleader authz gap; B and C on ordering, the Stop handover race, aliases
and the hop guard; A alone on the e2e placement and weak evidence; B alone on the parser mismatch (verified against
the binary); C alone on multi-line callers, the open dialog and the double timeout.
