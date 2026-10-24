# <Topic> record

## Asked

What was asked, from the epic README's project brief and goals, in 2-4 lines.

## Shipped

What shipped and the epic review verdict, in 2-4 lines; the MR or PR URLs and the deploy outcome in component mode.

## Tasks

One row per task file: task, status, verified head, review rounds, verification tail (the summary line). Status and verified head from the task file, rounds and tail from the orchestrator's notes; a task with no verified head is `unverified`, whatever its status says.

## Rulings

One entry per escalation judged, finding dropped or gap placed: what, why, and the cost if the call was wrong; "none" if none.

## Discovered and blocked

Each item named, with the blocker and who can clear it; "none" if none.

## Not pushed

What is committed locally and not pushed (main after a meta mode close, branches), and who pushes it.

## Lessons routed to

Each lesson names the check to add (a test, hook or lint rule) when the violation is mechanical, and the skill or rule to edit only when it is a judgement call.
