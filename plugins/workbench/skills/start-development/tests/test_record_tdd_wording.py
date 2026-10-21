"""The record never presents a tdd-revert result as TDD red evidence (F13)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILES = [
    ROOT / "skills" / "start-development" / "templates" / "record.md",
    ROOT / "agents" / "record-writer.md",
]


def test_files_forbid_quoting_tdd_revert_as_red_evidence():
    for f in FILES:
        text = f.read_text()
        assert "tdd-revert" in text, f.name
        assert "never quoted as TDD red evidence" in text, f.name
        assert "tests.red" in text, f.name
        assert "verify-task.py:343-366" in text, f.name
