"""adopt: existing checkouts and URLs become components without losing local state."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


def g(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def ok(*args, cwd):
    p = g(*args, cwd=cwd)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def make_origin(tmp_path, name="proj", default="trunk"):
    bare = tmp_path / "origins" / f"{name}.git"
    bare.parent.mkdir(parents=True, exist_ok=True)
    ok("init", "-q", "--bare", "-b", default, str(bare), cwd=tmp_path)
    return bare


def make_source(tmp_path, name="proj", origin=True, files=None):
    """A checkout on branch feature (remote default trunk) with a stash, a dirty tracked file,
    untracked and ignored files, a venv dir, and two linked worktrees (one inside, one outside)."""
    src = tmp_path / "elsewhere" / name
    src.mkdir(parents=True)
    ok("init", "-q", "-b", "trunk", cwd=src)
    (src / "README.md").write_text("hello\n")
    (src / ".gitignore").write_text(".env\n.venv/\n.claude/worktrees/\n")
    for rel, text in (files or {}).items():
        (src / rel).parent.mkdir(parents=True, exist_ok=True)
        (src / rel).write_text(text)
    ok("add", "-A", cwd=src)
    ok("commit", "-q", "-m", "init", cwd=src)
    bare = None
    if origin:
        bare = make_origin(tmp_path, name)
        ok("remote", "add", "origin", str(bare), cwd=src)
        ok("push", "-q", "origin", "trunk", cwd=src)
    ok("checkout", "-q", "-b", "feature", cwd=src)
    (src / "feature.txt").write_text("f\n")
    ok("add", "feature.txt", cwd=src)
    ok("commit", "-q", "-m", "feature", cwd=src)
    (src / "README.md").write_text("stashed change\n")
    ok("stash", "push", "-q", "-m", "keep-me", cwd=src)
    (src / "README.md").write_text("dirty change\n")
    (src / ".env").write_text("SECRET=1\n")
    (src / ".venv" / "bin").mkdir(parents=True)
    (src / ".venv" / "bin" / "python").write_text("#!/bin/sh\n")
    (src / "notes.txt").write_text("untracked\n")
    ok("worktree", "add", "-q", "-b", "wt-out", str(tmp_path / f"{name}-wt-out"), cwd=src)
    ok("worktree", "add", "-q", "-b", "wt-in", ".claude/worktrees/inner", cwd=src)
    return src, bare


def snapshot(root: Path) -> dict[str, bytes]:
    """Every file's bytes under root, skipping git metadata (.git dirs and .git files)."""
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if ".git" in rel.parts or p.is_dir():
            continue
        out[str(rel)] = p.read_bytes()
    return out


def status(repo: Path) -> str:
    return ok("status", "--porcelain", "--ignored", "--untracked-files=all", cwd=repo)


def test_adopt_path_moves_and_keeps_state(workbench, run_cli, tmp_path):
    src, bare = make_source(tmp_path)
    inode = src.stat().st_ino
    branches = ok("branch", "--format=%(refname:short) %(objectname)", cwd=src)
    stashes = ok("stash", "list", cwd=src)
    r = run_cli("adopt", "--path", str(src))
    assert r.returncode == 0, r.stderr
    dest = workbench / "code" / "proj"
    assert not src.exists()
    assert dest.stat().st_ino == inode, "moved with rename, not copied"
    assert (dest / ".git").is_dir()
    assert (dest / ".env").read_text() == "SECRET=1\n"
    assert (dest / ".venv/bin/python").is_file()
    assert (dest / "notes.txt").read_text() == "untracked\n"
    assert (dest / "README.md").read_text() == "dirty change\n"
    assert ok("branch", "--format=%(refname:short) %(objectname)", cwd=dest) == branches
    assert ok("stash", "list", cwd=dest) == stashes and "keep-me" in stashes
    assert ok("symbolic-ref", "--short", "HEAD", cwd=dest) == "feature"
    assert ok("config", "-f", ".gitmodules", "submodule.proj.path", cwd=workbench) == "code/proj"
    assert ok("config", "-f", ".gitmodules", "submodule.proj.url", cwd=workbench) == str(bare)
    assert ok("ls-files", "-s", "code/proj", cwd=workbench).startswith("160000 ")
    assert "code/proj" in ok("submodule", "status", cwd=workbench)
    assert f"moved {src}" in r.stdout


