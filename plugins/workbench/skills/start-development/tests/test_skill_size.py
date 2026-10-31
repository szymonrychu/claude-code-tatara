"""SKILL.md is loaded whole on every trigger: at most 150 lines, every reference it names exists."""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLUGIN = SKILL_DIR.parents[1]
REPO = PLUGIN.parents[1]
MAX_LINES = 150
# References that moved out of the skill, by the path SKILL.md links them with.
MOVED = {
    "tickets.md": "plugins/superpowers/references/tickets.md",
    **{
        n: f"${{CLAUDE_PLUGIN_ROOT}}/references/{n}"
        for n in (
            "worktrees.md",
            "hooks.md",
            "merge-hosts.md",
            "user-run-steps.md",
            "workbench-config.md",
        )
    },
}
LINK = re.compile(r"(?:\$\{CLAUDE_PLUGIN_ROOT\}/|plugins/[\w-]+/)?references/[a-z-]+\.md")
KEPT = ("non-negotiables.md",)


def test_skill_md_within_line_cap():
    text = (SKILL_DIR / "SKILL.md").read_text()
    n = len(text.splitlines())
    assert n <= MAX_LINES, f"SKILL.md is {n} lines, cap {MAX_LINES}"


def test_named_references_exist():
    text = (SKILL_DIR / "SKILL.md").read_text()
    named = set(LINK.findall(text))
    assert named, "SKILL.md names no reference"
    for link in named:
        if link.startswith("${CLAUDE_PLUGIN_ROOT}/"):
            path = PLUGIN / link.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
        elif link.startswith("plugins/"):
            path = REPO / link
        else:
            path = SKILL_DIR / link
        assert path.is_file(), link


def test_every_kept_reference_is_linked_from_skill():
    text = (SKILL_DIR / "SKILL.md").read_text()
    for name in KEPT:
        assert (SKILL_DIR / "references" / name).is_file(), name
        assert f"references/{name}" in text, name
    for name, link in MOVED.items():
        assert not (SKILL_DIR / "references" / name).exists(), name
        path = (
            PLUGIN / link.removeprefix("${CLAUDE_PLUGIN_ROOT}/")
            if link.startswith("${CLAUDE_PLUGIN_ROOT}/")
            else REPO / link
        )
        assert path.is_file() and link in text, link
    assert "retro.md" not in KEPT
