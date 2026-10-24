"""ticket.py task <epic> <task> --status: how the orchestrator records a task's outcome."""

import datetime

from ticket_repo_helpers import (
    cli,
    commit_all,
    git,
    last_subject,
    meta,
    mk_epic,
    mk_task,
    set_meta,
)

TODAY = datetime.date.today().isoformat()


def test_task_status_sets_fields_and_commits(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "alpha")
    set_meta(p, owns=["legacy-part"], estimate="6")  # an old task file keeps its legacy keys
    commit_all(repo)
    (repo / "unrelated.txt").write_text("not mine")
    r = cli(
        "task", ep, "alpha", "--status", "done", "--verified-head", "abc123",
        "--note", "review clean", "--root", root,
    )
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["status"] == "done" and m["verified_head"] == "abc123"
    assert m["owns"] == ["legacy-part"] and m["estimate"] == "6"
    notes = p.read_text().split("## Notes", 1)[1]
    assert f"- {TODAY} done: review clean" in notes
    assert last_subject(repo) == f"chore(ticket): {ep} task alpha done"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == [str(p.relative_to(repo))]
    assert git(repo, "status", "--porcelain").stdout.strip() == "?? unrelated.txt"

    r = cli("task", ep, "alpha", "--status", "escalated", "--root", root)
    assert r.returncode == 0, r.stderr
    m = meta(p)
    assert m["status"] == "escalated" and m["verified_head"] == "abc123"
    assert f"- {TODAY} escalated" in p.read_text().split("## Notes", 1)[1]
    assert last_subject(repo) == f"chore(ticket): {ep} task alpha escalated"

    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("task", ep, "alpha", "--status", "finished", "--root", root)
    assert r.returncode == 1 and "finished" in r.stderr
    r = cli("task", ep, "ghost", "--status", "done", "--root", root)
    assert r.returncode == 1 and "ghost" in r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert meta(p)["status"] == "escalated"
