# Housekeeping rules

The user's standing rules for every agent, harness and task.

1. **No em dash characters** in any code, comment, commit, message or other content. Use a plain hyphen.
2. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the user asks.
3. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass unless the test is no longer accurate; then say which and why. Tests guard against regressions (tests guarding no behaviour, B3, may go: flow item 12).
4. **One scratchpad per improvement.** Scratchpad edits land under `.scratchpad/<name>/` in the
   workbench root (the main checkout, never a worktree), `<name>` the improvement's kebab-case
   name (`workbench.py scratchpad <name>` prints it).
5. **One log dir per improvement.** Agent tool logs land in the gitignored `.logs/<name>/` in
   the workbench root (`workbench.py logs <name>` prints it).
6. **The orchestrator never edits.** It dispatches, verifies, and merges and pushes reviewed
   work; it answers for its subagents (flow item 5).
7. **Secrets.** Before changing anything that handles secret values, env, tokens,
   logging, errors, transcripts or RBAC, read `plugins/workbench/rules/secrets-model.md`.
