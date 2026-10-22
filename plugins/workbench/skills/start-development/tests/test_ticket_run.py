"""Tests for ticket.py tasks, worktrees and apply-run."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

AC = (
    "- AC1: it lists tasks [evidence: test:tests/test_x.py::test_lists]\n"
    "- AC2: docs say so [evidence: doc-section:README.md#Usage]\n"
    "- AC3: reads well [evidence: judgement]"
)


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    (r / "a.py").write_text("x = 1\n")
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    return r


@pytest.fixture
def root(repo):
    return repo / "docs" / "plans"


def mk_epic(root, title="Big epic"):
    r = cli("new-epic", "--root", root, "--title", title, "--force")
    assert r.returncode == 0, r.stderr
    return ticket.slug(title)


def mk_task(
    root,
    epic,
    title,
    *,
    req="Do the thing.",
    ac=AC,
    steps="1. write test\n2. code",
    files="a.py,b.py",
    extra=(),
):
    rf, af = root / f"{title}.req", root / f"{title}.ac"
    rf.write_text(req)
    af.write_text(ac)
    args = [
        "new-task",
        "--root",
        root,
        "--epic",
        epic,
        "--title",
        title,
        "--repo",
        "proj",
        "--value",
        "why",
        "--files",
        files,
        "--verify",
        "pytest -q tests/test_x.py",
        "--requirement-file",
        rf,
        "--ac-file",
        af,
        *extra,
    ]
    r = cli(*args)
    assert r.returncode == 0, r.stderr
    p = Path(r.stdout.strip().splitlines()[-1])
    rf.unlink()
    af.unlink()
    if steps is not None:
        text = p.read_text()
        start = text.index("## Steps")
        end = text.index("## Notes")
        p.write_text(text[:start] + f"## Steps\n\n{steps}\n\n" + text[end:])
    return p


def epic_branch(repo, ep):
    """The integration branch `move in-progress` would have made, for fixtures that skip it."""
    if git(repo, "branch", "--list", ep).stdout.strip() == "":
        git(repo, "branch", ep)


def commit_all(repo):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "tickets", "--allow-empty")


# ---------------------------------------------------------------- tasks


def test_tasks_field_mapping_and_ac(root):
    ep = mk_epic(root)
    mk_task(
        root,
        ep,
        "Alpha work",
        extra=[
            "--owns",
            "part-a",
            "--uses",
            "part-b",
            "--model",
            "sonnet",
            "--review",
            "light",
            "--depends-on",
            "zeta",
        ],
    )
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    (t,) = json.loads(r.stdout)
    assert t["id"] == t["short"] == "alpha-work"
    assert t["title"] == "Alpha work"
    assert t["repo"] == "proj" and t["value"] == "why"
    assert t["verify"] == "pytest -q tests/test_x.py"
    assert t["requirement"] == "Do the thing."
    assert t["files"] == ["a.py", "b.py"]
    assert t["owns"] == ["part-a"] and t["uses"] == ["part-b"]
    assert t["dependsOn"] == ["zeta"] and t["model"] == "sonnet" and t["review"] == "light"
    assert t["worktree"] == ""
    assert t["acsForAudit"] == []
    assert "Context the implementer needs" in t["notes"]
    assert t["ac"] == [
        {
            "id": "AC1",
            "text": "it lists tasks",
            "evidence": {"kind": "test", "ref": "tests/test_x.py::test_lists"},
        },
        {
            "id": "AC2",
            "text": "docs say so",
            "evidence": {"kind": "doc-section", "ref": "README.md#Usage"},
        },
        {"id": "AC3", "text": "reads well", "evidence": {"kind": "judgement", "ref": ""}},
    ]


def test_tasks_emits_one_entry_per_file_sorted(root):
    ep = mk_epic(root)
    mk_task(root, ep, "Zed")
    mk_task(root, ep, "Abe")
    out = json.loads(cli("tasks", ep, "--root", root).stdout)
    assert [t["id"] for t in out] == ["abe", "zed"]


@pytest.mark.parametrize(
    "kw,section",
    [
        ({"req": ""}, "Requirement"),
        ({"ac": ""}, "Acceptance conditions"),
        ({"steps": None}, "Steps"),
        ({"files": ""}, "Files"),
    ],
)
def test_tasks_refuses_empty_section(root, kw, section):
    ep = mk_epic(root)
    if "files" in kw:
        p = mk_task(root, ep, "Bare")
        text = p.read_text().replace("- `a.py`\n- `b.py`", "")
        p.write_text(text)
    else:
        mk_task(root, ep, "Bare", **kw)
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 1
    assert section in r.stderr and "bare" in r.stderr
    assert r.stdout == ""


def test_tasks_refuses_malformed_ac_line(root):
    ep = mk_epic(root)
    mk_task(root, ep, "Bad ac", ac="- AC1: no evidence here")
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 1 and "AC1" in r.stderr or "acceptance" in r.stderr.lower()


# ---------------------------------------------------------------- worktrees


def test_worktrees_creates_via_create_and_writes_frontmatter(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Alpha work")
    commit_all(repo)
    epic_branch(repo, ep)
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    name = f"{ep}-alpha-work"
    wt = repo / ".claude" / "worktrees" / name
    assert wt.is_dir()
    meta = ticket.load(p.read_text(), p).meta
    assert meta["worktree"] == str(wt) and meta["branch"] == name
    assert meta["status"] == "in-progress"
    assert git(repo, "branch", "--list", name).stdout.strip().endswith(name)
    assert git(repo, "log", "-1", "--format=%s").stdout.strip() == f"chore(ticket): {ep} worktrees"
    assert git(repo, "status", "--porcelain", "--", "docs").stdout.strip() == ""


def test_worktrees_keeps_live_legacy_double_hyphen_record(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Alpha work")
    commit_all(repo)
    legacy = f"{ep}--alpha-work"
    wt = repo / ".claude" / "worktrees" / legacy
    git(repo, "worktree", "add", "-b", legacy, str(wt), "main")
    ticket._write_task(p, ticket._read_doc(p), [], worktree=str(wt), branch=legacy)
    commit_all(repo)
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    meta = ticket.load(p.read_text(), p).meta
    assert meta["worktree"] == str(wt) and meta["branch"] == legacy
    assert not (repo / ".claude" / "worktrees" / f"{ep}-alpha-work").exists()


def test_worktrees_after_move_in_progress_is_status_noop(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    p = root / "in-progress" / ep / "tasks" / "alpha-work.md"
    assert ticket.load(p.read_text(), p).meta["status"] == "in-progress"

    def listing():
        return [
            {k: v for k, v in t.items() if k not in ("worktree", "branch")}
            for t in json.loads(cli("tasks", ep, "--root", root).stdout)
        ]

    tasks_before = listing()
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    assert (repo / ".claude" / "worktrees" / f"{ep}-alpha-work").is_dir()
    assert ticket.load(p.read_text(), p).meta["status"] == "in-progress"
    assert listing() == tasks_before
    assert cli("lint", "--root", root).returncode == 0
    mk_task(root, ep, "Beta work")
    assert cli("lint", "--root", root).returncode == 0


def test_worktrees_reuses_existing_tree(repo, root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Alpha work")
    commit_all(repo)
    epic_branch(repo, ep)
    assert cli("worktrees", ep, "--root", root).returncode == 0
    head = git(repo, "rev-parse", "HEAD").stdout
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    assert "reused" in r.stdout
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert ticket.load(p.read_text(), p).meta["status"] == "in-progress"


def test_worktrees_uses_create_not_a_copy(repo, root, monkeypatch):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    calls = []

    def fake(name, base="main", repo=None, start=None):
        calls.append((name, base, repo))
        return {"name": name, "path": str(start / "x"), "branch": name, "base": base, "notes": []}

    monkeypatch.setattr(ticket, "_create", lambda: fake)
    ticket.main(["worktrees", ep, "--root", str(root), "--base", "dev"])
    assert calls == [(f"{ep}-alpha-work", "dev", None)]


def test_worktrees_passes_task_repo_in_workbench(tmp_path):
    wb = tmp_path / "wb"
    (wb / "code" / "proj").mkdir(parents=True)
    git(wb, "init", "-b", "main")
    git(wb, "config", "user.email", "t@t")
    git(wb, "config", "user.name", "t")
    (wb / ".gitmodules").write_text("")
    git(wb, "add", "-A")
    git(wb, "commit", "-m", "i", "--allow-empty")
    assert ticket._task_repo(wb / "docs" / "plans", "proj") == "proj"
    assert ticket._task_repo(wb / "docs" / "plans", "other") is None


def test_worktrees_refused_in_linked_worktree(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    git(repo, "worktree", "add", "-b", "side", str(repo.parent / "side"))
    side_root = repo.parent / "side" / "docs" / "plans"
    r = cli("worktrees", ep, "--root", side_root)
    assert r.returncode == 1 and "main checkout" in r.stderr
    r = cli("apply-run", ep, repo / "none.json", "--root", side_root)
    assert r.returncode == 1 and "main checkout" in r.stderr


# ---------------------------------------------------------------- apply-run


def run_return(**over):
    base = {
        "run": "big-epic",
        "tasks": [
            {
                "id": "t-done",
                "branch": "b-done",
                "clean": True,
                "verified": True,
                "verification": {"head": "abc123", "passed": True},
                "stopped": None,
                "processGaps": [],
                "acsForAudit": ["AC3"],
            },
            {
                "id": "t-proc",
                "branch": "b-proc",
                "clean": False,
                "processOnly": True,
                "verified": True,
                "verification": {"head": "def456"},
                "stopped": None,
                "processGaps": [
                    {
                        "taskId": "t-proc",
                        "what": "no red evidence: tdd",
                        "where": "x.py",
                        "gate": "no-red-evidence",
                    }
                ],
            },
            {
                "id": "t-unver",
                "branch": "b-unver",
                "clean": True,
                "verified": False,
                "verification": {"head": "999"},
                "stopped": None,
            },
            {
                "id": "t-esc",
                "branch": "b-esc",
                "clean": False,
                "verified": True,
                "verification": {"head": "111"},
                "stopped": "round-cap",
            },
            {
                "id": "t-blk",
                "branch": None,
                "clean": False,
                "verified": False,
                "verification": None,
                "stopped": "blocked",
            },
        ],
        "escalated": [{"id": "t-esc", "reason": "round-cap", "findings": []}],
        "blocked": [{"id": "t-blk", "reason": "needs key", "whoCanClear": "user"}],
        "provides": [{"taskId": "t-done", "name": "helper-x", "where": "a.py:x"}],
        "discovered": [
            {
                "taskId": "t-done",
                "what": "Fix the flaky parser",
                "where": "lib/parser.py",
                "why": "outside my files",
            }
        ],
    }
    base.update(over)
    return base


def setup_run(repo, root):
    ep = mk_epic(root)
    for t in ("t-done", "t-proc", "t-unver", "t-esc", "t-blk"):
        mk_task(root, ep, t)
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    return ep


def meta_of(root, ep, slug):
    p = root / "in-progress" / ep / "tasks" / f"{slug}.md"
    return ticket.load(p.read_text(), p).meta


def test_apply_run_status_mapping_and_fields(repo, root):
    ep = setup_run(repo, root)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    r = cli("apply-run", ep, rj, "--root", root)
    assert r.returncode == 0, r.stderr
    assert "t-done" in r.stdout
    d = meta_of(root, ep, "t-done")
    assert d["status"] == "done" and d["branch"] == "b-done"
    assert d["verified_head"] == "abc123" and d["run"] == "big-epic"
    assert d["acs_for_audit"] == ["AC3"] and d["process_gaps"] == []
    assert d["provides"] == ["helper-x"]
    p = meta_of(root, ep, "t-proc")
    assert p["status"] == "done"
    assert p["process_gaps"] == ["no red evidence: tdd"]
    assert meta_of(root, ep, "t-unver")["status"] == "in-progress"
    assert meta_of(root, ep, "t-esc")["status"] == "escalated"
    assert meta_of(root, ep, "t-blk")["status"] == "blocked"
    assert (
        git(repo, "log", "-1", "--format=%s").stdout.strip()
        == f"chore(ticket): {ep} apply-run big-epic"
    )


def test_apply_run_audit_ids_round_trip_into_tasks(repo, root):
    ep = setup_run(repo, root)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    # the discovered task is complete, so a full export works
    assert cli("tasks", ep, "--root", root).returncode == 0
    out = {
        t["id"]: t
        for t in json.loads(cli("tasks", ep, "--root", root, "--only", "t-done,t-proc").stdout)
    }
    assert out["t-done"]["acsForAudit"] == ["AC3"]
    assert out["t-proc"]["acsForAudit"] == []


def test_apply_run_creates_todo_task_from_discovered(repo, root):
    ep = setup_run(repo, root)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    r = cli("apply-run", ep, rj, "--root", root)
    assert r.returncode == 0, r.stderr
    new = meta_of(root, ep, "fix-the-flaky-parser")
    assert new["status"] == "todo" and new["title"] == "Fix the flaky parser"
    p = root / "in-progress" / ep / "tasks" / "fix-the-flaky-parser.md"
    body = p.read_text()
    assert "Fix the flaky parser" in body and "lib/parser.py" in body
    assert "outside my files" in body
    notes = body[body.index("## Notes") :]
    assert "t-done" in notes
    assert "fix-the-flaky-parser" in r.stdout
    # applying the same return twice does not duplicate the task
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    assert len(list((root / "in-progress" / ep / "tasks").glob("fix-the-flaky-parser*"))) == 1


def test_apply_run_unknown_task_refused_without_writing(repo, root):
    ep = setup_run(repo, root)
    rj = repo / "return.json"
    ret = run_return()
    ret["tasks"].append(
        {"id": "ghost", "clean": True, "verified": True, "verification": {"head": "z"}}
    )
    rj.write_text(json.dumps(ret))
    r = cli("apply-run", ep, rj, "--root", root)
    assert r.returncode == 1 and "ghost" in r.stderr
    assert meta_of(root, ep, "t-done")["status"] == "in-progress"


def test_worktree_create_skill_uses_epic_task_naming():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "worktree-create" / "SKILL.md").read_text()
    assert "t4-decode-cardstate" not in text
    assert "<epic>-<task>" in text
    assert "<epic>--<task>" not in text


def test_tasks_out_writes_file_instead_of_stdout(root, tmp_path):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    out = tmp_path / "tasks.json"
    r = cli("tasks", ep, "--out", str(out), "--root", root)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == ""
    (t,) = json.loads(out.read_text())
    assert t["id"] == "alpha-work"


def test_apply_run_refuses_epic_not_in_progress(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "t-done")
    commit_all(repo)
    rj = repo / "return.json"
    rj.write_text(
        json.dumps(run_return(tasks=[], blocked=[], escalated=[], provides=[], discovered=[]))
    )
    r = cli("apply-run", ep, rj, "--root", root)
    assert r.returncode == 1 and "todo" in r.stderr and "in-progress" in r.stderr


def test_apply_run_discovered_overlapping_other_epic_is_blocked(repo, root):
    other = mk_epic(root, "Other epic")
    mk_task(root, other, "theirs", files="lib/parser.py")
    commit_all(repo)
    assert cli("move", other, "in-progress", "--root", root).returncode == 0
    ep = setup_run(repo, root)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    r = cli("apply-run", ep, rj, "--root", root)
    assert r.returncode == 0, r.stderr
    new = meta_of(root, ep, "fix-the-flaky-parser")
    assert new["status"] == "blocked"
    body = (root / "in-progress" / ep / "tasks" / "fix-the-flaky-parser.md").read_text()
    notes = body[body.index("## Notes") :]
    assert "lib/parser.py" in notes and "other-epic" in notes
    assert "blocked" in r.stdout


def test_apply_run_discovered_overlapping_blocker_epic_stays_todo(repo, root):
    base = mk_epic(root, "Base epic")
    mk_task(root, base, "theirs", files="lib/parser.py")
    commit_all(repo)
    assert cli("move", base, "in-progress", "--root", root).returncode == 0
    ep = mk_epic(root)
    for t in ("t-done", "t-proc", "t-unver", "t-esc", "t-blk"):
        mk_task(root, ep, t)
    p = root / "todo" / ep / "README.md"
    doc = ticket.load(p.read_text(), p)
    doc.meta["blockers"] = ["Base epic"]
    p.write_text(ticket.dump(doc))
    git(repo, "mv", str(root / "todo" / ep), str(root / "in-progress" / ep))
    commit_all(repo)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    assert meta_of(root, ep, "fix-the-flaky-parser")["status"] == "todo"


# ---------------------------------------------------------------- time (report only)


def set_estimate(root, ep, slug, minutes):
    p = root / ep / "tasks" / f"{slug}.md"
    text = re.sub(r"^estimate: .*$", f"estimate: {minutes}", p.read_text(), count=1, flags=re.M)
    p.write_text(re.sub(r"^estimate_by: .*$", "estimate_by: override", text, count=1, flags=re.M))


def readme_time(root, phase, ep):
    text = (root / phase / ep / "README.md").read_text()
    return text.split("## Time", 1)[1].split("\n## ", 1)[0].strip() if "## Time" in text else None


def test_epic_template_has_a_time_section_and_task_template_the_fields():
    t = (ROOT / "skills/start-development/templates/epic.md").read_text()
    assert "\n## Time\n" in t
    task = (ROOT / "skills/start-development/templates/task.md").read_text()
    assert "estimate:" in task and "actual:" in task


def test_tasks_emits_estimate_and_regenerates_time_section(root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha")
    mk_task(root, ep, "Beta")
    set_estimate(root / "todo", ep, "alpha", 45)
    set_estimate(root / "todo", ep, "beta", 30)
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    out = {t["id"]: t for t in json.loads(r.stdout)}
    assert out["alpha"]["estimate"] == 45 and out["beta"]["estimate"] == 30
    assert out["alpha"]["actual"] == 0
    time = readme_time(root, "todo", ep)
    assert "Estimate: 75 agent-min" in time and "Actual: 0 min" in time
    assert "Remaining estimate: 75 min" in time


def test_tasks_without_estimates_still_work(root):
    ep = mk_epic(root)
    task = mk_task(root, ep, "Alpha")
    task.write_text(re.sub(r"^estimate: .*$", 'estimate: ""', task.read_text(), flags=re.M))
    r = cli("tasks", ep, "--root", root)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)[0]["estimate"] == 0
    assert "Estimate: 0 agent-min" in readme_time(root, "todo", ep)


def test_tasks_only_does_not_shrink_the_time_totals(root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha")
    mk_task(root, ep, "Beta")
    set_estimate(root / "todo", ep, "alpha", 45)
    set_estimate(root / "todo", ep, "beta", 30)
    assert cli("tasks", ep, "--root", root, "--only", "alpha").returncode == 0
    assert "Estimate: 75 agent-min" in readme_time(root, "todo", ep)


def test_apply_run_writes_actual_from_duration_and_updates_time(repo, root):
    ep = setup_run(repo, root)
    for slug, m in (("t-done", 40), ("t-proc", 20), ("t-unver", 10), ("t-esc", 10), ("t-blk", 10)):
        set_estimate(root / "in-progress", ep, slug, m)
    commit_all(repo)
    ret = run_return()
    for t, ms in zip(ret["tasks"], (125_000, 60_000, 0, 30_000, 0), strict=True):
        t["durationMs"] = ms
    rj = repo / "return.json"
    rj.write_text(json.dumps(ret))
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    assert meta_of(root, ep, "t-done")["actual"] == "2"
    assert meta_of(root, ep, "t-proc")["actual"] == "1"
    assert meta_of(root, ep, "t-esc")["actual"] == "1"
    time = readme_time(root, "in-progress", ep)
    assert "Estimate: 90 agent-min" in time and "Actual: 4 min" in time
    assert "Remaining estimate: 30 min" in time  # t-done and t-proc are done
    # re-applying the same run replaces the actual instead of adding to it
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    assert meta_of(root, ep, "t-done")["actual"] == "2"


def test_new_task_estimate_flag_is_written_and_validated(root):
    ep = mk_epic(root)
    p = mk_task(root, ep, "Alpha", extra=["--estimate", "45"])
    m = ticket.load(p.read_text(), p).meta
    assert m["estimate"] == "45" and m["estimate_by"] == "override"
    r = cli(
        "new-task",
        "--root",
        root,
        "--epic",
        ep,
        "--title",
        "Bad",
        "--repo",
        "proj",
        "--value",
        "v",
        "--files",
        "a.py",
        "--verify",
        "x",
        "--estimate",
        "soon",
    )
    assert r.returncode == 1 and "estimate" in r.stderr


def write_run_dir(d, agents, bad=()):
    """agents: {agentId: (label, [iso timestamps])}; journal has one `started` line each."""
    d.mkdir()
    lines = [
        json.dumps({"type": "started", "agentId": a, "label": lab})
        for a, (lab, _) in agents.items()
    ]
    (d / "journal.jsonl").write_text("\n".join(["not json", *lines]) + "\n")
    for a, (_, stamps) in agents.items():
        rows = "\n".join(json.dumps({"timestamp": s}) for s in stamps)
        (d / f"agent-{a}.jsonl").write_text(rows + "\n")
    for a in bad:
        (d / f"agent-{a}.jsonl").unlink()


def test_apply_run_run_dir_derives_actual_from_transcript_timestamps(repo, root):
    ep = setup_run(repo, root)
    commit_all(repo)
    run_dir = repo / "run"
    write_run_dir(
        run_dir,
        {
            "a1": ("pe:impl:t-done", ["2026-01-01T10:00:00Z", "2026-01-01T10:01:00Z"]),
            "a2": ("pe:review:t-done", ["2026-01-01T10:02:00Z", "2026-01-01T10:03:00Z"]),
            "a3": ("pe:impl:t-proc#2", ["2026-01-01T10:00:00Z", "2026-01-01T10:02:00Z"]),
            "a4": ("pe:impl:t-esc", ["2026-01-01T10:00:00Z", "2026-01-01T10:09:00Z"]),
        },
        bad=("a4",),
    )
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    assert cli("apply-run", ep, rj, "--root", root, "--run-dir", run_dir).returncode == 0
    # agent-minutes: the summed per-agent spans (impl 1 + review 1), not the 3 min wall span
    assert meta_of(root, ep, "t-done")["actual"] == "2"
    assert meta_of(root, ep, "t-proc")["actual"] == "2"
    assert not meta_of(root, ep, "t-esc").get("actual")


def test_apply_run_without_run_dir_adds_no_actual(repo, root):
    ep = setup_run(repo, root)
    commit_all(repo)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    assert cli("apply-run", ep, rj, "--root", root).returncode == 0
    assert not meta_of(root, ep, "t-done").get("actual")


def test_apply_run_missing_run_dir_does_not_fail(repo, root):
    ep = setup_run(repo, root)
    commit_all(repo)
    rj = repo / "return.json"
    rj.write_text(json.dumps(run_return()))
    assert cli("apply-run", ep, rj, "--root", root, "--run-dir", repo / "nope").returncode == 0


def test_worktrees_fork_from_epic_branch(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    epic_branch(repo, ep)
    git(repo, "checkout", "-q", ep)
    (repo / "epic.txt").write_text("e")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "epic only")
    git(repo, "checkout", "-q", "main")
    assert cli("worktrees", ep, "--root", root).returncode == 0
    wt = repo / ".claude" / "worktrees" / f"{ep}-alpha-work"
    assert (wt / "epic.txt").is_file()


def test_worktrees_refuses_missing_integration_branch(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    r = cli("worktrees", ep, "--root", root)
    assert r.returncode == 1
    assert f"integration branch {ep} missing in" in r.stderr
    assert f"run ticket.py worktrees {ep} --integration" in r.stderr
    assert not (repo / ".claude" / "worktrees" / f"{ep}-alpha-work").exists()


def test_worktrees_integration_creates_tree_for_in_progress_epic(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    assert cli("move", ep, "in-progress", "--root", root).returncode == 0
    git(repo, "worktree", "remove", "--force", str(repo / ".claude" / "worktrees" / ep))
    git(repo, "branch", "-D", ep)
    r = cli("worktrees", ep, "--root", root, "--integration")
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("integration ") and "(created)" in r.stdout
    assert (repo / ".claude" / "worktrees" / ep).is_dir()
    assert not (repo / ".claude" / "worktrees" / f"{ep}-alpha-work").exists()
    again = cli("worktrees", ep, "--root", root, "--integration")
    assert "(reused)" in again.stdout


def test_worktrees_integration_refuses_epic_not_in_progress(repo, root):
    ep = mk_epic(root)
    mk_task(root, ep, "Alpha work")
    commit_all(repo)
    r = cli("worktrees", ep, "--root", root, "--integration")
    assert r.returncode == 1 and "in-progress" in r.stderr
