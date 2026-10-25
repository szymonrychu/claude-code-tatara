"""The plugin README rules list names every rule file the AGENTS.md block embeds."""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
README = REPO / "plugins" / "workbench" / "README.md"
AGENTS_MD = REPO / "scripts" / "harness" / "agents_md.py"
TICKET = REPO / "plugins/workbench/skills/start-development/scripts/ticket.py"


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


def required_flags(sub):
    out = subprocess.run(
        [sys.executable, str(TICKET), sub, "--help"], capture_output=True, text=True, check=True
    ).stdout
    usage = out.split("\n\n", 1)[0]
    return re.findall(r"--[a-z-]+", re.sub(r"\[[^\]]*\]", "", usage))


def test_readme_ticket_commands_match_tool():
    done = [s for s in spans("ticket.py task ") if "--status done" in s]
    new_task = spans("ticket.py new-task")
    assert done and new_task
    assert [s for s in done if "--points-actual" not in s] == []
    required = required_flags("new-task")
    assert "--points" in required and "--epic" in required
    for span in new_task:
        assert [f for f in required if f not in span] == [], span
        after = span.split("new-task", 1)[1].split()
        assert after and after[0].startswith("--"), f"positional after new-task: {span}"


def test_readme_names_new_subcommands():
    readme = README.read_text()
    missing = [
        c for c in ("retro", "deltas", "actuals", "migrate") if f"`ticket.py {c}" not in readme
    ]
    assert not missing, f"README lacks ticket.py subcommands: {missing}"
