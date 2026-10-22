"""verify-task --exclude-ref: text a merged dependency added is not gated against the dependent."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verify_task as base  # noqa: E402
from test_verify_task import Triage, branch, commit, git, verify  # noqa: E402

repo = base.repo
DEP_TODO = "TODO fill in the dependency placeholder"


def forward_merged(repo):
    """main -> dep (adds a TODO and a deferral) -> feature merges dep, then adds its own TODO."""
    branch(repo, "dep")
    commit(repo, {"AGENTS.md": f"# a\n{DEP_TODO}\nlater we split this\n"})
    git(repo, "checkout", "-q", "main")
    branch(repo, "feature")
    git(repo, "merge", "-q", "--no-edit", "dep")
    commit(repo, {"own.py": "x = 1  # TODO own debt\n"})


def test_exclude_ref_drops_dependency_text_from_debt_and_parking(repo):
    forward_merged(repo)
    tri = Triage()
    plain = verify(repo, "true", "--no-tier", triage=tri)
    assert {d["file"] for d in plain["debtMarkers"]} == {"AGENTS.md", "own.py"}
    assert [p["file"] for p in plain["parking"]] == ["AGENTS.md"]
    got = verify(repo, "true", "--no-tier", "--exclude-ref", "dep", triage=Triage())
    assert [d["file"] for d in got["debtMarkers"]] == ["own.py"]
    assert got["parking"] == []
    assert got["excludedByRef"] == 3


def test_a_line_the_dependent_adds_is_still_gated(repo):
    forward_merged(repo)
    commit(repo, {"AGENTS.md": f"# a\n{DEP_TODO}\nlater we split this\nTODO new\n"})
    got = verify(repo, "true", "--no-triage", "--exclude-ref", "dep")
    gated = sorted((d["file"], d["line"]) for d in got["debtMarkers"])
    assert gated == [("AGENTS.md", 4), ("own.py", 1)]
    assert got["excludedByRef"] == 3


def test_exclude_ref_is_repeatable_and_defaults_to_zero(repo):
    branch(repo, "d1")
    commit(repo, {"one.py": "# TODO one\n"})
    git(repo, "checkout", "-q", "main")
    branch(repo, "d2")
    commit(repo, {"two.py": "# TODO two\n"})
    git(repo, "checkout", "-q", "main")
    branch(repo, "feature")
    git(repo, "merge", "-q", "--no-edit", "d1")
    git(repo, "merge", "-q", "--no-edit", "d2")
    assert verify(repo, "true", "--no-triage")["excludedByRef"] == 0
    got = verify(repo, "true", "--no-triage", "--exclude-ref", "d1", "--exclude-ref", "d2")
    assert got["debtMarkers"] == [] and got["excludedByRef"] == 2
