# Hooks that hold the line

Read from `start-development`. A rule an agent is only told about loses to the
"end the turn and report" reflex; these hooks make the rule mechanical. Both
ship with the plugin (`.claude-plugin/plugin.json`) and fire only in agent
worktrees - `<configdir>/worktrees/<name>` from `worktree-create` (task trees and
epic integration trees alike) and the legacy `.worktrees/<branch>/<repo>` from `git-worktrees-create`. The main checkout
belongs to the human and is never blocked.

## The commit guard

`hooks/subagent-commit-guard.py`, on SubagentStop: a subagent cannot end its
turn in a worktree holding uncommitted work. Five agents once ended their turn
"waiting on the background run" with 11 to 118 dirty files and zero commits;
the guard sends the agent back to run its check, commit what passes, and only
then stop.

## The verification-freshness guard

`hooks/verify-recorder.py`, on PostToolUse and PostToolUseFailure, records the
last test or lint run in an agent worktree - the command, the HEAD it ran on,
whether the tree was dirty, whether it passed - to
`<git dir>/workbench-verify.json`. The SubagentStop guard reads that record, so
a subagent cannot end a turn in a worktree whose last test run was not on its
HEAD. A run on an older HEAD (the stale green of a docs-only or test-only
commit made after the run), on a dirty tree, or a run that failed sends the
agent back to re-run that command on what it committed. A worktree with no
recorded run is left to the independent verifier in `workbench:plan-execute`.

## Both guards fire once

A payload with `stop_hook_active` set means the agent already got the message,
and the turn is allowed to end, so nothing can wedge. The independent verifier
still runs the task's `verify` on the committed HEAD afterwards; the hooks
catch the agent before it reports, the verifier decides what is believed.

## Inside Workflow subagents

Do the plugin hooks fire inside Workflow subagents? PreToolUse does. The
round-2 run `wf_e7529755-1fb` (2026-10-11) shows `guard-bash` blocking
`git stash pop -q` and `git checkout b5d065e -- ...` inside Workflow
implementer transcripts. Measured with `hook-evidence.py` on that run's
transcript directory:

```
15  block: guard-bash:
11  block: last verification ran on
workbench hooks seen: guard-bash, freshness-guard
```

A hook that prints nothing on allow leaves no `hook_success` record, so silence
proves nothing. PostToolUse and SubagentStop are proven by the probe, not by
absence.

Probe procedure:

1. Create a throwaway worktree with `worktree-create`.
2. Run `Workflow({scriptPath: '${CLAUDE_PLUGIN_ROOT}/workflows/hook-probe.js', args: {worktree: <path>}})`.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hook-evidence.py <that run's transcript dir>`.
4. Remove the worktree with `git worktree remove`.

What the result means:

- Recorder found (`recordFound`): PostToolUse fires, so the freshness record is written.
- Stop guard saw a block (`sawBlock`): SubagentStop fires, so the commit guard and freshness guard hold.
- Agent type resolved: plugin agent names such as `workbench:verifier` work as `agentType`.

Whichever way the probe comes out, the independent verifier in
`workbench:plan-execute` is the net: it re-runs each task's `verify` on the
committed HEAD, so a hook that does not fire costs a round, not a false green.
