"""project_files: init writes the real project into AGENTS.md, .mise.toml and the docs."""

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def new(run_cli, *extra, comps=("api:python", "web:typescript")):
    args = ["new", "--name", "demo", "--remote", "local-bare"]
    for c in comps:
        args += ["--component", c]
    return run_cli(*args, *extra)


def test_agents_md_project_block(workbench, run_cli, allow_file):
    r = new(
        run_cli,
        "--purpose",
        "A booking service for dentists.",
        "--hard-rule",
        "No PII in logs",
        "--hard-rule",
        "Every endpoint is authenticated",
        "--risk",
        "The payments path",
        "--role",
        "api=HTTP backend",
        "--role",
        "web=Customer UI",
    )
    assert r.returncode == 0, r.stderr
    text = (workbench / "AGENTS.md").read_text()
    assert "workbench:uninitialised" not in text
    assert "Template maintenance" not in text
    assert "A booking service for dentists." in text
    assert "- No PII in logs\n- Every endpoint is authenticated" in text
    assert "The payments path" in text
    assert "| Submodule | Lang | Role | Build |" in text
    assert "| api | python | HTTP backend | `mise run --cd code/api test` |" in text
    assert "| web | typescript | Customer UI |" in text
    assert "Filled by init" not in text
    assert "<!-- workbench:rules:begin -->" in text and "## Ground rules" in text
    assert "## Forge" in text
    assert "not on a known forge" in text


def test_missing_answers_become_ask_placeholders(workbench, run_cli, allow_file):
    assert new(run_cli).returncode == 0
    text = (workbench / "AGENTS.md").read_text()
    assert text.count("_Ask the user:") == 3
    assert "| api | python | ask the user |" in text


def test_forge_wording_from_origin_hosts(workbench, run_cli, allow_file):
    import sys
    from importlib import import_module

    sys.path.insert(0, str(workbench / "scripts/init_engine"))
    pf = import_module("project_files")
    assert pf.forge_of("git@github.com:o/r.git") == "github"
    assert pf.forge_of("https://gitlab.example.com/g/r") == "gitlab"
    assert pf.forge_of("ssh://git@git.corp.example/r") == "local"
    assert pf.forge_of("/srv/remotes/r.git") == "local"
    gh = pf.forge_section([("a", "https://github.com/o/a")])
    assert "pull requests" in gh and "merge requests" not in gh
    gl = pf.forge_section([("a", "git@gitlab.com:g/a.git")])
    assert "merge requests" in gl and "pull requests" not in gl
    both = pf.forge_section([("a", "https://github.com/o/a"), ("b", "https://gitlab.com/g/b")])
    assert "a: PR" in both and "b: MR" in both


def test_code_tasks_fan_out(workbench, run_cli, allow_file):
    before = (workbench / ".mise.toml").read_text()
    assert new(run_cli).returncode == 0
    after = (workbench / ".mise.toml").read_text()
    begin = "# workbench:code-tasks:begin\n"
    end = "# workbench:code-tasks:end"
    assert before.split(begin)[0] == after.split(begin)[0]
    assert before.split(end)[1] == after.split(end)[1]
    block = after.split(begin)[1].split(end)[0]
    for task in ("test", "lint", "fmt"):
        assert f'[tasks."code:{task}"]' in block
        for comp in ("api", "web"):
            assert f'"mise run --cd code/{comp} {task}"' in block


def test_docs_reset(workbench, run_cli, allow_file):
    assert new(run_cli, "--role", "api=HTTP backend").returncode == 0
    arch = (workbench / "docs/architecture.md").read_text()
    assert "- `code/api` (python): HTTP backend" in arch
    assert "- `code/web` (typescript):" in arch
    assert "uninitialised" not in arch
    mem = (workbench / "MEMORY.md").read_text()
    assert "project initialised; components: api, web; adoption method: new" in mem
    assert "plugins/workbench imported" not in mem
    assert len([ln for ln in mem.splitlines() if ln[:2] == "20"]) == 1
    road = (workbench / "ROADMAP.md").read_text()
    assert "the agent asks the user" in road and "No requirements are recorded" in road


def test_idempotent(workbench, run_cli, allow_file):
    assert new(run_cli, "--purpose", "Keep me", "--role", "api=Kept role").returncode == 0
    sys_path = str(workbench / "scripts/init_engine")
    snapshot = {
        f: (workbench / f).read_text()
        for f in ("AGENTS.md", ".mise.toml", "docs/architecture.md", "MEMORY.md", "ROADMAP.md")
    }
    code = (
        f"import sys; sys.path.insert(0, {sys_path!r}); import project_files as p; "
        f"from pathlib import Path; p.write_all(Path({str(workbench)!r}), today='2099-01-01')"
    )
    for _ in range(2):
        subprocess.run(["python3", "-c", code], check=True, capture_output=True)
    for f, text in snapshot.items():
        now = (workbench / f).read_text()
        if f == "MEMORY.md":
            assert now.startswith(text)
        else:
            assert now == text, f
    assert "Keep me" in snapshot["AGENTS.md"] and "Kept role" in snapshot["AGENTS.md"]


def test_adopt_url_rewrites_for_new_component(workbench, run_cli, allow_file, tmp_path):
    assert new(run_cli, "--risk", "Billing", comps=("api:python",)).returncode == 0
    src = tmp_path / "ext"
    src.mkdir()
    for cmd in (
        ["init", "-q", "-b", "main"],
        ["commit", "-q", "--allow-empty", "-m", "i"],
    ):
        subprocess.run(["git", *cmd], cwd=src, check=True, capture_output=True)
    (src / "go.mod").write_text("module x\n")
    subprocess.run(["git", "add", "-A"], cwd=src, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "go"], cwd=src, check=True, capture_output=True)
    r = run_cli("adopt", "--url", str(src), "--name", "ext", "--role", "ext=Adopted service")
    assert r.returncode == 0, r.stderr
    text = (workbench / "AGENTS.md").read_text()
    assert "| ext | go | Adopted service |" in text
    assert "| api | python |" in text and "Billing" in text
    assert "code/ext" in (workbench / ".mise.toml").read_text()
    mem = (workbench / "MEMORY.md").read_text()
    assert mem.count("project initialised") == 1 and "ext" in mem.splitlines()[-1]


def test_role_for_unknown_component_refused(workbench, run_cli, allow_file):
    r = new(run_cli, "--role", "nope=x")
    assert r.returncode == 1 and "names no component" in r.stderr


def test_invalid_role_shape_refused_before_anything_is_created(workbench, run_cli, allow_file):
    r = new(run_cli, "--role", "noequals")
    assert r.returncode == 1 and "<component>=<text>" in r.stderr
    assert not (workbench / "code" / "api").exists()


def test_repo_template_markers_exist():
    assert "# workbench:code-tasks:begin" in (REPO / ".mise.toml").read_text()
    assert "workbench:project:begin" in (REPO / "AGENTS.md").read_text()
