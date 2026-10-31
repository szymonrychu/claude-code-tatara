import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = {
    "agent": (ROOT / "agents/worktree-merger.md").read_text(),
    "skill": (ROOT / "skills/worktree-merge/SKILL.md").read_text(),
}


def _plan_close(text: str) -> str:
    m = re.search(r"^## Plan close\n(.*?)(?=^## )", text, re.S | re.M)
    assert m, "no Plan close section"
    return m.group(1)


def test_plan_close_goes_through_ticket_close():
    for name, text in DOCS.items():
        section = _plan_close(text)
        assert "ticket.py close" in section, name
        assert not re.search(r"--name <plan>\s+--base main", section), name
        assert "--base main --keep" not in section, name
        assert "never fast-forward" in section.lower(), name


def test_no_direct_plan_to_main_close_command_anywhere():
    for name, text in DOCS.items():
        assert not re.search(r"--name <plan>[^\n]*\n?[^\n]*--base main", text), name


def test_merger_close_role_is_conflict_only():
    for name, text in DOCS.items():
        section = " ".join(_plan_close(text).split())
        assert "rebase conflict" in section, name
        assert "plan tree" in section, name
        assert "ticket.py close" in section, name


def test_no_epic_anywhere():
    for name, text in DOCS.items():
        assert not re.search(r"\bepics?\b|integration tree", text, re.I), name
        assert "ticket.py move <plan> in-progress" in text or name == "agent", name


def test_gate_wording_is_the_retro_gate():
    skill = " ".join(DOCS["skill"].split())
    assert "retro.md" in skill
    assert "done-task gate" not in skill
