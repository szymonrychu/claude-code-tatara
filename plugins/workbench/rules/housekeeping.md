# Housekeeping rules

The user's standing rules for every agent, harness and task.

1. **No em dash characters** in any code, comment, commit, message or content of
   any kind. Use a plain hyphen.
2. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the
   user explicitly asks for it.
3. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass, unless the test itself is no longer accurate; then say which test and
   why. Tests guard against regressions.
4. **One scratchpad per improvement.** Every scratchpad edit lands under
   `.scratchpad/<name>/` in the workbench root (the main checkout, never a
   worktree), `<name>` being the improvement's kebab-case name
   (`workbench.py scratchpad <name>` prints it).
5. **One log dir per improvement.** Every log of every tool the agents run lands
   in the gitignored `.logs/<name>/` in the workbench root
   (`workbench.py logs <name>` prints it).
6. **The orchestrator never edits.** It dispatches, verifies with the repo's test and lint
   commands, and merges and pushes reviewed work; it is accountable for its subagents
   (full rule: "Superpowers flow", item 5).
7. **Secrets.** Before changing anything that handles secret values, env, tokens,
   logging, errors, transcripts or RBAC in any component, read
   `plugins/workbench/rules/secrets-model.md`.
