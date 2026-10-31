# Hooks that hold the line

A rule an agent is only told about loses to the "end the turn and report" reflex; these hooks make the
rule mechanical. They ship with the plugin (`.claude-plugin/plugin.json`).

| Hook | Event | Enforces |
|---|---|---|
| `guard-bash.py` | PreToolUse/Bash | denies destructive commands (stash pop, file-scoped restores, force-push without lease, applies, bulk deletes) and any `git commit` whose message holds an em dash (U+2014; `-m`, heredoc, or a `-F`/`--file` file read relative to the event cwd) with an actionable reason |
| `bash-output-filter.py` | PreToolUse/Bash | caps noisy test and log output before it reaches context; the full output is spilled to `.logs/bash-output/` in the main checkout (`$TMPDIR` when there is none) |
| `protect_files.py` | PreToolUse/Edit,Write | blocks edits to secrets, state files, `.git` and encrypted-secret files, and any edit that adds an em dash (U+2014) |
| `format-file.sh` | PostToolUse/Edit,Write | formats the edited file when a formatter for its language is installed |
| `agent-usage-recorder.py` | SubagentStart and SubagentStop | records each subagent's time, model and tokens to `.logs/agents/<agentId>.json` in the main checkout (the usage record below); never blocks |

## The em dash check

protect-files also denies an edit or write whose new content contains an em dash (U+2014): Write
`content`, Edit `new_string`, MultiEdit `edits[].new_string`, NotebookEdit `new_source`, the added
lines of a Codex `apply_patch` envelope, and the same fields under other harnesses' names (Copilot
`file_text` and `new_str`, Antigravity `CodeContent` and `ReplacementContent`). The reason tells the
agent to use a plain hyphen. Removing an em dash is allowed: `old_string` and `-` patch lines are
never read. The path check runs first, and the hook stays fail-closed. Every harness that emits
protect-files (Claude Code, Copilot, Codex, Gemini CLI, Cursor, Antigravity) gets the check, because
the adapter hands the normalised tool input to the same `core.protect_files`.

## The usage record

`agent-usage-recorder.py` keeps one record per subagent at `.logs/agents/<agentId>.json` in the main
checkout, resolved from the event cwd, so an agent working in a worktree still records there.
SubagentStart (spawn and every resume) writes the start time, the agent id and type, the agent
transcript path.
SubagentStop recomputes model, end and tokens (input, cache creation, cache read and output, and
their total) from the whole agent transcript and overwrites the record, keeping the first start, so a
fix round that stops the same agent again grows the one record without double counting.
Internal agents (an empty agent type) write nothing. The recorder makes no decision: on any error it
exits 0 with no output, so it never blocks or slows a stop. It is Claude-only: the Copilot, Codex,
Gemini CLI, Cursor and Antigravity targets keep explicit hook allowlists and none emits it.
