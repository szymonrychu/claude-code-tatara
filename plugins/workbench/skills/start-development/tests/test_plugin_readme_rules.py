"""The plugin README rules list names every rule file the AGENTS.md block embeds."""

import re
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


def spans(prefix):
    return [s for s in re.findall(r"`([^`\n]+)`", README.read_text()) if prefix in s]


def test_readme_ticket_commands_match_tool():
    done = [s for s in spans("ticket.py task ") if "--status done" in s]
    new_task = spans("ticket.py new-task")
    assert done and new_task
    assert [s for s in done if "--points-actual" not in s] == []
    assert [s for s in new_task if "--points" not in s] == []


def test_readme_names_new_subcommands():
    readme = README.read_text()
    missing = [c for c in ("retro", "deltas", "actuals") if f"`ticket.py {c}" not in readme]
    assert not missing, f"README lacks ticket.py subcommands: {missing}"
