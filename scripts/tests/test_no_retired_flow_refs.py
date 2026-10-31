"""No tracked file names a retired workbench flow skill or agent.

Retired names are built from parts so this file does not match itself. A name matches only
as a whole token: `workbench:reviewer` and `plan-writer-prompt.md` are other names.
"""

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
START, PLAN, WB = "start-", "plan-", "workbench:"
RETIRED_NAMES = (
    START + "development",
    START + "discovery",
    PLAN + "run",
    "interro" + "gate",
    PLAN + "writer",
    START + "debugging",
    START + "review",
    WB + "debug",
    WB + "review",
    "skills/" + "debug",
    "skills/" + "review",
    "ep" + "ic-run",
)
PATTERN = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(n) for n in RETIRED_NAMES) + r")(?![\w-])"
)
EXEMPT = {
    "MEMORY.md",
    "scripts/tests/test_no_retired_flow_refs.py",
    "plugins/workbench/scripts/tests/test_retired_workbench_flow.py",
}


def scanned_files() -> list[str]:
    """Return the tracked files the scan reads.

    Returns:
        list[str]: repo-relative paths minus docs/plans, every CHANGELOG.md and EXEMPT.
    """
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [
        p
        for p in out.splitlines()
        if p
        and not p.startswith("docs/plans/")
        and Path(p).name != "CHANGELOG.md"
        and p not in EXEMPT
        and (REPO / p).is_file()
    ]


def test_pattern_matches_whole_names_only():
    assert PATTERN.search("use " + WB + "review here")
    assert not PATTERN.search(WB + "reviewer")
    assert not PATTERN.search(PLAN + "writer-prompt.md")


def test_no_tracked_file_names_a_retired_flow_name():
    hits = []
    for rel in scanned_files():
        text = (REPO / rel).read_text(errors="ignore")
        hits += [f"{rel}: {m}" for m in sorted(set(PATTERN.findall(text)))]
    assert not hits, "\n".join(hits)
