"""Every `ticket.py <sub>` the flow docs name is a real subcommand of ticket.py."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "workbench"
SD = ROOT / "skills" / "start-development"
SP = ROOT.parent / "superpowers"
TICKET = SP / "scripts" / "ticket.py"
DOCS = [
    SD / "SKILL.md",
    *sorted((SD / "references").glob("*.md")),
    *sorted((SP / "references").glob("*.md")),
    ROOT / "skills" / "plan-run" / "SKILL.md",
    *(
        ROOT / "agents" / f"{n}.md"
        for n in ("plan-writer", "implementer", "reviewer", "worktree-merger")
    ),
]


def subcommands():
    out = subprocess.run(
        [sys.executable, str(TICKET), "--help"], capture_output=True, text=True, check=True
    ).stdout
    m = re.search(r"\{([a-z,-]+)\}", out)
    assert m, out
    return set(m.group(1).split(","))


def named_subcommands(text):
    names = set()
    for span in (m for line in text.splitlines() for m in re.findall(r"`([^`\n]*)`", line)):
        for m in re.finditer(r"ticket\.py(?: --root \S+)? ([a-z][a-z-]*)", span):
            names.add(m.group(1))
    return names


def test_help_lists_the_plan_subcommands():
    assert subcommands() == {
        "slug",
        "new",
        "check",
        "path",
        "rename",
        "move",
        "worktrees",
        "close",
        "reap",
        "migrate",
    }


def test_every_named_subcommand_is_real():
    real = subcommands()
    bad = []
    for doc in DOCS:
        if not doc.is_file():
            continue
        for name in sorted(named_subcommands(doc.read_text()) - real):
            bad.append(f"{doc.relative_to(ROOT)}: ticket.py {name}")
    assert not bad, bad


def test_skill_names_the_flow_commands():
    text = re.sub(r"\s+", " ", (SD / "SKILL.md").read_text())
    for needle in (
        "ticket.py check --title",
        "ticket.py new --title",
        "ticket.py path <plan>",
        "ticket.py move <plan> in-progress",
        "ticket.py close <plan> --verify",
        "chore(ticket): <plan> <event>",
    ):
        assert needle in text, needle


def test_ticket_commits_its_own_changes():
    t = re.sub(r"\s+", " ", (SD / "SKILL.md").read_text())
    assert "the orchestrator commits them" in t
