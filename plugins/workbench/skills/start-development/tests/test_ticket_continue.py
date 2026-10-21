"""ticket.py continue: apply the last return, record rulings, gate merges, refresh, write args."""

import json
import os
import sys
from pathlib import Path

import pytest

SD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SD / "scripts"))
import ticket  # noqa: E402
from test_ticket_run import cli, commit_all, git, mk_epic, mk_task  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
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


@pytest.fixture
def epic(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha")
    mk_task(root, ep, "Beta", extra=("--depends-on", "alpha"))
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    # the epic branch carries the ticket move
    git(repo / ".claude" / "worktrees" / ep, "merge", "--ff-only", "main")
    return ep


def meta(root, ep, slug):
    p = root / "in-progress" / ep / "tasks" / f"{slug}.md"
    return ticket.load(p.read_text(), p).meta


def ret(repo, alpha_head=True):
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    alpha = {
        "id": "alpha",
        "branch": "b-alpha",
        "verified": alpha_head,
        "clean": False,
        "stopped": "gate-repeat",
    }
    if alpha_head:
        alpha["verification"] = {"head": head}
    beta = {"id": "beta", "branch": "big-epic-beta", "verified": False, "clean": False}
    return {
        "run": "r1",
        "tasks": [alpha, beta],
        "escalated": [{"id": "alpha", "reason": "gate-repeat"}],
    }


def write_ret(repo, data):
    p = repo / "return.json"
    p.write_text(json.dumps(data))
    return p


def test_apply_and_accept(repo, root, epic, tmp_path):
    out = tmp_path / "out"
    rj = write_ret(repo, ret(repo))
    r = cli(
        "continue",
        epic,
        "--root",
        root,
        "--out-dir",
        out,
        "--accept",
        "alpha",
        "--reason",
        "false finding",
        "--return",
        rj,
    )
    assert r.returncode == 0, r.stderr
    assert meta(root, epic, "alpha")["status"] == "done"
    assert meta(root, epic, "beta")["status"] == "in-progress"
    rulings = json.loads((root / "in-progress" / epic / "rulings.json").read_text())
    assert [(x["task"], x["accept"], x["reason"]) for x in rulings] == [
        ("alpha", True, "false finding")
    ]
    assert "## Ruling" in (root / "in-progress" / epic / "tasks" / "alpha.md").read_text()
    args = json.loads((out / f"{epic}-args.json").read_text())
    assert [t["id"] for t in args["tasks"]] == ["beta"]
    assert args["tasks"][0]["dependsOn"] == []
    lines = r.stdout.strip().splitlines()
    assert lines[-1] == str(out / f"plan-execute-{epic}.js")
    assert any("heartbeat.py --run <runId>" in x for x in lines)
    assert (repo / ".claude" / "worktrees" / f"{epic}-beta").is_dir()
    assert not (repo / ".claude" / "worktrees" / f"{epic}-alpha").exists()
    subjects = git(repo, "log", "--format=%s").stdout
    assert f"chore(ticket): {epic} continue" in subjects
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""


def test_accept_unverified_fails(repo, root, epic, tmp_path):
    rj = write_ret(repo, ret(repo, alpha_head=False))
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli(
        "continue",
        epic,
        "--root",
        root,
        "--out-dir",
        tmp_path / "o",
        "--accept",
        "alpha",
        "--reason",
        "x",
        "--return",
        rj,
    )
    assert r.returncode == 1 and "alpha" in r.stderr and "unverified" in r.stderr
    assert not (root / "in-progress" / epic / "rulings.json").exists()
    assert meta(root, epic, "alpha")["status"] == "in-progress"
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert not (tmp_path / "o").exists()


def test_prints_script_path(repo, root, epic, tmp_path):
    out = tmp_path / "out"
    rj = write_ret(repo, ret(repo))
    r = cli("continue", epic, "--root", root, "--out-dir", out, "--return", rj)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == str(out / f"plan-execute-{epic}.js")
    assert (out / f"plan-execute-{epic}.js").is_file()


def test_accept_needs_reason(repo, root, epic, tmp_path):
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "o", "--accept", "alpha")
    assert r.returncode == 1 and "reason" in r.stderr


