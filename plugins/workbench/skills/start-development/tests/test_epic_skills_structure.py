"""Structure of the four epic lifecycle skills: thin wrappers over ticket.py."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

# skill -> ticket.py invocations its body must name verbatim
SKILLS = {
    "epic-create": ["ticket.py check --title", "ticket.py new-epic", "--force", "exit 3"],
    "epic-task-create": ["ticket.py new-task --epic", "ticket.py lint"],
    "epic-move": [
        "ticket.py move <epic> in-progress",
        "ticket.py move <epic> done",
        "ticket.py tasks <epic>",
    ],
    "epic-worktrees-remove": [
        "ticket.py reap --epic <epic> --dry-run",
        "ticket.py reap --epic <epic>",
    ],
}


def read(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def frontmatter(text):
    lines = text.split("\n")
    assert lines[0] == "---"
    end = lines.index("---", 1)
    return dict(ln.split(": ", 1) for ln in lines[1:end])


@pytest.mark.parametrize("name", SKILLS)
def test_skill_exists_with_matching_frontmatter(name):
    assert (ROOT / "skills" / name / "SKILL.md").is_file()
    text = read(name)
    fm = frontmatter(text)
    assert set(fm) == {"name", "description"}
    assert fm["name"] == name
    desc = fm["description"]
    assert desc.startswith('"') and desc.endswith('"') and len(desc) > 2
    text.encode("ascii")


@pytest.mark.parametrize("name,needles", SKILLS.items())
def test_body_names_ticket_subcommands(name, needles):
    body = read(name)
    for n in needles:
        assert n in body, f"{name} must mention {n!r}"


def test_skills_are_short():
    for name in SKILLS:
        assert len(read(name).splitlines()) <= 45
