import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = {
    "agent": (ROOT / "agents/worktree-merger.md").read_text(),
    "skill": (ROOT / "skills/worktree-merge/SKILL.md").read_text(),
}


def _epic_close(text: str) -> str:
    m = re.search(r"^## Epic close\n(.*?)(?=^## )", text, re.S | re.M)
    assert m, "no Epic close section"
    return m.group(1)


def test_epic_close_goes_through_ticket_close():
    for name, text in DOCS.items():
        section = _epic_close(text)
        assert "ticket.py close" in section, name
        assert not re.search(r"--name <epic>\s+--base main", section), name
        assert "--base main --keep" not in section, name
        assert "never fast-forward" in section.lower(), name


def test_no_direct_epic_to_main_close_command_anywhere():
    for name, text in DOCS.items():
        assert not re.search(r"--name <epic>[^\n]*\n?[^\n]*--base main", text), name


def test_merger_close_role_is_conflict_only():
    for name, text in DOCS.items():
        section = " ".join(_epic_close(text).split())
        assert "rebase conflict" in section, name
        assert "integration tree" in section, name
        assert "ticket.py close" in section, name
