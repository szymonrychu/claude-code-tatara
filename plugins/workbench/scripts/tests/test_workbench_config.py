"""workbench.py config reader: schema, defaults, overlap globs, CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS / "lib"))
import workbench  # noqa: E402

CLI = SCRIPTS / "lib" / "workbench.py"


def repo(tmp_path, cfg=None, raw=None):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".claude").mkdir()
    if cfg is not None:
        raw = json.dumps(cfg)
    if raw is not None:
        (tmp_path / ".claude" / "workbench.json").write_text(raw)
    return tmp_path


def test_defaults_without_file(tmp_path):
    r = repo(tmp_path)
    c = workbench.load_config(r)
    assert c["refRunners"] == {} and c["suites"] == [] and c["deploy"] == {}
    assert c["overlapIgnore"] == workbench.DEFAULT_OVERLAP_IGNORE


def test_overlap_ignore_appends_repo_globs(tmp_path):
    r = repo(
        tmp_path,
        {
            "refRunners": {"*.go": "go test {file}"},
            "suites": ["make test"],
            "deploy": {"command": "make deploy", "verify": "make check"},
            "overlapIgnore": ["docs/**"],
        },
    )
    sub = r / "a" / "b"
    sub.mkdir(parents=True)
    c = workbench.load_config(sub)
    assert c["refRunners"] == {"*.go": "go test {file}"}
    assert c["suites"] == ["make test"]
    assert c["deploy"] == {"command": "make deploy", "verify": "make check"}
    assert c["overlapIgnore"] == workbench.DEFAULT_OVERLAP_IGNORE + ["docs/**"]
    assert workbench.DEFAULT_OVERLAP_IGNORE == [
        "*README.md",
        "MEMORY.md",
        "**/SKILL.md",
        "tests/README.md",
        "CHANGELOG.md",
    ]


@pytest.mark.parametrize(
    "cfg,key",
    [
        ({"bogus": 1}, "bogus"),
        ({"refRunners": []}, "refRunners"),
        ({"refRunners": {"*.go": 3}}, "refRunners"),
        ({"suites": "x"}, "suites"),
        ({"suites": [1]}, "suites"),
        ({"deploy": {"command": "x"}}, "deploy"),
        ({"deploy": {"command": "x", "verify": 2}}, "deploy"),
        ({"deploy": {"command": "x", "verify": "y", "z": "w"}}, "deploy"),
        ({"overlapIgnore": "x"}, "overlapIgnore"),
        ([], "workbench.json"),
    ],
)
def test_bad_config_raises(tmp_path, cfg, key):
    r = repo(tmp_path, cfg)
    with pytest.raises(workbench.ConfigError) as e:
        workbench.load_config(r)
    assert "workbench.json" in str(e.value) and key in str(e.value)


def test_malformed_json(tmp_path):
    r = repo(tmp_path, raw="{nope")
    with pytest.raises(workbench.ConfigError) as e:
        workbench.load_config(r)
    assert "workbench.json" in str(e.value)


def test_overlap_ignored_globs():
    g = workbench.DEFAULT_OVERLAP_IGNORE
    assert workbench.overlap_ignored("README.md", g)
    assert workbench.overlap_ignored("skills/x/README.md", g)
    assert workbench.overlap_ignored("MEMORY.md", g)
    assert workbench.overlap_ignored("SKILL.md", g)
    assert workbench.overlap_ignored("skills/a/b/SKILL.md", g)
    assert workbench.overlap_ignored("tests/README.md", g)
    assert workbench.overlap_ignored("CHANGELOG.md", g)
    assert not workbench.overlap_ignored("src/app.py", g)
    assert not workbench.overlap_ignored("docs/MEMORY.md.bak", g)
    assert workbench.overlap_ignored("docs/a/b.md", ["docs/**/b.md"])
    assert workbench.overlap_ignored("docs/b.md", ["docs/**/b.md"])


def test_config_for_repo_fallback(tmp_path):
    root = tmp_path / "wb"
    (root / "code").mkdir(parents=True)
    (root / ".gitmodules").write_text("")
    comp = root / "code" / "svc"
    comp.mkdir()
    repo(comp, {"suites": ["svc test"]})
    # plans root is its own git repo with a config
    top = repo(root, {"suites": ["root test"]})
    assert workbench.config_for_repo(top, "svc")["suites"] == ["svc test"]
    assert workbench.config_for_repo(top, "missing")["suites"] == ["root test"]
    assert workbench.config_for_repo(top, "superrepo")["suites"] == ["root test"]


def test_config_cli(tmp_path):
    r = repo(tmp_path, {"suites": ["a"]})
    out = subprocess.run(
        [sys.executable, str(CLI), "config", "--repo", str(r)], capture_output=True, text=True
    )
    assert out.returncode == 0
    assert json.loads(out.stdout)["suites"] == ["a"]
    (r / ".claude" / "workbench.json").write_text('{"x": 1}')
    bad = subprocess.run(
        [sys.executable, str(CLI), "config", "--repo", str(r)], capture_output=True, text=True
    )
    assert bad.returncode == 1 and bad.stderr.startswith("workbench.py: ")
    assert "x" in bad.stderr


def test_overlap_ignored_dot_prefixed_paths():
    assert workbench.overlap_ignored("./.github/x.md", [".github/x.md"])
    assert workbench.overlap_ignored("./docs/a.md", ["docs/a.md"])


def test_harness_key_valid(tmp_path):
    h = {"targets": ["copilot", "codex"], "models": {"codex": {"fast": "gpt-x"}}}
    c = workbench.load_config(repo(tmp_path, {"harness": h}))
    assert c["harness"] == h


def test_harness_models_optional(tmp_path):
    c = workbench.load_config(repo(tmp_path, {"harness": {"targets": ["cursor"]}}))
    assert c["harness"]["targets"] == ["cursor"]


def test_harness_absent_defaults_empty(tmp_path):
    assert workbench.load_config(repo(tmp_path))["harness"] == {"targets": [], "models": {}}


@pytest.mark.parametrize(
    "bad",
    [
        {"targets": ["vim"]},
        {"targets": "codex"},
        {"targets": [1]},
        {},
        "codex",
        {"targets": ["codex"], "models": ["x"]},
        {"targets": ["codex"], "models": {"gemini": {"a": "b"}}, "extra": 1},
        {"targets": ["codex"], "models": {"vim": {"a": "b"}}},
        {"targets": ["codex"], "models": {"codex": {"a": 1}}},
        {"targets": ["codex"], "models": {"codex": "m"}},
    ],
)
def test_harness_invalid_names_key(tmp_path, bad):
    with pytest.raises(workbench.ConfigError, match="harness"):
        workbench.load_config(repo(tmp_path, {"harness": bad}))


def test_harness_key(tmp_path):
    h = {"targets": ["copilot", "codex"], "models": {"codex": {"fast": "gpt-x"}}}
    assert workbench.load_config(repo(tmp_path, {"harness": h}))["harness"] == h
    with pytest.raises(workbench.ConfigError, match="harness"):
        workbench.load_config(repo(tmp_path / "u", {"harness": {"targets": ["vim"]}}))
