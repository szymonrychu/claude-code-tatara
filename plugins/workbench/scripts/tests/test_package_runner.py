"""workbench.py package_root / runner_for / runner CLI."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import workbench  # noqa: E402

CLI = SCRIPTS / "lib" / "workbench.py"


def repo(tmp_path, files=None, cfg=None):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for rel, text in (files or {}).items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    if cfg is not None:
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "workbench.json").write_text(json.dumps(cfg))
    return tmp_path


def test_package_root_markers(tmp_path):
    r = repo(tmp_path, {"nodes/a/pyproject.toml": "", "nodes/a/tests/t.py": "", "x/y.py": ""})
    assert workbench.package_root(r / "nodes/a/tests/t.py", r) == r / "nodes/a"
    assert workbench.package_root(r / "x/y.py", r) == r


def test_package_root_each_marker(tmp_path):
    r = repo(tmp_path, {"a/package.json": "{}", "a/t.js": "", "b/package.xml": "", "b/t.py": ""})
    assert workbench.package_root(r / "a/t.js", r) == r / "a"
    assert workbench.package_root(r / "b/t.py", r) == r / "b"


def test_uv_lock_with_pytest_uses_uv_run(tmp_path):
    r = repo(
        tmp_path,
        {
            "nodes/a/pyproject.toml": "",
            "nodes/a/uv.lock": '[[package]]\nname = "pytest"\nversion = "8"\n',
            "nodes/a/tests/test_x.py": "",
        },
    )
    got = workbench.runner_for("nodes/a/tests/test_x.py::test_one", r)
    assert got["cwd"] == str(r / "nodes/a")
    assert got["argv"] == ["uv", "run", "--frozen", "pytest", "tests/test_x.py::test_one", "-q"]
    assert got["source"] == "builtin"


def test_pyproject_without_lock(tmp_path):
    r = repo(tmp_path, {"p/pyproject.toml": ""})
    got = workbench.runner_for("p/t_x.py::a", r)
    assert got["argv"] == ["pytest", "t_x.py::a", "-q"]


def test_uv_lock_without_pytest_uses_path_pytest(tmp_path):
    r = repo(
        tmp_path,
        {"p/pyproject.toml": "", "p/uv.lock": '[[package]]\nname = "pytest-cov"\n', "p/t.py": ""},
    )
    assert workbench.runner_for("p/t.py::a", r)["argv"] == ["pytest", "t.py::a", "-q"]


def test_pyproject_declares_pytest_with_lock(tmp_path):
    for i, body in enumerate(
        [
            '[project]\nname="x"\ndependencies=["pytest>=8"]\n',
            '[project.optional-dependencies]\ndev=["pytest"]\n',
            '[dependency-groups]\ndev=["pytest>=8"]\n',
        ]
    ):
        r = repo(tmp_path / str(i), {"pyproject.toml": body, "uv.lock": "", "t.py": ""})
        assert workbench.runner_for("t.py::a", r)["argv"][:4] == ["uv", "run", "--frozen", "pytest"]


def test_vitest_package_runner(tmp_path):
    pj = json.dumps({"devDependencies": {"vitest": "1"}})
    r = repo(tmp_path, {"fe/package.json": pj})
    got = workbench.runner_for("fe/src/a.test.ts::renders", r)
    assert got["cwd"] == str(r / "fe")
    assert got["argv"] == ["npx", "vitest", "run", "src/a.test.ts", "-t", "renders"]


def test_node_test(tmp_path):
    r = repo(tmp_path, {"n/package.json": "{}"})
    got = workbench.runner_for("n/a.test.mjs::works", r)
    assert got["argv"] == ["node", "--test", "--test-name-pattern", "works", "a.test.mjs"]


def test_package_xml_uses_path_pytest(tmp_path):
    r = repo(tmp_path, {"ros/package.xml": ""})
    got = workbench.runner_for("ros/t.py::a", r)
    assert got["argv"] == ["pytest", "t.py::a", "-q"]
    assert workbench.runner_for("ros/t.js::a", r) is None


def test_bats_anywhere(tmp_path):
    r = repo(tmp_path, {"p/pyproject.toml": ""})
    got = workbench.runner_for("p/t.bats::does it", r)
    assert got["argv"] == ["bats", "-f", "does it", "t.bats"]
    assert got["cwd"] == str(r / "p")


def test_root_refs_keep_current_forms(tmp_path):
    r = repo(tmp_path)
    assert workbench.runner_for("scripts/t.py::a", r)["argv"] == ["pytest", "scripts/t.py::a", "-q"]
    assert workbench.runner_for("t.js::a", r)["argv"] == [
        "node",
        "--test",
        "--test-name-pattern",
        "a",
        "t.js",
    ]
    assert workbench.runner_for("t.bats::a", r)["argv"] == ["bats", "-f", "a", "t.bats"]
    assert workbench.runner_for("notes.md::a", r) is None


def test_ref_runners_override(tmp_path):
    r = repo(
        tmp_path,
        {"nodes/a/pyproject.toml": ""},
        cfg={"refRunners": {"nodes/**/*.py": "make -C . test T={ref} F={file} N={name} P={pkg}"}},
    )
    got = workbench.runner_for("nodes/a/tests/t.py::case", r)
    assert got["source"] == "refRunners"
    assert got["cwd"] == str(r / "nodes/a")
    assert got["argv"] == [
        "bash",
        "-c",
        "make -C . test T=tests/t.py::case F=tests/t.py N=case P=a",
    ]


def test_cli(tmp_path):
    r = repo(tmp_path, {"p/pyproject.toml": ""})
    ok = subprocess.run(
        [sys.executable, str(CLI), "runner", "p/t.py::a", "--repo", str(r)],
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0 and json.loads(ok.stdout)["source"] == "builtin"
    no = subprocess.run(
        [sys.executable, str(CLI), "runner", "x.md::a", "--repo", str(r)],
        capture_output=True,
        text=True,
    )
    assert no.returncode == 2
    assert "workbench.py: no runner for x.md::a" in no.stderr


def test_no_runner_exits_2(tmp_path):
    r = repo(tmp_path, {"p/pyproject.toml": ""})
    assert workbench.runner_for("p/t.cpp::a", r) is None
    for ref in ("p/t.cpp::a", "p/t.tsx::a"):
        no = subprocess.run(
            [sys.executable, str(CLI), "runner", ref, "--repo", str(r)],
            capture_output=True,
            text=True,
        )
        assert no.returncode == 2
        assert f"workbench.py: no runner for {ref}" in no.stderr


def test_ref_runners_shell_braces_kept(tmp_path):
    r = repo(tmp_path, cfg={"refRunners": {"*.py": "awk '{print}' ${HOME} {ref} {unknown}"}})
    got = workbench.runner_for("a.py::x", r)
    assert got["argv"][2] == "awk '{print}' ${HOME} a.py::x {unknown}"
