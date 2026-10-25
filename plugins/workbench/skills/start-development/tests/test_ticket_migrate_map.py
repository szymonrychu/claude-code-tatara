"""ticket.py migrate: the old-to-new task mapping, the names map and the dry run."""

import json
import re
import sys
from pathlib import Path

from ticket_repo_helpers import cli, commit_all, git, mk_epic, mk_task, ticket

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import agent_usage  # noqa: E402
import calibration  # noqa: E402
from ticket_cmds import migrate  # noqa: E402

KEYS = [
    "title",
    "status",
    "repo",
    "value",
    "files",
    "verify",
    "depends_on",
    "model",
    "review",
    "verified_head",
    "points",
    "expected_minutes",
    "expected_tokens",
    "points_actual",
    "actual_minutes",
    "actual_tokens",
    "actual_roles",
    "actual_role_tokens",
]
KEPT = KEYS[:10]
DROPPED = [
    "estimate",
    "estimate_by",
    "actual",
    "worktree",
    "branch",
    "run",
    "provides",
    "owns",
    "uses",
    "process_gaps",
    "acs_for_audit",
    "fork_point",
]
ACTUALS = ("actual_minutes", "actual_tokens", "actual_roles", "actual_role_tokens")
EXPECTED = ("points", "expected_minutes", "expected_tokens")
START = "2026-10-24T10:00:00.000Z"
TASK_LINE = re.compile(r"^([a-z0-9-]+/[a-z0-9-]+): ")


def old_meta(epic="ep-one", slug="alpha", **kw):
    """An old-scheme task frontmatter in the shape of docs/plans/done/*/tasks (medium-only-hold)."""
    meta = {
        "title": f"{slug} title",
        "status": "done",
        "repo": "workbench",
        "value": "A task with open medium findings never lands",
        "files": ["plugins/x.js", "plugins/tests/x.test.mjs"],
        "verify": "cd plugins/workbench && node --test x.test.mjs",
        "depends_on": [],
        "owns": [],
        "uses": [],
        "model": "sonnet",
        "estimate": "5",
        "actual": "4",
        "review": "",
        "worktree": f"/w/.claude/worktrees/{epic}--{slug}",
        "branch": f"{epic}--{slug}",
        "verified_head": "6fe6d7ba001735aa25a4bf1aa9d8f55d1b9d9931",
        "run": epic,
        "provides": [],
        "acs_for_audit": ["AC1", "AC2"],
        "process_gaps": [],
        "fork_point": "abc1234",
        "estimate_by": "formula",
        "actual_roles": "impl 1, verify 1, review 1, fix 1, false-finding 1",
    }
    meta.update(kw)
    return meta


def bootstrap_meta(**kw):
    """A new-scheme task without points (housekeeping-rules-estimates, calibration-lib)."""
    meta = {
        "title": "Calibration lib",
        "status": "done",
        "repo": "workbench",
        "value": "Expected minutes and tokens per storypoint come from measured history",
        "files": ["plugins/workbench/scripts/lib/calibration.py"],
        "verify": "mise run lint",
        "depends_on": [],
        "model": "opus",
        "review": "",
        "verified_head": "297bdf4",
        "points_actual": "3",
        "actual_minutes": "11",
        "actual_tokens": "388955",
        "actual_roles": "impl 8, review 4",
        "actual_role_tokens": "impl 282670, review 106285",
    }
    meta.update(kw)
    return {k: meta[k] for k in KEYS if k in meta}  # template order, as new-task writes


def body(notes=""):
    return f"\n# A task\n\n## Requirement\n\nDo it.\n\n## Notes\n\n{notes}\n"


def rec(agent_id, epic, task, role, start, end, total):
    return {
        "agentId": agent_id,
        "agentType": f"workbench:{'implementer' if role == 'impl' else 'reviewer'}",
        "model": "claude-sonnet-5-5",
        "epic": epic,
        "task": task,
        "role": role,
        "transcript": "",
        "start": start,
        "end": end,
        "tokens": {
            "input": total,
            "cache_creation": 0,
            "cache_read": 0,
            "output": 0,
            "total": total,
        },
    }


