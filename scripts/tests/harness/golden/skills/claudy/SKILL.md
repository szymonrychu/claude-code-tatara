---
name: claudy
description: "d claudy"
---
Then run the epic through `plan-execute`, one run per epic,
named by the epic slug over the args JSON that `ticket.py args` writes:

```
# no workflow runtime in this harness: run the `plan-execute` skill over
# <scratchpad dir>/<epic>-args.json; it writes its return to <scratchpad dir>/<epic>-return.json
```

When the `plan-execute` skill finishes, `ticket.py apply-run <epic> <scratchpad dir>/<epic>-return.json` (the return file that skill writes) writes results back into the task files.

The `plan-execute` skill runs in this session, so there is no run to wait on; every wait inside it is a bounded wait with a stated maximum (10 minutes unless a tool sets a shorter one), after which you re-check and report what resolved and what did not; when it finishes, read its return file per plugins/core/skills/claudy/references/run-handback.md.
**Relaunch:** `ticket.py continue <epic> --out-dir <dir> --return <scratchpad dir>/<epic>-return.json --accept <ids>` applies the return.

Numbered prose questions (each with its options and a recommended answer) for genuine option choices, prose otherwise. Ask with numbered prose questions (each with its options and a recommended answer).
Wait with a stated maximum (10 minutes unless a tool sets a shorter one) on the log.
