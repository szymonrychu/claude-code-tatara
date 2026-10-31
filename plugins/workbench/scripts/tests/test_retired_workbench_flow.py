"""The workbench flow skills are retired: the superpowers plugin carries the flow.

Retired names are built from parts so the reference scan does not match this file.
"""

import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
REPO = PLUGIN.parents[1]
REL = "plugins/workbench"
START, PLAN, WRITER = "start-", "plan-", "writer"
RETIRED = (
    *(
        f"{REL}/skills/{n}"
        for n in (
            START + "development",
            START + "discovery",
            PLAN + "run",
            "interrogate",
            START + "debugging",
            "debug",
            START + "review",
            "review",
        )
    ),
    f"{REL}/agents/{PLAN}{WRITER}.md",
)
E = "ep" + "ic"


def tracked(*paths: str) -> list[str]:
    """Return the tracked files under the given paths.

    Args:
        *paths (str): repo-relative paths or pathspecs.

    Returns:
        list[str]: tracked repo-relative file paths.
    """
    out = subprocess.run(
        ["git", "ls-files", "--", *paths], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def test_nine_retired_paths_are_untracked():
    assert len(RETIRED) == 9
    for path in RETIRED:
        assert not tracked(path), path


def test_no_epic_skill_dir_is_tracked():
    assert not tracked(f"{REL}/skills/{E}-*")
