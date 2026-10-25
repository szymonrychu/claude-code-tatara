"""ticket.py deltas: estimate against actual per task, MdAPE per metric, and the bucket table."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
from ticket_repo_helpers import cli, commit_all, epic_dir, git, mk_epic, mk_task, task_path, ticket

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import calibration  # noqa: E402

NR = "not recorded"
METRICS = ("points", "minutes", "tokens")


def edit(path: Path, drop=(), notes="", **kw) -> None:
    doc = ticket.load(path.read_text(), path)
    for key in drop:
        doc.meta.pop(key, None)
    doc.meta.update(kw)
    body = doc.body.replace("## Notes\n", f"## Notes\n\n{notes}\n", 1) if notes else doc.body
    path.write_text(ticket.dump(ticket.Doc(doc.meta, body)))


def measured(root, ep, task, pa, am, at, **kw) -> None:
    edit(
        task_path(root, ep, task),
        status="done",
        points_actual=pa,
        actual_minutes=am,
        actual_tokens=at,
        **kw,
    )


def to_done(repo, root, ep) -> None:
    (root / "done").mkdir(exist_ok=True)
    git(repo, "mv", str(epic_dir(root, ep)), str(root / "done" / ep))
    git(repo, "commit", "-m", f"chore(ticket): {ep} move done")


def deltas(root, logs, *args):
    return cli("deltas", *args, "--logs", logs, "--root", root)


def as_json(r):
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def by_slug(report):
    return {row["slug"]: row for row in report["rows"]}


def test_epic_deltas(repo, root, tmp_path):
    logs = tmp_path / "logs"
    ep = mk_epic(root)
    for s in ("alpha", "beta", "gamma"):
        mk_task(root, ep, s)  # points 3: seed expected 34 minutes, 2250000 tokens
    measured(root, ep, "alpha", "5", "51", "4500000")
    measured(root, ep, "beta", "3", "17", "1125000")
    commit_all(repo)

    report = as_json(deltas(root, logs, ep, "--json"))
    assert report["epic"] == ep
    rows = by_slug(report)
    assert set(rows) == {"alpha", "beta", "gamma"}
    alpha = rows["alpha"]
    assert alpha["legacy"] is False
    assert alpha["points"] == {
        "estimate": 3,
        "actual": 5,
        "difference": 2,
        "ratio": pytest.approx(5 / 3),
    }
    assert alpha["minutes"] == {"estimate": 34, "actual": 51, "difference": 17, "ratio": 1.5}
    assert alpha["tokens"] == {
        "estimate": 2250000,
        "actual": 4500000,
        "difference": 2250000,
        "ratio": 2.0,
    }
    assert rows["beta"]["minutes"] == {
        "estimate": 34,
        "actual": 17,
        "difference": -17,
        "ratio": 0.5,
    }
    assert rows["beta"]["points"]["difference"] == 0
    # gamma has no actuals: reported as missing, never filled with a guess
    for metric in METRICS:
        assert rows["gamma"][metric]["actual"] is None
        assert rows["gamma"][metric]["difference"] is None
        assert rows["gamma"][metric]["ratio"] is None
    # points (3, 5), (3, 3): 0.4, 0; minutes (34, 51), (34, 17): 1/3, 1; tokens 0.5, 1
    assert report["mdape"] == {
        "points": pytest.approx(0.2),
        "minutes": pytest.approx(2 / 3),
        "tokens": pytest.approx(0.75),
    }

    r = deltas(root, logs, ep)
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    alpha_line = next(ln for ln in lines if ln.startswith("| alpha |"))
    assert [c.strip() for c in alpha_line.strip("|").split("|")] == [
        "alpha", "3", "5", "+2", "1.67", "34", "51", "+17", "1.50",
        "2250000", "4500000", "+2250000", "2.00",
    ]  # fmt: skip
    gamma_line = next(ln for ln in lines if ln.startswith("| gamma |"))
    assert gamma_line.count(NR) == 9
    assert "- MdAPE points: 20.0%" in lines
    assert "- MdAPE minutes: 66.7%" in lines
    assert "- MdAPE tokens: 75.0%" in lines


def test_all_includes_legacy_minutes(repo, root, tmp_path):
    logs = tmp_path / "logs"
    first = mk_epic(root, "First epic")
    mk_task(root, first, "alpha")
    measured(root, first, "alpha", "3", "68", "2250000")
    mk_task(root, first, "old")
    old = task_path(root, first, "old")
    legacy_keys = ("points", "expected_minutes", "expected_tokens")
    edit(old, drop=legacy_keys, notes="- Estimate: 5 points.", status="done",
         estimate="45", actual="60")  # fmt: skip
    mk_task(root, first, "bare")
    edit(task_path(root, first, "bare"), drop=legacy_keys, status="done", estimate="6", actual="")
    second = mk_epic(root, "Second epic")
    mk_task(root, second, "beta")
    measured(root, second, "beta", "3", "34", "4500000")
    live = mk_epic(root, "Live epic")
    mk_task(root, live, "gamma")
    measured(root, live, "gamma", "8", "500", "9000000")
    commit_all(repo)
    to_done(repo, root, first)
    to_done(repo, root, second)
    before = (root / "done" / first / "tasks" / "old.md").read_bytes()

    report = as_json(deltas(root, logs, "--all", "--json"))
    assert [e["epic"] for e in report["epics"]] == [first, second]  # the live epic is not done
    rows = by_slug(report["epics"][0])
    legacy = rows["old"]
    assert legacy["legacy"] is True
    assert legacy["minutes"] == {
        "estimate": 45,
        "actual": 60,
        "difference": 15,
        "ratio": pytest.approx(4 / 3),
    }
    # minutes only: the Notes points estimate is ignored, so the row is never bucketed by points
    for metric in ("points", "tokens"):
        assert legacy[metric] == {
            "estimate": None,
            "actual": None,
            "difference": None,
            "ratio": None,
        }
    assert rows["bare"]["legacy"] is False  # an empty `actual` is not a legacy measurement
    assert rows["bare"]["minutes"]["actual"] is None
    assert rows["alpha"]["legacy"] is False
    # minutes (34, 68), (45, 60), (34, 34): 0.5, 0.25, 0 -> 0.25; tokens 0, 0.5 -> 0.25
    assert report["epics"][0]["mdape"]["minutes"] == pytest.approx(0.375)
    assert report["mdape"] == {
        "points": pytest.approx(0.0),
        "minutes": pytest.approx(0.25),
        "tokens": pytest.approx(0.25),
    }
    # never written, and never in the rows new-task buckets by points
    assert (root / "done" / first / "tasks" / "old.md").read_bytes() == before
    assert "old" not in json.dumps(ticket.calibration_rows(root))
    buckets = as_json(deltas(root, logs, "--buckets", "--json"))
    assert sum(b["n"] for b in buckets.values()) == 3  # alpha, beta, gamma; never the legacy row

    r = deltas(root, logs, "--all")
    assert r.returncode == 0, r.stderr
    assert "| old (legacy) |" in r.stdout
    assert f"## {first}" in r.stdout and f"## {second}" in r.stdout
    assert "- MdAPE minutes: 25.0%" in r.stdout.split("## All done epics", 1)[1]


def test_buckets_match_new_task(repo, root, tmp_path):
    logs = tmp_path / "logs"
    ep = mk_epic(root)
    for i, s in enumerate(("alpha", "beta", "gamma", "delta")):
        mk_task(root, ep, s)
        measured(root, ep, s, "3", str(30 + i), str(2000000 + i))
    edit(task_path(root, ep, "delta"), points="5")
    commit_all(repo)

    expected = calibration.bucket_table(ticket.calibration_rows(root))
    assert expected[3]["source"] == "history"  # three done tasks at 3 points
    buckets = as_json(deltas(root, logs, "--buckets", "--json"))
    assert buckets == {str(p): row for p, row in expected.items()}

    r = deltas(root, logs, "--buckets")
    assert r.returncode == 0, r.stderr
    line = next(ln for ln in r.stdout.splitlines() if ln.startswith("| 3 |"))
    cells = [c.strip() for c in line.strip("|").split("|")]
    assert cells == ["3", str(expected[3]["minutes"]), str(expected[3]["tokens"]), "3", "history"]


def _tree_digest(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if ".git" in p.relative_to(path).parts or not p.is_file():
            continue
        h.update(str(p).encode() + p.read_bytes())
    return h.hexdigest()


def test_read_only(repo, root, tmp_path):
    logs = tmp_path / "logs"
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    measured(root, ep, "alpha", "3", "40", "2000000")
    commit_all(repo)
    to_done(repo, root, ep)
    head = git(repo, "rev-parse", "HEAD").stdout
    digest = _tree_digest(repo)

    for args in (
        (ep,),
        (ep, "--json"),
        ("--all",),
        ("--all", "--json"),
        ("--buckets",),
        ("--buckets", "--json"),
        (ep, "--buckets", "--json"),
    ):
        r = deltas(root, logs, *args)
        assert r.returncode == 0, (args, r.stderr)

    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert git(repo, "status", "--porcelain", "--untracked-files=all").stdout == ""
    assert _tree_digest(repo) == digest
    assert not logs.exists()


def test_needs_a_mode(root, tmp_path):
    logs = tmp_path / "logs"
    r = deltas(root, logs)
    assert r.returncode == 1 and "deltas:" in r.stderr
    ep = mk_epic(root)
    r = deltas(root, logs, ep, "--all")
    assert r.returncode == 1 and "deltas:" in r.stderr