def test_worktree_repaired(workbench, run_cli, tmp_path):
    src, _ = make_source(tmp_path)
    r = run_cli("adopt", "--path", str(src))
    assert r.returncode == 0, r.stderr
    dest = workbench / "code" / "proj"
    outer = tmp_path / "proj-wt-out"
    inner = dest / ".claude/worktrees/inner"
    for wt, branch in ((outer, "wt-out"), (inner, "wt-in")):
        assert ok("symbolic-ref", "--short", "HEAD", cwd=wt) == branch
        (wt / f"{branch}.txt").write_text("x\n")
        ok("add", f"{branch}.txt", cwd=wt)
        ok("commit", "-q", "-m", branch, cwd=wt)
        assert ok("rev-parse", branch, cwd=dest) == ok("rev-parse", "HEAD", cwd=wt)
    listed = ok("worktree", "list", "--porcelain", cwd=dest)
    paths = [line.split(" ", 1)[1] for line in listed.splitlines() if line.startswith("worktree ")]
    assert sorted(Path(p).resolve() for p in paths) == sorted(
        p.resolve() for p in (dest, outer, inner)
    )
    assert "prunable" not in listed
    assert "worktree repaired" in r.stdout


def test_branch_is_remote_default(workbench, run_cli, tmp_path):
    src, _ = make_source(tmp_path)
    assert ok("symbolic-ref", "--short", "HEAD", cwd=src) == "feature"
    r = run_cli("adopt", "--path", str(src), "--name", "svc")
    assert r.returncode == 0, r.stderr
    assert ok("config", "-f", ".gitmodules", "submodule.svc.branch", cwd=workbench) == "trunk"
    assert ok("config", "-f", ".gitmodules", "submodule.svc.path", cwd=workbench) == "code/svc"
    assert "branch trunk (remote default)" in r.stdout


def test_branch_falls_back_to_current(workbench, run_cli, tmp_path):
    src, bare = make_source(tmp_path)
    ok("symbolic-ref", "HEAD", "refs/heads/unborn", cwd=bare)
    r = run_cli("adopt", "--path", str(src))
    assert r.returncode == 0, r.stderr
    assert ok("config", "-f", ".gitmodules", "submodule.proj.branch", cwd=workbench) == "feature"
    assert "branch feature (current branch)" in r.stdout


def _refused(r, src, inode, workbench, name):
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert r.stderr.startswith("refused: ") and r.stderr.count("\n") == 1, r.stderr
    assert src.exists() and src.stat().st_ino == inode
    assert not (workbench / "code" / name).exists() or name == "taken"
    assert not (workbench / ".git").exists(), "nothing done before the refusal"
    assert not (workbench / ".gitmodules").exists()


def test_refusals_move_nothing(workbench, run_cli, tmp_path):
    inside = workbench / "inner"
    inside.mkdir()
    ok("init", "-q", "-b", "main", cwd=inside)
    ok("commit", "-q", "--allow-empty", "-m", "x", cwd=inside)
    ok("remote", "add", "origin", "https://example.com/x.git", cwd=inside)
    r = run_cli("adopt", "--path", str(inside))
    _refused(r, inside, inside.stat().st_ino, workbench, "inner")
    assert "inside the workbench" in r.stderr

    r = run_cli("adopt", "--path", str(tmp_path), "--name", "outer")
    _refused(r, tmp_path, tmp_path.stat().st_ino, workbench, "outer")

    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "f.txt").write_text("x")
    r = run_cli("adopt", "--path", str(plain))
    _refused(r, plain, plain.stat().st_ino, workbench, "plain")
    assert "not a git checkout" in r.stderr

    r = run_cli("adopt", "--path", str(tmp_path / "missing"))
    assert r.returncode == 1 and "does not exist" in r.stderr

    lone, _ = make_source(tmp_path, "lone", origin=False)
    st = status(lone)
    r = run_cli("adopt", "--path", str(lone))
    _refused(r, lone, lone.stat().st_ino, workbench, "lone")
    assert "no origin" in r.stderr and "--remote local-bare" in r.stderr
    assert status(lone) == st

    src, _ = make_source(tmp_path)
    sub = src / "docs"
    sub.mkdir()
    r = run_cli("adopt", "--path", str(sub))
    _refused(r, sub, sub.stat().st_ino, workbench, "docs")
    assert "not the top" in r.stderr

    wt = tmp_path / "proj-wt-out"
    r = run_cli("adopt", "--path", str(wt))
    _refused(r, wt, wt.stat().st_ino, workbench, "wt-out")
    assert "linked worktree" in r.stderr

    r = run_cli("adopt", "--path", str(src), "--name", "Bad_Name")
    _refused(r, src, src.stat().st_ino, workbench, "Bad_Name")

    (workbench / "code" / "taken").mkdir()
    r = run_cli("adopt", "--path", str(src), "--name", "taken")
    _refused(r, src, src.stat().st_ino, workbench, "taken")
    assert "already exists" in r.stderr

    r = run_cli("adopt", "--path", str(src), "--remote", "local-bare")
    _refused(r, src, src.stat().st_ino, workbench, "proj")
    assert "already has an origin" in r.stderr

    r = run_cli("adopt", "--path", str(lone), "--remote", "url:https://example.com/x.git")
    _refused(r, lone, lone.stat().st_ino, workbench, "lone")


