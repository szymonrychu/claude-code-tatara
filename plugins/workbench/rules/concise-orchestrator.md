# Concise orchestrator output

The orchestrator's context is the costliest thing in a session: every turn re-reads it.
After the initial discussion of a task, every update, reply and status is VERY short.

- Progress update: one line. `<what moved> - <next> - <decision needed, if any>`.
- Poll with nothing actionable: no tool call, no text beyond the line itself.
- Never restate a notification. Never paste logs, tables, JSON or diffs unless asked; cite a path.
- A finished task: what landed, verified how (the real output's summary line), what is next.
  Three lines at most.
- Subagent prompts and reports follow the same rule: capped reports (a word limit); read their
  files, not their transcripts.
- Detail only when the user asks or a decision needs it.
