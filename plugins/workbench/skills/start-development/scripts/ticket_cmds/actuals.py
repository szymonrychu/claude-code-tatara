"""ticket.py actuals: backfill the usage records the recorder hook missed (agent_usage.backfill)."""

from pathlib import Path

import agent_usage  # scripts/lib, on sys.path through ticket.py


def register(sub, t) -> None:
    sp = sub.add_parser("actuals", help="backfill .logs/agents records from harness transcripts")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("--backfill", action="store_true", help="write the missing records")
    sp.add_argument(
        "--transcripts",
        help="subagent transcripts dir (default: the project's dir under the harness home)",
    )
    sp.add_argument("--refresh", action="store_true", help="rewrite records that already exist")
    sp.add_argument(
        "--logs", help="the logs dir holding agents/ (default: the main checkout's .logs)"
    )


def run(a, t) -> int:
    if not a.backfill:
        raise t.TicketError("actuals: nothing to do; pass --backfill")
    root = Path(a.root)
    epic = t.resolve_epic(a.epic, root).name
    logs = Path(a.logs) if a.logs else t.workbench.logs_dir(root)
    if logs is None:
        raise t.TicketError("actuals: no logs dir; pass --logs")
    main = t.workbench.main_checkout(root)
    if a.transcripts:
        transcripts = Path(a.transcripts)
    elif main:
        transcripts = agent_usage.default_transcripts_dir(main)
    else:
        raise t.TicketError("actuals: not in a git checkout; pass --transcripts")
    for record in agent_usage.backfill(transcripts, logs, refresh=a.refresh, epic=epic):
        minutes = agent_usage.aggregate([record])["minutes"]
        label = f"{record['epic']}/{record['task']}/{record['role']}"
        shown = "-" if minutes is None else minutes
        print(f"{record['agentId']} {label} {shown} {record['tokens']['total']}")
    return 0
