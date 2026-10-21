"""run-status and continue fixes: review-shallow processOnly, roadmap merged tasks, MERGE lines."""

import sys
from pathlib import Path

SD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SD / "scripts"))
import ticket  # noqa: E402
from test_ticket_continue import epic as continue_epic  # noqa: E402,F401
from test_ticket_continue import repo, root, write_ret  # noqa: E402,F401
from test_ticket_run import cli, git  # noqa: E402

DOCS = Path(__file__).resolve().parents[3] / "skills" / "start-development" / "references"


def test_review_shallow_stays_escalated():
    t = {"id": "a", "verified": True, "processOnly": True, "stopped": "review-shallow"}
    assert ticket._run_status(t, set(), {"a"}) == "escalated"


def test_other_process_only_still_done():
    t = {"id": "a", "verified": True, "processOnly": True, "stopped": "gate-repeat"}
    assert ticket._run_status(t, set(), {"a"}) == "done"
    assert ticket._run_status({**t, "stopped": ""}, set(), set()) == "done"


def _mk(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_roadmap_open_files_drops_merged(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    plans = r / "docs" / "plans"
    readme = "---\ntitle: {}\nblockers: []\nstage: build\n---\n"
    _mk(plans / "in-progress" / "busy" / "README.md", readme.format("busy"))
    _mk(
        plans / "in-progress" / "busy" / "tasks" / "b1.md",
        "---\ntitle: b1\nstatus: in-progress\nrepo: proj\nbranch: busy--b1\n"
        "files: [src/a.py]\nestimate: 1\n---\nb\n",
    )
    _mk(plans / "todo" / "next" / "README.md", readme.format("next"))
    _mk(
        plans / "todo" / "next" / "tasks" / "n1.md",
        "---\ntitle: n1\nstatus: todo\nfiles: [src/a.py]\nestimate: 1\n---\nb\n",
    )
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    out = cli("roadmap", "--root", plans)
    assert "overlaps busy: src/a.py" in out.stdout, out.stdout + out.stderr
    git(r, "branch", "busy--b1")  # merged: the branch tip is already in main
    out = cli("roadmap", "--root", plans)
    assert out.stdout.splitlines()[-1] == "runnable: next", out.stdout + out.stderr


def test_merge_line_has_name_and_repo(repo, root, continue_epic, tmp_path):  # noqa: F811
    ep = continue_epic
    assert cli("worktrees", ep, "--root", root).returncode == 0
    wt = repo / ".claude" / "worktrees" / f"{ep}--alpha"
    (wt / "mine.txt").write_text("m")
    git(wt, "add", "-A")
    git(wt, "commit", "-m", "alpha work")
    head = git(wt, "rev-parse", "HEAD").stdout.strip()
    data = {
        "run": "r1",
        "tasks": [
            {
                "id": "alpha",
                "branch": f"{ep}--alpha",
                "verified": True,
                "clean": False,
                "stopped": "gate-repeat",
                "verification": {"head": head},
            },
            {"id": "beta", "branch": "b-beta", "verified": False, "clean": False},
        ],
        "escalated": [{"id": "alpha", "reason": "gate-repeat"}],
    }
    rj = write_ret(repo, data)
    out = tmp_path / "out"
    r = cli(
        "continue",
        ep,
        "--root",
        root,
        "--out-dir",
        out,
        "--accept",
        "alpha",
        "--reason",
        "ok",
        "--return",
        rj,
    )
    assert r.returncode == 2, r.stderr
    assert f"MERGE alpha --name {ep}--alpha --repo proj" in r.stdout.splitlines()
    assert not out.exists()


def test_tickets_md_documents_merge_gate():
    text = (DOCS / "tickets.md").read_text()
    for needle in ("exit 2", "MERGE <task> --name", "--repo", "workbench:worktree-merger"):
        assert needle in text
