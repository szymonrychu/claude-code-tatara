"""Every shipped agent must be free of personal paths and private-infra vocabulary."""

import re
from pathlib import Path

import pytest

AGENTS = sorted((Path(__file__).resolve().parents[2] / "agents").glob("*.md"))

# Built at run time so this file does not itself trip the personal-term lint.
HOMELAB_WORDS = [
    "home" + "lab",
    "har" + "bor",
    "key" + "cloak",
    "oauth2-" + "proxy",
    "kan" + "iko",
    "KUBE_CONFIG" + "_B64",
]
PATH_MARKERS = ["$HOME" + "/.claude", "/Us" + "ers/", "~/Doc" + "uments"]


def test_agents_found():
    assert len(AGENTS) >= 4


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.name)
def test_core_agents_are_generic(path):
    text = path.read_text()
    for marker in PATH_MARKERS:
        assert marker not in text, f"{path.name}: {marker}"
    lowered = text.lower()
    for word in HOMELAB_WORDS:
        assert word.lower() not in lowered, f"{path.name}: {word}"


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.name)
def test_plugin_root_paths_exist(path):
    plugin_root = path.parents[1]
    for rel in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+\.\w+)", path.read_text()):
        assert (plugin_root / rel).exists(), f"{path.name}: {rel} does not exist"
