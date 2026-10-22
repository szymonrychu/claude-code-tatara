import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

NEW = ("new", "--name", "demo-app", "--component", "api:python", "--remote", "local-bare")


def g(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def load_wb(root: Path):
    path = root / "plugins/workbench/scripts/lib/workbench.py"
    spec = importlib.util.spec_from_file_location("wb_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_slug_collapses_and_trims():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "init_engine"))
    import finalize

    assert finalize.slug("  My Demo_App!! ") == "my-demo-app"


def seed_epics(root: Path):
    epic = root / "docs/plans/in-progress/old-epic/tasks"
    epic.mkdir(parents=True)
    (epic / "t.md").write_text("x")
    (root / "docs/plans/todo/another").mkdir(parents=True)
    (root / "docs/plans/todo/another/README.md").write_text("x")
    (root / "docs/plans/done/finished").mkdir(parents=True)
    (root / "docs/plans/done/finished/README.md").write_text("x")
    (root / "docs/research").mkdir()
    (root / "docs/research/brief.md").write_text("secret")


def init(run_cli, *extra):
    r = run_cli(*NEW, *extra)
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def test_marketplace_rename_and_packs(workbench, run_cli, allow_file):
    init(run_cli, "--pack", "infra", "--pack", "secrets", "--license-holder", "Acme")
    market = json.loads((workbench / ".claude-plugin/marketplace.json").read_text())
    assert market["name"] == "demo-app-workbench"
    settings = json.loads((workbench / ".claude/settings.json").read_text())
    assert list(settings["extraKnownMarketplaces"]) == ["demo-app-workbench"]
    assert settings["enabledPlugins"] == {
        "workbench@demo-app-workbench": True,
        "workbench-infra@demo-app-workbench": True,
        "workbench-observability@demo-app-workbench": False,
        "workbench-secrets@demo-app-workbench": True,
    }
    assert "workbench-template" not in (workbench / ".claude/settings.json").read_text()


def test_no_pack_all_false(workbench, run_cli, allow_file):
    init(run_cli, "--license-holder", "Acme")
    enabled = json.loads((workbench / ".claude/settings.json").read_text())["enabledPlugins"]
    assert [k for k, v in enabled.items() if v] == ["workbench@demo-app-workbench"]


def test_workbench_config_written(workbench, run_cli, allow_file):
    init(
        run_cli,
        "--harness",
        "cursor",
        "--harness",
        "codex,gemini",
        "--deploy-command",
        "make ship",
        "--deploy-verify",
        "make check",
        "--license-holder",
        "Acme",
    )
    cfg = load_wb(workbench).load_config(workbench)
    assert cfg["harness"]["targets"] == ["cursor", "codex", "gemini"]
    assert cfg["deploy"] == {"command": "make ship", "verify": "make check"}
    assert "refRunners" in json.loads((workbench / ".claude/workbench.json").read_text())


def test_no_deploy_without_command(workbench, run_cli, allow_file):
    init(run_cli, "--license-holder", "Acme")
    raw = json.loads((workbench / ".claude/workbench.json").read_text())
    assert "deploy" not in raw
    assert "harness" not in raw


def test_deploy_verify_without_command_refused(workbench, run_cli, allow_file):
    r = run_cli(*NEW, "--deploy-verify", "x", "--license-holder", "Acme")
    assert r.returncode == 1
    assert "--deploy-command" in r.stderr


def test_unknown_harness_refused(workbench, run_cli, allow_file):
    r = run_cli(*NEW, "--harness", "emacs", "--license-holder", "Acme")
    assert r.returncode == 1
    assert "emacs" in r.stderr


def test_template_history_cleared(workbench, run_cli, allow_file):
    seed_epics(workbench)
    init(run_cli, "--license-holder", "Acme")
    for phase in ("todo", "in-progress", "done"):
        assert sorted(p.name for p in (workbench / "docs/plans" / phase).iterdir()) == [".gitkeep"]
    assert not (workbench / "docs/research").exists() or not any(
        (workbench / "docs/research").iterdir()
    )


@pytest.mark.parametrize("option", ["mit", "none", "file"])
def test_license_options(workbench, run_cli, allow_file, tmp_path, option):
    plugin_license = workbench / "plugins/workbench/LICENSE"
    plugin_license.write_text("keep")
    if option == "mit":
        init(run_cli, "--license", "mit", "--license-holder", "Acme Corp")
        text = (workbench / "LICENSE").read_text()
        assert text.startswith("MIT License")
        assert "Acme Corp" in text
        assert "Szymon" not in text
    elif option == "none":
        init(run_cli, "--license", "none")
        assert not (workbench / "LICENSE").exists()
    else:
        lic = tmp_path / "prop.txt"
        lic.write_text("All rights reserved by Acme.\n")
        init(run_cli, "--license-file", str(lic))
        assert (workbench / "LICENSE").read_text() == "All rights reserved by Acme.\n"
    assert plugin_license.read_text() == "keep"


def test_license_file_missing_refused(workbench, run_cli, allow_file, tmp_path):
    r = run_cli(*NEW, "--license-file", str(tmp_path / "nope"))
    assert r.returncode == 1
    assert "nope" in r.stderr


def test_single_commit_no_push(workbench, run_cli, allow_file):
    init(run_cli, "--license-holder", "Acme")
    log = g("log", "--format=%s", cwd=workbench).stdout.splitlines()
    assert log == ["chore(workbench): initialise demo-app"]
    assert g("status", "--porcelain", cwd=workbench).stdout == ""
    assert g("remote", cwd=workbench).stdout.strip() == ""


def test_user_plugin_collision_disabled_locally(workbench, run_cli, allow_file, tmp_path):
    user = tmp_path / "user-settings.json"
    user.write_text(json.dumps({"enabledPlugins": {"workbench@other-market": True}}))
    init(run_cli, "--user-settings", str(user), "--license-holder", "Acme")
    local = json.loads((workbench / ".claude/settings.local.json").read_text())
    assert local == {"enabledPlugins": {"workbench@other-market": False}}
    assert "settings.local.json" not in g("ls-files", cwd=workbench).stdout


def test_collision_uses_resolved_config_dir(workbench, run_cli, allow_file, tmp_path):
    (workbench / ".cursor").mkdir()
    (workbench / ".claude/workbench.json").rename(workbench / ".cursor/workbench.json")
    (workbench / ".cursor/workbench.json").write_text(json.dumps({"harness": {"active": "cursor"}}))
    (workbench / ".claude/settings.json").rename(workbench / ".cursor/settings.json")
    (workbench / ".claude").rmdir()
    user = tmp_path / "u.json"
    user.write_text(json.dumps({"enabledPlugins": {"workbench@other-market": True}}))
    init(run_cli, "--user-settings", str(user), "--license-holder", "Acme")
    assert (workbench / ".cursor/settings.local.json").is_file()
    assert not (workbench / ".claude").exists()


def test_no_collision_no_local_file(workbench, run_cli, allow_file, tmp_path):
    init(run_cli, "--user-settings", str(tmp_path / "absent.json"), "--license-holder", "Acme")
    assert not (workbench / ".claude/settings.local.json").exists()


def test_adopt_finalizes_and_rerun_is_idempotent(workbench, run_cli, allow_file, tmp_path):
    init(run_cli, "--pack", "infra", "--license-holder", "Acme")
    remote = tmp_path / "ext.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(remote)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-b", "main", str(seed)], check=True)
    (seed / "f").write_text("x")
    g("add", "-A", cwd=seed)
    g("commit", "-m", "i", cwd=seed)
    g("push", str(remote), "main", cwd=seed)
    r = run_cli("adopt", "--url", f"file://{remote}", "--name", "ext")
    assert r.returncode == 0, r.stdout + r.stderr
    enabled = json.loads((workbench / ".claude/settings.json").read_text())["enabledPlugins"]
    assert enabled["workbench-infra@demo-app-workbench"] is True
    assert (workbench / "LICENSE").read_text().count("Acme") >= 1
    assert g("status", "--porcelain", cwd=workbench).stdout == ""


