"""The in-repo superpowers fork and its helpers are retired: vanilla superpowers governs.

Retired paths stay untracked, the init engine's RETIRED list drops them on a template update,
and the project settings enable the official superpowers plugin only.
"""

import json
import re
import subprocess
from pathlib import Path

from init_engine import owned

REPO = Path(__file__).resolve().parents[2]

WB = "plugins/workbench"
RETIRED = (
    "plugins/superpowers",
    "docs/plans",
    "mise-tasks/superpowers-diff",
    "mise-tasks/test/superpowers",
    "mise-tasks/lint/superpowers",
    "scripts/superpowers_diff.py",
    f"{WB}/skills/worktree-create",
    f"{WB}/skills/worktree-merge",
    f"{WB}/agents/implementer.md",
    f"{WB}/agents/reviewer.md",
    f"{WB}/agents/worktree-" + "merger.md",
    f"{WB}/agents/panel-reviewer.md",
    f"{WB}/references/review-checklist.md",
    f"{WB}/references/worktrees.md",
    f"{WB}/hooks/verify-recorder.py",
    f"{WB}/hooks/subagent-commit-guard.py",
    f"{WB}/rules/tdd.md",
)
# Paths a template update must drop so the fork never comes back (docs/plans is instance-owned).
UPDATE_DROPPED = tuple(p for p in RETIRED if not p.startswith(("docs/", "mise-tasks/", "scripts/")))


def tracked(*paths: str) -> list[str]:
    """Return the tracked files under the given paths.

    Args:
        *paths (str): repo-relative paths.

    Returns:
        list[str]: tracked repo-relative file paths.
    """
    out = subprocess.run(
        ["git", "ls-files", "--", *paths], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def test_retired_paths_are_untracked():
    for path in RETIRED:
        assert not tracked(path), path


def test_template_update_drops_retired_plugin_paths():
    for path in UPDATE_DROPPED:
        assert path in owned.RETIRED, path


def test_marketplace_has_no_superpowers_entry():
    market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
    assert "superpowers" not in {p["name"] for p in market["plugins"]}


def test_settings_enable_official_superpowers_only():
    settings = json.loads((REPO / ".claude/settings.json").read_text())
    enabled = settings["enabledPlugins"]
    assert enabled["superpowers@claude-plugins-official"] is True
    assert not [k for k in enabled if k.startswith("superpowers@") and "official" not in k]
    official = settings["extraKnownMarketplaces"]["claude-plugins-official"]
    assert official == {
        "source": {"source": "github", "repo": "anthropics/claude-plugins-official"}
    }


# The retired flow vocabulary, built from parts so this file does not match itself.
_PLAN, _WM, _WB = "plan", "worktree-" + "merger", "workbench:"
RETIRED_WORDS = re.compile(
    "|".join(
        (
            r"ticket\.py",
            _PLAN + r"\.md",
            "implementation-" + _PLAN,
            r"retro\.md",
            _WM,
            _WB + "reviewer",
            _WB + "implementer",
            _PLAN + " tree",
            "start-" + "development",
            _PLAN + "-run",
            _PLAN + "-writer",
        )
    )
)
SCANNED = ("plugins", "docs", "scripts", "AGENTS.md", "CLAUDE.md", "README*", "mise*", ".claude")


def test_no_live_reference_to_the_retired_flow():
    hits = []
    for rel in tracked(*SCANNED):
        path = REPO / rel
        if path.name == "CHANGELOG.md" or not path.is_file():
            continue
        for n, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            if RETIRED_WORDS.search(line):
                hits.append(f"{rel}:{n}: {line.strip()[:100]}")
    assert not hits, "\n".join(hits)
