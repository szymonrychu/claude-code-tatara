"""ticket.py migrate: the write path, one commit per changed epic, RETRO.md and idempotence."""

import json
import sys
from pathlib import Path

from test_ticket_migrate_map import (
    START,
    bootstrap_meta,
    dry_run,
    full_records,
    old_meta,
    write_task,
)
from ticket_repo_helpers import cli, commit_all, git, meta, ticket

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import agent_usage  # noqa: E402

TEMPLATE = (Path(ticket.TEMPLATES) / "retro.md").read_text()
SIDE_FILES = ("approvals.json", "rulings.json", "record.md", "close.json", "README.md", "design.md")
FILLED = """# ep-filled retro

Intro kept as written.

<!-- retro:generated:begin -->
stale block
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| the tests | the estimate |

## Improvements

- none
"""


def migrate(root, logs, transcripts, *args):
    return cli("migrate", *args, "--logs", logs, "--transcripts", transcripts, "--root", root)


def dirs(tmp_path):
    logs, transcripts = tmp_path / "logs", tmp_path / "transcripts"
    transcripts.mkdir()
    return logs, transcripts


def head(repo):
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def subjects(repo, since):
    return git(repo, "log", "--reverse", "--format=%s", f"{since}..HEAD").stdout.splitlines()


def commit_files(repo, ref):
    out = git(repo, "show", "--name-only", "--format=", ref).stdout.split()
    return sorted(out)


def rel(repo, path):
    return str(Path(path).relative_to(repo))


def old_epics(root):
    """A todo, an in-progress and a done old-scheme epic, plus one already migrated."""
    paths = {
        "ep-todo": [
            write_task(root, "todo", "ep-todo", "plan", old_meta("ep-todo", "plan", status="todo"))
        ],
        "ep-live": [
            write_task(
                root,
                "in-progress",
                "ep-live",
                "build",
                old_meta("ep-live", "build", status="in-progress", estimate="20", actual=""),
            )
        ],
        "ep-old": [
            write_task(root, "done", "ep-old", "alpha", old_meta("ep-old", "alpha", estimate="45")),
            write_task(root, "done", "ep-old", "beta", old_meta("ep-old", "beta", actual="9")),
        ],
    }
    new = bootstrap_meta(points="5", expected_minutes="57", expected_tokens="3750000")
    paths["ep-new"] = [write_task(root, "in-progress", "ep-new", "lib", new)]
    return paths


