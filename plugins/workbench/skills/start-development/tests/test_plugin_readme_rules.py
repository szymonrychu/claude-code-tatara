"""The plugin README rules list names every rule file the AGENTS.md block embeds."""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
README = REPO / "plugins" / "workbench" / "README.md"
AGENTS_MD = REPO / "scripts" / "harness" / "agents_md.py"


def rule_files():
    m = re.search(r"^RULE_FILES = \((.*?)\)", AGENTS_MD.read_text(), re.M)
    return re.findall(r'"([^"]+\.md)"', m.group(1))


def test_readme_lists_every_rules_block_file():
    readme = README.read_text()
    names = rule_files()
    assert names
    missing = [n for n in names if f"`rules/{n}`" not in readme]
    assert not missing, f"README rules list lacks: {missing}"


RETIRED_SUBCOMMANDS = (
    "new-epic",
    "new-task",
    "tasks",
    "task",
    "amend",
    "questions",
    "lint",
    "stage",
    "review",
    "actuals",
    "deltas",
    "retro",
    "roadmap",
    "index",
    "existing",
)


def test_readme_names_every_ticket_subcommand_and_no_retired_one():
    readme = README.read_text()
    ticket = REPO / "plugins/superpowers/scripts/ticket.py"
    out = subprocess.run(
        [sys.executable, str(ticket), "--help"], capture_output=True, text=True, check=True
    ).stdout
    real = re.search(r"\{([a-z,-]+)\}", out).group(1).split(",")
    missing = [c for c in real if f"`ticket.py {c}" not in readme]
    assert not missing, f"README lacks ticket.py subcommands: {missing}"
    named = [c for c in RETIRED_SUBCOMMANDS if f"`ticket.py {c}" in readme]
    assert not named, f"README names retired subcommands: {named}"


def test_housekeeping_rule_one_names_the_plan_writers():
    rule = (REPO / "plugins/workbench/rules/housekeeping.md").read_text()
    flat = " ".join(rule.split())
    for needle in (
        "plan.md and implementation-plan.md are written by the plan-writer",
        "retro.md by the reviewer",
        "dispatching",
    ):
        assert needle in flat, needle
    assert "design.md" not in flat and "record.md" not in flat
