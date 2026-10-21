"""ticket.py decide records a gate answer in design.md and approvals.json (D9)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"

AC = "- AC1: it works [evidence: test:tests/test_x.py::test_works]"
DESIGN = """# Big design

## Summary

s

## Decisions

### D1: First
Do the first thing. (user decision)

### D2: Second
Do the second thing. (user decision)

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 First | alpha |
| D2 Second | beta |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|

## Review focus

- x
"""
LEDGER = [
    {"id": "A1", "text": "first", "decisions": ["D1"], "tasks": ["alpha"], "status": "approved"},
    {"id": "A2", "text": "second", "decisions": ["D2"], "tasks": ["beta"], "status": "approved"},
]


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


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
def epic(repo):
    root = repo / "docs" / "plans"
    assert cli("new-epic", "--root", root, "--title", "Big epic", "--force").returncode == 0
    d = root / "todo" / "big-epic"
    readme = d / "README.md"
    t = readme.read_text()
    t = t.replace("What: \nHow: \nWhy: ", "What: w\nHow: h\nWhy: y")
    for h in ("Description", "Goals", "Non-goals"):
        t = t.replace(f"## {h}\n\n\n", f"## {h}\n\nfilled\n")
    readme.write_text(t)
    for title in ("alpha", "beta", "gamma"):
        (root / f"{title}.req").write_text("Do the thing.")
        (root / f"{title}.ac").write_text(AC)
        r = cli(
            "new-task",
            "--root",
            root,
            "--epic",
            "big-epic",
            "--title",
            title,
            "--repo",
            "proj",
            "--value",
            "why",
            "--files",
            f"{title}.py",
            "--verify",
            "pytest -q",
            "--requirement-file",
            root / f"{title}.req",
            "--ac-file",
            root / f"{title}.ac",
        )
        assert r.returncode == 0, r.stderr
        (root / f"{title}.req").unlink()
        (root / f"{title}.ac").unlink()
        p = d / "tasks" / f"{title}.md"
        text = p.read_text()
        s, e = text.index("## Steps"), text.index("## Notes")
        text = text[:s] + "## Steps\n\n1. do it\n\n" + text[e:]
        stub = "What is true and observable when the task is done."
        p.write_text(text.replace(stub, "It works."))
    (d / "design.md").write_text(DESIGN)
    (d / "approvals.json").write_text(json.dumps(LEDGER, indent=2) + "\n")
    cli("tasks", "big-epic", "--root", root)  # settles the derived README Time section
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "epic")
    return root, d


def decide(root, *args):
    return cli("decide", "big-epic", *args, "--root", root)


def test_baseline_epic_lints_clean(epic):
    root, d = epic
    r = subprocess.run(
        ["node", str(ROOT / "workflows" / "validate-tasks.mjs"), "--epic", str(d)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def test_decide_new_approval(epic, repo):
    root, d = epic
    r = decide(root, "A3", "Use the new thing", "--tasks", "alpha,gamma")
    assert r.returncode == 0, r.stderr
    design = (d / "design.md").read_text()
    assert "### D3: Use the new thing\nUse the new thing (user decision)" in design
    assert design.index("### D3:") < design.index("## Decision coverage")
    assert "| D3 Use the new thing | alpha, gamma |" in design
    assert design.index("| D2 Second | beta |") < design.index("| D3 ")
    ledger = json.loads((d / "approvals.json").read_text())
    assert ledger[-1] == {
        "id": "A3",
        "text": "Use the new thing",
        "decisions": ["D3"],
        "tasks": ["alpha", "gamma"],
        "status": "approved",
    }
    log = git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert log == "chore(ticket): big-epic decide A3"
    files = git(repo, "show", "--name-only", "--format=").stdout.split()
    assert sorted(files) == [
        "docs/plans/todo/big-epic/approvals.json",
        "docs/plans/todo/big-epic/design.md",
    ]


def test_decide_existing_approval(epic):
    root, d = epic
    r = decide(root, "A1", "Extra for first", "--tasks", "gamma,alpha", "--title", "Extra")
    assert r.returncode == 0, r.stderr
    ledger = json.loads((d / "approvals.json").read_text())
    a1 = ledger[0]
    assert a1["decisions"] == ["D1", "D3"]
    assert a1["tasks"] == ["alpha", "gamma"]
    assert len(ledger) == 2
    assert "### D3: Extra" in (d / "design.md").read_text()


def test_title_defaults_to_first_60_chars(epic):
    root, d = epic
    text = "x" * 80
    assert decide(root, "A3", text, "--tasks", "alpha").returncode == 0
    assert f"### D3: {'x' * 60}\n" in (d / "design.md").read_text()


def test_unknown_task_fails_before_write(epic, repo):
    root, d = epic
    before = (d / "design.md").read_text()
    r = decide(root, "A3", "t", "--tasks", "alpha,nope")
    assert r.returncode == 1 and "nope" in r.stderr
    assert (d / "design.md").read_text() == before
    assert git(repo, "status", "--porcelain").stdout == ""


def test_missing_design_fails(epic):
    root, d = epic
    (d / "design.md").unlink()
    r = decide(root, "A3", "t", "--tasks", "alpha")
    assert r.returncode == 1 and "design.md" in r.stderr


def test_done_epic_fails(epic, repo):
    root, d = epic
    (root / "done").mkdir()
    git(repo, "mv", str(d), str(root / "done" / "big-epic"))
    r = decide(root, "A3", "t", "--tasks", "alpha")
    assert r.returncode == 1 and "done" in r.stderr


def test_decide_rolls_back_on_lint_failure(epic, repo):
    root, d = epic
    ledger_path = d / "approvals.json"
    broken = json.loads(ledger_path.read_text())
    broken[1]["decisions"] = []  # empty decisions make the post-write lint fail
    ledger_path.write_text(json.dumps(broken, indent=2) + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "break")
    head = git(repo, "rev-parse", "HEAD").stdout
    design, ledger = (d / "design.md").read_text(), ledger_path.read_text()
    r = decide(root, "A3", "t", "--tasks", "alpha")
    assert r.returncode == 1
    assert "approvals:" in r.stdout + r.stderr
    assert (d / "design.md").read_text() == design
    assert ledger_path.read_text() == ledger
    assert git(repo, "rev-parse", "HEAD").stdout == head


def test_decide_keeps_lint_green(epic):
    root, d = epic
    r = decide(root, "A3", "Use the new thing", "--tasks", "alpha,gamma")
    assert r.returncode == 0, r.stderr
    validator = str(ROOT / "workflows" / "validate-tasks.mjs")
    lint = subprocess.run(["node", validator, "--epic", str(d)], capture_output=True, text=True)
    assert lint.returncode == 0, lint.stdout + lint.stderr