def full_records(epic="ep-one", task="alpha"):
    # impl 10:00-10:20 (1000 tokens), review 10:25-10:31 (400): 31 minutes, 1400 tokens
    return [
        rec("i1", epic, task, "impl", START, "2026-10-24T10:20:00.000Z", 1000),
        rec(
            "r1", epic, task, "review", "2026-10-24T10:25:00.000Z", "2026-10-24T10:31:00.000Z", 400
        ),
    ]


def mapped(meta, notes="", records=()):
    return migrate.migrate_meta(ticket, meta, body(notes), list(records))


def write_task(root, phase, epic, slug, meta, notes=""):
    d = root / phase / epic
    (d / "tasks").mkdir(parents=True, exist_ok=True)
    readme = d / "README.md"
    if not readme.exists():
        readme.write_text(f'---\ntitle: "{epic}"\n---\n\n# {epic}\n')
    path = d / "tasks" / f"{slug}.md"
    path.write_text(ticket.dump(ticket.Doc(meta, body(notes))))
    return path


def transcript(folder, agent_id, prompt, agent_type="workbench:implementer", total=100):
    lines = [
        {"type": "user", "timestamp": START, "message": {"content": prompt}},
        {
            "type": "assistant",
            "timestamp": "2026-10-24T10:09:00.000Z",
            "message": {"id": "m1", "model": "claude-sonnet-5-5", "usage": {"input_tokens": total}},
        },
    ]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"agent-{agent_id}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    (folder / f"agent-{agent_id}.meta.json").write_text(json.dumps({"agentType": agent_type}))


def dry_run(root, logs, transcripts, *args):
    return cli(
        "migrate", *args, "--dry-run", "--logs", logs, "--transcripts", transcripts, "--root", root
    )


def test_keys_order_and_drops():
    old = old_meta(extra_key="anything", points_actual="")
    new = mapped(old)
    assert list(new) == KEYS
    assert list(new) == list(ticket._template("task.md").meta)
    for key in KEPT:
        assert new[key] == old[key], key
    assert not set(new) & set(DROPPED + ["extra_key"])
    # values go through ticket.dump: the body is untouched and the text round-trips
    text = ticket.dump(ticket.Doc(new, body("- a note")))
    assert ticket.load(text, "x") == ticket.Doc(new, body("- a note"))
    assert ticket.dump(ticket.load(text, "x")) == text
    # a key the old file lacks takes the template default
    lean = {k: v for k, v in old.items() if k not in ("depends_on", "review")}
    assert mapped(lean)["depends_on"] == [] and mapped(lean)["review"] == ""


def test_points_from_legacy_estimate():
    for minutes, points in (("5", 1), ("17", 1), ("45", 3), ("46", 5), ("90", 8)):
        new = mapped(old_meta(estimate=minutes))
        assert points == calibration.points_for_minutes(int(minutes))
        assert new["points"] == str(points)
        assert new["expected_minutes"] == minutes
        assert new["expected_tokens"] == str(calibration.SEED[points][1])
    for estimate in ("", "about an hour", "4.5", "-3"):
        new = mapped(old_meta(estimate=estimate))
        assert [new[k] for k in EXPECTED] == ["", "", ""], estimate
    assert [mapped(old_meta(estimate=None))[k] for k in EXPECTED] == ["", "", ""]


def test_points_from_notes_line():
    new = mapped(bootstrap_meta(), notes="- Estimate: 5 points: a lib and its tests.")
    assert new["points"] == "5"
    assert (new["expected_minutes"], new["expected_tokens"]) == tuple(map(str, calibration.SEED[5]))
    assert new["points_actual"] == "3"  # stays as recorded against points 5
    old = bootstrap_meta()
    assert [new[k] for k in ACTUALS] == [old[k] for k in ACTUALS]
    # an old task with an empty legacy estimate falls back to the Notes line
    legacy = mapped(old_meta(estimate=""), notes="- Estimate: 2 points.")
    assert legacy["points"] == "2"
    assert legacy["expected_minutes"] == str(calibration.SEED[2][0])
    # no estimate and no Notes line: nothing invented
    assert [mapped(bootstrap_meta())[k] for k in EXPECTED] == ["", "", ""]


