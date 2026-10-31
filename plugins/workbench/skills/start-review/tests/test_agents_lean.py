"""The plan flow's agents: one plan-writer, one implementer, one whole-diff reviewer, one merger."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AGENTS = ROOT / "agents"
REPO = ROOT.parents[1]


def _text(name):
    return (AGENTS / f"{name}.md").read_text()


def _frontmatter(name):
    text = _text(name)
    assert text.startswith("---\n"), name
    end = text.index("\n---\n", 4)
    fm = {}
    for line in text[4:end].splitlines():
        if line[:1] not in (" ", "\t") and ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm, text[end + 5 :]


def _section(body, heading):
    parts = re.split(r"^## ", body, flags=re.M)
    for part in parts[1:]:
        if part.split("\n", 1)[0].strip() == heading:
            return part
    raise AssertionError(f"no ## {heading}")


RETIRED_AGENTS = (
    "spec-reviewer",
    "quality-reviewer",
    "planner",
    "record-writer",
    "retro-writer",
    "scope-auditor",
)


def test_retired_agents_are_untracked():
    out = subprocess.run(
        ["git", "ls-files", "--", *(f"plugins/workbench/agents/{n}.md" for n in RETIRED_AGENTS)],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert out.strip() == ""


def test_implementer_is_lean():
    fm, body = _frontmatter("implementer")
    assert fm["name"] == "implementer"
    assert fm["model"] == "sonnet"
    text = _text("implementer")
    for field in ("owns", "uses", "provides", "reimplemented"):
        assert f"`{field}`" not in text, field
    lowered = text.lower()
    for phrase in ("forks from", "git merge", "readset", "approved item"):
        assert phrase not in lowered, phrase
    for word in ("undelivered", "discovered", "tests.red", "handoff"):
        assert word in text, word
    flat = " ".join(body.split())
    for phrase in (
        "plan tree",
        "main checkout",
        "implementation-plan.md",
        "chunk",
        "git log",
        "builds nothing outside",
        "recommended, never built",
        "200 words",
        "same agent",
        "Never edit, delete, skip or xfail an existing test",
        "WIP:",
    ):
        assert phrase in flat, phrase
    assert "epic" not in flat.lower()
    text.encode("ascii")


def test_reviewer_verifies_then_reviews():
    fm, body = _frontmatter("reviewer")
    assert fm["name"] == "reviewer"
    assert "model" not in fm
    assert fm["tools"] == "[Read, Write, Grep, Glob, Bash]"
    order = " ".join(_section(body, "Order").split())
    steps = (
        "git status --porcelain",
        "git rev-parse HEAD",
        "Final verify",
        "under-delivery",
        "over-delivery",
        "debt markers",
        "quality",
    )
    positions = [order.find(step) for step in steps]
    assert -1 not in positions, dict(zip(steps, positions, strict=True))
    assert positions == sorted(positions), dict(zip(steps, positions, strict=True))
    for marker in ("TODO", "FIXME", "later", "follow-up", "out of scope", "phase 2"):
        assert marker in order, marker
    output = _section(body, "Output")
    for key in (
        "head",
        "verifyPassed",
        "undelivered",
        "overDelivered",
        "findings",
        "declined",
        "cannotVerify",
    ):
        assert f"`{key}`" in output, key
    assert "pointsActual" not in _text("reviewer")
    retro = " ".join(_section(body, "Retro").split())
    for phrase in (
        "templates/retro.md",
        "ticket.py path <plan> retro",
        "only on a clean pass",
        "the only file you write",
        "Recommendations",
        "discovered",
    ):
        assert phrase in retro, phrase
    flat = " ".join(body.split())
    assert "same reviewer" in flat
    assert "review-checklist.md" in flat
    _text("reviewer").encode("ascii")


def test_worktree_merger_has_a_plan_close():
    body = _frontmatter("worktree-merger")[1]
    close = " ".join(_section(body, "Plan close").split())
    for phrase in (
        "ticket.py close <plan> --verify",
        "rebase conflict",
        "in the plan tree",
        "run close again",
        "pushes",
        "opens the MR",
        "ticket.py move <plan> done",
    ):
        assert phrase in close, phrase
    assert "epic" not in " ".join(body.split()).lower()


def test_start_review_names_no_split_reviewers():
    skill_dir = ROOT / "skills" / "start-review"
    hits = [
        f"{path.relative_to(skill_dir)}: {name}"
        for path in sorted(skill_dir.rglob("*"))
        if path.is_file() and "tests" not in path.relative_to(skill_dir).parts
        for name in ("spec-reviewer", "quality-reviewer", "spec reviewer", "quality reviewer")
        if name in path.read_text(errors="ignore")
    ]
    assert hits == []


def _flat(name):
    return " ".join(_text(name).split())


def test_agents_list_read_once_edit_once():
    for name in ("implementer", "reviewer"):
        flat = _flat(name)
        for phrase in ("list every file", "one pass"):
            assert phrase in flat, (name, phrase)
    assert "once per red or green step" in _flat("implementer")
    assert "Run each Verify once" in _flat("reviewer")


def test_no_test_tampering():
    for name in ("implementer", "reviewer"):
        flat = _flat(name)
        assert "edit, delete, skip or xfail" in flat, name
        assert "no longer accurate" in flat, name
        assert "say which test and why" in flat, name


def test_reviewer_flags_xfail_and_compat_shims():
    flat = _flat("reviewer")
    assert "an added skip or xfail" in flat
    assert "backward compatibility shim" in flat
    assert "the plan did not ask for" in flat
    assert "high finding" in flat


def test_implementer_asks_instead_of_guessing():
    text = _text("implementer")
    report = " ".join(_section(_frontmatter("implementer")[1], "Report").split())
    assert "`questions`" in report
    flat = " ".join(text.split())
    assert "do not guess" in flat.lower()
    assert "backward compatibility" in flat


def test_reviewer_reports_no_points():
    assert "pointsActual" not in _text("reviewer")
    assert "storypoints" not in _text("reviewer").lower()
