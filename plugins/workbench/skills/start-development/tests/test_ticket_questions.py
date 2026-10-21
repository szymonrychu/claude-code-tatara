"""ticket.py questions: the open-questions store across todo epics (D9, M4)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402,F401


def epic(root, name, design, phase="todo"):
    d = root / phase / name
    d.mkdir(parents=True)
    (d / "README.md").write_text(f"---\ntitle: {name}\n---\n\n# {name}\n")
    if design is not None:
        (d / "design.md").write_text(design)
    return d


def run(root, *args):
    # test_ticket_files swaps sys.modules["ticket"]; main and its TicketError must match
    return sys.modules["ticket"].main(["questions", "--root", str(root), *args])


@pytest.fixture
def plans(tmp_path):
    r = tmp_path / "docs" / "plans"
    epic(
        r,
        "alpha",
        "# A\n\n## Goals\n\nx\n\n## Open questions\n\n"
        "- Q1: Which db? [recommended: sqlite]\n- Q2: Done one [answer: yes]\n"
        "- Q3: No rec\n\n## Research\n\nz\n",
    )
    epic(r, "beta", "# B\n\n## Goals\n\nx\n")
    epic(r, "gamma", None)
    epic(
        r,
        "delta",
        "## Open questions\n\n- Q1: In progress? [recommended: n]\n",
        phase="in-progress",
    )
    return r


def test_aggregates_open_questions(plans, capsys):
    assert run(plans) == 0
    out = capsys.readouterr().out.splitlines()
    assert out == ["alpha Q1: Which db? [recommended: sqlite]", "alpha Q3: No rec"]


def test_list_json(plans, capsys):
    assert run(plans, "--json") == 0
    data = json.loads(capsys.readouterr().out)
    assert data == [
        {"epic": "alpha", "id": "Q1", "question": "Which db?", "recommended": "sqlite"},
        {"epic": "alpha", "id": "Q3", "question": "No rec", "recommended": None},
    ]


def test_add_creates_section(plans, capsys):
    assert run(plans, "--add", "beta", "Why?", "--recommended", "because") == 0
    assert run(plans, "--add", "beta", "Again?") == 0
    text = (plans / "todo" / "beta" / "design.md").read_text()
    assert "## Open questions\n\n- Q1: Why? [recommended: because]\n- Q2: Again?\n" in text
    assert run(plans, "--add", "alpha", "Next?") == 0
    assert "- Q4: Next?" in (plans / "todo" / "alpha" / "design.md").read_text()


def test_add_section_before_following_h2(plans):
    assert run(plans, "--add", "alpha", "Next?") == 0
    text = (plans / "todo" / "alpha" / "design.md").read_text()
    assert text.index("- Q4: Next?") < text.index("## Research")


def test_answer_closes_question(plans, capsys):
    assert run(plans, "--answer", "alpha", "Q1", "postgres") == 0
    text = (plans / "todo" / "alpha" / "design.md").read_text()
    assert "- Q1: Which db? [answer: postgres]" in text
    assert "recommended: sqlite" not in text
    capsys.readouterr()
    run(plans)
    assert capsys.readouterr().out.splitlines() == ["alpha Q3: No rec"]


@pytest.mark.parametrize(
    "args",
    [
        ["--answer", "nope", "Q1", "x"],
        ["--answer", "alpha", "Q9", "x"],
        ["--add", "nope", "x"],
        ["--add", "gamma", "x"],
    ],
)
def test_unknown_errors_no_write(plans, args, capsys):
    before = {p: p.read_text() for p in plans.rglob("*.md")}
    assert run(plans, *args) == 1
    assert "ticket.py:" in capsys.readouterr().err
    assert before == {p: p.read_text() for p in plans.rglob("*.md")}
    assert not (plans / "todo" / "gamma" / "design.md").exists()


def test_commits_as_questions(tmp_path):
    r = tmp_path / "docs" / "plans"
    epic(r, "alpha", "# A\n")
    for c in (
        ["init", "-q"],
        ["add", "-A"],
        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"],
    ):
        subprocess.run(["git", "-C", str(tmp_path), *c], check=True)
    assert run(r, "--add", "alpha", "Q?") == 0
    log = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "-1", "--format=%s"], capture_output=True, text=True
    ).stdout.strip()
    assert log == "chore(ticket): alpha questions"
