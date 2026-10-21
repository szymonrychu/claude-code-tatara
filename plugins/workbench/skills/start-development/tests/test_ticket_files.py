"""Tests for ticket.py core: layout, slugs, frontmatter, new-epic, new-task, path, guard, commit."""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SD = ROOT / "skills" / "start-development"
SCRIPT = SD / "scripts" / "ticket.py"


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


def new_epic(root, title="Cost and ticketing", *extra):
    return cli("new-epic", "--root", root, "--title", title, "--force", *extra)


def new_task(root, epic="cost-and-ticketing", title="Ticket core", *extra):
    return cli(
        "new-task",
        "--root",
        root,
        "--epic",
        epic,
        "--title",
        title,
        "--repo",
        "plugin",
        "--value",
        "One tool",
        "--files",
        "a.py,b.py",
        "--verify",
        'pytest -q -k "x y"',
        *extra,
    )


# (2) slugs and worktree names
def test_slug_cli_prints_capped_slug(root):
    r = cli("slug", "A Very Long Title That Goes Past The Twenty Eight Cap")
    assert r.returncode == 0
    out = r.stdout.strip()
    assert out == "a-very-long-title-that-goes"[:28].rstrip("-")
    assert len(out) <= 28 and not out.endswith("-")


def test_worktree_name_single_hyphen_cap_57(t):
    assert t.worktree_name("epic", "task") == "epic-task"
    a, b = "a" * 28, "b" * 28
    assert len(t.worktree_name(a, b)) == 57 == t.WORKTREE_MAX
    with pytest.raises(t.TicketError, match=r"58 characters, max 57"):
        t.worktree_name(a + "c", b)


# (1) layout
def test_phases_and_default_root(t):
    assert t.PHASES == ("todo", "in-progress", "done")
    assert t.default_root().parts[-2:] == ("docs", "plans")


