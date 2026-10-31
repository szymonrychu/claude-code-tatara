"""Pins the project settings that switch this repo to the vendored superpowers flow."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKET = "claude-code-tatara-workbench"
EXISTING = ("workbench", "workbench-infra", "workbench-observability", "workbench-secrets")


def enabled_plugins() -> dict:
    """Return the enabledPlugins map of the committed project settings.

    Returns:
        dict: plugin key -> enabled flag.
    """
    return json.loads((ROOT / ".claude" / "settings.json").read_text())["enabledPlugins"]


def test_vendored_superpowers_enabled():
    assert enabled_plugins()[f"superpowers@{MARKET}"] is True


def test_official_superpowers_and_template_workbench_disabled():
    plugins = enabled_plugins()
    assert plugins["superpowers@claude-plugins-official"] is False
    assert plugins["workbench@workbench-template"] is False


def test_existing_entries_unchanged():
    plugins = enabled_plugins()
    for name in EXISTING:
        assert plugins[f"{name}@{MARKET}"] is True
