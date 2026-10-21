# Concise orchestrator output

The orchestrator's context is the most expensive thing in a session: every turn
re-reads all of it. After the initial discussion of a task, every update,
notification reply, heartbeat reply and status is VERY short.

- Progress update: one line. `<what moved> - <next> - <decision needed, if any>`.
- Heartbeat or poll result with nothing actionable: no tool call, and no text
  beyond the line itself.
- Never restate what a notification already says. Never paste logs, tables,
  JSON or diffs unless asked; cite a path instead.
- A finished task: what landed, verified how (the one summary line of the real
  output), what is next. Three lines at most.
- Subagent prompts and reports follow the same rule: ask for capped reports
  (a word limit), and read their files rather than their full transcripts.
- Detail only when the user asks for it, or a decision needs it.
