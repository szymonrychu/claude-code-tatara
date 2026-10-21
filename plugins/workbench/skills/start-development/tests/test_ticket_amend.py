"""ticket.py amend: record a mid-epic scope change and re-validate (D9)."""

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from test_ticket_run import cli, commit_all, git, mk_epic, mk_task


@pytest.fixture
def repo(tmp_path_factory):
    r = tmp_path_factory.mktemp("proj")
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    return r


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


NEW_AC = "- AC1: new behaviour [evidence: test:tests/test_x.py::test_new]"


def amend(root, ep, task, tmp_path, req="Changed scope.", ac=None, reason="user changed scope"):
    rf = tmp_path / "req.md"
    rf.write_text(req)
    args = ["amend", ep, task, "--root", root, "--requirement-file", rf, "--reason", reason]
    if ac is not None:
        af = tmp_path / "ac.md"
        af.write_text(ac)
        args += ["--ac-file", af]
    return cli(*args)


def make_valid(epic_dir, task):
    """Fill the sections the epic lint requires so only the amend can break it."""
    readme = epic_dir / "README.md"
    text = readme.read_text()
    for label in ("What", "How", "Why"):
        text = text.replace(f"{label}:", f"{label}: filled", 1)
    for name in ("Description", "Goals", "Non-goals"):
        text = text.replace(f"## {name}\n", f"## {name}\n\nfilled\n", 1)
    readme.write_text(text)
    (epic_dir / "approvals.json").write_text("[]\n")
    body = task.read_text()
    task.write_text(body.replace("## Expected outcome\n", "## Expected outcome\n\nit works\n", 1))


def setup(root, repo):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Alpha work")
    make_valid(p.parents[1], p)
    commit_all(repo)
    return ep, p


def test_amend_replaces_and_notes(root, repo, tmp_path):
    ep, p = setup(root, repo)
    r = amend(root, ep, "alpha-work", tmp_path)
    assert r.returncode == 0, r.stderr + r.stdout
    text = p.read_text()
    assert "Changed scope." in text and "Do the thing." not in text
    today = datetime.date.today().isoformat()
    assert f"- {today} amended: user changed scope" in text
    assert (
        git(repo, "log", "-1", "--format=%s").stdout.strip()
        == f"chore(ticket): {ep} amend alpha-work"
    )
    assert git(repo, "status", "--porcelain").stdout.strip() == ""


def test_amend_replaces_ac(root, repo, tmp_path):
    ep, p = setup(root, repo)
    r = amend(root, ep, "alpha-work", tmp_path, ac=NEW_AC)
    assert r.returncode == 0, r.stderr + r.stdout
    text = p.read_text()
    assert "new behaviour" in text and "it lists tasks" not in text


def test_amend_keeps_ac_when_not_given(root, repo, tmp_path):
    ep, p = setup(root, repo)
    r = amend(root, ep, "alpha-work", tmp_path)
    assert r.returncode == 0, r.stderr + r.stdout
    assert "it lists tasks" in p.read_text() and "Changed scope." in p.read_text()


def test_amend_refuses_done(root, repo, tmp_path):
    ep, p = setup(root, repo)
    p.write_text(p.read_text().replace("status: todo", "status: done", 1))
    commit_all(repo)
    before = p.read_text()
    r = amend(root, ep, "alpha-work", tmp_path)
    assert r.returncode != 0 and "done" in r.stderr
    assert p.read_text() == before


def test_amend_refuses_done_epic(root, repo, tmp_path):
    ep, p = setup(root, repo)
    done = root / "done"
    done.mkdir(exist_ok=True)
    src = next(root.glob(f"*/{ep}"))
    git(repo, "mv", str(src), str(done / ep))
    commit_all(repo)
    r = amend(root, ep, "alpha-work", tmp_path)
    assert r.returncode != 0 and "done" in r.stderr


def test_amend_rolls_back(root, repo, tmp_path):
    ep, p = setup(root, repo)
    before = p.read_text()
    head = git(repo, "rev-parse", "HEAD").stdout
    r = amend(root, ep, "alpha-work", tmp_path, ac="- AC1: bad line without evidence")
    assert r.returncode == 1
    assert "AC1" in r.stderr + r.stdout
    assert p.read_text() == before
    assert git(repo, "rev-parse", "HEAD").stdout == head


def test_amend_unknown_task(root, repo, tmp_path):
    ep, _ = setup(root, repo)
    r = amend(root, ep, "nope", tmp_path)
    assert r.returncode != 0 and "nope" in r.stderr