def test_rerun_keeps_epics_and_research(workbench, run_cli, allow_file, tmp_path):
    init(run_cli, "--license-holder", "Acme")
    (workbench / "docs/plans/todo/mine").mkdir()
    (workbench / "docs/plans/todo/mine/README.md").write_text("mine")
    (workbench / "docs/research").mkdir()
    (workbench / "docs/research/note.md").write_text("n")
    g("add", "-A", cwd=workbench)
    g("commit", "-m", "work", cwd=workbench)
    remote = tmp_path / "ext.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(remote)], check=True)
    seed = tmp_path / "seed"
    subprocess.run(["git", "init", "-b", "main", str(seed)], check=True)
    (seed / "f").write_text("x")
    g("add", "-A", cwd=seed)
    g("commit", "-m", "i", cwd=seed)
    g("push", str(remote), "main", cwd=seed)
    r = run_cli("adopt", "--url", f"file://{remote}", "--name", "ext")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (workbench / "docs/plans/todo/mine/README.md").read_text() == "mine"
    assert (workbench / "docs/research/note.md").is_file()


def test_collision_rule_is_doctors(workbench, run_cli, allow_file, tmp_path):
    """finalize delegates to scripts/doctor.py: a patched rule there changes init."""
    doctor = workbench / "scripts/doctor.py"
    text = doctor.read_text().replace('k.startswith("workbench@")', 'k.startswith("zzz@")')
    doctor.write_text(text)
    user = tmp_path / "u.json"
    user.write_text(json.dumps({"enabledPlugins": {"workbench@other-market": True}}))
    init(run_cli, "--user-settings", str(user), "--license-holder", "Acme")
    assert not (workbench / ".claude/settings.local.json").exists()


