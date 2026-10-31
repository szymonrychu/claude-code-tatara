"""The epic and task flow is gone: its files are untracked and no plugin doc names it.

Retired names are built from parts so this file does not match itself.
"""

import re
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
REPO = PLUGIN.parents[1]
REL = "plugins/workbench"
SD = "skills/start-development"

E = "ep" + "ic"
DELETED = (
    # chunk 1
    *(f"skills/{E}-{n}" for n in ("create", "migrate", "move", "task-create", "worktrees-remove")),
    *(f"{SD}/templates/{n}.md" for n in ("design", E, "record", "task")),
    *(
        f"{SD}/scripts/ticket_cmds/{n}.py"
        for n in ("actuals", "amend", "deltas", "questions", "retro", "roadmap", "task_cmd")
    ),
    *(
        f"{SD}/tests/test_ticket_{n}.py"
        for n in (
            "amend",
            "deltas",
            "lint",
            "questions",
            "reap_task",
            "retro",
            "roadmap",
            "task_status",
            "names",
            "overlap_ignore",
            "migrate_map",
            "migrate",
            "retired_run_loop",
        )
    ),
    f"{SD}/tests/test_{E}_skills_structure.py",
    # chunk 2
    "scripts/lib/calibration.py",
    "scripts/tests/test_calibration.py",
    # chunk 3
    f"skills/{E}-run",
    f"{SD}/references/retro.md",
    f"{SD}/tests/test_lean_flow_docs.py",
    f"{SD}/tests/test_planner_agent.py",
    *(f"agents/{n}.md" for n in ("planner", "record-writer", "retro-writer", "scope-auditor")),
)
RETIRED_TERMS = (
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
EXEMPT = (
    f"{REL}/CHANGELOG.md",
    f"{REL}/{SD}/scripts/ticket_cmds/migrate.py",
    f"{REL}/{SD}/references/tickets.md",
)


def tracked(*paths: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--", *paths], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p]


def plugin_files() -> list[str]:
    return [
        p
        for p in tracked(REL)
        if p not in EXEMPT and "/tests/" not in p and not Path(p).name.startswith("test_")
    ]


def test_deleted_paths_are_untracked():
    still = tracked(*(f"{REL}/{d}" for d in DELETED))
    assert not still, still


def test_no_retired_term_in_plugin_files():
    hits = []
    for rel in plugin_files():
        text = (REPO / rel).read_text(errors="ignore")
        hits += [f"{rel}: {t}" for t in RETIRED_TERMS if t in text]
    assert not hits, hits


def test_no_epic_word_in_skills_agents_rules_docs():
    hits = []
    for rel in plugin_files():
        if not rel.endswith(".md") or not rel.startswith(
            (f"{REL}/skills/", f"{REL}/agents/", f"{REL}/rules/")
        ):
            continue
        if re.search(rf"\b{E}s?\b", (REPO / rel).read_text(errors="ignore"), re.I):
            hits.append(rel)
    assert not hits, hits