def _engine(workbench, monkeypatch):
    """Import the copied engine in-process, fresh, so one module can be patched."""
    monkeypatch.syspath_prepend(str(workbench / "scripts/init_engine"))
    for mod in ("cli", "adopt", "gitops", "remotes", "scaffold"):
        monkeypatch.delitem(sys.modules, mod, raising=False)
    import adopt
    import cli

    return adopt, cli


def test_refuses_cross_device_move(workbench, tmp_path, monkeypatch, capsys):
    adopt, cli = _engine(workbench, monkeypatch)
    src, _ = make_source(tmp_path)
    real = adopt.device_of
    monkeypatch.setattr(
        adopt, "device_of", lambda p: real(p) + (1 if p.resolve() == src.resolve() else 0)
    )
    rc = cli.main(["--root", str(workbench), "adopt", "--path", str(src)])
    assert rc == 1
    assert "different filesystem" in capsys.readouterr().err
    assert src.exists() and not (workbench / "code/proj").exists()


def test_adopted_repo_untouched(workbench, run_cli, tmp_path):
    src, _ = make_source(tmp_path)
    before_status = status(src)
    before_files = snapshot(src)
    r = run_cli("adopt", "--path", str(src))
    assert r.returncode == 0, r.stderr
    dest = workbench / "code" / "proj"
    assert status(dest) == before_status
    assert snapshot(dest) == before_files


def test_monorepo_keeps_its_own_files(workbench, run_cli, tmp_path):
    files = {
        "AGENTS.md": "# mono agents\n",
        "CLAUDE.md": "@AGENTS.md\n",
        ".claude/settings.json": '{"permissions": {"allow": []}}\n',
        ".claude/skills/deploy/SKILL.md": "---\nname: deploy\n---\n",
        ".mcp.json": '{"mcpServers": {}}\n',
        "docs/plans/todo/.gitkeep": "",
        ".github/workflows/ci.yml": "name: ci\n",
        "services/a/main.py": "print('a')\n",
        "services/b/main.go": "package main\n",
    }
    src, _ = make_source(tmp_path, "mono", files=files)
    r = run_cli("adopt", "--path", str(src))
    assert r.returncode == 0, r.stderr
    dest = workbench / "code" / "mono"
    for rel, text in files.items():
        assert (dest / rel).read_text() == text, rel
    for rel in (".mcp.json", ".github", ".claude/skills", "services"):
        assert not (workbench / rel).exists(), rel
    assert "# mono agents" not in (workbench / "AGENTS.md").read_text()
    assert ok("config", "-f", ".gitmodules", "submodule.mono.path", cwd=workbench) == "code/mono"


def test_reports_plan_worktree_paths(workbench, run_cli, tmp_path):
    old = tmp_path / "elsewhere" / "proj" / ".claude/worktrees/epic--task"
    task = f"---\ntitle: t\nworktree: {old}\n---\n"
    rel = "docs/plans/in-progress/epic/tasks/task.md"
    src, _ = make_source(tmp_path, files={rel: task, "docs/plans/done/x.md": "worktree: rel\n"})
    r = run_cli("adopt", "--path", str(src))
    assert r.returncode == 0, r.stderr
    dest = workbench / "code" / "proj"
    assert (dest / rel).read_text() == task
    lines = [line for line in r.stdout.splitlines() if "worktree path" in line]
    assert len(lines) == 1
    assert f"code/proj/{rel}" in lines[0] and str(old) in lines[0]
    assert "not rewritten" in lines[0]


def test_no_origin_local_bare_creates_origin(workbench, run_cli, tmp_path):
    src, _ = make_source(tmp_path, "lone", origin=False)
    bares = tmp_path / "bares"
    r = run_cli("adopt", "--path", str(src), "--remote", f"local-bare:{bares}")
    assert r.returncode == 0, r.stderr
    bare = (bares / "lone.git").resolve()
    dest = workbench / "code" / "lone"
    assert ok("remote", "get-url", "origin", cwd=dest) == str(bare)
    assert ok("symbolic-ref", "HEAD", cwd=bare) == "refs/heads/feature"
    for b in ("trunk", "feature", "wt-out", "wt-in"):
        assert ok("rev-parse", b, cwd=bare) == ok("rev-parse", b, cwd=dest)
    assert ok("config", "-f", ".gitmodules", "submodule.lone.url", cwd=workbench) == str(bare)
    assert ok("config", "-f", ".gitmodules", "submodule.lone.branch", cwd=workbench) == "feature"
    assert ok("stash", "list", cwd=dest).count("keep-me") == 1


