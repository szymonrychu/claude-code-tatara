# Approvals

Only when the `orchestrator_approval_*` tools are available.

- A yes/no permission to act (merge, deploy, apply, delete) is asked by the session that will act, with
  `orchestrator_approval_ask` on its own task, one approval per action.
- Never ask it as a numbered line in a chat or project-room update, and never with `orchestrator_decision_ask`.
- The verdict arrives as a chat notice `Approval D-<id> (T-<n>) GO|NO-GO|EXPIRED ...`. Before acting on GO, re-read the
  task with `orchestrator_task_get`. NO-GO or EXPIRED means do not act.
- A superleader never relays an approval or its answer. Its updates say only `N approvals open: <approvals page url>`.
