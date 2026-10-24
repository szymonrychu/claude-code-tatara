# Hooks that hold the line

Read from `start-development`. A rule an agent is only told about loses to the "end the turn and
report" reflex; these hooks make the rule mechanical. They ship with the plugin
(`.claude-plugin/plugin.json`).

| Hook | Event | Enforces |
|---|---|---|
| `guard-bash.py` | PreToolUse/Bash | denies destructive commands (stash pop, file-scoped restores, force-push without lease, applies, bulk deletes) with an actionable reason |
| `bash-output-filter.py` | PreToolUse/Bash | caps noisy test and log output before it reaches context |
| `protect_files.py` | PreToolUse/Edit,Write | blocks edits to secrets, state files, `.git` and encrypted-secret files |
| `format-file.sh` | PostToolUse/Edit,Write | formats the edited file when a formatter for its language is installed |
| `verify-recorder.py` | PostToolUse and PostToolUseFailure/Bash | records each test or lint run in an agent worktree |
| `subagent-commit-guard.py` | SubagentStop | the commit guard and the verification-freshness guard below |

The two SubagentStop guards fire only in agent worktrees - `<configdir>/worktrees/<name>` from
`worktree-create` (epic integration trees) and the legacy `.worktrees/<branch>/<repo>` from
`git-worktrees-create`. The main checkout belongs to the human and is never blocked.

## The commit guard

A subagent cannot end its turn in a worktree holding uncommitted work. Agents once ended their turn
"waiting on the background run" with 11 to 118 dirty files and zero commits; the guard sends the agent
back to run its check, commit what passes, and only then stop.

## The verification-freshness guard

`verify-recorder.py` writes the last test or lint run in an agent worktree - the command, the HEAD it
ran on, whether the tree was dirty, whether it passed - to `<git dir>/workbench-verify.json`. The
SubagentStop guard reads it, so a subagent cannot end a turn in a worktree whose last test run was not
on its HEAD. A run on an older HEAD (the stale green of a docs-only or test-only commit made after the
run), on a dirty tree, or a run that failed sends the agent back to re-run that command on what it
committed. A worktree with no recorded run is left to the reviewer, who runs the task's `verify` on HEAD.

## Both guards fire once

A payload with `stop_hook_active` set means the agent already got the message, and the turn is allowed
to end, so nothing can wedge. The hooks catch the agent before it reports; the reviewer, who did not
write the code, decides what is believed by running the task's `verify` on the committed HEAD.
