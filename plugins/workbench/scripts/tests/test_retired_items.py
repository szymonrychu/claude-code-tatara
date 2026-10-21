"""Retirement pins: items removed from the plugin must stay removed."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
THIS = "plugins/workbench/scripts/tests/test_retired_items.py"

RETIRED_PATHS = [
    "plugins/workbench/scripts/chart-drift-scan.py",
    "plugins/workbench/workflows/chart-drift-audit.js",
    "plugins/workbench/scripts/infra-watch.sh",
    "plugins/workbench/commands/chart-drift.md",
    "plugins/workbench/commands/infra-watch.md",
    "plugins/workbench/commands/bump-chart-usage.md",
    "plugins/workbench/commands/bump-chart-version.md",
    "plugins/workbench/commands/bump-container-usage.md",
    "plugins/workbench/commands/bump-container-version.md",
    "plugins/workbench/commands/upgrade-release.md",
    "plugins/workbench/commands/git-commit-mr.md",
]
# Terms are split so this file itself does not match them.
TERMS = [
    "chart" + "-drift",
    "infra" + "-watch",
    "bump" + "-chart",
    "bump" + "-container",
    "upgrade" + "-release",
    "git-commit" + "-mr",
]
EXEMPT = {"plugins/workbench/CHANGELOG.md", "plugins/workbench/README.md", THIS}


def _tracked():
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return [p for p in out.split("\0") if p and (ROOT / p).is_file()]


def test_homelab_items_are_gone():
    tracked = set(_tracked())
    assert not [p for p in RETIRED_PATHS if p in tracked]
    hits = []
    for p in tracked:
        if not p.startswith("plugins/workbench/") or p in EXEMPT:
            continue
        text = (ROOT / p).read_text(errors="ignore").lower()
        hits += [(p, t) for t in TERMS if t in text]
    assert not hits, hits