def test_relative_path_uses_invoking_cwd(workbench, tmp_path):
    src, _ = make_source(tmp_path)
    env = {**os.environ, "INIT_ENGINE_CWD": str(src.parent)}
    r = subprocess.run(
        [sys.executable, str(workbench / "scripts/init_engine/cli.py"), "adopt", "--path", "proj"],
        cwd=workbench,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert (workbench / "code/proj/.git").is_dir()


def test_adopt_url(workbench, run_cli, tmp_path, allow_file):
    src, bare = make_source(tmp_path)
    ok("push", "-q", "origin", "feature", cwd=src)
    r = run_cli("adopt", "--url", str(bare))
    assert r.returncode == 0, r.stderr
    dest = workbench / "code" / "proj"
    assert src.exists(), "url mode never touches a local checkout"
    assert ok("symbolic-ref", "--short", "HEAD", cwd=dest) == "trunk"
    assert (dest / "README.md").read_text() == "hello\n"
    assert not (dest / ".env").exists()
    assert ok("config", "-f", ".gitmodules", "submodule.proj.branch", cwd=workbench) == "trunk"
    assert ok("config", "-f", ".gitmodules", "submodule.proj.url", cwd=workbench) == str(bare)

    r = run_cli("adopt", "--url", f"file://{bare}", "--name", "again")
    assert r.returncode == 0, r.stderr
    assert ok("config", "-f", ".gitmodules", "submodule.again.path", cwd=workbench) == "code/again"
    assert ok("config", "-f", ".gitmodules", "submodule.again.branch", cwd=workbench) == "trunk"

    r = run_cli("adopt", "--url", str(bare))
    assert r.returncode == 1 and "already exists" in r.stderr


def test_adopt_url_branch_falls_back_to_clone(workbench, tmp_path, monkeypatch, allow_file):
    adopt, cli = _engine(workbench, monkeypatch)
    _, bare = make_source(tmp_path)
    monkeypatch.setattr(adopt, "remote_default_branch", lambda url, cwd=None: None)
    rc = cli.main(["--root", str(workbench), "adopt", "--url", str(bare)])
    assert rc == 0
    assert ok("config", "-f", ".gitmodules", "submodule.proj.branch", cwd=workbench) == "trunk"
    tracked = ok("ls-files", cwd=workbench).split()
    assert ".gitmodules" in tracked and "code/proj" in tracked


def test_adopt_url_refusals(workbench, run_cli, tmp_path):
    _, bare = make_source(tmp_path)
    r = run_cli("adopt", "--url", str(bare))
    assert r.returncode == 1
    assert "-c protocol.file.allow=always submodule add" in r.stderr
    assert not (workbench / "code/proj").exists()
    r = run_cli("adopt", "--url", "https://example.com/Bad_Repo.git")
    assert r.returncode == 1 and "--name" in r.stderr


def test_usage_errors(run_cli, tmp_path):
    assert run_cli("adopt").returncode == 2
    assert run_cli("adopt", "--path", str(tmp_path), "--url", "x").returncode == 2


def test_mise_task_adopt():
    task = REPO / "mise-tasks/init/adopt"
    assert task.is_file() and task.stat().st_mode & 0o111
    text = task.read_text()
    assert "cli.py adopt" in text and "INIT_ENGINE_CWD" in text


@pytest.mark.parametrize("flag", ["--path", "--url"])
def test_help_lists_flags(run_cli, flag):
    out = run_cli("adopt", "--help").stdout
    assert flag in out and "--name" in out and "--remote" in out


def test_adopt_allows_owner_vocabulary(workbench, run_cli, tmp_path, allow_file):
    import hashlib
    import json

    from init_helpers import personal_lint

    lint = personal_lint(workbench, "zorbax-owner")
    src, _ = make_source(tmp_path)
    bare = tmp_path / "zorbax-owner" / "proj.git"
    bare.parent.mkdir()
    ok("clone", "-q", "--bare", str(tmp_path / "origins" / "proj.git"), str(bare), cwd=tmp_path)
    r = run_cli("adopt", "--url", str(bare))
    assert r.returncode == 0, r.stderr
    assert "zorbax-owner" in (workbench / ".gitmodules").read_text()
    allow = json.loads((workbench / "scripts/personal-allow.local.json").read_text())["allow"]
    assert allow == [{"path": "**", "pattern": hashlib.sha256(b"zorbax-owner").hexdigest()}]
    assert lint().returncode == 0, lint().stdout
    assert ok("status", "--porcelain", cwd=workbench) == ""
