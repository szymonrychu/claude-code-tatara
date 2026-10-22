"""init update: generated-file conflicts, key renames and every abort path."""

import json
import sys
from importlib import import_module

from init_helpers import LINT, sh, template_commit, write


def state(project):
    return (
        sh("rev-parse", "HEAD", cwd=project).stdout,
        sh("status", "--porcelain", cwd=project).stdout,
        sh("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=project, check=False).returncode,
    )


def assert_untouched(project, before):
    assert state(project) == before
    assert before[1] == "" and before[2] != 0


def test_generated_conflict_keeps_project_side(project, run_cli, tmp_path):
    write(project, "AGENTS.md", (project / "AGENTS.md").read_text() + "\nproject line\n")
    write(project, ".claude/workbench.json", '{"project": 1}\n')
    sh("add", "-A", cwd=project)
    sh("commit", "-m", "project edits", cwd=project)
    template_commit(
        project,
        tmp_path,
        {
            "AGENTS.md": (project / "AGENTS.md").read_text().replace("project line", "other")
            + "\ntemplate line\n",
            ".claude/workbench.json": '{"template": 1}\n',
            "tooling.txt": "v2\n",
        },
    )
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    assert "kept project side: AGENTS.md" in r.stdout.splitlines()
    assert "kept project side: .claude/workbench.json" in r.stdout.splitlines()
    assert "<<<<<<<" not in (project / "AGENTS.md").read_text()
    assert "template line" not in (project / "AGENTS.md").read_text()
    assert json.loads((project / ".claude/workbench.json").read_text()) == {"project": 1}
    assert (project / "tooling.txt").read_text() == "v2\n"
    assert sh("status", "--porcelain", cwd=project).stdout == ""


def test_template_market_keys_renamed(project):
    sys.path.insert(0, str(project / "scripts" / "init_engine"))
    try:
        update = import_module("update")
    finally:
        sys.path.pop(0)
    name = json.loads((project / ".claude-plugin/marketplace.json").read_text())["name"]
    assert name != "workbench-template"
    path = project / ".claude/settings.json"
    settings = json.loads(path.read_text())
    assert settings["enabledPlugins"][f"workbench-infra@{name}"] is False
    settings["enabledPlugins"]["workbench-infra@workbench-template"] = True
    settings["enabledPlugins"]["workbench-newpack@workbench-template"] = True
    settings["extraKnownMarketplaces"]["workbench-template"] = {"source": "template"}
    path.write_text(json.dumps(settings))
    update.rename_template_keys(project)
    out = json.loads(path.read_text())
    enabled = out["enabledPlugins"]
    assert not [k for k in enabled if k.endswith("@workbench-template")]
    assert enabled[f"workbench-infra@{name}"] is False
    assert enabled[f"workbench-newpack@{name}"] is True
    assert "workbench-template" not in out["extraKnownMarketplaces"]
    assert out["extraKnownMarketplaces"][name] == settings["extraKnownMarketplaces"][name]


def test_unknown_conflict_aborts_cleanly(project, run_cli, tmp_path):
    write(project, "tooling.txt", "project\n")
    sh("add", "-A", cwd=project)
    sh("commit", "-m", "project tooling", cwd=project)
    before = state(project)
    template_commit(project, tmp_path, {"tooling.txt": "theirs\n", "new/file.txt": "n\n"})
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert r.stderr.startswith("refused: template update conflicts outside the known paths:")
    assert r.stderr.splitlines()[1:] == ["tooling.txt"]
    assert_untouched(project, before)
    assert not (project / "new").exists()
    assert (project / "tooling.txt").read_text() == "project\n"


def test_lint_failure_aborts_cleanly(project, run_cli, tmp_path):
    template_commit(project, tmp_path, {"tooling.txt": "v2\n", "added.txt": "a\n"})
    before = state(project)
    r = run_cli("update", "--lint-command", "seq 1 30; exit 3")
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    lines = r.stderr.splitlines()
    assert lines[-20:] == [str(i) for i in range(11, 31)]
    assert "10" not in lines
    assert_untouched(project, before)
    assert not (project / "added.txt").exists()


def test_refresh_failure_aborts_cleanly(project, run_cli, tmp_path):
    broken = "import sys\nsys.exit('boom')\n"
    template_commit(project, tmp_path, {"scripts/harness/setup.py": broken, "added.txt": "a\n"})
    before = state(project)
    r = run_cli("update", *LINT)
    assert r.returncode == 1
    assert r.stderr.startswith("refused:")
    assert "boom" in r.stderr
    assert_untouched(project, before)
    assert not (project / "added.txt").exists()


def test_update_renames_template_market_keys_end_to_end(project, run_cli, tmp_path):
    name = json.loads((project / ".claude-plugin/marketplace.json").read_text())["name"]
    path = project / ".claude/settings.json"
    settings = json.loads(path.read_text())
    settings["enabledPlugins"]["workbench-newpack@workbench-template"] = True
    path.write_text(json.dumps(settings, indent=2) + "\n")
    sh("add", "-A", cwd=project)
    sh("commit", "-m", "project settings", cwd=project)
    template_commit(project, tmp_path, {"tooling.txt": "v2\n"})
    r = run_cli("update", *LINT)
    assert r.returncode == 0, r.stderr
    out = json.loads(path.read_text())
    assert out["enabledPlugins"][f"workbench-newpack@{name}"] is True
    assert not [k for k in out["enabledPlugins"] if k.endswith("@workbench-template")]
    assert sh("status", "--porcelain", cwd=project).stdout == ""