def test_existing_points_kept():
    meta = bootstrap_meta(points="8", expected_minutes="100", expected_tokens="")
    new = mapped(meta, notes="- Estimate: 3 points.")
    assert new["points"] == "8"
    assert new["expected_minutes"] == "100"
    assert new["expected_tokens"] == str(calibration.SEED[8][1])
    new = mapped(bootstrap_meta(points="2", expected_minutes="", expected_tokens="7"))
    assert (new["expected_minutes"], new["expected_tokens"]) == (str(calibration.SEED[2][0]), "7")
    # points win over a legacy estimate too
    new = mapped(old_meta(points="13", estimate="5"))
    assert [new[k] for k in EXPECTED] == ["13", *map(str, calibration.SEED[13])]


def test_actuals_from_legacy_and_records(repo, root, tmp_path):
    impl_only = full_records()[:1]
    # legacy number only
    new = mapped(old_meta(actual="4"))
    assert [new[k] for k in ACTUALS] == ["4", "", "", ""]
    # records covering impl and review: minutes, tokens and roles from them
    new = mapped(old_meta(actual=""), records=full_records())
    assert [new[k] for k in ACTUALS] == ["31", "1400", "impl 20, review 6", "impl 1000, review 400"]
    # a legacy number wins for minutes; tokens and roles still come from the records
    new = mapped(old_meta(actual="7"), records=full_records())
    assert [new[k] for k in ACTUALS] == ["7", "1400", "impl 20, review 6", "impl 1000, review 400"]
    # a partial set (impl only) gives nothing; the legacy number is still written
    assert [mapped(old_meta(actual="7"), records=impl_only)[k] for k in ACTUALS] == [
        "7",
        "",
        "",
        "",
    ]
    assert [mapped(old_meta(actual=""), records=impl_only)[k] for k in ACTUALS] == [""] * 4
    # neither source
    assert [mapped(old_meta(actual=""))[k] for k in ACTUALS] == [""] * 4
    # no legacy key: the new-scheme actuals stay as recorded, records or not
    new = mapped(bootstrap_meta(), records=full_records())
    assert [new[k] for k in ACTUALS] == [bootstrap_meta()[k] for k in ACTUALS]

    # the dry run names the partial match
    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    transcripts.mkdir()
    write_task(root, "done", "ep-one", "alpha", old_meta(actual="7"))
    write_task(root, "done", "ep-one", "beta", old_meta(slug="beta", actual=""))
    commit_all(repo)
    agent_usage.write_record(logs, impl_only[0])
    agent_usage.write_record(logs, rec("x1", "ep-one", "beta", "review", START, START, 5))
    r = dry_run(root, logs, transcripts, "ep-one")
    assert r.returncode == 0, r.stderr
    assert "partial: ep-one/alpha (impl)" in r.stdout.splitlines()
    assert "partial: ep-one/beta (review)" in r.stdout.splitlines()


def test_legacy_roles_dropped():
    for roles in (
        "impl 4, verify 3, review 2, fix 2",
        "impl 8, review 8",
        "impl 1, verify 1, review 1, fix 1, false-finding 1",
        "",
    ):
        new = mapped(old_meta(actual_roles=roles))
        assert new["actual_roles"] == "" and new["actual_role_tokens"] == "", roles
        assert not ticket._number_problems(new, "alpha")
        new = mapped(old_meta(actual_roles=roles), records=full_records())
        assert new["actual_roles"] == "impl 20, review 6", roles


