"""The repo's own top-level docs name none of the retired epic flow's terms.

Retired names are built from parts so this file does not match itself.
"""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
E = "ep" + "ic"
TERMS = (
    f"{E}-run",
    f"{E}-create",
    f"{E}-move",
    f"{E}-task-create",
    f"{E}-worktrees-remove",
    f"{E}-migrate",
    "scope-" + "auditor",
    "record-" + "writer",
    "retro-" + "writer",
    "workbench:" + "planner",
    "new-" + "task",
    "points_" + "actual",
    "builder " + "check",
)
DOCS = ("AGENTS.md", "CLAUDE.md", "README.md", "docs/harnesses.md")


def test_top_level_docs_are_tracked_and_clean():
    tracked = subprocess.run(
        ["git", "ls-files", "--", *DOCS], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    assert sorted(tracked) == sorted(DOCS)
    hits = []
    for doc in DOCS:
        text = (REPO / doc).read_text()
        hits += [f"{doc}: {t}" for t in TERMS if t in text]
        if re.search(rf"\b{E}s?\b", text, re.I):
            hits.append(f"{doc}: the word {E}")
    assert not hits, hits