def test_harness_targets_generated_before_the_commit(workbench, run_cli, allow_file):
    init(run_cli, "--harness", "cursor", "--harness", "copilot")
    args = (workbench.parent / "harness-args").read_text().split()
    assert args[-2:] == ["cursor", "copilot"] and "--root" in args
    assert g("status", "--porcelain", cwd=workbench).stdout == ""


def test_facts_md_cleared(workbench, run_cli, allow_file):
    (workbench / "docs/plans/facts.md").write_text("facts")
    init(run_cli)
    assert not (workbench / "docs/plans/facts.md").exists()


def test_owned_paths_retired_from_tracked_files(workbench, run_cli, allow_file):
    seed_epics(workbench)
    plans = workbench / "docs/plans"
    for name in ("contracts.json", "index.json", "facts.md"):
        (plans / name).write_text("x")
    (workbench / "docs/handoffs").mkdir()
    (workbench / "docs/handoffs/h.md").write_text("x")
    init(run_cli, "--license-holder", "Acme")
    tracked = g("ls-files", cwd=workbench).stdout.splitlines()
    for gone in (
        "docs/plans/contracts.json",
        "docs/plans/index.json",
        "docs/plans/facts.md",
        "docs/research/brief.md",
        "docs/handoffs/h.md",
        "docs/plans/todo/another/README.md",
    ):
        assert gone not in tracked
    for phase in ("todo", "in-progress", "done"):
        assert f"docs/plans/{phase}/.gitkeep" in tracked


def test_owned_module_lists_exact_entries():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "init_engine"))
    import owned

    assert owned.INSTANCE_OWNED == (
        ("docs/plans/todo", "phase"),
        ("docs/plans/in-progress", "phase"),
        ("docs/plans/done", "phase"),
        ("docs/plans/contracts.json", "delete"),
        ("docs/plans/index.json", "delete"),
        ("docs/plans/facts.md", "delete"),
        ("docs/research", "delete"),
        ("docs/handoffs", "delete"),
        ("MEMORY.md", "rewritten"),
        ("ROADMAP.md", "rewritten"),
    )
    assert "AGENTS.md" in owned.GENERATED_ON_CONFLICT


def test_clear_template_history_derives_from_owned_list(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "init_engine"))
    import finalize
    import owned

    monkeypatch.setattr(
        owned,
        "INSTANCE_OWNED",
        (("a/phase", "phase"), ("b.txt", "delete"), ("c", "delete"), ("keep.md", "rewritten")),
    )
    (tmp_path / "a/phase/x").mkdir(parents=True)
    (tmp_path / "b.txt").write_text("x")
    (tmp_path / "c").mkdir()
    (tmp_path / "keep.md").write_text("k")
    (tmp_path / "docs/research").mkdir(parents=True)
    (tmp_path / "docs/research/r.md").write_text("r")
    finalize.clear_template_history(tmp_path)
    assert [p.name for p in (tmp_path / "a/phase").iterdir()] == [".gitkeep"]
    assert not (tmp_path / "b.txt").exists() and not (tmp_path / "c").exists()
    assert (tmp_path / "keep.md").read_text() == "k"
    assert (tmp_path / "docs/research/r.md").exists()
