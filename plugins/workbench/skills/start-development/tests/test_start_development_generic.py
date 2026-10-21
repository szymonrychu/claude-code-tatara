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


def test_meta_mode_origin_rule():
    assert "has an `origin` remote" in FLAT
    assert "lands like a component" in FLAT
    assert "with no `origin` remote it never commits" in FLAT
    assert "Meta mode with no `origin` remote ends here" in FLAT
    assert "With an `origin` remote it continues into phase 6" in FLAT


def test_health_step_conditional():
    assert "when the `workbench-observability` pack is enabled" in FLAT
    assert "`deploy.verify`" in FLAT


def test_infra_agents_conditional_no_superpowers():
    assert "when the `workbench-infra` pack is enabled" in FLAT
    assert not re.search(r"Terraform or chart changes: `tf-planner`", FLAT)
    assert "superpowers" not in TEXT
