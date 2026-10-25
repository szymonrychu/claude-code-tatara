"""ticket.py retro: RETRO.md's measured Tasks table and Deltas, and the earlier retros."""

import json
import sys
from pathlib import Path

from ticket_repo_helpers import (
    cli,
    commit_all,
    epic_dir,
    git,
    last_subject,
    mk_epic,
    mk_task,
    set_meta,
    task_path,
    ticket,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import agent_usage  # noqa: E402

BEGIN, END = "<!-- retro:generated:begin -->", "<!-- retro:generated:end -->"
TASKS_HEADER = [
    "Task",
    "Points (estimate)",
    "Points (post-delivery)",
    "Minutes (expected)",
    "Minutes (actual)",
    "Tokens (expected)",
    "Tokens (actual)",
]
DELTAS_HEADER = [
    "Task",
    "Points (post-delivery - estimate)",
    "Minutes (actual / expected)",
    "Tokens (actual / expected)",
]
NR = "not recorded"


def usage_record(agent_id, epic, task, role, start, end, total):
    return {
        "agentId": agent_id,
        "agentType": f"workbench:{'implementer' if role == 'impl' else 'reviewer'}",
        "model": "claude-sonnet-5-5",
        "epic": epic,
        "task": task,
        "role": role,
        "transcript": "",
        "start": start,
        "end": end,
        "tokens": {
            "input": total,
            "cache_creation": 0,
            "cache_read": 0,
            "output": 0,
            "total": total,
        },
    }


def to_in_progress(repo, root, ep):
    (root / "in-progress").mkdir(exist_ok=True)
    git(repo, "mv", str(root / "todo" / ep), str(root / "in-progress" / ep))
    git(repo, "commit", "-m", f"chore(ticket): {ep} move in-progress")


def setup_epic(repo, root, slugs=("alpha", "beta", "gamma", "delta")):
    ep = mk_epic(root)
    for s in slugs:
        mk_task(root, ep, s)
    commit_all(repo)
    to_in_progress(repo, root, ep)
    return ep


def done(root, ep, task, points_actual, logs, transcripts):
    r = cli(
        "task", ep, task, "--status", "done", "--verified-head", "abc123",
        "--points-actual", points_actual, "--logs", logs, "--transcripts", transcripts,
        "--root", root,
    )  # fmt: skip
    assert r.returncode == 0, r.stderr


def retro(root, ep, logs, transcripts):
    return cli("retro", ep, "--logs", logs, "--transcripts", transcripts, "--root", root)


def retro_path(root, ep):
    return epic_dir(root, ep) / "RETRO.md"


def table(text, section):
    """The rows of the first table in a section, header first, the separator dropped."""
    body = ticket._sections(text)[section]
    rows = [ln for ln in body.splitlines() if ln.startswith("|")]
    cells = [[c.strip() for c in ln.strip("|").split("|")] for ln in rows]
    return [cells[0]] + cells[2:]


def dirs(tmp_path):
    transcripts = tmp_path / "transcripts"
    transcripts.mkdir()
    return tmp_path / "logs", transcripts


def test_tasks_in_delivery_order(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    ep = setup_epic(repo, root)
    # beta waits on delta: dependency order is alpha, gamma, delta, beta (ties in slug order)
    set_meta(task_path(root, ep, "beta"), depends_on=["delta"])
    commit_all(repo)
    agent_usage.write_record(
        logs,
        usage_record(
            "g1", ep, "gamma", "impl", "2026-10-24T10:00:00.000Z", "2026-10-24T10:20:00.000Z", 1000
        ),
    )
    agent_usage.write_record(
        logs,
        usage_record(
            "g2", ep, "gamma", "review", "2026-10-24T10:21:00.000Z", "2026-10-24T10:30:00.000Z", 500
        ),
    )
    done(root, ep, "gamma", "5", logs, transcripts)
    done(root, ep, "alpha", "3", logs, transcripts)

    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 0, r.stderr
    text = retro_path(root, ep).read_text()
    rows = table(text, "Tasks")
    assert rows[0] == TASKS_HEADER
    assert [row[0] for row in rows[1:]] == ["gamma", "alpha", "delta", "beta", "Total"]
    assert rows[1] == ["gamma", "3", "5", "34", "30", "2250000", "1500"]
    assert rows[2] == ["alpha", "3", "3", "34", NR, "2250000", NR]
    assert rows[3] == ["delta", "3", NR, "34", NR, "2250000", NR]
    assert rows[5] == [
        "Total",
        "12",
        "8 (2 of 4 tasks)",
        "136",
        "30 (1 of 4 tasks)",
        "9000000",
        "1500 (1 of 4 tasks)",
    ]


def test_deltas_section(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    ep = setup_epic(repo, root, ("alpha", "beta", "gamma"))
    done(root, ep, "alpha", "5", logs, transcripts)
    done(root, ep, "beta", "5", logs, transcripts)
    set_meta(task_path(root, ep, "alpha"), actual_minutes="40", actual_tokens="3000000")
    set_meta(
        task_path(root, ep, "beta"),
        points="5",
        expected_minutes="50",
        expected_tokens="4000000",
        actual_minutes="45",
        actual_tokens="5000000",
    )
    commit_all(repo)

    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 0, r.stderr
    text = retro_path(root, ep).read_text()
    rows = table(text, "Deltas")
    assert rows[0] == DELTAS_HEADER
    assert rows[1:] == [
        ["alpha", "+2", "1.18", "1.33"],
        ["beta", "0", "0.90", "1.25"],
        ["gamma", NR, NR, NR],
    ]
    deltas = ticket._sections(text)["Deltas"]
    # (3, 5), (5, 5): 0.4 and 0; (34, 40), (50, 45): 0.15 and 0.111; tokens 0.25 and 0.2
    assert "MdAPE points: 20.0%" in deltas
    assert "MdAPE minutes: 13.1%" in deltas
    assert "MdAPE tokens: 22.5%" in deltas


def test_rerun_keeps_written_sections(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    ep = setup_epic(repo, root, ("alpha",))
    done(root, ep, "alpha", "3", logs, transcripts)
    assert retro(root, ep, logs, transcripts).returncode == 0
    path = retro_path(root, ep)
    first = path.read_text()
    assert first.count(BEGIN) == 1 and first.count(END) == 1
    head, rest = first.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    head = head.replace("\n", "\nWritten above the block by hand.\n", 1)
    tail = (
        "\n\n## Retro\n\n| Went well | Went bad / could be improved |\n|---|---|\n"
        "| tests first | one rerun |\n\n## Improvements\n\n- Code: split the parser.\n"
        "- Tech debt: none.\n\n"
    )
    generated = BEGIN + rest.split(END, 1)[0] + END
    path.write_text(head + generated + tail)
    set_meta(task_path(root, ep, "alpha"), actual_minutes="77", actual_tokens="99")
    commit_all(repo)

    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 0, r.stderr
    second = path.read_text()
    new_head, new_rest = second.split(BEGIN, 1)
    new_generated, new_tail = new_rest.split(END, 1)
    assert new_head == head
    assert new_tail == tail
    assert new_generated != generated
    assert table(second, "Tasks")[1] == ["alpha", "3", "3", "34", "77", "2250000", "99"]
    assert last_subject(repo) == f"chore(ticket): {ep} retro"

    # without the markers a rerun refuses rather than overwrite the hand-written file
    path.write_text("# hand made\n\n## Retro\n\nkeep me\n")
    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 1 and "retro:generated" in r.stderr
    assert path.read_text() == "# hand made\n\n## Retro\n\nkeep me\n"


def test_commit_and_refusals(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    ep = setup_epic(repo, root, ("alpha",))
    (repo / "unrelated.txt").write_text("not mine")
    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 0, r.stderr
    path = retro_path(root, ep)
    assert last_subject(repo) == f"chore(ticket): {ep} retro"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == [str(path.relative_to(repo))]
    assert git(repo, "status", "--porcelain").stdout.strip() == "?? unrelated.txt"
    text = path.read_text()
    assert text.splitlines()[0] == "# Big epic retro"
    assert ticket.slug("Big epic") == ep

    # an unchanged rerun succeeds without an empty commit
    head = git(repo, "rev-parse", "HEAD").stdout
    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 0, r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head

    # a todo epic is refused
    todo = mk_epic(root, title="Other work")
    commit_all(repo)
    r = retro(root, todo, logs, transcripts)
    assert r.returncode == 1 and "todo" in r.stderr
    assert not (root / "todo" / todo / "RETRO.md").exists()

    # a linked worktree is refused
    head = git(repo, "rev-parse", "HEAD").stdout
    wt = repo.parent / "linked"
    git(repo, "worktree", "add", "-b", "side", str(wt))
    r = retro(wt / "docs" / "plans", ep, logs, transcripts)
    assert r.returncode == 1 and "main checkout" in r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head


def test_path_retro(repo, root):
    ep = setup_epic(repo, root, ("alpha",))
    r = cli("path", "--root", root, ep, "retro")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(root.resolve() / "in-progress" / ep / "RETRO.md")


def write_done_epic(repo, root, name, with_retro=True):
    d = root / "done" / name
    d.mkdir(parents=True)
    (d / "README.md").write_text(f'---\ntitle: "{name}"\n---\n\n# {name}\n')
    if with_retro:
        (d / "RETRO.md").write_text(
            f"# {name} retro\n\n{BEGIN}\n## Tasks\n\nt\n\n## Deltas\n\nd\n{END}\n\n"
            f"## Retro\n\nwent well in {name}\n\n## Improvements\n\n- improve {name}\n"
        )
    git(repo, "add", "-A", "--", "docs")
    git(repo, "commit", "-m", f"chore(ticket): {name} move done")


def test_history(repo, root):
    for name in ("old", "mid", "new"):
        write_done_epic(repo, root, name)
    write_done_epic(repo, root, "newest", with_retro=False)
    live = setup_epic(repo, root, ("alpha",))
    (epic_dir(root, live) / "RETRO.md").write_text("## Retro\n\nlive\n\n## Improvements\n\nx\n")
    commit_all(repo)

    r = cli("retro", "--history", "--limit", "2", "--root", root)
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout)
    assert [e["epic"] for e in got] == ["new", "mid"]
    assert got[0]["retro"] == "went well in new"
    assert got[0]["improvements"] == "- improve new"
    assert got[1]["retro"] == "went well in mid"

    r = cli("retro", "--history", "--root", root)
    assert r.returncode == 0, r.stderr
    assert [e["epic"] for e in json.loads(r.stdout)] == ["new", "mid", "old"]

    assert cli("retro", "--root", root).returncode == 1
    assert cli("retro", "new", "--history", "--root", root).returncode == 1


def test_falls_back_to_records_and_notes(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    ep = setup_epic(repo, root, ("alpha", "beta"))
    # alpha was marked done by a ticket.py that did not stamp: no points key, no actuals,
    # its estimate only in Notes
    alpha = task_path(root, ep, "alpha")
    doc = ticket.load(alpha.read_text(), alpha)
    doc.meta.pop("points")
    doc.meta["status"] = "done"
    body = doc.body.rstrip("\n") + "\n- Estimate: 8 points.\n"
    alpha.write_text(ticket.dump(ticket.Doc(doc.meta, body)))
    set_meta(task_path(root, ep, "beta"), points="")
    commit_all(repo, f"chore(ticket): {ep} task alpha done")
    start, mid, end = "2026-10-24T10:00:00.000Z", "2026-10-24T10:20:00.000Z", "10:31:00.000Z"
    for rec in (
        usage_record("a1", ep, "alpha", "impl", start, mid, 1000),
        usage_record(
            "a2", ep, "alpha", "review", "2026-10-24T10:25:00.000Z", f"2026-10-24T{end}", 400
        ),
        usage_record("b1", ep, "beta", "impl", start, "2026-10-24T12:00:00.000Z", 9000),
        usage_record("x1", "other-epic", "alpha", "impl", start, "2026-10-24T13:00:00.000Z", 7000),
    ):
        agent_usage.write_record(logs, rec)

    r = retro(root, ep, logs, transcripts)
    assert r.returncode == 0, r.stderr
    rows = table(retro_path(root, ep).read_text(), "Tasks")
    assert rows[1] == ["alpha", "8", NR, "34", "31", "2250000", "1400"]
    # beta has no points and no Notes estimate; its own records still give its actuals
    assert rows[2] == ["beta", NR, NR, "34", "120", "2250000", "9000"]
