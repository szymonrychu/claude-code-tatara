# Multi-epic planning and launch

Before planning parallel epics:
- `ticket.py contract list` shows the shared contracts; `ticket.py contract add <name> --kind ... --owner ... --file ...`
  registers a new one (one defining file, one owner epic).
- `ticket.py graph --todo` shows the dependency graph of the todo epics.

## Running epics concurrently

- `ticket.py roadmap` gives the epic dependency graph, the runnable epics and a one-line status per epic.
- Launch one plan-execute run per runnable epic concurrently, and the next runnable epic when a run lands
  (re-run `ticket.py roadmap` after each landing).
- plan-execute stays one epic per run; never merge two epics into one run.
