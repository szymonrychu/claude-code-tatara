"""Tests for ticket.py core: layout, slugs, frontmatter, new, path, old-format refusal, guard,
commit."""

import datetime
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SD = ROOT / "skills" / "start-development"
SCRIPT = SD / "scripts" / "ticket.py"
OLD_FORMAT = "old epic format under {}; run ticket.py migrate --all"


def _load():
    spec = importlib.util.spec_from_file_location("ticket", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ticket"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def t():
    return _load()


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def new(root, title="Cost and ticketing", *extra):
    return cli("new", "--root", root, "--title", title, "--force", *extra)


# slugs
def test_slug_cli_prints_capped_slug(root):
    r = cli("slug", "A Very Long Title That Goes Past The Twenty Eight Cap")
    assert r.returncode == 0
    out = r.stdout.strip()
    assert out == "a-very-long-title-that-goes"[:28].rstrip("-")
    assert len(out) <= 28 and not out.endswith("-")


# layout
def test_phases_and_default_root(t):
    assert t.PHASES == ("todo", "in-progress", "done")
    assert t.default_root().parts[-2:] == ("docs", "plans")


# new
def test_new_writes_plan_md_from_the_template(t, root):
    r = new(root, "Cost and ticketing", "--repos", "a,b")
    assert r.returncode == 0, r.stderr
    p = root / "todo" / "cost-and-ticketing" / "plan.md"
    assert r.stdout.strip().splitlines()[-1] == str(p)
    assert sorted(x.name for x in p.parent.iterdir()) == ["plan.md"]
    text = p.read_text()
    doc = t.load(text, p)
    assert list(doc.meta) == ["title", "repos", "created", "owner", "rung"]
    assert doc.meta == {
        "title": "Cost and ticketing",
        "repos": ["a", "b"],
        "created": datetime.date.today().isoformat(),
        "owner": "",
        "rung": "",
    }
    assert re.findall(r"^# (.+)$", text, re.M) == ["Cost and ticketing"]
    template = (SD / "templates" / "plan.md").read_text()
    assert re.findall(r"^## (.+)$", text, re.M) == re.findall(r"^## (.+)$", template, re.M)
    assert t.dump(doc) == text


def test_new_without_repos_is_an_empty_list(t, root):
    assert new(root, "Alpha").returncode == 0
    p = root / "todo" / "alpha" / "plan.md"
    assert t.load(p.read_text(), p).meta["repos"] == []


def test_new_refuses_a_title_without_usable_characters(root):
    r = new(root, "!!!")
    assert r.returncode == 1 and "no usable characters" in r.stderr
    assert not (root / "todo").exists()


@pytest.mark.parametrize("phase", ["todo", "in-progress", "done"])
def test_new_refuses_existing_slug_in_any_phase(root, phase):
    (root / phase / "dup").mkdir(parents=True)
    (root / phase / "dup" / "plan.md").write_text("---\ntitle: Dup\n---\n")
    r = new(root, "Dup")
    assert r.returncode == 1
    assert f"plan slug 'dup' already exists in {phase}" in r.stderr


def test_new_has_no_task_or_epic_options(root):
    for opt in ("--blockers", "--goals-file", "--what"):
        r = cli("new", "--root", root, "--title", "X", opt, "y")
        assert r.returncode == 2 and opt in r.stderr, opt


# frontmatter
def test_frontmatter_scalars_and_quotes(t):
    text = (
        "---\na: plain\nb: 'sin''gle'\nc: \"dou\\\"ble\"\nd: [x, 'y z', \"w\"]\ne: []\n---\nbody\n"
    )
    doc = t.load(text, "f.md")
    assert doc.meta == {
        "a": "plain",
        "b": "sin'gle",
        "c": 'dou"ble',
        "d": ["x", "y z", "w"],
        "e": [],
    }
    assert doc.body == "body\n"


@pytest.mark.parametrize("fm", ["a:\n  b: 1\n", "a:\n  - x\n  - y\n", "a: {b: 1}\n"])
def test_frontmatter_rejects_nested(t, fm):
    with pytest.raises(t.TicketError, match=r"f\.md:2: unsupported frontmatter"):
        t.load(f"---\n{fm}---\n", "f.md")


def test_frontmatter_roundtrip_awkward_values(t):
    meta = {
        "t": "has: colon, and # hash",
        "q": 'a "quote" \\ back',
        "e": "",
        "l": ["a, b", "c"],
        "n": "123",
        "s": " lead",
    }
    out = t.dump(t.Doc(meta, "B\n"))
    again = t.load(out, "x")
    assert again.meta == meta and t.dump(again) == out


def test_frontmatter_roundtrip_of_the_plan_template(t):
    p = SD / "templates" / "plan.md"
    text = p.read_text()
    assert t.dump(t.load(text, p)) == text


# path
@pytest.mark.parametrize(
    "kind,rel",
    [
        ("plan", "plan.md"),
        ("implementation", "implementation-plan.md"),
        ("retro", "retro.md"),
        ("close", "close.json"),
    ],
)
def test_path(root, kind, rel):
    new(root)
    r = cli("path", "--root", root, "cost-and-ticketing", kind)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(root.resolve() / "todo" / "cost-and-ticketing" / rel)


@pytest.mark.parametrize("kind", ["readme", "design", "record", "tasks", "approvals"])
def test_path_has_no_epic_kinds(root, kind):
    new(root)
    r = cli("path", "--root", root, "cost-and-ticketing", kind)
    assert r.returncode == 2 and kind in r.stderr


def test_path_follows_phase_and_unknown_plan(root):
    (root / "in-progress" / "p1").mkdir(parents=True)
    (root / "in-progress" / "p1" / "plan.md").write_text("---\ntitle: P1\n---\n")
    r = cli("path", "--root", root, "p1", "plan")
    assert r.returncode == 0 and "in-progress" in r.stdout
    bad = cli("path", "--root", root, "ghost", "plan")
    assert bad.returncode == 1 and "unknown plan 'ghost'" in bad.stderr


def test_resolve_plan_slug_or_dir(t, root, tmp_path):
    new(root)
    d = root / "todo" / "cost-and-ticketing"
    assert t.resolve_plan("cost-and-ticketing", root) == d
    assert t.resolve_plan(str(d), root) == d
    with pytest.raises(t.TicketError, match="unknown plan"):
        t.resolve_plan("ghost", root)
    outside = tmp_path / "elsewhere" / "p"
    outside.mkdir(parents=True)
    with pytest.raises(t.TicketError, match="outside the plans root"):
        t.resolve_plan(str(outside), root)


# old-format refusal
def _old_epic(root, phase="done", name="old-epic"):
    d = root / phase / name
    (d / "tasks").mkdir(parents=True)
    (d / "README.md").write_text("---\ntitle: Old\n---\n\n# Old\n")
    return d


@pytest.mark.parametrize(
    "args",
    [
        ["new", "--title", "Fresh"],
        ["check", "--title", "Fresh"],
        ["rename", "good", "Better"],
        ["path", "good", "plan"],
        ["move", "good", "in-progress"],
        ["move", "good", "done"],
        ["worktrees", "good"],
        ["close", "good", "--verify", "true"],
        ["reap", "--dry-run"],
    ],
)
def test_old_epic_format_is_refused_by_every_plan_command(root, args):
    new(root, "Good")
    old = _old_epic(root)
    r = cli(*args, "--root", root)
    assert r.returncode == 1, (args, r.stdout, r.stderr)
    assert OLD_FORMAT.format(old.resolve()) in r.stderr, r.stderr
    assert sorted(p.name for p in (root / "todo").iterdir()) == ["good"]


def test_old_epic_format_refused_when_the_plan_itself_is_old(root):
    old = _old_epic(root, "todo")
    r = cli("path", "--root", root, "old-epic", "plan")
    assert r.returncode == 1
    assert OLD_FORMAT.format(old.resolve()) in r.stderr


def test_dir_with_neither_plan_nor_readme_is_refused(root):
    (root / "todo" / "empty").mkdir(parents=True)
    r = cli("check", "--root", root, "--title", "Fresh")
    assert r.returncode == 1 and "no plan.md under" in r.stderr


# (8, 12) reference doc
def test_tickets_reference():
    text = (SD / "references" / "tickets.md").read_text()
    for needle in (
        "docs/plans/<phase>/<epic>/README.md",
        "todo",
        "in-progress",
        "done",
        "57",
        "Integration branch",
        "slug freeze",
        "main checkout",
        "discovered",
        "{what, where, why}",
        "design.md",
        "record.md",
        "record-writer",
        "escalated",
        "blocked",
    ):
        assert needle.lower() in text.lower(), needle
    for gone in ("<epic>--<task>", "approvals.json", "Run name", "rulings.json"):
        assert gone not in text, gone
    assert text.isascii()


def _doc(name):
    return " ".join((SD / "references" / name).read_text().split())


def test_tickets_doc_integration_naming_and_collision_rule():
    text = _doc("tickets.md")
    for needle in (
        "Integration branch",
        "<configdir>/worktrees/<epic>",
        "Collision rule",
        "still on disk",
    ):
        assert needle in text, needle
    for cmd in ("new-epic", "new-task", "rename"):
        assert cmd in text, cmd
    assert "MERGE <task>" not in text


def test_worktrees_doc_integration_lifecycle():
    text = _doc("worktrees.md")
    for needle in (
        "The integration tree",
        "<configdir>/worktrees/<epic>",
        "move <epic> in-progress",
        "worktree-merger",
        "Every role on a task",
        "never calls the built-in `EnterWorktree`",
        "move <epic> done",
    ):
        assert needle in text, needle
    for gone in ("<epic>-<task>", "merge.py --base <epic> --keep", "fork_point", "forward merge"):
        assert gone not in text, gone


def test_tickets_doc_close():
    text = _doc("tickets.md")
    for needle in ("close <epic> --verify <cmd>", "close.json", "exit 4"):
        assert needle in text, needle
    assert "fork_point" not in text


# guard and commit helper
@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "a@b.c")
    git(r, "config", "user.name", "T")
    (r / "seed.txt").write_text("x")
    git(r, "add", "-A")
    git(r, "commit", "-qm", "seed")
    return r


