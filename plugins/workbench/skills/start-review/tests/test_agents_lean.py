"""The lean loop's agents: one implementer, one reviewer, one scope auditor, one planner."""

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


def test_split_reviewers_retired():
    out = subprocess.run(
        [
            "git",
            "ls-files",
            "plugins/workbench/agents/spec-reviewer.md",
            "plugins/workbench/agents/quality-reviewer.md",
        ],
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
        "integration worktree",
        "main checkout",
        "150 words",
        "same agent",
        "Never weaken or delete an existing test",
        "WIP:",
    ):
        assert phrase in flat, phrase
    text.encode("ascii")


def test_reviewer_verifies_then_reviews():
    fm, body = _frontmatter("reviewer")
    assert fm["name"] == "reviewer"
    assert "model" not in fm
    assert fm["tools"] == "[Read, Grep, Glob, Bash]"
    order = " ".join(_section(body, "Order").split())
    steps = (
        "git status --porcelain",
        "git rev-parse HEAD",
        "verify command",
        "every acceptance condition",
        "debt markers",
        "quality",
    )
    positions = [order.find(step) for step in steps]
    assert -1 not in positions, dict(zip(steps, positions, strict=True))
    assert positions == sorted(positions), dict(zip(steps, positions, strict=True))
    for marker in ("TODO", "FIXME", "later", "follow-up", "out of scope", "phase 2"):
        assert marker in order, marker
    assert "test:<file>::<name>" in order
    output = _section(body, "Output")
    for key in ("head", "verifyPassed", "unmetAcs", "findings", "declined", "cannotVerify"):
        assert f"`{key}`" in output, key
    flat = " ".join(body.split())
    assert "same reviewer" in flat
    assert "review-checklist.md" in flat
    _text("reviewer").encode("ascii")


def test_scope_auditor_and_planner_are_lean():
    for name in ("scope-auditor", "planner"):
        lowered = _text(name).lower()
        for word in ("ledger", "approvals", "plan-execute", "validate-tasks", "shared-parts"):
            assert word not in lowered, (name, word)
    audit = " ".join(_text("scope-auditor").split())
    for phrase in (
        "git diff <base>...<epic>",
        "Goals",
        "Non-goals",
        "every task",
        "acceptance condition",
        "duplicate sweep",
        "suggestedTask",
    ):
        assert phrase in audit, phrase
    fm, body = _frontmatter("planner")
    assert fm["model"] == "opus"
    flat = " ".join(body.split())
    for phrase in (
        "ticket.py lint <epic>",
        "ticket.py new-task",
        "verbatim",
        "`test:`",
        "`command:`",
        "depends_on",
        "one test file's worth of behaviour, at most 8 files",
        "more than five files",
    ):
        assert phrase in flat, phrase
    for word in ("contract", "ticket.py graph", "ticket.py facts", "ticket.py estimate"):
        assert word not in flat, word


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