def test_names_map_matches_legacy_transcripts(repo, root, tmp_path):
    write_task(root, "done", "ep-one", "alpha", old_meta())
    write_task(
        root,
        "done",
        "ep-one",
        "beta",
        old_meta(slug="beta", worktree="/w/.claude/worktrees/ep-one-beta-tree", branch=""),
    )
    write_task(root, "done", "ep-one", "gamma", old_meta(slug="gamma"))
    write_task(root, "todo", "ep-two", "delta", old_meta("ep-two", "delta", status="todo"))
    names = migrate.names_map(ticket, root)
    assert names["ep-one/tasks/alpha.md"] == ("ep-one", "alpha")
    assert names["ep-two/tasks/delta.md"] == ("ep-two", "delta")
    for name, owner in ticket.ticket_names(root).items():
        assert names[name] == owner
    assert names["ep-one-alpha"] == ("ep-one", "alpha")
    assert names["ep-one"] == ("ep-one", None)
    assert names["ep-one--alpha"] == ("ep-one", "alpha")  # legacy branch and tree basename
    assert names["ep-one-beta-tree"] == ("ep-one", "beta")
    assert names["ep-two--delta"] == ("ep-two", "delta")

    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    session = transcripts / "s1" / "subagents" / "workflows" / "wf_1"
    # lean-development-flow style: the prompt names the task file under its old phase
    transcript(
        session,
        "a1",
        "Task file (read it in full first): /x/docs/plans/in-progress/ep-one/tasks/alpha.md",
    )
    transcript(session, "a2", "Work in /w/.claude/worktrees/ep-one-beta-tree only.", total=7)
    transcript(session, "a3", "Review branch ep-one--gamma.", "workbench:reviewer", total=9)
    transcript(session, "a4", "Plan ep-one/tasks/alpha.md", "workbench:planner")
    got = agent_usage.records_by_task("ep-one", logs, transcripts, names=names)
    assert sorted(got) == ["alpha", "beta", "gamma"]
    assert [r["agentId"] for r in got["alpha"]] == ["a1"]
    assert got["beta"][0]["tokens"]["total"] == 7
    assert got["gamma"][0]["role"] == "review"


def test_names_map_rejects_head_and_free_text(repo, root, tmp_path):
    write_task(root, "done", "ep-one", "alpha", old_meta(branch="HEAD", worktree=""))
    write_task(
        root,
        "done",
        "ep-one",
        "beta",
        old_meta(slug="beta", branch="current worktree branch (commit 2e13385)", worktree=""),
    )
    write_task(
        root,
        "done",
        "ep-one",
        "gamma",
        old_meta(slug="gamma", branch="ep-one--gamma (merged by hand)", worktree="/w/unrelated"),
    )
    names = migrate.names_map(ticket, root)
    assert "HEAD" not in names and "" not in names
    assert "unrelated" not in names
    assert not [n for n in names if " " in n]
    assert set(names) == set(ticket.ticket_names(root)) | {
        f"ep-one/tasks/{s}.md" for s in ("alpha", "beta", "gamma")
    }

    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    transcript(transcripts / "s1", "h1", "Commit on HEAD and report.")
    assert agent_usage.records_by_task("ep-one", logs, transcripts, names=names) == {}


def test_malformed_mapping_refused(repo, root, tmp_path):
    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    transcripts.mkdir()
    write_task(
        root, "done", "ep-one", "alpha", old_meta(estimate=""), notes="- Estimate: 4 points."
    )
    write_task(root, "done", "ep-one", "beta", old_meta(slug="beta"))
    write_task(root, "done", "ep-two", "gamma", bootstrap_meta(points_actual="x"))
    commit_all(repo)
    head = git(repo, "rev-parse", "HEAD").stdout

    r = dry_run(root, logs, transcripts, "--all")
    assert r.returncode == 1
    assert r.stdout == ""
    err = r.stderr.splitlines()
    assert any("ep-one/alpha" in line and "points" in line and "'4'" in line for line in err)
    assert any("ep-two/gamma" in line and "points_actual" in line for line in err)
    assert git(repo, "status", "--porcelain").stdout == ""
    assert git(repo, "rev-parse", "HEAD").stdout == head


