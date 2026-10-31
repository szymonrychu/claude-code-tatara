"""Pins the project settings that enable the official (vanilla) superpowers plugin."""

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


def test_official_superpowers_enabled_and_no_fork():
    plugins = enabled_plugins()
    assert plugins["superpowers@claude-plugins-official"] is True
    assert f"superpowers@{MARKET}" not in plugins


def test_template_workbench_disabled():
    assert enabled_plugins()["workbench@workbench-template"] is False


def test_existing_entries_unchanged():
    plugins = enabled_plugins()
    for name in EXISTING:
        assert plugins[f"{name}@{MARKET}"] is True
