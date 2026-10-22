"""Clone, ask, get a working project: the template instantiated three ways, offline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import denylist_terms, git, production_env, run, secret_shaped  # noqa: E402

BEGIN = "<!-- workbench:uninitialised:begin -->"


def assert_healthy(tree: Path, components: int) -> None:
    doc = run(sys.executable, "scripts/doctor.py", "--root", str(tree), cwd=tree).stdout
    assert "metarepo" in doc, doc
    assert f"components: {components}" in doc, doc
    assert BEGIN not in (tree / "AGENTS.md").read_text()
    run(sys.executable, "scripts/check_personal.py", "--root", str(tree), cwd=tree)


def assert_single_commit_clean(tree: Path, mise) -> None:
    assert git("status", "--porcelain", cwd=tree) == ""
    log = git("log", "--format=%s", cwd=tree).splitlines()
    assert len([m for m in log if m.startswith("chore(workbench): initialise")]) == 1, log
    assert len(log) == 2, log  # the template commit plus the one init commit
    r = mise("run", "lint", check=False)
    assert r.returncode == 0, (r.stdout, r.stderr)


def make_origin_repo(
    base: Path, name: str, owner: str = "origins", secret: str | None = None
) -> Path:
    """A checkout with an origin, a stash, an untracked .env and a linked worktree.
    `owner` is the directory holding the bare origin, so it appears in the origin URL;
    `secret` is committed to the checkout as a fixture file."""
    bare = base / owner / f"{name}.git"
    bare.parent.mkdir(parents=True)
    git("init", "-q", "--bare", "-b", "main", str(bare), cwd=base)
    src = base / "elsewhere" / name
    src.mkdir(parents=True)
    git("init", "-q", "-b", "main", cwd=src)
    (src / "README.md").write_text("hello\n")
    (src / ".gitignore").write_text(".env\n")
    (src / ".mise.toml").write_text('[tasks.test]\nrun = "true"\n')
    if secret:
        (src / "fixture.txt").write_text(f"token = {secret}\n")
    git("add", "-A", cwd=src)
    git("commit", "-q", "-m", "init", cwd=src)
    git("remote", "add", "origin", str(bare), cwd=src)
    git("push", "-q", "origin", "main", cwd=src)
    git("branch", "--set-upstream-to=origin/main", "main", cwd=src)
    (src / "README.md").write_text("stashed\n")
    git("stash", "push", "-q", "-m", "keep", cwd=src)
    (src / ".env").write_text("SECRET=1\n")
    git("worktree", "add", "-q", "-b", "wt", str(base / f"{name}-wt"), cwd=src)
    return src


def test_init_leaves_clean_green_tree(template, engine, mise, tmp_path):
    engine(
        "new", "--name", "demo",
        "--component", "api:python", "--component", "svc:go",
        "--remote", f"local-bare:{tmp_path / 'remotes'}",
        "--purpose", "A demo project", "--harness", "cursor,copilot",
    )  # fmt: skip
    for name in ("api", "svc"):
        assert (tmp_path / "remotes" / f"{name}.git").is_dir()
        assert (template / "code" / name / ".git").exists()
    assert_healthy(template, 2)
    out = mise("run", "code:test")
    assert out.returncode == 0, out.stderr
    assert_single_commit_clean(template, mise)
    tracked = git("ls-files", cwd=template).splitlines()
    assert any(f.startswith(".cursor/rules/") for f in tracked), tracked
    assert any(f.startswith(".github/instructions/") for f in tracked), tracked
    r = mise("run", "harness-setup", "--", "--check", check=False)
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert not (template / "docs/plans/facts.md").exists()


def test_adopt_existing_repo(template, engine, mise, tmp_path):
    src = make_origin_repo(tmp_path, "legacy")
    wt = tmp_path / "legacy-wt"
    engine("adopt", "--path", str(src), "--purpose", "Adopted project")
    comp = template / "code" / "legacy"
    assert git("stash", "list", cwd=comp).count("keep") == 1
    assert (comp / ".env").read_text() == "SECRET=1\n"
    assert git("remote", "get-url", "origin", cwd=comp) == str(tmp_path / "origins" / "legacy.git")
    assert_healthy(template, 1)
    mise("run", "code:test")
    assert_single_commit_clean(template, mise)
    # the linked worktree still resolves its repository and can commit
    assert wt.is_dir()
    assert git("rev-parse", "--is-inside-work-tree", cwd=wt) == "true"
    (wt / "new.txt").write_text("x\n")
    git("add", "new.txt", cwd=wt)
    git("commit", "-q", "-m", "in worktree", cwd=wt)
    assert "in worktree" in git("log", "-1", "--format=%s", "wt", cwd=comp)


def test_component_add_remove(template, engine, tmp_path):
    engine(
        "new", "--name", "demo", "--component", "api:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}", "--purpose", "demo",
    )  # fmt: skip
    engine(
        "component", "add", "--component", "worker:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}",
    )  # fmt: skip
    assert (template / "code/worker/.git").exists()
    assert_healthy(template, 2)
    assert git("status", "--porcelain", cwd=template) == ""
    assert git("log", "-1", "--format=%s", cwd=template) == "chore(workbench): add component worker"
    # refusal path: a dirty checkout keeps the component and changes nothing
    (template / "code/worker/README.md").write_text("dirty\n")
    before = git("status", "--porcelain", cwd=template)
    r = engine("component", "remove", "--name", "worker", check=False)
    assert r.returncode == 1 and "uncommitted" in r.stderr, (r.stdout, r.stderr)
    assert (template / "code/worker").is_dir()
    assert git("status", "--porcelain", cwd=template) == before
    # clean again: removal succeeds
    git("checkout", "--", "README.md", cwd=template / "code/worker")
    engine("component", "remove", "--name", "worker")
    assert not (template / "code/worker").exists()
    assert "worker" not in (template / ".gitmodules").read_text()
    assert_healthy(template, 1)


def assert_green(tree: Path, mise) -> None:
    """lint and test exit 0 and nothing is left uncommitted."""
    for task in ("lint", "test"):
        r = run("mise", "run", task, cwd=tree, check=False, env=production_env())
        assert r.returncode == 0, (task, r.stdout[-3000:], r.stderr[-3000:])
        assert git("status", "--porcelain", cwd=tree) == "", task


def test_new_init_leaves_green_tree(template, engine, mise, tmp_path):
    denylist_terms(template, "quokkaproj")
    engine(
        "new", "--name", "quokkaproj", "--component", "api:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}", "--purpose", "quokkaproj demo",
    )  # fmt: skip
    assert "quokkaproj" in (template / "AGENTS.md").read_text().lower()
    assert_green(template, mise)


def test_adopt_leaves_green_tree(template, engine, mise, tmp_path):
    denylist_terms(template, "wombatowner")
    secret = secret_shaped()
    src = make_origin_repo(tmp_path, "legacy", owner="wombatowner", secret=secret)
    engine("adopt", "--path", str(src), "--purpose", "Adopted project")
    assert "wombatowner" in (template / ".gitmodules").read_text()
    assert secret in (template / "code/legacy/fixture.txt").read_text()
    assert_green(template, mise)


def test_second_component_add_stays_green(template, engine, mise, tmp_path):
    denylist_terms(template, "wombatowner", "quokkaproj")
    src = make_origin_repo(tmp_path, "legacy", owner="wombatowner", secret=secret_shaped())
    engine("adopt", "--path", str(src), "--purpose", "quokkaproj adopted")
    assert_green(template, mise)
    engine(
        "component", "add", "--component", "worker:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}",
    )  # fmt: skip
    assert (template / "code/worker/.git").exists()
    assert_green(template, mise)


def test_suite_green_on_initialised_copy(template, engine, tmp_path):
    engine(
        "new", "--name", "demo", "--component", "api:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}", "--purpose", "demo",
    )  # fmt: skip
    # the suite asserts production git behaviour, so it runs without the e2e file-transport grant
    r = run(
        sys.executable, "-m", "pytest", "scripts/tests", "-q", "-p", "no:cacheprovider",
        cwd=template, check=False, env=production_env(),
    )  # fmt: skip
    assert r.returncode == 0, r.stdout[-4000:] + r.stderr[-2000:]
