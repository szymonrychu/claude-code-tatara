"""The skills/debug/SKILL.md alias of the workbench:start-debugging skill."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "debug" / "SKILL.md"


def _split():
    text = SKILL.read_text()
    assert text.startswith("---\n"), "missing frontmatter"
    end = text.index("\n---", 4)
    return text[4:end], text[end + 4 :]


def _keys():
    head, _ = _split()
    return [line.partition(":")[0].strip() for line in head.splitlines() if line.strip()]


def test_skill_exists_and_ascii():
    assert SKILL.is_file()
    SKILL.read_text().encode("ascii")


def test_frontmatter_name_equals_directory_and_has_description():
    head, _ = _split()
    assert "name: debug" in head.splitlines()
    assert "description" in _keys()
    assert set(_keys()) <= {"name", "description", "argument-hint"}


def test_body_invokes_the_skill_with_arguments():
    _, body = _split()
    for needle in ("workbench:start-debugging", "Skill", "$ARGUMENTS"):
        assert needle in body, needle


def test_commands_directory_retired():
    out = subprocess.run(
        ["git", "ls-files", "plugins/workbench/commands"],
        cwd=ROOT.parents[1],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert out.strip() == ""
