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
    "epic-migrate": [
        "ticket.py migrate --all --dry-run",
        "ticket.py migrate --all",
        "retro-writer",
        "record.md",
        "ticket.py retro <epic>",
        "ticket.py deltas --all --buckets",
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


def test_epic_task_create_names_only_flags_new_task_has():
    import re
    import subprocess
    import sys

    ticket = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
    helptext = subprocess.run(
        [sys.executable, str(ticket), "new-task", "--help"],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    body = read("epic-task-create")
    flags = set(re.findall(r"--[a-z][a-z-]*", body))
    assert flags
    for flag in flags:
        assert flag in helptext, f"{flag} is not a new-task flag"


def test_epic_migrate_names_only_real_flags():
    import re
    import subprocess
    import sys

    ticket = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
    helptext = ""
    for sub in ("migrate", "retro", "deltas"):
        helptext += subprocess.run(
            [sys.executable, str(ticket), sub, "--help"],
            capture_output=True, text=True, check=True,
        ).stdout  # fmt: skip
    flags = set(re.findall(r"--[a-z][a-z-]*", read("epic-migrate")))
    assert flags
    for flag in flags:
        assert flag in helptext, f"{flag} is not a migrate, retro or deltas flag"


def test_epic_run_skips_done_tasks_and_caps_are_one_number_per_role():
    run = " ".join(read("epic-run").split())
    assert "skip tasks already `done`" in run
    agents = ROOT / "agents"
    assert "at most 200 words" in (agents / "implementer.md").read_text()
    assert "At most 250 words" in (agents / "reviewer.md").read_text()
    assert "acEvidence" in (agents / "implementer.md").read_text().split("## Report")[1]
    assert "Replaces the verifier" not in (agents / "reviewer.md").read_text()
