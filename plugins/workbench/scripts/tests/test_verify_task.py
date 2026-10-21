"""verify-task.py: every output field on tmp git repos, triage stubbed."""

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
SCRIPT = SCRIPTS / "verify-task.py"
_spec = importlib.util.spec_from_file_location("verify_task", SCRIPT)
vt = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
_spec.loader.exec_module(vt)

TEST_RE = r"(^|/)(tests?/|test_[^/]*\.py$|[^/]*\.(test|spec)\.[^/]*$|[^/]*_(test|spec)\.[^/]*$)"
MARKERS = "TODO, FIXME, follow-up, round N (any number)"


def git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def write(root, files):
    for name, content in files.items():
        p = Path(root, name)
        if content is None:
            p.unlink()
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)


def commit(root, files, msg="c"):
    write(root, files)
    git(root, "add", "-A")
    git(root, "commit", "-qm", msg)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    git(root, "config", "commit.gpgsign", "false")
    commit(root, {"README.md": "# r\n"}, "base")
    return root


def branch(root, name="feature"):
    git(root, "checkout", "-q", "-b", name)


class Triage:
    """Stub for triage.run: flags parking lines containing 'later', everything plausible."""

    def __init__(self, tier="full", verdict="yes"):
        self.calls, self.tier, self.verdict = [], tier, verdict

    def __call__(self, mode, data, **_):
        self.calls.append((mode, data))
        if mode == "parking":
            return [{**x, "reason": "defers"} for x in data if "later" in x["text"]]
        if mode == "ac-plausible":
            return [{"id": a["id"], "verdict": self.verdict, "reason": "stub"} for a in data]
        return {"classifierTier": self.tier, "reasons": ["stub"]}


def verify(root, command="true", *extra, triage=None, base="main", acs=None):
    argv = [
        "--worktree",
        str(root),
        "--cmd",
        command,
        "--base",
        base,
        "--markers",
        MARKERS,
        "--test-re",
        TEST_RE,
        *extra,
    ]
    if acs is not None:
        f = Path(root).parent / "acs.json"
        f.write_text(json.dumps(acs))
        argv += ["--acs", str(f)]
    code, out = vt.build(argv, triage_run=triage)
    assert code == 0
    return out


def stub_bin(tmp_path, monkeypatch, names, exit_code=0):
    """Fake executables that append their argv to $RECORD.

    Version probes are answered, not recorded: verify-task runs commands via
    `bash -lc`, and a CI image's login profile may run `node -v` on its own.
    """
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    rec = tmp_path / "record.txt"
    probe = 'case "$*" in -v|--version) echo "0.0.0-stub"; exit 0;; esac\n'
    for n in names:
        p = d / n
        p.write_text(f'#!/bin/bash\n{probe}echo "{n} $*" >> "{rec}"\nexit {exit_code}\n')
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{d}{os.pathsep}{os.environ['PATH']}")
    return rec


# ---- head, clean, exit, evidence ----


def test_head_exit_evidence_and_clean(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    out = verify(repo, "seq 1 100; exit 0", "--no-triage")
    assert out["head"] == git(repo, "rev-parse", "HEAD")
    assert (out["exit"], out["passed"], out["clean"]) == (0, True, True)
    lines = out["evidence"].splitlines()
    assert len(lines) == 40 and lines[0] == "61" and lines[-1] == "100"


def test_failing_command_is_not_passed_but_exit_is_zero_from_cli(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--worktree", str(repo), "--cmd", "echo boom; exit 3",
         "--base", "main", "--markers", MARKERS, "--test-re", TEST_RE, "--no-triage"],
        capture_output=True,
        text=True,
    )  # fmt: skip
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert (out["exit"], out["passed"]) == (3, False)
    assert "boom" in out["evidence"]


