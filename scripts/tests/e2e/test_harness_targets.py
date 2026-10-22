"""Every harness target proven on a real instantiated project (D14, G5, G9): setup, check,
parse, no Claude files touched, guard hooks deny through the adapter, skill paths resolve, clean
restores the tree, and the config dir migrates to the harness dir and back."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import tomllib

sys.path.insert(0, str(Path(__file__).parent))
from helpers import REPO, git, run  # noqa: E402

sys.path.insert(0, str(REPO / "scripts/init_engine"))
from project_files import is_initialised  # noqa: E402

sys.path.insert(0, str(REPO / "plugins/workbench/hooks/tests"))
import harness_payloads as hp  # noqa: E402

TARGETS = ["copilot", "cursor", "codex", "gemini", "antigravity"]
MCP = {
    "mcpServers": {
        "local": {"command": "npx", "args": ["-y", "some-mcp"]},
        "remote": {"type": "http", "url": "https://mcp.example.com/mcp"},
    }
}
OWNED = ("workbench.json", "settings.local.json", "harness-manifest.json")
DENY = "terraform destroy -auto-approve"
PLUGIN_PATH = re.compile(r"plugins/[A-Za-z0-9_-]+/[A-Za-z0-9_./-]*[A-Za-z0-9_]")


def core():
    spec = importlib.util.spec_from_file_location(
        "_wb_core_e2e", REPO / "plugins/workbench/scripts/lib/workbench.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def project(template, engine, tmp_path) -> Path:
    """A new project: one component, infra and observability packs, a stdio and an HTTP MCP
    server, committed. workbench.json is rewritten in the canonical json layout the generators
    use, so a setup and clean round trip can be byte-identical.
    Template-only: init refuses an already initialised workbench's components."""
    if is_initialised(template):
        pytest.skip("template-only: the workbench is initialised")
    engine(
        "new", "--name", "demo", "--component", "api:python",
        "--remote", f"local-bare:{tmp_path / 'remotes'}", "--purpose", "A demo project",
        "--pack", "infra", "--pack", "observability",
    )  # fmt: skip
    cfg = template / ".claude/workbench.json"
    cfg.write_text(json.dumps(json.loads(cfg.read_text()), indent=2) + "\n")
    (template / ".mcp.json").write_text(json.dumps(MCP, indent=2) + "\n")
    git("add", "-A", cwd=template)
    git("commit", "-q", "-m", "mcp servers", cwd=template)
    return template


def setup(root: Path, *args, check=True):
    return run("mise", "run", "harness-setup", "--", *args, cwd=root, check=check)


def porcelain(root: Path) -> str:
    return git("status", "--porcelain", "-uall", cwd=root)


def owned_files(root: Path, target: str) -> list[str]:
    cdir = core().config_dir(root)
    return json.loads((cdir / "harness-manifest.json").read_text())[target]


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)


def parse_generated(root: Path, files: list[str]) -> list[str]:
    """Parse every JSON and TOML file; return the adapter commands found in them."""
    commands = []
    for rel in files:
        path = root / rel
        if path.suffix == ".json":
            data = json.loads(path.read_text())
        elif path.suffix == ".toml":
            data = tomllib.loads(path.read_text())
        else:
            continue
        commands += [s for s in walk_strings(data) if "adapter.py" in s]
    return commands


def payload_for(target: str) -> dict:
    return next(h for h in hp.ALL if h.harness == target).shell(DENY, "/w")


def adapter_run(root: Path, command: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        command, shell=True, cwd=root, input=json.dumps(payload), capture_output=True, text=True
    )


def check_hooks(root: Path, target: str, commands: list[str]) -> None:
    assert commands, f"{target}: no hook command runs the adapter"
    denied = 0
    for cmd in commands:
        assert f"--harness {target}" in cmd, cmd
        if "--hook guard-bash" in cmd and "--event pre-tool" in cmd:
            p = adapter_run(root, cmd, payload_for(target))
            assert p.returncode == 2, f"{cmd}: {p.returncode} {p.stdout} {p.stderr}"
            assert "terraform destroy" in p.stderr
            denied += 1
        else:  # the adapter must start and answer: allow (0) or a documented block (2)
            p = adapter_run(root, cmd, {})
            assert p.returncode in (0, 2), f"{cmd}: {p.returncode} {p.stderr}"
            assert "No such file" not in p.stderr and "Traceback" not in p.stderr, p.stderr
    assert denied, f"{target}: no guard-bash pre-tool hook was generated"


