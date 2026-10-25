"""start-development works without the infra/observability packs and in versioned metarepos."""

import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
TEXT = SKILL.read_text()
FLAT = re.sub(r"\s+", " ", TEXT)


def test_meta_mode_closes_by_local_fast_forward():
    assert "Meta mode tasks commit on the integration branch `<epic>`" in FLAT
    assert "rebase plus fast-forward of the local main" in FLAT
    assert "with or without an `origin` remote" in FLAT
    assert "pushing main stays with the user" in FLAT
    assert "ticket.py close <epic> --verify" in FLAT
    assert "never commits" not in FLAT
    assert "ends at reviewed, test-green edits" not in FLAT


def test_health_step_conditional():
    assert "when the `workbench-observability` pack is enabled" in FLAT
    assert "`deploy.verify`" in FLAT


def test_infra_agents_conditional_no_superpowers():
    assert "when the `workbench-infra` pack is enabled" in FLAT
    assert not re.search(r"Terraform or chart changes: `tf-planner`", FLAT)
    assert "superpowers" not in TEXT