def test_guard_non_git_passes(t, root):
    t.require_main_checkout(root)


def test_guard_main_checkout_passes(t, repo):
    (repo / "docs" / "plans").mkdir(parents=True)
    t.require_main_checkout(repo / "docs" / "plans")


def test_guard_linked_worktree_refuses(repo, tmp_path):
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", "-b", "side", str(wt))
    plans = wt / "docs" / "plans"
    plans.mkdir(parents=True)
    r = cli("new", "--root", plans, "--title", "X")
    assert r.returncode == 1
    assert "ticket.py: run in the main checkout, not a linked worktree" in r.stderr
    assert not (plans / "todo").exists()


def test_commit_helper_commits_only_given_paths(t, repo):
    plans = repo / "docs" / "plans"
    (plans / "todo" / "e").mkdir(parents=True)
    f = plans / "todo" / "e" / "plan.md"
    f.write_text("hi")
    (repo / "dirty.txt").write_text("unrelated")
    (repo / "seed.txt").write_text("changed")
    t.commit_ticket_change("e", "new", [f], plans)
    log = git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert log == "chore(ticket): e new"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == ["docs/plans/todo/e/plan.md"]
    status = git(repo, "status", "--porcelain").stdout
    assert "dirty.txt" in status and "seed.txt" in status


def test_commit_helper_refuses_paths_outside_root(t, repo, tmp_path):
    plans = repo / "docs" / "plans"
    plans.mkdir(parents=True)
    with pytest.raises(t.TicketError, match="outside"):
        t.commit_ticket_change("e", "new", [repo / "seed.txt"], plans)


def test_commit_helper_noop_outside_git(t, root):
    f = root / "x.md"
    f.write_text("x")
    t.commit_ticket_change("e", "ev", [f], root)


def test_new_commits_exactly_plan_md(repo):
    plans = repo / "docs" / "plans"
    (repo / "dirty.txt").write_text("unrelated")
    r = cli("new", "--root", plans, "--title", "Alpha")
    assert r.returncode == 0, r.stderr
    assert git(repo, "log", "-1", "--format=%s").stdout.strip() == "chore(ticket): alpha new"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == ["docs/plans/todo/alpha/plan.md"]
    assert "?? dirty.txt" in git(repo, "status", "--porcelain").stdout
