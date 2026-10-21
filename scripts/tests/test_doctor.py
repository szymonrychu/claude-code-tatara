"""Pins scripts/doctor.py: state, plugins, collision override, broken-tree exits."""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOCTOR = REPO / "scripts" / "doctor.py"
MARKET = "workbench-template"
UNINIT = "<!-- workbench:uninitialised:begin -->\nx\n<!-- workbench:uninitialised:end -->\n"


def _tree(tmp_path, agents=UNINIT, settings=None, plugins=("workbench",)):
    root = tmp_path / "tree"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"name": MARKET, "plugins": [{"name": p} for p in plugins]})
    )
    if agents is not None:
        (root / "AGENTS.md").write_text(agents)
    if settings is None:
        settings = {"enabledPlugins": {f"{p}@{MARKET}": True for p in plugins}}
    (root / ".claude" / "settings.json").write_text(
        settings if isinstance(settings, str) else json.dumps(settings)
    )
    return root


def _user(tmp_path, enabled):
    f = tmp_path / "user-settings.json"
    f.write_text(json.dumps({"enabledPlugins": enabled, "other": 1}))
    return f


def _run(root, user=None):
    cmd = [sys.executable, str(DOCTOR), "--root", str(root)]
    cmd += ["--user-settings", str(user or root.parent / "absent.json")]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=root)


def test_uninitialised_state(tmp_path):
    r = _run(_tree(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "kind: none (uninitialised, no .gitmodules)" in r.stdout
    assert "state: uninitialised" in r.stdout
    assert "plugins: workbench@workbench-template" in r.stdout


def test_initialised_state_when_block_gone(tmp_path):
    r = _run(_tree(tmp_path, agents="# project\n"))
    assert r.returncode == 0, r.stderr
    assert "state: initialised" in r.stdout


def test_conflicting_user_plugin_disabled_locally(tmp_path):
    root = _tree(tmp_path)
    local = root / ".claude" / "settings.local.json"
    local.write_text(json.dumps({"keep": True, "enabledPlugins": {"a@b": True}}))
    user = _user(tmp_path, {"workbench@personal": True, f"workbench@{MARKET}": True, "x@y": True})
    r = _run(root, user)
    assert r.returncode == 0, r.stderr
    assert 'wrote "workbench@personal": false' in r.stdout
    data = json.loads(local.read_text())
    assert data == {"keep": True, "enabledPlugins": {"a@b": True, "workbench@personal": False}}
    before = local.read_text()
    r2 = _run(root, user)
    assert r2.returncode == 0
    assert local.read_text() == before
    assert "wrote" not in r2.stdout
    assert json.loads(user.read_text())["other"] == 1


def test_no_collision_writes_nothing(tmp_path):
    root = _tree(tmp_path)
    r = _run(root, _user(tmp_path, {f"workbench@{MARKET}": True, "workbench@old": False}))
    assert r.returncode == 0
    assert not (root / ".claude" / "settings.local.json").exists()


def test_override_follows_active_harness_dir(tmp_path):
    root = _tree(tmp_path)
    (root / ".cursor").mkdir()
    (root / ".cursor" / "workbench.json").write_text(json.dumps({"harness": {"active": "cursor"}}))
    r = _run(root, _user(tmp_path, {"workbench@personal": True}))
    assert r.returncode == 0, r.stderr
    assert (root / ".cursor" / "settings.local.json").is_file()
    assert not (root / ".claude" / "settings.local.json").exists()


def test_missing_agents_md_fails(tmp_path):
    r = _run(_tree(tmp_path, agents=None))
    assert r.returncode == 1
    assert "AGENTS.md" in r.stderr


def test_invalid_settings_json_fails(tmp_path):
    r = _run(_tree(tmp_path, settings="{nope"))
    assert r.returncode == 1
    assert "settings.json" in r.stderr


def test_mismatch_fails(tmp_path):
    root = _tree(tmp_path, settings={"enabledPlugins": {f"ghost@{MARKET}": True}})
    r = _run(root)
    assert r.returncode == 1
    assert "ghost" in r.stderr


def test_real_repo_is_healthy():
    r = subprocess.run(
        [sys.executable, str(DOCTOR), "--user-settings", "/nonexistent"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr


def test_uninitialised_template_no_gitmodules(tmp_path):
    root = _tree(tmp_path)
    wbpy = REPO / "plugins" / "workbench" / "scripts" / "lib" / "workbench.py"
    for sub in ("root", "doctor"):
        r = subprocess.run(
            [sys.executable, str(wbpy), sub, "--from", str(root)], capture_output=True, text=True
        )
        assert r.returncode == 0, r.stderr
    assert "kind: none (uninitialised, no .gitmodules)" in r.stdout
    d = _run(root)
    assert d.returncode == 0, d.stderr
    assert "kind: none (uninitialised, no .gitmodules)" in d.stdout


def test_local_disable_is_gitignored(tmp_path):
    user = _user(tmp_path, {"workbench@personal": True})
    local = REPO / ".claude" / "settings.local.json"
    existed = local.exists()
    r = _run(REPO, user)
    assert r.returncode == 0, r.stderr
    try:
        assert local.is_file()
        ig = subprocess.run(["git", "check-ignore", "-q", str(local)], cwd=REPO)
        assert ig.returncode == 0
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(local)], cwd=REPO, capture_output=True
        )
        assert tracked.returncode != 0
        assert "personal" not in (REPO / ".claude" / "settings.json").read_text()
    finally:
        if not existed:
            local.unlink(missing_ok=True)
