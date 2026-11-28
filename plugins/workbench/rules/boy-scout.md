# Boy scout rule

Leave the tree better than you found it; someone else's loose end never excuses incomplete work.

1. **Simplify what you touch.** If code you are already working in can be made
   simpler without changing behaviour, do it. No refactor tour: only files the task touches.
2. **Functional but uncommitted work gets committed.** Review, confirm green, commit; do not route around.
3. **Uncommitted work that blocks full delivery must be cleared, not worked
   around.** Review it, adjust it until lint and tests pass, commit it on its
   own, then commit your work on top. Never leave your change in a broken tree
   or cite a pre-existing failure as a reason your task is unfinished.

Commit boundaries stay honest: pre-existing work and your work are separate, adjacent
commits with their own messages. Fixing someone's lint does not fold their feature into yours.

Do not commit work that is broken, half-finished or unverifiable.
"Functional" means you ran the checks and they passed.
