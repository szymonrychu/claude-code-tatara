"""Estimator: parameter file, formulas, refit and CLI."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib"
FIX = Path(__file__).resolve().parent / "estimator_tasks.json"
spec = importlib.util.spec_from_file_location("estimator", LIB / "estimator.py")
est = importlib.util.module_from_spec(spec)
sys.modules["estimator"] = est
spec.loader.exec_module(est)

TRUE = [
    "mise run test",
    "mise run test && mise run lint",
    "make test",
    "npm test",
    "pnpm test",
    "yarn test",
    "go test ./...",
    "cargo test",
    "pytest",
    "pytest -q",
    "uv run pytest",
    "bash scripts/run-tests.sh",
    "cd plugins/workbench && bash scripts/run-tests.sh",
]
FALSE = [
    "pytest tests/test_x.py -q",
    "cd plugins/workbench && bash scripts/run-tests.sh --only workflows",
    "node --test workflows/tests/a.test.mjs",
    "cargo test parser::",
    "go test ./pkg/x -run TestY",
    "ruff check scripts",
]


def test_full_suite_patterns():
    for c in TRUE:
        assert est.full_suite(c), c
    for c in FALSE:
        assert not est.full_suite(c), c


def test_full_suite_suites_entry():
    assert est.full_suite("./ci  all", suites=["./ci all"])
    assert not est.full_suite("./ci one", suites=["./ci all"])


def test_task_minutes():
    assert est.task_minutes(0, "ruff check") == 4
    assert est.task_minutes(6, "pytest") == round(4.0 * 7**0.22 * 6.9)
    assert (
        est.task_minutes(1, "x", params={"intercept": 0.1, "exponent": 0, "fullSuiteFactor": 1})
        == 1
    )


def test_parallelism():
    assert est.parallelism(5) == 1.5
    assert est.parallelism(15) == 1.5
    assert est.parallelism(30) == 3.0
    assert est.parallelism(99) == 3.0
    assert est.parallelism(22) == 2.2


def test_epic_estimate():
    tasks = [
        {"id": "a", "minutes": 10, "depends_on": [], "status": "done"},
        {"id": "b", "minutes": 30, "depends_on": ["a"], "status": "todo"},
        {"id": "c", "minutes": 20, "depends_on": ["b"], "status": "todo"},
        {"id": "d", "minutes": 5, "depends_on": [], "status": "todo"},
    ]
    r = est.epic_estimate(tasks)
    assert r["sum"] == 65 and r["remaining"] == 55
    assert r["cp"] == 60 and r["path"] == ["a", "b", "c"]
    assert r["p"] == 1.5
    assert r["runWall"] == 60 and r["epicWall"] == 120
    assert r["longest"] == [
        {"id": "b", "minutes": 30},
        {"id": "c", "minutes": 20},
        {"id": "a", "minutes": 10},
    ]


def test_refit_matches_brief_on_measured_tasks():
    rows = json.loads(FIX.read_text())
    assert len(rows) == 94
    p = est.refit(rows)
    assert abs(p["intercept"] - 3.996) < 0.02
    assert abs(p["exponent"] - 0.2203) < 0.005
    assert abs(p["fullSuiteFactor"] - 6.865) < 0.05
    assert abs(est.mdape(rows, est.load()["task"]) - 0.443) < 0.01


def test_cli_refit_fixture_and_write(tmp_path):
    cfg = tmp_path / "estimator.json"
    cfg.write_text((LIB / "estimator.json").read_text())
    r = subprocess.run(
        [sys.executable, str(LIB / "estimator.py"), "refit", "--fixture", str(FIX)],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(r.stdout)
    assert {"intercept", "exponent", "fullSuiteFactor", "mdape"} <= set(out)
    r = subprocess.run(
        [
            sys.executable,
            str(LIB / "estimator.py"),
            "refit",
            "--fixture",
            str(FIX),
            "--write",
            "--config",
            str(cfg),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    new = json.loads(cfg.read_text())
    assert new["task"]["exponent"] == json.loads(r.stdout)["exponent"]
    assert new["epic"]["k"] == 2.0 and new["fullSuitePatterns"]


def test_cli_refit_plans_root(tmp_path):
    t = tmp_path / "done" / "e" / "tasks"
    t.mkdir(parents=True)
    for i, (files, verify, actual) in enumerate(
        [(1, "ruff check", 5), (3, "pytest", 40), (6, "mise run test", 60), (2, "ruff", 6)]
    ):
        (t / f"t{i}.md").write_text(
            f"---\ntitle: T\nstatus: done\nfiles: [{', '.join(f'f{j}' for j in range(files))}]\n"
            f'verify: "{verify}"\nactual: {actual}\n---\nbody\n'
        )
    (t / "skip.md").write_text(
        '---\ntitle: S\nstatus: done\nfiles: [a]\nverify: x\nactual: ""\n---\n'
    )
    r = subprocess.run(
        [sys.executable, str(LIB / "estimator.py"), "refit", "--plans-root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["mdape"] >= 0


def test_full_suite_matches_repo_suites():
    assert est.full_suite("./ci  all", suites=["./ci all"])
    assert est.full_suite("cd x && ./ci all", suites=["./ci all"])
    assert not est.full_suite("./ci all --one", suites=["./ci all"])


def test_task_minutes_formula():
    assert est.task_minutes(4, "pytest tests/test_x.py -q") == 6
    assert est.task_minutes(4, "mise run test") == 39
    assert est.task_minutes(0, "ruff check scripts") == 4


def test_epic_estimate_epic_a():
    tasks = [{"id": "c0", "minutes": 325, "depends_on": [], "status": "todo"}]
    rest, n = 1341 - 325, 61
    for i in range(n):
        m = rest // n + (1 if i < rest % n else 0)
        tasks.append({"id": f"t{i}", "minutes": m, "depends_on": [], "status": "todo"})
    r = est.epic_estimate(tasks)
    assert r["sum"] == 1341 and r["cp"] == 325
    assert r["p"] == 3.0
    assert round(r["runWall"]) == 447 and round(r["epicWall"]) == 894


def test_parallelism_interpolates():
    assert est.parallelism(10) == 1.5
    assert est.parallelism(16) == 1.6
    assert est.parallelism(40) == 3.0


def test_fixture_mdape_under_half():
    rows = json.loads(FIX.read_text())
    assert len(rows) == 94
    assert est.mdape(rows, est.load()["task"]) < 0.5


def test_refit_reproduces_params():
    p = est.refit(json.loads(FIX.read_text()))
    assert abs(p["intercept"] - 4.0) <= 0.2
    assert abs(p["exponent"] - 0.22) <= 0.03
    assert abs(p["fullSuiteFactor"] - 6.9) <= 0.5


def test_params_come_from_json(tmp_path):
    cfg = json.loads((LIB / "estimator.json").read_text())
    base = est.task_minutes(4, "x", params=est.load()["task"])
    cfg["task"]["intercept"] = 8.0
    f = tmp_path / "e.json"
    f.write_text(json.dumps(cfg))
    assert est.task_minutes(4, "x", params=est.load(f)["task"]) > base


def test_refit_cli_writes_task_params(tmp_path):
    cfg = tmp_path / "estimator.json"
    cfg.write_text((LIB / "estimator.json").read_text())
    before = json.loads(cfg.read_text())
    subprocess.run(
        [
            sys.executable,
            str(LIB / "estimator.py"),
            "refit",
            "--fixture",
            str(FIX),
            "--write",
            "--config",
            str(cfg),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    after = json.loads(cfg.read_text())
    assert {k: v for k, v in after.items() if k != "task"} == {
        k: v for k, v in before.items() if k != "task"
    }
    assert set(after["task"]) == set(before["task"])


def test_full_suite_examples():
    ex = est.load()["fullSuiteExamples"]
    assert len(ex) >= 7
    for e in ex:
        assert est.full_suite(e["command"]) is e["full"], e["command"]
