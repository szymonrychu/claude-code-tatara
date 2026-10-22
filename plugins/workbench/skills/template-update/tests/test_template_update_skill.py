"""template-update skill: frontmatter, engine call only through mise, refusals, README."""

import re
import subprocess
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
ROOT = SKILLS.parents[2]
CLI = ROOT / "scripts" / "init_engine" / "cli.py"
BODY = (SKILLS / "template-update" / "SKILL.md").read_text()
README = (SKILLS.parent / "README.md").read_text()


def test_frontmatter():
    m = re.match(r"---\nname: template-update\ndescription: >\n((?:  .+\n)+)---\n", BODY)
    assert m, "frontmatter"
    desc = " ".join(m.group(1).split())
    assert len(m.group(1)) > 80
    for trigger in (
        "update from the template",
        "pull template updates",
        "refresh the workbench from the template",
    ):
        assert trigger in desc


def test_engine_only_through_mise_task():
    for bad in ("cli.py", "init_engine", "CLAUDE_PLUGIN_ROOT", "git push"):
        assert bad not in BODY.replace("never push", "")
    assert "mise run init:update" in BODY


def test_flags_exist_in_cli_help():
    helptext = subprocess.run(
        [sys.executable, str(CLI), "update", "--help"], capture_output=True, text=True, check=True
    ).stdout
    calls = re.findall(r"mise run init:update(?: -- ([^\n`]*))?", BODY)
    assert calls
    flags = {f for c in calls for f in re.findall(r"--[a-z][a-z-]*", c)}
    assert {"--url", "--branch", "--base"} <= flags
    for flag in flags:
        assert flag in helptext, flag


def test_asks_only_for_unrelated_history_base():
    assert "Ask the user nothing on the normal path" in BODY
    assert "only question" in BODY
    assert "candidate base" in BODY
    assert "mise run init:update -- --base <sha>" in BODY


def test_reports_commit_and_refusals():
    for needle in (
        "kept project side:",
        "nothing was pushed",
        "git rev-parse HEAD",
        "Template-Commit:",
        "init:refresh",
        "template/<branch>",
        "run `init` first",
        "up to date",
        "Dirty tree",
        "Lint failure",
    ):
        assert needle in BODY, needle


def test_readme_lists_the_skill():
    assert re.search(r"^template-update\s+\S", README, re.M)
    assert "mise run init:update" in README