def test_clean_false_when_dirty_before(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    (repo / "stray.txt").write_text("x")
    assert verify(repo, "true", "--no-triage")["clean"] is False


def test_clean_false_when_command_dirties_tree(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    out = verify(repo, "touch junk.txt", "--no-triage")
    assert out["clean"] is False and out["passed"] is True


def test_command_runs_in_cwd_through_bash(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    out = verify(repo, 'test -f a.py && [ "${BASH_VERSION:+y}" = y ] && echo here', "--no-triage")
    assert out["passed"] and "here" in out["evidence"]


# ---- install ----


def test_install_runs_for_missing_deps_only(repo, tmp_path, monkeypatch):
    rec = stub_bin(tmp_path, monkeypatch, ["npm", "pnpm", "yarn", "uv"])
    branch(repo)
    commit(
        repo,
        {"package.json": "{}", "package-lock.json": "{}", "pyproject.toml": "", "uv.lock": ""},
    )
    out = verify(repo, "true", "--install", "--no-triage")
    assert out["passed"]
    assert rec.read_text().splitlines() == ["npm ci", "uv sync --frozen"]


@pytest.mark.parametrize(
    "lock,expected",
    [
        ("pnpm-lock.yaml", "pnpm install --frozen-lockfile"),
        ("yarn.lock", "yarn install --immutable"),
    ],
)
def test_install_picks_package_manager_by_lockfile(repo, tmp_path, monkeypatch, lock, expected):
    rec = stub_bin(tmp_path, monkeypatch, ["npm", "pnpm", "yarn"])
    branch(repo)
    commit(repo, {"package.json": "{}", lock: ""})
    verify(repo, "true", "--install", "--no-triage")
    assert rec.read_text().splitlines() == [expected]


def test_install_skipped_without_flag_or_when_present(repo, tmp_path, monkeypatch):
    rec = stub_bin(tmp_path, monkeypatch, ["npm", "uv"])
    branch(repo)
    commit(repo, {"package.json": "{}", "pyproject.toml": ""})
    verify(repo, "true", "--no-triage")
    (repo / "node_modules").mkdir()
    (repo / ".venv").mkdir()
    verify(repo, "true", "--install", "--no-triage")
    assert not rec.exists()


@pytest.mark.parametrize(
    "files",
    [
        {"pyproject.toml": '[project]\nname = "x"\nversion = "1"\n'},
        {"pyproject.toml": "[tool.ruff]\nline-length = 100\n"},
    ],
)
def test_install_runs_no_uv_without_lock(repo, tmp_path, monkeypatch, files):
    rec = stub_bin(tmp_path, monkeypatch, ["uv"])
    branch(repo)
    commit(repo, files)
    out = verify(repo, "true", "--install", "--no-triage")
    assert not rec.exists()
    assert out["clean"] and out["passed"]
    if "[project]" in files["pyproject.toml"]:
        assert "no uv.lock" in json.dumps(out["installed"])
    else:
        assert out["installed"] == []


def test_install_runs_uv_sync_with_lock(repo, tmp_path, monkeypatch):
    rec = stub_bin(tmp_path, monkeypatch, ["uv"])
    branch(repo)
    commit(repo, {"pyproject.toml": "[tool.ruff]\n", "uv.lock": ""})
    verify(repo, "true", "--install", "--no-triage")
    assert rec.read_text().splitlines() == ["uv sync --frozen"]


def test_install_uv_requires_lock(repo, tmp_path, monkeypatch):
    rec = stub_bin(tmp_path, monkeypatch, ["uv"])
    branch(repo)
    commit(repo, {"pyproject.toml": '[project]\nname = "x"\nversion = "1"\n'})
    out = verify(repo, "true", "--install", "--no-triage")
    assert not rec.exists()
    assert out["clean"] and "no uv.lock" in json.dumps(out["installed"])


# ---- debtMarkers ----


def test_debt_markers_only_on_added_lines(repo):
    commit(repo, {"old.py": "a = 1\n# TODO old debt\nb = 2\nc = 3\nd = 4\n"}, "seed")
    branch(repo)
    commit(
        repo,
        {
            # line 5 changes; the TODO on line 2 is context, a removed line carries FIXME
            "old.py": "a = 1\n# TODO old debt\nb = 2\nc = 3\nd = 5\n",
            "new.py": "x = 1\n# FIXME later\ny = 2  # see round 7 for this\n",
        },
    )
    out = verify(repo, "true", "--no-triage")
    got = {(d["file"], d["line"], d["marker"]) for d in out["debtMarkers"]}
    assert got == {("new.py", 2, "FIXME"), ("new.py", 3, "round N (any number)")}


def test_debt_marker_on_removed_line_is_not_reported(repo):
    commit(repo, {"f.py": "a = 1\n# TODO old\nb = 2\n"}, "seed")
    branch(repo)
    commit(repo, {"f.py": "a = 1\nb = 2\n"})
    assert verify(repo, "true", "--no-triage")["debtMarkers"] == []


# ---- parking ----


def test_parking_sends_comment_docstring_and_markdown_lines(repo):
    branch(repo)
    commit(
        repo,
        {
            "m.py": (
                'def f():\n    """Do it later maybe."""\n    x = "later"\n'
                "    return x  # fix later\n"
            ),
            "n.js": "// handle later\nconst later = 1\n",
            "docs.md": "# T\nWe will do this later.\n",
        },
    )
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    sent = {(x["file"], x["line"]) for m, d in tri.calls if m == "parking" for x in d}
    assert ("m.py", 2) in sent and ("m.py", 4) in sent  # docstring, trailing comment
    assert ("m.py", 3) not in sent and ("n.js", 2) not in sent  # plain code
    assert ("n.js", 1) in sent and ("docs.md", 2) in sent
    flagged = {(p["file"], p["line"]) for p in out["parking"]}
    assert flagged == {("m.py", 2), ("m.py", 4), ("n.js", 1), ("docs.md", 2)}
    assert all(p["reason"] == "defers" and "text" in p for p in out["parking"])


def test_no_triage_skips_every_call(repo):
    branch(repo)
    commit(repo, {"m.py": "# later\n"})
    tri = Triage()
    out = verify(repo, "true", "--no-triage", triage=tri, acs=[
        {"id": "AC1", "text": "doc", "evidence": {"kind": "judgement"}}])  # fmt: skip
    assert tri.calls == []
    assert out["parking"] == [] and out["tierHint"] is None
    assert out["acs"][0]["plausible"] is None


# ---- changedSincePrevious ----


def test_changed_since_previous(repo):
    branch(repo)
    commit(repo, {"a.py": "1\n", "b.py": "1\n"})
    prev = git(repo, "rev-parse", "HEAD")
    commit(repo, {"a.py": "2\n", "c.py": "1\n", "b.py": None})
    out = verify(repo, "true", "--no-triage", "--prev-head", prev)
    got = {(c["file"], c["status"]) for c in out["changedSincePrevious"]}
    assert got == {("a.py", "M"), ("c.py", "A"), ("b.py", "D")}
    assert verify(repo, "true", "--no-triage")["changedSincePrevious"] is None


# ---- diffstat and tierHint ----


def test_diffstat_splits_test_files_by_regex(repo):
    branch(repo)
    commit(
        repo,
        {
            "src/a.py": "1\n2\n3\n",
            "tests/test_a.py": "1\n2\n",
            "b.spec.js": "1\n",
            "docs.md": "x\n",
        },
    )
    out = verify(repo, "true", "--no-triage")
    assert out["diffstat"] == {"files": 4, "addedNonTest": 4, "addedTest": 3}


def test_tier_hint_is_classifier_tier_with_inputs(repo):
    branch(repo)
    commit(repo, {"src/a.py": "1\n"})
    tri = Triage(tier="panel")
    out = verify(repo, "true", "--requirement", "add auth", triage=tri)
    assert out["tierHint"] == "panel"
    mode, data = next(c for c in tri.calls if c[0] == "tier")
    assert data["requirement"] == "add auth" and data["files"] == ["src/a.py"]
    assert data["diffstat"]["files"] == 1


# ---- acs ----


def ac(id_, text, kind, ref=None):
    ev = {"kind": kind}
    if ref:
        ev["ref"] = ref
    return {"id": id_, "text": text, "evidence": ev}


def by_id(out):
    return {a["id"]: a for a in out["acs"]}


def test_ac_test_met_from_command_output(repo):
    branch(repo)
    commit(repo, {"src/a.py": "1\n"})
    cmd = (
        "echo 'tests/test_a.py::test_parses_input PASSED'; echo 'tests/test_a.py::test_bad FAILED'"
    )
    out = verify(repo, cmd, triage=Triage(), acs=[
        ac("A1", "parses input", "test", "tests/test_a.py::test_parses_input"),
        ac("A2", "bad one", "test", "tests/test_a.py::test_bad")])  # fmt: skip
    a = by_id(out)
    assert a["A1"]["met"] is True and "output" in a["A1"]["how"]
    assert a["A2"]["met"] is False  # no pytest stub on PATH or re-run fails


def test_ac_test_not_ok_line_does_not_count(repo, tmp_path, monkeypatch):
    stub_bin(tmp_path, monkeypatch, ["bats"], exit_code=1)
    branch(repo)
    commit(repo, {"src/a.py": "1\n"})
    out = verify(repo, "echo 'not ok 1 thing works'", "--no-triage", acs=[
        ac("A1", "thing works", "test", "t/x.bats::thing works")])  # fmt: skip
    assert by_id(out)["A1"]["met"] is False


@pytest.mark.parametrize(
    "ref,expected",
    [
        ("tests/test_a.py::test_x", "pytest tests/test_a.py::test_x -q"),
        ("tests/a.test.mjs::the name", "node --test --test-name-pattern the name tests/a.test.mjs"),
        ("tests/a.bats::the name", "bats -f the name tests/a.bats"),
    ],
)
def test_ac_test_rerun_path_by_runner(repo, tmp_path, monkeypatch, ref, expected):
    rec = stub_bin(tmp_path, monkeypatch, ["pytest", "node", "bats"])
    branch(repo)
    commit(repo, {
        "src/a.py": "1\n",
        "tests/test_a.py": "def test_x():\n    pass\n",
        "tests/a.test.mjs": "test('the name', () => {})\n",
    })  # fmt: skip
    out = verify(repo, "echo nothing relevant", "--no-triage", acs=[ac("A1", "x", "test", ref)])
    a = by_id(out)["A1"]
    assert a["met"] is True and "re-ran" in a["how"]
    assert rec.read_text().strip() == expected


def test_ac_test_rerun_failing_is_not_met(repo, tmp_path, monkeypatch):
    stub_bin(tmp_path, monkeypatch, ["pytest"], exit_code=1)
    branch(repo)
    commit(repo, {"src/a.py": "1\n", "tests/test_a.py": "def test_x():\n    pass\n"})
    out = verify(
        repo, "true", "--no-triage", acs=[ac("A1", "x", "test", "tests/test_a.py::test_x")]
    )
    assert by_id(out)["A1"]["met"] is False


@pytest.mark.parametrize(
    "ref,files",
    [
        ("tests/test_a.py::test_x", {"tests/test_a.py": "def test_other():\n    pass\n"}),
        ("tests/test_a.py::test_x", {}),
        ("tests/a.test.mjs::the name", {"tests/a.test.mjs": "test('another name', () => {})\n"}),
    ],
)
def test_ac_test_ref_missing_is_named_and_not_rerun(repo, tmp_path, monkeypatch, ref, files):
    rec = stub_bin(tmp_path, monkeypatch, ["pytest", "node"])
    branch(repo)
    commit(repo, {"src/a.py": "1\n", **files})
    out = verify(repo, "true", "--no-triage", acs=[ac("A1", "x", "test", ref)])
    a = by_id(out)["A1"]
    name = ref.split("::")[1]
    assert a["met"] is False and a["refMissing"] is True
    assert a["how"].startswith(f"ref-missing: no test named `{name}` in ")
    assert "; add or rename a test to exactly this name and file" in a["how"]
    assert not rec.exists() or not rec.read_text().strip()


def test_ac_test_ref_found_in_class_and_js_it_reruns(repo, tmp_path, monkeypatch):
    stub_bin(tmp_path, monkeypatch, ["pytest", "node"])
    branch(repo)
    commit(repo, {
        "tests/test_a.py": "class TestA:\n    def test_x(self):\n        pass\n",
        "tests/b.test.js": 'it("does b", () => {})\n',
    })  # fmt: skip
    out = verify(repo, "true", "--no-triage", acs=[
        ac("A1", "x", "test", "tests/test_a.py::test_x"),
        ac("A2", "y", "test", "tests/b.test.js::does b")])  # fmt: skip
    got = by_id(out)
    assert got["A1"]["met"] is True and got["A2"]["met"] is True
    assert "refMissing" not in got["A1"]


def test_ac_symbol_command_doc_section_judgement(repo):
    branch(repo)
    commit(
        repo,
        {
            "src/a.py": "def frobnicate():\n    pass\n",
            "docs/guide.md": "# Guide\n\n## Install steps\n\ntext\n",
            "untouched.py": "def ghost(): pass\n",
        },
    )
    out = verify(
        repo,
        "true",
        triage=Triage(),
        acs=[
            ac("S1", "frobnicate exists", "symbol", "frobnicate"),
            ac("S2", "ghost exists", "symbol", "ghost_missing"),
            ac("C1", "cmd ok", "command", "test -f src/a.py"),
            ac("C2", "cmd bad", "command", "test -f nope"),
            ac("D1", "install documented", "doc-section", "docs/guide.md#install steps"),
            ac("D2", "absent section", "doc-section", "docs/guide.md#Missing"),
            ac("D3", "no file", "doc-section", "docs/none.md#X"),
            ac("J1", "reads well", "judgement"),
        ],
    )
    a = by_id(out)
    assert a["S1"]["met"] is True and "src/a.py" in a["S1"]["how"]
    assert a["S2"]["met"] is False
    assert (a["C1"]["met"], a["C2"]["met"]) == (True, False)
    assert (a["D1"]["met"], a["D2"]["met"], a["D3"]["met"]) == (True, False, False)
    assert a["J1"]["met"] is None
    assert all(x["how"] for x in a.values())


def test_ac_symbol_not_found_in_untouched_file(repo):
    branch(repo)
    commit(repo, {"src/a.py": "x = 1\n"})
    commit(repo, {"other.py": "def ghost(): pass\n"}, "later")
    git(repo, "checkout", "-q", "-b", "g2", "HEAD~1")  # other.py not in this diff
    out = verify(repo, "true", "--no-triage", acs=[ac("S", "ghost", "symbol", "ghost")])
    assert by_id(out)["S"]["met"] is False


def test_ac_plausible_asked_for_doc_judgement_and_tokenless_refs_only(repo):
    branch(repo)
    commit(repo, {"src/a.py": "def parse_widget():\n    pass\n", "d.md": "## Setup\n\nsteps\n"})
    tri = Triage(verdict="unsure")
    out = verify(
        repo,
        "true",
        triage=tri,
        acs=[
            ac("T1", "parse widget works", "symbol", "parse_widget"),  # shares a token
            ac("T2", "handles empty input", "symbol", "parse_widget"),  # shares none
            ac("D1", "setup documented", "doc-section", "d.md#Setup"),
            ac("J1", "tidy", "judgement"),
            ac("C1", "cmd", "command", "true"),
        ],
    )
    a = by_id(out)
    assert a["T1"]["plausible"] is None and a["C1"]["plausible"] is None
    assert {a[k]["plausible"] for k in ("T2", "D1", "J1")} == {"unsure"}
    sent = [x["id"] for m, d in tri.calls if m == "ac-plausible" for x in d]
    assert sorted(sent) == ["D1", "J1", "T2"]
    d1 = next(x for m, d in tri.calls if m == "ac-plausible" for x in d if x["id"] == "D1")
    assert "steps" in d1["snippet"]


# ---- tdd revert ----


def tdd_repo(repo):
    commit(repo, {"lib_a.py": "OLD\n", "gone.py": "keep me\n", "tests/test_a.py": "t\n"}, "seed")
    branch(repo)
    commit(
        repo, {"lib_a.py": "NEW\n", "added.py": "hi\n", "gone.py": None, "tests/test_a.py": "t2\n"}
    )


TDD_CMD = "grep -q NEW lib_a.py && test -f added.py && test ! -e gone.py"


def test_tdd_revert_modified_added_deleted(repo):
    tdd_repo(repo)
    head = git(repo, "rev-parse", "HEAD")
    out = verify(repo, TDD_CMD, "--no-triage", "--tdd-revert")
    assert out["tdd"] == {
        "ran": True,
        "failedOnBase": True,
        "passedOnHead": True,
        "files": ["added.py", "gone.py", "lib_a.py"],
    }
    assert out["clean"] is True and out["passed"] is True
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / "lib_a.py").read_text() == "NEW\n" and not (repo / "gone.py").exists()


def test_tdd_revert_reports_when_command_passes_on_base(repo):
    tdd_repo(repo)
    out = verify(repo, "true", "--no-triage", "--tdd-revert")
    assert out["tdd"]["failedOnBase"] is False and out["tdd"]["passedOnHead"] is True
    assert out["clean"] is True


def test_tdd_revert_restores_tree_after_an_error(repo, monkeypatch):
    tdd_repo(repo)
    real = vt.run_shell
    calls = []

    def flaky(cmd, cwd):
        calls.append(cmd)
        if len(calls) == 3:  # the head re-run, after the base state is in place
            raise RuntimeError("boom")
        return real(cmd, cwd)

    monkeypatch.setattr(vt, "run_shell", flaky)
    out = verify(repo, TDD_CMD, "--no-triage", "--tdd-revert")
    assert "boom" in out["tdd"]["error"]
    assert out["clean"] is True
    assert (repo / "lib_a.py").read_text() == "NEW\n" and not (repo / "gone.py").exists()


def test_tdd_revert_keeps_executable_bit(repo):
    commit(repo, {"run.sh": "#!/bin/sh\necho old\n"}, "seed")
    branch(repo)
    (repo / "tool.sh").write_text("#!/bin/sh\n")
    (repo / "tool.sh").chmod(0o755)
    commit(repo, {"run.sh": "#!/bin/sh\necho new\n"})
    git(repo, "add", "-A")
    out = verify(repo, "true", "--no-triage", "--tdd-revert")
    assert out["clean"] is True


def test_tdd_absent_without_flag(repo):
    branch(repo)
    commit(repo, {"a.py": "1\n"})
    assert verify(repo, "true", "--no-triage")["tdd"] is None


# ---- never touches history, usage errors ----


def test_never_changes_history_or_branch(repo):
    tdd_repo(repo)
    before = (git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--show-current"))
    git_stash = git(repo, "stash", "list")
    verify(repo, TDD_CMD, "--tdd-revert", "--no-triage")
    assert (git(repo, "rev-parse", "HEAD"), git(repo, "branch", "--show-current")) == before
    assert git(repo, "stash", "list") == git_stash == ""


@pytest.mark.parametrize(
    "argv",
    [
        ["--cmd", "true", "--base", "main", "--test-re", "x"],  # no --markers
        ["--cmd", "true", "--base", "main", "--markers", "TODO"],  # no --test-re
        ["--cmd", "true", "--base", "main", "--markers", "TODO", "--test-re", "("],
        ["--base", "main", "--markers", "TODO", "--test-re", "x"],  # no --command
    ],
)
def test_usage_errors_exit_2(argv):
    r = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)
    assert r.returncode == 2


def test_command_and_note_fields(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    out = verify(repo, "echo hi", "--no-triage")
    assert out["command"] == "echo hi"
    assert "triage skipped" in out["note"]
    out = verify(repo, "echo hi", triage=Triage())
    assert out["note"] == ""


def test_note_reports_triage_failure(repo):
    branch(repo)
    commit(repo, {"a.py": "# later\nx = 1\n"})

    def boom(mode, data):
        raise RuntimeError("down")

    out = verify(repo, "true", triage=boom)
    assert out["tierHint"] is None and "triage" in out["note"]


def test_triage_log_is_passed_to_triage(repo, monkeypatch):
    import triage

    seen = []

    def fake(mode, data, **kw):
        seen.append(kw.get("log"))
        return {"classifierTier": "light", "reasons": []} if mode == "tier" else []

    monkeypatch.setattr(triage, "run", fake)
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    verify(repo, "true", "--triage-log", "/tmp/x.jsonl", triage=None)
    assert seen and set(seen) == {"/tmp/x.jsonl"}


def test_triage_usage_is_summed_into_the_verify_json(repo, monkeypatch):
    import triage

    def fake(mode, data, **kw):
        kw["usage"]["calls"] += 1
        kw["usage"]["input_tokens"] += 10
        kw["usage"]["output_tokens"] += 3
        return {"classifierTier": "light", "reasons": []} if mode == "tier" else []

    monkeypatch.setattr(triage, "run", fake)
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    out = verify(repo, "true", triage=None)
    assert out["triageUsage"] == {"calls": 1, "input_tokens": 10, "output_tokens": 3}
    out = verify(repo, "true", "--no-triage")
    assert out["triageUsage"] == {"calls": 0, "input_tokens": 0, "output_tokens": 0}


def test_no_tier_skips_only_the_tier_call(repo):
    branch(repo)
    commit(repo, {"a.py": "x = 1\n"})
    tri = Triage()
    out = verify(repo, "true", "--no-tier", triage=tri)
    assert [m for m, _ in tri.calls] == []
    assert out["tierHint"] is None
    assert "tier" not in out["note"]
    tri = Triage()
    assert verify(repo, "true", triage=tri)["tierHint"] == "full"
    assert [m for m, _ in tri.calls] == ["tier"]


# ---- rule-documenting prose ----

# Built by concatenation so this test file carries no literal debt marker itself.
TD = "TO" + "DO"
FU = "follow" + "-up"


def test_backticked_and_quoted_prose_is_neither_debt_nor_parking(repo):
    branch(repo)
    commit(
        repo,
        {
            "SKILL.md": (
                "`later` is a parking word\n"
                f'Never write "{TD}" or "{FU}" in a diff\n'
                f'Use `{TD}` and "later" sparingly\n'
            ),
        },
    )
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    assert out["debtMarkers"] == []
    sent = [x for m, d in tri.calls if m == "parking" for x in d]
    assert sent == [] or all("later" not in x["text"] for x in sent)
    assert out["parking"] == []


def test_still_flagged_code_comment(repo):
    branch(repo)
    commit(repo, {"f.py": f"x = 1\n# {TD} later\n"})
    out = verify(repo, "true", "--no-triage")
    assert [(d["file"], d["line"], d["marker"]) for d in out["debtMarkers"]] == [("f.py", 2, TD)]


def test_still_flagged_unquoted_markdown_deferral(repo):
    branch(repo)
    commit(repo, {"note.md": f"# Notes\nThe export is deferred to a {FU}\n"})
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    assert [(d["file"], d["line"]) for d in out["debtMarkers"]] == [("note.md", 2)]
    sent = [x for m, d in tri.calls if m == "parking" for x in d]
    assert any(FU in x["text"] for x in sent)


def test_quoted_text_in_code_files_is_still_scanned(repo):
    branch(repo)
    commit(repo, {"f.py": f'x = "{TD}"\n'})
    assert len(verify(repo, "true", "--no-triage")["debtMarkers"]) == 1


# ---- string literals in test files ----

SKIP_MARKERS = MARKERS + ", .skip(, pytest.mark.skip, xfail, t.Skip("


def test_marker_words_inside_string_literals_of_test_files_are_not_debt(repo):
    branch(repo)
    body = (
        f"const a = {{ marker: '{TD}' }}\n"
        f'expect(p).toContain("Round 2 of at most")\n'
        f"const t = `{FU} Round 3 of ${{n}}`\n"
        "const c = 'it\\'s' + '" + TD + "'\n"
    )
    commit(repo, {"workflows/tests/a.test.mjs": body, "tests/test_x.py": f'x = "{TD}"\n'})
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    assert out["debtMarkers"] == []
    assert out["parking"] == []


def test_comments_and_skips_in_test_files_are_still_flagged(repo):
    branch(repo)
    commit(
        repo,
        {
            "workflows/tests/b.test.mjs": (
                f"// {TD} later\n"
                f"const s = 'a' // it's a {TD}\n"
                "it.skip('works', () => {})\n"
                "t.Skip('no')\n"
            ),
            "tests/test_y.py": (
                f"x = 1  # {TD}\n@pytest.mark.skip\ndef test_a(): pass\n@pytest.mark.xfail\n"
            ),
        },
    )
    out = verify_markers(repo, SKIP_MARKERS)
    got = {(d["file"], d["line"]) for d in out["debtMarkers"]}
    assert ("workflows/tests/b.test.mjs", 1) in got
    assert ("workflows/tests/b.test.mjs", 2) in got
    assert ("workflows/tests/b.test.mjs", 3) in got
    assert ("workflows/tests/b.test.mjs", 4) in got
    assert ("tests/test_y.py", 1) in got
    assert ("tests/test_y.py", 2) in got
    assert ("tests/test_y.py", 4) in got


def verify_markers(root, markers):
    code, out = vt.build(
        [
            "--worktree",
            str(root),
            "--cmd",
            "true",
            "--base",
            "main",
            "--markers",
            markers,
            "--test-re",
            TEST_RE,
            "--no-triage",
        ]
    )
    assert code == 0
    return out


def test_non_test_files_keep_string_literal_scanning(repo):
    branch(repo)
    commit(repo, {"src/a.mjs": f"const a = '{TD}'\nconst b = \"{FU}\"\n"})
    out = verify(repo, "true", "--no-triage")
    got = [(d["file"], d["line"]) for d in out["debtMarkers"]]
    assert got == [("src/a.mjs", 1), ("src/a.mjs", 2)]


# ---- bare-filename test refs, node spec reporter, moved lines ----


def test_bare_filename_ref_resolves_by_diff_basename(repo, tmp_path, monkeypatch):
    rec = stub_bin(tmp_path, monkeypatch, ["pytest"])
    branch(repo)
    commit(repo, {"pkg/tests/test_a.py": "def test_x():\n    pass\n"})
    out = verify(repo, "true", "--no-triage", acs=[ac("A1", "x", "test", "test_a.py::test_x")])
    assert by_id(out)["A1"]["met"] is True
    assert rec.read_text().strip() == "pytest pkg/tests/test_a.py::test_x -q"


def test_bare_filename_ref_falls_back_to_git_ls_files(repo, tmp_path, monkeypatch):
    rec = stub_bin(tmp_path, monkeypatch, ["node"])
    commit(repo, {"workflows/tests/a.test.mjs": "test('the name', () => {})\n"}, "seed")
    branch(repo)
    commit(repo, {"src/a.py": "1\n"})
    out = verify(repo, "true", "--no-triage", acs=[ac("A1", "x", "test", "a.test.mjs::the name")])
    assert by_id(out)["A1"]["met"] is True
    assert rec.read_text().strip() == (
        "node --test --test-name-pattern the name workflows/tests/a.test.mjs"
    )


def test_bare_filename_ref_ambiguous_and_missing_say_so(repo, tmp_path, monkeypatch):
    stub_bin(tmp_path, monkeypatch, ["pytest"], exit_code=1)
    branch(repo)
    commit(repo, {"a/test_a.py": "1\n", "b/test_a.py": "1\n"})
    out = verify(repo, "true", "--no-triage", acs=[
        ac("A1", "x", "test", "test_a.py::test_x"),
        ac("A2", "y", "test", "test_none.py::test_y")])  # fmt: skip
    a = by_id(out)
    assert "ambiguous ref: 2 files named test_a.py" in a["A1"]["how"]
    assert "no file named test_none.py" in a["A2"]["how"]


def test_node_spec_reporter_pass_line_counts(repo):
    branch(repo)
    commit(repo, {"src/a.py": "1\n"})
    cmd = "printf '\\xe2\\x9c\\x94 the name (1.5ms)\\n\\xe2\\x9c\\x96 other (2ms)\\n'"
    out = verify(repo, cmd, "--no-triage", acs=[
        ac("A1", "x", "test", "t/a.test.mjs::the name"),
        ac("A2", "y", "test", "t/a.test.mjs::other")])  # fmt: skip
    a = by_id(out)
    assert a["A1"]["met"] is True and "output" in a["A1"]["how"]
    assert a["A2"]["met"] is False


def test_moved_lines_are_not_debt_or_parking(repo):
    commit(repo, {"w.js": "  'leave a TODO: report it, do not fix it later' +\n"}, "seed")
    branch(repo)
    commit(
        repo,
        {
            "w.js": "const p = 1\n",
            "agents/i.md": "  leave a TODO: report it, do not fix it later\n",
        },
    )
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    assert out["debtMarkers"] == []
    assert [d for m, d in tri.calls if m == "parking" and d] == []


def test_new_text_alongside_moved_text_is_still_flagged(repo):
    commit(repo, {"w.js": "  'a TODO right here',\n"}, "seed")
    branch(repo)
    commit(repo, {"w.js": "const p = 1\n", "i.md": "a TODO right here\nand a FIXME new\n"})
    out = verify(repo, "true", "--no-triage")
    assert [(d["file"], d["line"]) for d in out["debtMarkers"]] == [("i.md", 2)]


def test_rewrapped_unescaped_interpolated_text_is_moved(repo):
    js = (
        "const m = [\n"
        "  '## Context ceiling - hand off, do not push on',\n"
        "  '- Stop working once your context passes ~300k tokens OR you have made ' +\n"
        "  '150 tool calls,',\n"
        "  'not (another task\\'s files, another repo), put it in "
        "' + `${cfg.file}` + '  - never just mention it',\n"
        "].join('\\n')\n"
    )
    commit(repo, {"w.js": js}, "seed")
    branch(repo)
    md = (
        "## Context ceiling - hand off, do not push on\n"
        "- Stop working once your context passes ~300k tokens OR you have made 150 tool calls,\n"
        "not (another task's files, another repo), put it in   - never just mention it\n"
    )
    commit(repo, {"w.js": "const m = 1\n", "agents/i.md": md})
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    assert [d for m, d in tri.calls if m == "parking" and d] == []
    assert out["debtMarkers"] == []


def test_heading_from_trailing_colon_is_moved(repo):
    commit(repo, {"w.js": "  'Escalation rules and a TODO list:' +\n"}, "seed")
    branch(repo)
    commit(repo, {"w.js": "const p = 1\n", "i.md": "## Escalation rules and a TODO list\n"})
    out = verify(repo, "true", "--no-triage")
    assert out["debtMarkers"] == []


def test_docs_plans_skipped_in_parking_and_debt(repo):
    branch(repo)
    commit(
        repo,
        {
            "docs/plans/p.md": "Buckets, per the plan: ports everything not about reviews TODO\n",
            "src/a.md": "a real TODO here\n",
        },
    )
    tri = Triage()
    out = verify(repo, "true", triage=tri)
    assert [d["file"] for d in out["debtMarkers"]] == ["src/a.md"]
    sent = [x["file"] for m, d in tri.calls if m == "parking" for x in (d or [])]
    assert "docs/plans/p.md" not in sent


CLASS_SRC = (
    "class TestA:\n    def test_x(self):\n        pass\n\n"
    "class TestB:\n    def test_y(self):\n        pass\n"
)


@pytest.mark.parametrize(
    "ref,src,missing",
    [
        ("tests/test_a.py::TestA::test_x", CLASS_SRC, False),
        ("tests/test_a.py::TestA::test_y", CLASS_SRC, True),
        ("tests/test_a.py::TestC::test_x", CLASS_SRC, True),
        ("tests/test_a.py::test_p[1-2]", "def test_p(a, b):\n    pass\n", False),
        ("tests/test_a.py::test_q[1-2]", "def test_p(a, b):\n    pass\n", True),
        ("tests/test_a.py::TestA::test_x[a-b]", CLASS_SRC, False),
    ],
)
def test_ac_test_ref_class_and_param_forms(repo, tmp_path, monkeypatch, ref, src, missing):
    stub_bin(tmp_path, monkeypatch, ["pytest"])
    branch(repo)
    commit(repo, {"src/a.py": "1\n", "tests/test_a.py": src})
    out = verify(repo, "true", "--no-triage", acs=[ac("A1", "x", "test", ref)])
    a = by_id(out)["A1"]
    assert a.get("refMissing", False) is missing
    assert a["met"] is not missing


def test_class_ref_resolves(tmp_path):
    (tmp_path / "t.py").write_text(
        "class TestA:\n    def test_in(self):\n        pass\n\n"
        "class TestB:\n    def test_other(self):\n        pass\n\n"
        "def test_top():\n    pass\n"
    )
    miss = lambda n: vt._test_name_missing(str(tmp_path), "t.py", n)  # noqa: E731
    assert miss("TestA::test_in") is False
    assert miss("TestB::test_in") is True  # def is in another class
    assert miss("TestC::test_in") is True  # class absent
    assert miss("TestA::test_top") is True  # def is outside the class
    assert miss("test_top") is False


@pytest.mark.parametrize("ref", ["test_p[1-2]", "TestA::test_p[a-b-c]"])
def test_parametrized_id_resolves(tmp_path, ref):
    (tmp_path / "t.py").write_text(
        "class TestA:\n    def test_p(self, a):\n        pass\n\ndef test_p(a):\n    pass\n"
    )
    assert vt._test_name_missing(str(tmp_path), "t.py", ref) is False
    assert vt._test_name_missing(str(tmp_path), "t.py", ref.replace("test_p", "test_q")) is True
