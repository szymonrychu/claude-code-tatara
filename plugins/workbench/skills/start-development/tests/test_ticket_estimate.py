"""ticket.py estimate, formula estimates on new-task, and per-role actuals from the run dir."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
import estimator  # noqa: E402
import ticket  # noqa: E402
from test_ticket_run import (  # noqa: E402
    cli,
    commit_all,
    git,
    meta_of,
    mk_epic,
    mk_task,
    readme_time,
    run_return,
    setup_run,
    write_run_dir,
)

VERIFY = "pytest -q tests/test_x.py"  # the verify mk_task passes


def task_meta(p):
    return ticket.load(p.read_text(), p).meta


def test_new_task_without_estimate_writes_formula_minutes(root):
    ep = mk_epic(root)
    m = task_meta(mk_task(root, ep, "Alpha"))
    assert m["estimate"] == str(estimator.task_minutes(2, VERIFY))
    assert m["estimate_by"] == "formula"
    assert m["actual_roles"] == ""


def test_new_task_estimate_by(root):
    ep = mk_epic(root)
    m = task_meta(mk_task(root, ep, "Alpha", extra=["--estimate", "45"]))
    assert m["estimate"] == "45" and m["estimate_by"] == "override"


def test_estimate_writes_formula_minutes_and_keeps_overrides(repo, root):
    ep = mk_epic(root)
    a = mk_task(root, ep, "Alpha", files="a.py,b.py,c.py,d.py")
    b = mk_task(root, ep, "Beta", extra=["--estimate", "45"])
    a.write_text(re.sub(r"^estimate: .*$", "estimate: 1", a.read_text(), flags=re.M))
    commit_all(repo)
    r = cli("estimate", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    assert task_meta(a)["estimate"] == str(estimator.task_minutes(4, VERIFY))
    assert task_meta(a)["estimate_by"] == "formula"
    assert task_meta(b)["estimate"] == "45" and task_meta(b)["estimate_by"] == "override"
    lines = r.stdout.strip().splitlines()
    assert lines[0].startswith("Estimate: ") and "agent-min" in lines[0]
    assert re.match(r"^Longest path: \w+ \(\d+ min\)(, \w+ \(\d+ min\))*$", lines[-1])
    assert "Estimate:" in readme_time(root, "todo", ep)
    assert git(repo, "log", "-1", "--format=%s").stdout.strip() == f"chore(ticket): {ep} estimate"


def test_estimate_json_prints_epic_estimate(root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha")
    r = cli("estimate", ep, "--root", root, "--json")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert {"sum", "cp", "p", "epicWall", "longest"} <= set(out)
    assert out["longest"][0]["id"] == "alpha"


def test_time_line_shows_critical_path_and_expected_wall(root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha")
    mk_task(root, ep, "Beta")
    assert cli("tasks", ep, "--root", root).returncode == 0
    time = readme_time(root, "todo", ep)
    assert re.fullmatch(
        r"Estimate: \d+ agent-min \| Critical path: \d+ min \| "
        r"Expected wall at P=[\d.]+: \d+\.\d h \(k=[\d.]+\) \| Actual: 0 min \| "
        r"Remaining estimate: \d+ min",
        time,
    ), time


def test_run_dir_matches_hash_n_labels(tmp_path):
    d = tmp_path / "run"
    write_run_dir(
        d,
        {
            "a1": ("pe:impl:alpha#1", ["2026-01-01T10:00:00Z", "2026-01-01T10:02:00Z"]),
            "a2": ("pe:review:alpha+1", ["2026-01-01T10:03:00Z", "2026-01-01T10:04:00Z"]),
            "a3": ("pe:verify:alpha", ["2026-01-01T10:02:00Z", "2026-01-01T10:03:00Z"]),
        },
    )
    out = ticket._run_dir_durations(d)
    assert out["alpha"]["durationMs"] == 4 * 60000
    assert out["alpha"]["roleMs"] == {"impl": 120000, "review": 60000, "verify": 60000}


def test_apply_run_writes_actual_and_roles(repo, root):
    ep = setup_run(repo, root)
    commit_all(repo)
    d = repo / "run"
    write_run_dir(
        d,
        {
            "a1": ("pe:impl:t-done", ["2026-01-01T10:00:00Z", "2026-01-01T10:02:00Z"]),
            "a2": ("pe:review:t-done", ["2026-01-01T10:03:00Z", "2026-01-01T10:04:00Z"]),
            "a3": ("pe:fix:t-done#2", ["2026-01-01T10:05:00Z", "2026-01-01T10:08:00Z"]),
        },
    )
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    assert cli("apply-run", ep, rj, "--root", root, "--run-dir", d).returncode == 0
    m = meta_of(root, ep, "t-done")
    assert m["actual"] == "6"
    assert m["actual_roles"] == "impl 2, review 1, fix 3"
    # same run again: replaced, not doubled
    assert cli("apply-run", ep, rj, "--root", root, "--run-dir", d).returncode == 0
    m = meta_of(root, ep, "t-done")
    assert m["actual"] == "6" and m["actual_roles"] == "impl 2, review 1, fix 3"
    # a different run adds
    rj.write_text(json.dumps({**run_return(), "run": "second"}))
    assert cli("apply-run", ep, rj, "--root", root, "--run-dir", d).returncode == 0
    m = meta_of(root, ep, "t-done")
    assert m["actual"] == "12" and m["actual_roles"] == "impl 4, review 2, fix 6"


def test_apply_run_duration_fallback_without_run_dir(repo, root):
    ep = setup_run(repo, root)
    commit_all(repo)
    ret = run_return()
    ret["tasks"][0]["durationMs"] = 125_000
    rj = repo / "return.json"
    rj.write_text(json.dumps(ret))
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    m = meta_of(root, ep, ret["tasks"][0]["id"])
    assert m["actual"] == "2" and not m.get("actual_roles")


def test_estimate_prints_three_longest_path_tasks(root):
    ep = mk_epic(root)
    for n in ("Alpha", "Beta", "Gamma", "Delta"):
        mk_task(root, ep, n)
    r = cli("estimate", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    last = r.stdout.strip().splitlines()[-1]
    assert last.startswith("Longest path: ")
    assert len(last.split("), ")) <= 3
    out = json.loads(cli("estimate", ep, "--root", root, "--json").stdout)
    assert {"sum", "cp", "epicWall", "longest"} <= set(out)
