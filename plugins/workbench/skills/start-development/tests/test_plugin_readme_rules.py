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
