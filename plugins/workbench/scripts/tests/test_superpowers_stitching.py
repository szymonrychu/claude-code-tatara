"""Workbench helpers are stitched to the vanilla superpowers skills they serve."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
WB = REPO / "plugins" / "workbench"
STITCHES = {
    "superpowers:using-git-worktrees": [
        f"skills/{n}/SKILL.md"
        for n in ("git-worktrees-create", "git-worktrees-commit", "git-worktrees-push")
    ],
    "superpowers:finishing-a-development-branch": [
        f"skills/{n}/SKILL.md"
        for n in ("pullrequests-list", "pullrequests-update", "pullrequests-watch")
    ],
    "superpowers:receiving-code-review": ["skills/pullrequests-review-loop/SKILL.md"],
    "superpowers:brainstorming": [
        *(
            f"skills/{n}/SKILL.md"
            for n in (
                "start-research",
                "research-code-external",
                "research-code-internal",
                "research-docs",
                "research-papers",
            )
        ),
        "agents/reuse-hunter.md",
    ],
}


def test_each_helper_names_the_vanilla_skill_it_serves():
    missing = [
        f"{rel}: {skill}"
        for skill, rels in STITCHES.items()
        for rel in rels
        if skill not in (WB / rel).read_text()
    ]
    assert not missing, "\n".join(missing)


def test_grafana_debugging_continues_in_systematic_debugging():
    text = (
        REPO / "plugins/workbench-observability/skills/grafana-debugging-start/SKILL.md"
    ).read_text()
    assert "superpowers:systematic-debugging" in text


def test_template_update_names_no_fork():
    text = (WB / "skills/template-update/SKILL.md").read_text()
    assert "plugins/" + "superpowers" not in text
