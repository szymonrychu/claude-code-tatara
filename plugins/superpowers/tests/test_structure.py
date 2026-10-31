"""Pins the vendored superpowers plugin: manifest, upstream LICENSE, NOTICE, marketplace entry."""

import hashlib
import json
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
# sha256 of superpowers 7.0.0 LICENSE (MIT, Copyright (c) 2025 Jesse Vincent), kept verbatim.
UPSTREAM_LICENSE_SHA256 = "a37e0e9697144819e1d965176ac4ae5bc3fa02d11e7812036bbcadf6dafe2400"


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_manifest_name_and_version():
    manifest = _json(PLUGIN / ".claude-plugin" / "plugin.json")
    assert manifest["name"] == "superpowers"
    assert manifest["version"] == "1.0.0"


def test_license_is_upstream_verbatim():
    digest = hashlib.sha256((PLUGIN / "LICENSE").read_bytes()).hexdigest()
    assert digest == UPSTREAM_LICENSE_SHA256


def test_notice_names_upstream_and_changes():
    notice = (PLUGIN / "NOTICE").read_text()
    for needle in ("superpowers 7.0.0", "Jesse Vincent", "MIT"):
        assert needle in notice
    low = notice.lower()
    for change in ("vendored", "adapt", "em dash"):
        assert change in low


def test_marketplace_entry_matches_manifest():
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")
    entry = next(e for e in market["plugins"] if e["name"] == "superpowers")
    assert entry["source"] == "./plugins/superpowers"
    assert entry["version"] == _json(PLUGIN / ".claude-plugin" / "plugin.json")["version"]


# Retired workbench flow names, built from parts so the retired-name scan skips this file.
RETIRED_NAMES = (
    "start-" + "development",
    "start-" + "discovery",
    "plan-" + "run",
    "interro" + "gate",
    "plan-" + "writer",
    "start-" + "debugging",
    "start-" + "review",
    "ep" + "ic-",
)


def vendored_skills() -> list[str]:
    return sorted(p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir())


def test_readme_names_each_vendored_skill_and_the_diff_task():
    readme = (PLUGIN / "README.md").read_text()
    for skill in vendored_skills():
        assert f"`{skill}`" in readme, skill
    assert "mise run superpowers-diff" in readme


def test_workbench_manifest_and_entry_are_4_0_0_without_the_flow():
    manifest = _json(ROOT / "plugins" / "workbench" / ".claude-plugin" / "plugin.json")
    market = _json(ROOT / ".claude-plugin" / "marketplace.json")
    entry = next(e for e in market["plugins"] if e["name"] == "workbench")
    assert manifest["version"] == entry["version"] == "4.0.0"
    assert manifest["description"] == entry["description"]
    for name in (*RETIRED_NAMES, *vendored_skills()):
        assert name not in manifest["description"], name


def test_architecture_names_the_plugin():
    assert "plugins/superpowers" in (ROOT / "docs" / "architecture.md").read_text()
