import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
from merge import main  # noqa: E402

SKILL = (ROOT / "skills/worktree-merge/SKILL.md").read_text()
CONFIG_DOC = (ROOT / "skills/start-development/references/workbench-config.md").read_text()


def test_bad_config_prints_err(tmp_path, capsys):
    repo = tmp_path / "proj"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    (repo / ".claude").mkdir()
    (repo / ".claude" / "workbench.json").write_text(json.dumps({"bogus": 1}))
    rc = main(["--name", "nope", "--repo", str(repo)])
    cap = capsys.readouterr()
    assert rc != 0
    assert "[ERR]" in cap.err and "bogus" in cap.err
    assert "Traceback" not in cap.err


def test_skill_documents_merge_features():
    terms = ("union", "overlapIgnore", "empty", "--no-suites", "exit 4", "after the fast-forward")
    for term in terms:
        assert term in SKILL, term


def test_config_doc_suites_and_paths():
    assert "after the fast-forward" in CONFIG_DOC
    assert "before merging" not in CONFIG_DOC
    assert "basename" in CONFIG_DOC and "cd {pkg}" in CONFIG_DOC
    assert "package root path" not in CONFIG_DOC
    assert "${CLAUDE_PLUGIN_ROOT}/scripts/lib/workbench.py" in CONFIG_DOC
    assert "`scripts/lib/workbench.py" not in CONFIG_DOC
