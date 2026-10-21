"""SKILL.md is loaded whole on every trigger; keep it small and keep its moved blocks linked."""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
MAX_BYTES = 14 * 1024
MOVED = [
    "phases-1-3.md",
    "phase-4-execute.md",
    "phases-5-7.md",
    "non-negotiables.md",
]


def test_skill_md_within_budget():
    size = (SKILL_DIR / "SKILL.md").stat().st_size
    assert size <= MAX_BYTES, f"SKILL.md is {size} bytes, budget {MAX_BYTES}"


def test_moved_blocks_are_linked_and_exist():
    text = (SKILL_DIR / "SKILL.md").read_text()
    for name in MOVED:
        assert (SKILL_DIR / "references" / name).is_file(), name
        assert f"references/{name}" in text, name


def test_args_block_lives_in_reference():
    ref = (SKILL_DIR / "references" / "phase-4-execute.md").read_text()
    assert "Workflow({" in ref and "verifierAgent" in ref
    assert "verifierAgent" not in (SKILL_DIR / "SKILL.md").read_text()


def test_skill_md_size_and_references():
    test_skill_md_within_budget()
    test_moved_blocks_are_linked_and_exist()
    test_args_block_lives_in_reference()