def test_dry_run_changes_nothing(repo, root, tmp_path):
    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    transcripts.mkdir()
    write_task(root, "todo", "ep-todo", "plan", old_meta("ep-todo", "plan", status="todo"))
    write_task(
        root,
        "in-progress",
        "ep-live",
        "build",
        old_meta("ep-live", "build", status="in-progress", estimate="", actual=""),
    )
    write_task(root, "done", "ep-old", "alpha", old_meta("ep-old", "alpha", estimate="45"))
    write_task(
        root,
        "done",
        "ep-old",
        "beta",
        old_meta("ep-old", "beta", actual="", verified_head="$(see below)"),
    )
    write_task(root, "done", "ep-new", "lib", bootstrap_meta(), notes="- Estimate: 5 points.")
    commit_all(repo)
    head = git(repo, "rev-parse", "HEAD").stdout
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    agent_usage.write_record(logs, rec("i1", "ep-old", "beta", "impl", START, START, 5))

    r = dry_run(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    out = r.stdout.splitlines()
    alpha = next(line for line in out if line.startswith("ep-old/alpha:"))
    assert 'points: absent -> "3"' in alpha
    assert 'expected_minutes: absent -> "45"' in alpha
    assert 'expected_tokens: absent -> "2250000"' in alpha
    assert 'actual_minutes: absent -> "4"' in alpha
    assert 'actual_roles: "impl 1, verify 1, review 1, fix 1, false-finding 1" -> ""' in alpha
    assert "drop: " + ", ".join(sorted(DROPPED)) in alpha
    assert "title:" not in alpha  # unchanged keys are not listed
    for prefix in ("ep-todo/plan:", "ep-live/build:", "ep-old/beta:", "ep-new/lib:"):
        assert any(line.startswith(prefix) for line in out), prefix
    new_lib = next(line for line in out if line.startswith("ep-new/lib:"))
    assert 'points: absent -> "5"' in new_lib and "drop:" not in new_lib
    assert "partial: ep-old/beta (impl)" in out
    # per done epic: the RETRO.md it would write, rows from the new values
    retros = [line for line in out if line.startswith("retro: ")]
    assert retros == [
        f"retro: {root / 'done' / 'ep-new' / 'RETRO.md'} (create)",
        f"retro: {root / 'done' / 'ep-old' / 'RETRO.md'} (create)",
    ]
    assert "| alpha title | 3 | not recorded | 45 | 4 | 2250000 | not recorded |" in out
    # retro's own fallback fills empty actuals from the records, as `ticket.py retro` does
    assert "| beta title | 1 | not recorded | 5 | 0 | 750000 | 5 |" in out
    # nothing tracked changed, nothing new under the root, HEAD did not move
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert git(repo, "status", "--porcelain").stdout == ""
    assert git(repo, "rev-parse", "HEAD").stdout == head

    assert dry_run(root, logs, transcripts, "ep-old", "--all").returncode == 1
    assert dry_run(root, logs, transcripts).returncode == 1
    one = dry_run(root, logs, transcripts, "ep-old")
    assert one.returncode == 0, one.stderr
    changed = {m.group(1) for m in map(TASK_LINE.match, one.stdout.splitlines()) if m}
    assert changed == {"ep-old/alpha", "ep-old/beta"}
    assert git(repo, "status", "--porcelain").stdout == ""


def test_dry_run_nothing_to_change(repo, root, tmp_path):
    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    transcripts.mkdir()
    ep = mk_epic(root)
    mk_task(root, ep, "alpha")
    mk_task(root, ep, "beta")
    write_task(
        root,
        "in-progress",
        "ep-new",
        "lib",
        bootstrap_meta(points="5", expected_minutes="57", expected_tokens="3750000"),
    )
    commit_all(repo)
    r = dry_run(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["migrate: nothing to change"]
    r = dry_run(root, logs, transcripts, ep)
    assert (r.returncode, r.stdout) == (0, "migrate: nothing to change\n")
