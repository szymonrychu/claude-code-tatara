"""start-development works without the infra/observability packs and in versioned metarepos."""

import re
from pathlib import Path

_MOVED = ("phases-1-3.md", "phase-4-execute.md", "phases-5-7.md", "non-negotiables.md")


def sd_text(skill):
    """SKILL.md plus the reference files its blocks moved to. References come first, so a section
    heading resolves to its full text rather than to the pointer left in SKILL.md."""
    refs = skill.parent / "references"
    return "\n".join([*((refs / n).read_text() for n in _MOVED), skill.read_text()])


TEXT = sd_text(Path(__file__).resolve().parents[1] / "SKILL.md")
FLAT = re.sub(r"\s+", " ", TEXT)


def test_meta_mode_closes_by_local_fast_forward():
    assert "Meta mode tasks land on the integration branch `<epic>`" in FLAT
    assert "rebase plus fast-forward of the local main" in FLAT
    assert "with or without an `origin` remote" in FLAT
    assert "pushing main stays with the user" in FLAT
    assert "ticket.py close <epic> --verify" in FLAT
    assert "never commits" not in FLAT
    assert "ends at reviewed, test-green edits" not in FLAT
    assert "Meta mode with no `origin` remote ends here" not in FLAT


def test_health_step_conditional():
    assert "when the `workbench-observability` pack is enabled" in FLAT
    assert "`deploy.verify`" in FLAT


def test_infra_agents_conditional_no_superpowers():
    assert "when the `workbench-infra` pack is enabled" in FLAT
    assert not re.search(r"Terraform or chart changes: `tf-planner`", FLAT)
    assert "superpowers" not in TEXT
