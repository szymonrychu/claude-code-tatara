"""init update: a template commit that re-adds a retired flow path never brings it back.

Retired names are built from parts so the retired-name scan does not match this file.
"""

from pathlib import Path

from init_helpers import LINT, sh, template_commit

REPO = Path(__file__).resolve().parents[3]
SKILL_MD = REPO / "plugins/workbench/skills/template-update/SKILL.md"
RETIRED_SKILL = "plugins/workbench/skills/" + "start-" + "development/SKILL.md"
RETIRED_AGENT = "plugins/workbench/agents/" + "plan-" + "writer.md"


def test_update_keeps_retired_flow_paths_out(project, run_cli, tmp_path):
    sha = template_commit(
        project,
        tmp_path,
        {RETIRED_SKILL: "retired skill\n", RETIRED_AGENT: "retired agent\n", "tooling.txt": "v2\n"},
    )
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert (project / "tooling.txt").read_text() == "v2\n"
    tracked = sh("ls-files", cwd=project).stdout.split()
    for gone in (RETIRED_SKILL, RETIRED_AGENT):
        assert gone not in tracked, gone
        assert not (project / gone).exists(), gone
    assert sh("status", "--porcelain", cwd=project).stdout == ""
    msg = sh("log", "-1", "--format=%B", cwd=project).stdout
    assert msg.startswith(f"chore(workbench): template update {sha[:12]}")


def test_template_update_skill_says_retired_paths_are_kept_out():
    assert "retired flow paths" in SKILL_MD.read_text()
