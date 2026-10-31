# Housekeeping rules

The user's standing rules for every agent, every harness and every task.

1. **No em dash characters** in any code, comment, commit, message or content of
   any kind. Use a plain hyphen.
2. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the
   user explicitly asks for it.
3. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass, unless the test itself is no longer accurate; then say which test and
   why. Tests make the code repeatable and guard against regressions.
4. **One scratchpad.** Every scratchpad edit lands under `.scratchpad` in the
   workbench root (the main checkout, never a worktree); it is the only
   scratchpad dir (`workbench.py scratchpad` prints it).
5. **One log dir.** Every log lands in the gitignored `.logs` in the workbench
   root (`workbench.py logs` prints it).
