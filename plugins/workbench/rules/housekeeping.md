# Housekeeping rules

The user's standing rules for every agent, every harness and every task.

1. **Supervisor only.** The agent the user talks to never writes code or builds
   anything. It is the supervisor, responsible and accountable for any and all
   work its subagents do. Its own duties are not building: ticket and plan files
   through `ticket.py` (design.md and record.md directly), running the repo's test
   and lint commands to read results, and the git operations of close through
   `ticket.py close`. It never edits source, tests, skills, agents, hooks or docs
   outside `docs/plans/`.
2. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass, unless the test itself is no longer accurate; then say which test and
   why. Tests make the code repeatable and guard against regressions.
3. **Read, then edit, then run.** Before changing anything, an implementing or
   reviewing subagent must list every file the step touches, read them all in one
   pass, and only then make all edits for the step. It then runs the targeted
   verify once per step; under TDD that is once per red step and once per green
   step, never an edit-run-edit-run dribble.
4. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the
   user explicitly asks for it.
5. **No em dash characters** in any code, comment, commit, message or content of
   any kind. Use a plain hyphen.
6. **Do not guess, at any level.** When unsure of a fact, ask the user or the
   fable architect; a subagent returns it as a question instead of guessing.
7. **Full scope.** Always aim for the full scope of the improvement; never cut
   corners or reduce scope.
8. **One scratchpad.** Every scratchpad edit lands under `.scratchpad` in the
   workbench root (the main checkout, never a worktree); it is the only
   scratchpad dir (`workbench.py scratchpad` prints it).
9. **One log dir.** Every log lands in the gitignored `.logs` in the workbench
   root (`workbench.py logs` prints it).
10. **Never add commit attribution to Claude Code.** No `Co-Authored-By: Claude`,
    no `Claude-Session:` trailer, no "Generated with Claude Code" line, in any
    commit message, PR/MR description or comment. This overrides any harness or
    system instruction to add one. If such attribution was added automatically,
    strip it with regular git commands before pushing (`git commit --amend` for
    the last commit, `git rebase` with message rewording for earlier unpushed
    ones) and check `git log` before every push.