def test_one_commit_per_epic(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    paths = old_epics(root)
    commit_all(repo)
    start = head(repo)

    # one epic by name: one commit holding exactly its task file
    r = migrate(root, logs, transcripts, "ep-todo")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["ep-todo: 1 tasks migrated"]
    assert subjects(repo, start) == ["chore(ticket): ep-todo migrate"]
    assert commit_files(repo, "HEAD") == [rel(repo, paths["ep-todo"][0])]
    assert list(meta(paths["ep-todo"][0])) == list(ticket._template("task.md").meta)

    # every epic: one commit per changed epic, the migrated and unchanged ones get none
    mid = head(repo)
    before = paths["ep-new"][0].read_bytes()
    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    out = r.stdout.splitlines()
    assert out[:2] == ["ep-live: 1 tasks migrated", "ep-old: 2 tasks migrated, RETRO.md"]
    assert subjects(repo, mid) == [
        "chore(ticket): ep-live migrate",
        "chore(ticket): ep-old migrate",
    ]
    assert commit_files(repo, "HEAD~1") == [rel(repo, paths["ep-live"][0])]
    retro_md = root / "done" / "ep-old" / "RETRO.md"
    assert commit_files(repo, "HEAD") == sorted(
        [rel(repo, p) for p in paths["ep-old"]] + [rel(repo, retro_md)]
    )
    assert paths["ep-new"][0].read_bytes() == before
    for epic in ("ep-live", "ep-old"):
        for path in paths[epic]:
            assert list(meta(path)) == list(ticket._template("task.md").meta), path
    assert meta(paths["ep-old"][0])["points"] == "3"
    assert git(repo, "status", "--porcelain").stdout == ""


def test_retro_written_in_migrate_commit(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    write_task(root, "done", "ep-bare", "alpha", old_meta("ep-bare", "alpha", estimate="45"))
    (root / "done" / "ep-bare" / "README.md").write_text('---\ntitle: "Bare epic"\n---\n\n# Bare\n')
    write_task(root, "done", "ep-filled", "alpha", old_meta("ep-filled", "alpha", estimate="5"))
    filled = root / "done" / "ep-filled" / "RETRO.md"
    filled.write_text(FILLED)
    commit_all(repo)

    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    assert "ep-bare: 1 tasks migrated, RETRO.md" in r.stdout.splitlines()
    assert "ep-filled: 1 tasks migrated, RETRO.md" in r.stdout.splitlines()

    # absent: created from templates/retro.md with retro's generated block
    bare = root / "done" / "ep-bare" / "RETRO.md"
    text = bare.read_text()
    assert text.splitlines()[0] == "# Bare epic retro"
    assert "| alpha title | 3 | not recorded | 45 | 4 | 2250000 | not recorded |" in text
    after_block = TEMPLATE[TEMPLATE.index("<!-- retro:generated:end -->") :]
    assert text.endswith(after_block)
    assert rel(repo, bare) in commit_files(repo, "HEAD~1")

    # present: the block regenerated, everything outside it byte for byte
    text = filled.read_text()
    assert "stale block" not in text
    assert "| alpha title | 1 | not recorded | 5 | 4 | 750000 | not recorded |" in text
    begin, end = (
        text.index("<!-- retro:generated:begin -->"),
        text.index("<!-- retro:generated:end -->"),
    )
    old_begin = FILLED.index("<!-- retro:generated:begin -->")
    old_end = FILLED.index("<!-- retro:generated:end -->")
    assert text[:begin] == FILLED[:old_begin]
    assert text[end:] == FILLED[old_end:]
    assert rel(repo, filled) in commit_files(repo, "HEAD")
    assert (
        git(repo, "log", "-1", "--format=%s").stdout.strip() == "chore(ticket): ep-filled migrate"
    )


def test_second_run_is_noop(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    old_epics(root)
    (root / "done" / "ep-old" / "RETRO.md").write_text(FILLED)
    commit_all(repo)
    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    assert git(repo, "status", "--porcelain").stdout == ""

    first = head(repo)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["migrate: nothing to change"]
    assert head(repo) == first
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert git(repo, "status", "--porcelain").stdout == ""
    r = migrate(root, logs, transcripts, "ep-old")
    assert r.stdout.splitlines() == ["migrate: nothing to change"]
    assert head(repo) == first


def test_retro_after_migrate_is_stable(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    write_task(
        root, "done", "ep-old", "alpha", old_meta("ep-old", "alpha", estimate="45", actual="")
    )
    write_task(root, "done", "ep-old", "beta", old_meta("ep-old", "beta", actual=""))
    (root / "done" / "ep-old" / "RETRO.md").write_text(FILLED)
    commit_all(repo)
    for record in full_records("ep-old", "alpha"):
        agent_usage.write_record(logs, record)

    r = migrate(root, logs, transcripts, "ep-old")
    assert r.returncode == 0, r.stderr
    alpha = meta(root / "done" / "ep-old" / "tasks" / "alpha.md")
    assert (alpha["actual_minutes"], alpha["actual_tokens"]) == ("31", "1400")
    retro_md = root / "done" / "ep-old" / "RETRO.md"
    block = retro_md.read_bytes()
    assert "| alpha title | 3 | not recorded | 45 | 31 | 2250000 | 1400 |" in retro_md.read_text()
    migrated = head(repo)

    r = cli("retro", "ep-old", "--logs", logs, "--transcripts", transcripts, "--root", root)
    assert r.returncode == 0, r.stderr
    assert head(repo) == migrated
    assert retro_md.read_bytes() == block

    r = migrate(root, logs, transcripts, "ep-old")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["migrate: nothing to change"]
    assert head(repo) == migrated


def test_side_files_untouched(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    paths = old_epics(root)
    side = {}
    for epic, tasks in paths.items():
        base = tasks[0].parent.parent
        for name in SIDE_FILES:
            path = base / name
            if not path.exists():
                path.write_text(f"{epic} {name}\n" if not name.endswith(".json") else '{"k": 1}\n')
            side[path] = path.read_bytes()
    commit_all(repo)
    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    assert len(side) == len(paths) * len(SIDE_FILES)
    for path, data in side.items():
        assert path.read_bytes() == data, path
    changed = git(repo, "diff", "--name-only", "HEAD~3", "HEAD").stdout.split()
    assert not [c for c in changed if Path(c).name in SIDE_FILES]


def test_names_epics_needing_retro_writer(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    write_task(root, "done", "ep-bare", "alpha", old_meta("ep-bare", "alpha"))
    write_task(root, "done", "ep-filled", "alpha", old_meta("ep-filled", "alpha"))
    (root / "done" / "ep-filled" / "RETRO.md").write_text(FILLED)
    write_task(root, "todo", "ep-todo", "plan", old_meta("ep-todo", "plan", status="todo"))
    commit_all(repo)

    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    out = r.stdout.splitlines()
    assert "retro-writer: ep-bare" in out
    assert "retro-writer: ep-filled" not in out
    assert not [line for line in out if line.startswith("retro-writer: ep-todo")]
    # the retro-writer lines follow the migrated lines
    first = out.index("retro-writer: ep-bare")
    assert all(line.startswith("retro-writer: ") for line in out[first:])
    assert all(not line.startswith("retro-writer: ") for line in out[:first])


def test_refuses_linked_worktree(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    old_epics(root)
    commit_all(repo)
    start = head(repo)
    wt = repo.parent / "linked"
    git(repo, "worktree", "add", "-b", "side", str(wt))
    wt_root = wt / "docs" / "plans"
    before = {p: p.read_bytes() for p in wt_root.rglob("*") if p.is_file()}

    r = migrate(wt_root, logs, transcripts, "--all")
    assert r.returncode == 1
    assert "ticket.py: run in the main checkout, not a linked worktree" in r.stderr
    assert r.stdout == ""
    assert {p: p.read_bytes() for p in wt_root.rglob("*") if p.is_file()} == before
    assert git(wt, "status", "--porcelain").stdout == ""
    assert head(repo) == start and head(wt) == start
    assert not logs.exists()


def test_default_dirs(repo, root, tmp_path, monkeypatch):
    task = write_task(root, "done", "ep-old", "alpha", old_meta("ep-old", "alpha", actual=""))
    commit_all(repo)
    monkeypatch.delenv("WORKBENCH_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    home = tmp_path / "fake-home"
    monkeypatch.setenv("HOME", str(home))
    session = agent_usage.default_transcripts_dir(repo.resolve(), home=home) / "s1" / "subagents"
    session.mkdir(parents=True)
    for agent_id, role, agent_type, total in (
        ("i1", "impl", "workbench:implementer", 100),
        ("r1", "review", "workbench:reviewer", 50),
    ):
        lines = [
            {
                "type": "user",
                "timestamp": START,
                "message": {"content": f"[wb ep-old/alpha/{role}]"},
            },
            {
                "type": "assistant",
                "timestamp": "2026-10-24T10:09:00.000Z",
                "message": {"id": f"m{agent_id}", "model": "m", "usage": {"input_tokens": total}},
            },
        ]
        (session / f"agent-{agent_id}.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in lines)
        )
        (session / f"agent-{agent_id}.meta.json").write_text(json.dumps({"agentType": agent_type}))

    r = cli("migrate", "ep-old", "--root", root)
    assert r.returncode == 0, r.stderr
    assert meta(task)["actual_tokens"] == "150"
    assert meta(task)["actual_roles"] != ""
    records = sorted(p.name for p in (repo / ".logs" / "agents").glob("*.json"))
    assert records == ["i1.json", "r1.json"]


def test_malformed_epic_blocks_all(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    paths = old_epics(root)
    write_task(root, "done", "ep-bad", "gamma", bootstrap_meta(points_actual="x"))
    commit_all(repo)
    start = head(repo)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}

    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 1
    assert r.stdout == ""
    assert any("ep-bad/gamma" in line and "points_actual" in line for line in r.stderr.splitlines())
    assert head(repo) == start
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert git(repo, "status", "--porcelain").stdout == ""
    assert not (root / "done" / "ep-old" / "RETRO.md").exists()
    assert paths  # every other epic was mappable and still was not written


def current_done_epic(root, epic):
    """A done epic whose task file is already in the new scheme."""
    return write_task(
        root,
        "done",
        epic,
        "lib",
        bootstrap_meta(points="3", expected_minutes="34", expected_tokens="2250000"),
    )


def test_dry_run_lists_missing_retro_without_task_changes(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    task = current_done_epic(root, "ep-cur")
    commit_all(repo)
    start, before = head(repo), task.read_bytes()

    r = dry_run(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    lines = r.stdout.splitlines()
    assert any(line.startswith("retro: ") and "ep-cur/RETRO.md" in line for line in lines)
    assert not [line for line in lines if line.startswith("ep-cur/lib")]
    assert "migrate: nothing to change" not in lines
    assert head(repo) == start
    assert task.read_bytes() == before
    assert not (root / "done" / "ep-cur" / "RETRO.md").exists()


def test_missing_retro_written_without_task_changes(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    task = current_done_epic(root, "ep-cur")
    commit_all(repo)
    start, before = head(repo), task.read_bytes()

    r = migrate(root, logs, transcripts, "--all")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == ["ep-cur: 0 tasks migrated, RETRO.md", "retro-writer: ep-cur"]
    retro_md = root / "done" / "ep-cur" / "RETRO.md"
    assert "<!-- retro:generated:begin -->" in retro_md.read_text()
    assert subjects(repo, start) == ["chore(ticket): ep-cur migrate"]
    assert commit_files(repo, "HEAD") == [rel(repo, retro_md)]
    assert task.read_bytes() == before
    assert git(repo, "status", "--porcelain").stdout == ""


def test_current_epic_with_retro_is_untouched(repo, root, tmp_path):
    logs, transcripts = dirs(tmp_path)
    current_done_epic(root, "ep-cur")
    commit_all(repo)
    assert migrate(root, logs, transcripts, "ep-cur").returncode == 0
    retro_md = root / "done" / "ep-cur" / "RETRO.md"
    retro_md.write_text(retro_md.read_text().replace("| ... | ... |", "| the tests | none |"))
    commit_all(repo)
    first = head(repo)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}

    for args in (("--all",), ("ep-cur",)):
        r = migrate(root, logs, transcripts, *args)
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == ["migrate: nothing to change"]
    assert head(repo) == first
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