def test_new_epic_readme(t, root):
    r = new_epic(
        root,
        "Cost and ticketing",
        "--blockers",
        "Other One,Other Two",
        "--repos",
        "a,b",
        "--what",
        "W",
        "--how",
        "H",
        "--why",
        "Y",
    )
    assert r.returncode == 0, r.stderr
    p = root / "todo" / "cost-and-ticketing" / "README.md"
    text = p.read_text()
    doc = t.load(text, p)
    m = doc.meta
    assert m["title"] == "Cost and ticketing"
    assert m["blockers"] == ["Other One", "Other Two"]
    assert m["stage"] == "build" and m["owner"] == "" and m["repos"] == ["a", "b"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", m["created"])
    assert re.findall(r"^## (.+)$", text, re.M) == [
        "Project brief",
        "Description",
        "Goals",
        "Non-goals",
        "Time",
        "Review",
    ]
    for line in ("What: W", "How: H", "Why: Y"):
        assert line in text
    assert t.dump(doc) == text


def test_new_epic_files(root, tmp_path):
    (tmp_path / "d.txt").write_text("Desc body")
    (tmp_path / "g.txt").write_text("- goal one")
    (tmp_path / "n.txt").write_text("- not this")
    r = new_epic(
        root,
        "Files",
        "--description-file",
        tmp_path / "d.txt",
        "--goals-file",
        tmp_path / "g.txt",
        "--non-goals-file",
        tmp_path / "n.txt",
    )
    assert r.returncode == 0, r.stderr
    text = (root / "todo" / "files" / "README.md").read_text()
    assert "Desc body" in text and "- goal one" in text and "- not this" in text


@pytest.mark.parametrize("phase", ["todo", "in-progress", "done"])
def test_new_epic_refuses_existing_in_any_phase(root, phase):
    (root / phase / "dup").mkdir(parents=True)
    r = new_epic(root, "Dup")
    assert r.returncode == 1
    assert phase in r.stderr


# (4) new-task
def test_new_task(t, root):
    new_epic(root)
    r = new_task(
        root,
        "cost-and-ticketing",
        "Ticket core",
        "--depends-on",
        "a,b",
        "--owns",
        "p",
        "--uses",
        "q",
        "--model",
        "sonnet",
        "--review",
        "full",
    )
    assert r.returncode == 0, r.stderr
    p = root / "todo" / "cost-and-ticketing" / "tasks" / "ticket-core.md"
    text = p.read_text()
    doc = t.load(text, p)
    m = doc.meta
    assert list(m) == [
        "title",
        "status",
        "repo",
        "value",
        "files",
        "verify",
        "depends_on",
        "owns",
        "uses",
        "model",
        "estimate",
        "actual",
        "review",
        "worktree",
        "branch",
        "verified_head",
        "run",
        "provides",
    ]
    assert m["status"] == "todo" and m["files"] == ["a.py", "b.py"]
    assert m["verify"] == 'pytest -q -k "x y"'
    assert m["depends_on"] == ["a", "b"] and m["owns"] == ["p"] and m["uses"] == ["q"]
    assert m["model"] == "sonnet" and m["review"] == "full"
    assert m["worktree"] == m["branch"] == m["verified_head"] == m["run"] == ""
    assert m["provides"] == []
    assert re.findall(r"^## (.+)$", text, re.M) == [
        "Requirement",
        "Acceptance conditions",
        "Files",
        "Interfaces",
        "Expected outcome",
        "Steps",
        "Notes",
    ]
    assert t.dump(doc) == text


def test_new_task_requirement_and_ac_files(root, tmp_path):
    new_epic(root)
    (tmp_path / "r.txt").write_text("Do the thing")
    (tmp_path / "ac.txt").write_text("- AC-1: works [evidence: test:t.py::x]")
    r = new_task(
        root,
        "cost-and-ticketing",
        "T",
        "--requirement-file",
        tmp_path / "r.txt",
        "--ac-file",
        tmp_path / "ac.txt",
    )
    assert r.returncode == 0, r.stderr
    text = (root / "todo" / "cost-and-ticketing" / "tasks" / "t.md").read_text()
    assert "Do the thing" in text and "- AC-1: works [evidence: test:t.py::x]" in text


def test_new_task_refusals(root):
    assert new_task(root, "nope").returncode == 1
    new_epic(root)
    assert new_task(root).returncode == 0
    dup = new_task(root)
    assert dup.returncode == 1 and "ticket-core" in dup.stderr
    (root / "done" / "closed").mkdir(parents=True)
    r = new_task(root, "closed")
    assert r.returncode == 1 and "done" in r.stderr


def test_new_task_in_progress_epic_allowed(root):
    (root / "in-progress" / "ip").mkdir(parents=True)
    assert new_task(root, "ip").returncode == 0


# (5) frontmatter
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


# (6) path
@pytest.mark.parametrize(
    "kind,rel",
    [
        ("readme", "README.md"),
        ("design", "design.md"),
        ("approvals", "approvals.json"),
        ("record", "record.md"),
        ("tasks", "tasks"),
    ],
)
def test_path(root, kind, rel):
    new_epic(root)
    r = cli("path", "--root", root, "cost-and-ticketing", kind)
    assert r.returncode == 0
    assert r.stdout.strip() == str(root.resolve() / "todo" / "cost-and-ticketing" / rel)


def test_path_follows_phase_and_unknown_epic(root):
    (root / "in-progress" / "e1").mkdir(parents=True)
    r = cli("path", "--root", root, "e1", "readme")
    assert "in-progress" in r.stdout
    bad = cli("path", "--root", root, "ghost", "readme")
    assert bad.returncode == 1


# (9) resolve_epic
def test_resolve_epic_slug_or_dir(t, root):
    new_epic(root)
    d = root / "todo" / "cost-and-ticketing"
    assert t.resolve_epic("cost-and-ticketing", root) == d
    assert t.resolve_epic(str(d), root) == d
    with pytest.raises(t.TicketError):
        t.resolve_epic("ghost", root)
    r = cli("path", "--root", root, str(d), "tasks")
    assert r.returncode == 0 and r.stdout.strip().endswith("cost-and-ticketing/tasks")


# (7) templates
def test_templates_have_no_parking_statuses():
    for name in ("epic.md", "task.md"):
        text = (SD / "templates" / name).read_text().lower()
        for word in ("deferred", "later", "wontfix", "follow-up"):
            assert word not in text, (name, word)


def test_task_statuses(t):
    assert t.TASK_STATUSES == ("todo", "in-progress", "done", "blocked", "escalated")
    assert t.EPIC_STAGES == ("build", "review")


# (8, 12) reference doc
def test_tickets_reference():
    text = (SD / "references" / "tickets.md").read_text()
    for needle in (
        "docs/plans/<phase>/<epic>/README.md",
        "todo",
        "in-progress",
        "done",
        "<epic>-<task>",
        "57",
        "Run name",
        "Integration branch",
        "slug freeze",
        "main checkout",
        "discovered",
        "{what, where, why}",
        "approvals.json",
        "design.md",
        "record.md",
        "record-writer",
        "escalated",
        "blocked",
    ):
        assert needle.lower() in text.lower(), needle
    assert "<epic>--<task>" not in text
    assert text.isascii()


def _doc(name):
    return (SD / "references" / name).read_text()


def test_tickets_doc_names_single_hyphen_and_integration():
    text = _doc("tickets.md")
    for needle in ("<epic>-<task>", "57", "Integration branch", "<configdir>/worktrees/<epic>"):
        assert needle in text, needle
    assert "<epic>--<task>" not in text


def test_tickets_doc_collision_rule_and_merge_line():
    text = _doc("tickets.md")
    assert "Collision rule" in text
    for cmd in ("new-epic", "new-task", "rename"):
        assert cmd in text, cmd
    assert "still on disk" in text
    assert "MERGE <task> --name <epic>-<task> --base <epic> --repo <repo>" in text


def test_worktrees_doc_integration_lifecycle():
    text = _doc("worktrees.md")
    for needle in (
        "<epic>-<task>",
        "57",
        "The integration tree",
        "<configdir>/worktrees/<epic>",
        "move <epic> in-progress",
        "worktree-merger",
        "merge.py --base <epic> --keep --verify",
        "Every role on a task",
        "never calls the built-in `EnterWorktree`",
        "move <epic> done",
    ):
        assert needle in text, needle


def test_tickets_doc_close_upgrade_and_fork_point():
    text = _doc("tickets.md")
    needles = ("close <epic> --verify <cmd>", "close.json", "worktrees <epic> --integration")
    for needle in (*needles, "fork_point"):
        assert needle in text, needle
    assert "recorded when the task lands" in text


# (10) guard and (11) commit helper
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
    r = cli("new-epic", "--root", plans, "--title", "X")
    assert r.returncode == 1
    assert "ticket.py: run in the main checkout, not a linked worktree" in r.stderr
    assert not (plans / "todo").exists()


def test_commit_helper_commits_only_given_paths(t, repo):
    plans = repo / "docs" / "plans"
    (plans / "todo" / "e").mkdir(parents=True)
    f = plans / "todo" / "e" / "README.md"
    f.write_text("hi")
    (repo / "dirty.txt").write_text("unrelated")
    (repo / "seed.txt").write_text("changed")
    t.commit_ticket_change("e", "new-epic", [f], plans)
    log = git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert log == "chore(ticket): e new-epic"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == ["docs/plans/todo/e/README.md"]
    status = git(repo, "status", "--porcelain").stdout
    assert "dirty.txt" in status and "seed.txt" in status


def test_commit_helper_noop_outside_git(t, root):
    f = root / "x.md"
    f.write_text("x")
    t.commit_ticket_change("e", "ev", [f], root)


def test_cli_commits_in_git_repo(repo):
    plans = repo / "docs" / "plans"
    (repo / "dirty.txt").write_text("unrelated")
    assert cli("new-epic", "--root", plans, "--title", "Alpha").returncode == 0
    assert git(repo, "log", "-1", "--format=%s").stdout.strip() == "chore(ticket): alpha new-epic"
    r = new_task(plans, "alpha", "First")
    assert r.returncode == 0, r.stderr
    subject = git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert subject == "chore(ticket): alpha new-task first"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert files == ["docs/plans/todo/alpha/tasks/first.md"]
    assert "?? dirty.txt" in git(repo, "status", "--porcelain").stdout