def test_merge_gate_exit_2(repo, root, epic, tmp_path):
    assert cli("worktrees", epic, "--root", root).returncode == 0
    wt = repo / ".claude" / "worktrees" / f"{epic}-alpha"
    (wt / "mine.txt").write_text("m")
    git(wt, "add", "-A")
    git(wt, "commit", "-m", "alpha work")
    head = git(wt, "rev-parse", "HEAD").stdout.strip()
    data = ret(repo)
    data["tasks"][0]["branch"] = f"{epic}-alpha"
    data["tasks"][0]["verification"] = {"head": head}
    rj = write_ret(repo, data)
    out = tmp_path / "out"
    r = cli(
        "continue",
        epic,
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
    assert f"MERGE alpha --name {epic}-alpha --base {epic} --repo proj" in r.stdout.splitlines()
    assert not out.exists()
    assert meta(root, epic, "alpha")["status"] == "done"
    # the merger lands the branch, then the rerun is clean and does not duplicate the ruling
    git(repo / ".claude" / "worktrees" / epic, "merge", "--no-edit", f"{epic}-alpha")
    r = cli(
        "continue",
        epic,
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
    assert r.returncode == 0, r.stderr
    assert (out / f"{epic}-args.json").is_file()
    rulings = json.loads((root / "in-progress" / epic / "rulings.json").read_text())
    assert len(rulings) == 1


def test_run_id_resolves_return(repo, root, epic, tmp_path):
    proj = tmp_path / "projects"
    wf = proj / "slug" / "sess" / "workflows"
    (proj / "slug" / "sess" / "subagents" / "workflows" / "wf_1").mkdir(parents=True)
    wf.mkdir(parents=True)
    (wf / "wf_1.json").write_text(
        json.dumps({"runId": "wf_1", "status": "completed", "result": ret(repo)})
    )
    env = dict(os.environ, CLAUDE_PROJECTS_DIR=str(proj))
    import subprocess

    r = subprocess.run(
        [
            sys.executable,
            str(SD / "scripts" / "ticket.py"),
            "continue",
            epic,
            "--root",
            str(root),
            "--out-dir",
            str(tmp_path / "o"),
            "--accept",
            "alpha",
            "--reason",
            "ok",
            "--run",
            "wf_1",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert meta(root, epic, "alpha")["status"] == "done"
    r = subprocess.run(
        [
            sys.executable,
            str(SD / "scripts" / "ticket.py"),
            "continue",
            epic,
            "--root",
            str(root),
            "--out-dir",
            str(tmp_path / "o"),
            "--run",
            "wf_missing",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1 and "wf_missing" in r.stderr


def test_refreshes_facts_only_when_present(repo, root, epic, tmp_path):
    rj = write_ret(repo, ret(repo))
    assert (
        cli(
            "continue", epic, "--root", root, "--out-dir", tmp_path / "o1", "--return", rj
        ).returncode
        == 0
    )
    assert not (root / "facts.md").exists()
    (root / "facts.md").write_text("stale\n")
    r = cli("continue", epic, "--root", root, "--out-dir", tmp_path / "o2")
    assert r.returncode == 0, r.stderr
    assert "Repo facts pack" in (root / "facts.md").read_text()


def test_idempotent(repo, root, epic, tmp_path):
    out = tmp_path / "out"
    rj = write_ret(repo, ret(repo))
    argv = (
        "continue",
        epic,
        "--root",
        root,
        "--out-dir",
        out,
        "--accept",
        "alpha",
        "--reason",
        "false finding",
        "--return",
        rj,
    )

    def snapshot():
        d = root / "in-progress" / epic
        files = [
            d / "README.md",
            d / "rulings.json",
            *sorted((d / "tasks").glob("*.md")),
            out / f"{epic}-args.json",
        ]
        return {str(p): p.read_bytes() for p in files}

    assert cli(*argv).returncode == 0
    first = snapshot()
    r = cli(*argv)
    assert r.returncode == 0, r.stderr
    second = snapshot()
    assert [k for k in first if first[k] != second[k]] == []


def _task_branch(repo, root, epic, name):
    """A done alpha whose recorded branch is `name` and carries one commit."""
    tree = repo / ".claude" / "worktrees" / f"{epic}-alpha-tmp"
    git(repo, "worktree", "add", "-q", "-b", name, str(tree), "main")
    (tree / "mine.txt").write_text("m")
    git(tree, "add", "-A")
    git(tree, "commit", "-m", "alpha work")
    head = git(tree, "rev-parse", "HEAD").stdout.strip()
    git(repo, "worktree", "remove", "--force", str(tree))
    return head


def _continue(repo, root, epic, tmp_path, head, branch):
    data = ret(repo)
    data["tasks"][0]["branch"] = branch
    data["tasks"][0]["verification"] = {"head": head}
    return cli(
        "continue", epic, "--root", root, "--out-dir", tmp_path / "out",
        "--accept", "alpha", "--reason", "ok", "--return", write_ret(repo, data),
    )  # fmt: skip


def test_merge_line_names_legacy_double_hyphen_branch(repo, root, epic, tmp_path):
    head = _task_branch(repo, root, epic, f"{epic}--alpha")
    r = _continue(repo, root, epic, tmp_path, head, f"{epic}--alpha")
    assert r.returncode == 2, r.stderr
    assert f"MERGE alpha --name {epic}--alpha --base {epic} --repo proj" in r.stdout.splitlines()


def test_gate_counts_patch_equivalent_task_as_merged_after_rebase(repo, root, epic, tmp_path):
    head = _task_branch(repo, root, epic, f"{epic}-alpha")
    itree = repo / ".claude" / "worktrees" / epic
    git(itree, "cherry-pick", head)  # same patch, new commit id: as after a rebase of <epic>
    r = _continue(repo, root, epic, tmp_path, head, f"{epic}-alpha")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MERGE" not in r.stdout
    args = json.loads((tmp_path / "out" / f"{epic}-args.json").read_text())
    assert args["baseRef"] == epic and args["mainCheckout"] == str(repo.resolve())
