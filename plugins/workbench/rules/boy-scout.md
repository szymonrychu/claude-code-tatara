# Boy scout rule

Leave the tree better than you found it, and never let someone else's loose
end become a reason your own work is incomplete.

1. **Simplify what you touch.** If code you are already working in can be made
   simpler without changing behaviour, do it. No refactor tour: only the files
   the task already touches.
2. **Functional but uncommitted work gets committed.** Review them, confirm
   they are green, and commit them; do not route around them.
3. **Uncommitted work that blocks full delivery must be cleared, not worked
   around.** Review it, adjust it until lint and tests pass, commit it as its
   own commit, then commit your work on top. Never leave your change in
   a broken tree, and never cite a pre-existing failure as a reason your task is unfinished.

Commit boundaries stay honest: pre-existing work and your work are separate,
adjacent commits with their own messages. Fixing someone's lint does not make
their feature yours or fold it into your commit.

Do not commit work that is broken, half-finished, or that you cannot verify.
"Functional" means you ran the checks and they passed.