def check_skills(root: Path, files: list[str]) -> None:
    skills = [f for f in files if f.endswith("/SKILL.md")]
    assert skills, "no skills generated"
    names = [Path(f).parent.name for f in skills]
    assert len(names) == len(set(names)), "duplicate skill names across plugins"
    assert {"kubectl-logs-query", "grafana-debugging-start", "start-development"} <= set(names)
    for rel in skills:
        body = (root / rel).read_text()
        assert "CLAUDE_PLUGIN_ROOT" not in body, rel
        for ref in PLUGIN_PATH.findall(body):
            assert (root / ref).exists(), f"{rel}: rewritten path {ref} does not exist"


def claude_dir_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted((root / ".claude").rglob("*"))
        if p.is_file()
    }


@pytest.mark.parametrize("target", TARGETS)
def test_each_target_roundtrip(project, target):
    before = porcelain(project)
    settings = (project / ".claude/settings.json").read_bytes()
    assert before == ""

    setup(project, target)
    assert setup(project, "--check", check=False).returncode == 0

    files = owned_files(project, target)
    assert files
    assert not (project / ".claude/skills").exists()
    assert (project / ".claude/settings.json").read_bytes() == settings
    parse_generated(project, files)
    check_skills(project, files)

    setup(project, "--clean", target)
    assert porcelain(project) == before
    assert (project / ".claude/settings.json").read_bytes() == settings


@pytest.mark.parametrize("target", TARGETS)
def test_generated_hooks_deny(project, target):
    setup(project, target)
    check_hooks(project, target, parse_generated(project, owned_files(project, target)))


@pytest.mark.parametrize("target", TARGETS)
def test_config_dir_migration_roundtrip(project, target):
    wb = core()
    before_tree = claude_dir_bytes(project)
    before = porcelain(project)

    setup(project, target)
    hdir = project / wb.HARNESS_DIRS[target]
    migrated = json.loads((hdir / "workbench.json").read_text())
    migrated["harness"].pop("active")
    expected_cfg = (json.dumps(migrated, indent=2) + "\n").encode()
    assert (hdir / "workbench.json").is_file()
    assert not (project / ".claude/workbench.json").exists()
    assert wb.config_dir(project) == hdir
    assert wb.active_harness(project) == target
    assert wb.load_config(project)["harness"]["active"] == target
    doc = run(sys.executable, "scripts/doctor.py", "--root", str(project), cwd=project).stdout
    assert "metarepo" in doc and "components: 1" in doc, doc

    setup(project, "claude")
    assert not (hdir / "workbench.json").exists()
    assert wb.config_dir(project) == project / ".claude"
    assert wb.active_harness(project) == "claude"
    after_tree = claude_dir_bytes(project)
    # byte-identical to before the setup; only the recorded harness.targets differs while generated
    assert after_tree.pop(".claude/workbench.json") == expected_cfg
    cfg_before = before_tree.pop(".claude/workbench.json")
    assert json.loads(expected_cfg)["refRunners"] == json.loads(cfg_before)["refRunners"]
    assert after_tree.pop(".claude/harness-manifest.json")  # records the generated files
    assert after_tree == before_tree

    setup(project, "--clean", target)
    assert porcelain(project) == before
    before_tree[".claude/workbench.json"] = cfg_before
    assert claude_dir_bytes(project) == before_tree


def test_clean_while_active_restores_tree(project):
    before = porcelain(project)
    config_before = (project / ".claude/workbench.json").read_bytes()
    setup(project, "codex")
    assert (project / ".codex/workbench.json").is_file()
    setup(project, "--clean", "codex")
    assert porcelain(project) == before
    assert (project / ".claude/workbench.json").read_bytes() == config_before


def test_all_targets(project):
    wb = core()
    before = porcelain(project)
    settings = (project / ".claude/settings.json").read_bytes()
    setup(project, "all")
    assert setup(project, "--check", check=False).returncode == 0
    assert (project / ".claude/settings.json").read_bytes() == settings
    assert wb.config_dir(project) == project / ".claude"  # several targets: no migration
    for target in TARGETS:
        parse_generated(project, owned_files(project, target))
    for target in TARGETS:
        setup(project, "--clean", target)
    assert porcelain(project) == before
