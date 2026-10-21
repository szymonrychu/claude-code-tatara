"""Tests for ticket.py rule: orchestrator rulings in task files and rulings.json (D1, D10)."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

SD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SD / "scripts"))
from test_ticket_run import cli, commit_all, git, mk_epic, mk_task  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "rule_mod", SD / "scripts" / "ticket_cmds" / "rule.py"
)
rule = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rule)

VALIDATE = SD.parents[1] / "workflows" / "validate-tasks.mjs"


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
def epic(root):
    ep = mk_epic(root)
    a = mk_task(root, ep, "Alpha")
    b = mk_task(root, ep, "Beta")
    c = mk_task(root, ep, "Gamma")
    commit_all(root.parents[1])
    return ep, root / "todo" / ep, a, b, c


def test_rule_accept_writes_both(epic, root):
    ep, d, a, b, c = epic
    r = cli(
        "rule",
        ep,
        "--accept",
        "alpha",
        "--reject",
        "beta",
        "--reason",
        "process only",
        "--root",
        root,
    )
    assert r.returncode == 0, r.stderr
    ta = a.read_text()
    assert re.search(r"^## Ruling\n\n- \d{4}-\d{2}-\d{2} accepted: process only$", ta, re.M)
    assert ta.index("## Ruling") < ta.index("## Notes")
    assert re.search(r"- \d{4}-\d{2}-\d{2} rejected: process only", b.read_text())
    assert "## Ruling" not in c.read_text()
    rl = json.loads((d / "rulings.json").read_text())
    assert [(e["task"], e["accept"], e["reason"]) for e in rl] == [
        ("alpha", True, "process only"),
        ("beta", False, "process only"),
    ]
    assert all(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z", e["at"]) for e in rl)


def test_rule_commits(epic, root):
    ep, *_ = epic
    r = cli("rule", ep, "--accept", "alpha", "--reason", "x", "--root", root)
    assert r.returncode == 0, r.stderr
    log = git(root.parents[1], "log", "-1", "--format=%s").stdout.strip()
    assert log == f"chore(ticket): {ep} rule"
    assert git(root.parents[1], "status", "--porcelain").stdout.strip() == ""


def test_rule_appends_second_ruling(epic, root):
    ep, d, a, *_ = epic
    cli("rule", ep, "--accept", "alpha", "--reason", "one", "--root", root)
    cli("rule", ep, "--accept", "alpha", "--reason", "two", "--root", root)
    assert a.read_text().count("## Ruling") == 1
    assert a.read_text().count(" accepted: ") == 2
    assert len(json.loads((d / "rulings.json").read_text())) == 2
    assert [e["reason"] for e in rule.read_rulings(d)] == ["one", "two"]


def test_rule_unknown_task_writes_nothing(epic, root):
    ep, d, a, *_ = epic
    before = a.read_text()
    r = cli("rule", ep, "--accept", "alpha,nope", "--reason", "x", "--root", root)
    assert r.returncode == 1 and "nope" in r.stderr
    assert a.read_text() == before and not (d / "rulings.json").exists()


def test_requires_main_checkout(epic, root, tmp_path):
    ep, *_ = epic
    wt = tmp_path / "wt"
    git(root.parents[1], "worktree", "add", "-b", "other", str(wt))
    r = cli("rule", ep, "--accept", "alpha", "--reason", "x", "--root", wt / "docs" / "plans")
    assert r.returncode == 1 and "main checkout" in r.stderr


def test_read_rulings_missing_is_empty(tmp_path):
    assert rule.read_rulings(tmp_path) == []


def _fill_section(text, name, body):
    return re.sub(rf"(^## {name}\n)\s*", rf"\g<1>\n{body}\n\n", text, count=1, flags=re.M)


def test_epic_with_rulings_lints(root):
    ep = mk_epic(root)
    ts = [mk_task(root, ep, t, files=f"{t.lower()}.py") for t in ("Alpha", "Beta")]
    d = root / "todo" / ep
    readme = d / "README.md"
    text = readme.read_text()
    for label in ("What", "How", "Why"):
        text = re.sub(rf"^{label}:[ \t]*$", f"{label}: text", text, flags=re.M)
    for name in ("Description", "Goals", "Non-goals"):
        text = _fill_section(text, name, "text")
    readme.write_text(text)
    for t in ts:
        t.write_text(_fill_section(t.read_text(), "Expected outcome", "It works."))
    (d / "approvals.json").write_text(
        json.dumps([{"id": "A1", "text": "all", "tasks": ["alpha", "beta"], "status": "approved"}])
    )
    commit_all(root.parents[1])
    base = subprocess.run(["node", str(VALIDATE), "--epic", str(d)], capture_output=True, text=True)
    assert base.returncode == 0, base.stderr + base.stdout
    r = cli("rule", ep, "--accept", "alpha", "--reject", "beta", "--reason", "x", "--root", root)
    assert r.returncode == 0, r.stderr
    assert (d / "rulings.json").exists() and "## Ruling" in ts[0].read_text()
    assert cli("lint", "--root", root).returncode == 0
    r = subprocess.run(["node", str(VALIDATE), "--epic", str(d)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
