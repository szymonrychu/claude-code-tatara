"""ticket.py migrate: old epic dirs (README.md, design.md, tasks/, RETRO.md, record.md,
approvals.json, rulings.json) become plan.md, implementation-plan.md and retro.md."""

import json
import re
import subprocess
import sys

import pytest
from ticket_repo_helpers import SCRIPT, git, init_repo, last_subject, meta, ticket

OLD_FILES = ("README.md", "design.md", "tasks", "RETRO.md", "record.md", "approvals.json")
OLD_FILES += ("rulings.json",)


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, cwd=cwd
    )


def fm(**kw) -> str:
    return ticket.dump(ticket.Doc(kw, ""))


# ---------------------------------------------------------------- fixtures: the current scheme

CUR_README_BODY = """
# Current epic

## Project brief

What: a widget
How: with a tool
Why: users asked

## Description

The long description.
It spans two lines.

## Goals

- Goal one
  - nested detail
- Goal two

## Non-goals

- Not this

## Review

Verdict: pass (2026-10-02)

All good.
"""

DESIGN_SECTIONS = {
    "Summary": "The summary.",
    "Intent and why": "The intent.",
    "Goals": "- design goal",
    "Non-goals": "- design non-goal",
    "Anti-goals": "- anti",
    "Constraints": "- constraint",
    "Decisions": "### D1: Use a tool\n\nBecause. (my call)\n\n### D2: Second\n\nAlso.",
    "Research": "| lens | ran |\n|---|---|\n| docs | ran |",
    "Research inputs": "- finding one - src - alpha",
    "Decision coverage": "| Decision | Tasks |\n|---|---|\n| D1 | alpha |",
    "Review focus": "- focus here",
    "Left to the builder": "- naming",
    "Assumptions and unknown facts": "- assumption",
    "Open questions": "- Q1: Which? [answer: this one]",
    "Irreversible operations in scope": "- deleting the old file",
}

TASK_KEYS = dict(
    title="",
    status="done",
    repo="workbench",
    value="why",
    files=[],
    verify="pytest -q",
    depends_on=[],
    model="sonnet",
    review="",
    verified_head="",
    points="3",
    expected_minutes="40",
    expected_tokens="100",
    points_actual="",
    actual_minutes="12",
    actual_tokens="90",
    actual_roles="impl 1, review 1",
    actual_role_tokens="impl 50, review 40",
)


def task_body(title, extra=""):
    return (
        f"\n# {title}\n\n## Requirement\n\nDo {title}.\n\n## Acceptance conditions\n\n"
        f"- AC1: {title} works [evidence: test:t.py::test_{title.lower()}]\n\n"
        f"## Files\n\n- `{title.lower()}.py`\n\n## Steps\n\n1. test first\n\n"
        f"## Notes\n\nNote for {title}.\n{extra}"
    )


def write_task(epic, slug, title, body_extra="", **kw):
    keys = {**TASK_KEYS, "title": title, **kw}
    p = epic / "tasks" / f"{slug}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(fm(**keys) + task_body(title, body_extra))
    return p


RETRO_MD = """# Current epic retro

<!-- retro:generated:begin -->
## Tasks

| Task | points |
|---|---|
| Alpha | 3 |

## Deltas

- MdAPE minutes: 10%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| Fast reviews | Slow verify |
| Clear plan | |

## Improvements

- Code:
  - tidy the helper
- Workflow:
  - run less
"""

RECORD_MD = """# Current epic record

## Asked

Asked for a widget.

## Shipped

Shipped the widget.
"""


def current_scheme(root, phase="done", name="cur-epic"):
    d = root / phase / name
    d.mkdir(parents=True)
    readme = fm(
        title="Current epic",
        blockers=[],
        stage="review",
        owner="Tess",
        repos=["workbench"],
        created="2026-10-01",
    )
    (d / "README.md").write_text(readme + CUR_README_BODY)
    design = "# Current epic design\n\n" + "".join(
        f"## {k}\n\n{v}\n\n" for k, v in DESIGN_SECTIONS.items()
    )
    (d / "design.md").write_text(design)
    write_task(d, "alpha", "Alpha", depends_on=["beta"], model="opus", verified_head="abc123")
    write_task(d, "beta", "Beta", files=["b.py", "c.py"], verified_head="def456")
    (d / "RETRO.md").write_text(RETRO_MD)
    (d / "record.md").write_text(RECORD_MD)
    (d / "close.json").write_text(json.dumps({"epic": name, "base": "main"}) + "\n")
    return d


# ---------------------------------------------------------------- fixtures: the older scheme

OLD_README_BODY = """
# Older epic

## Project brief

What: old thing

## Goals

- Old goal

## Non-goals

- Old non-goal

## Time

Estimate: 100 min | Actual: 0 min

## Review

Verdict: pass (2026-09-01)
"""

APPROVALS = [
    {"id": "A1", "text": "Approve one", "decisions": ["D1"], "tasks": ["gamma"]},
    {"id": "A2", "text": "Approve two", "status": "approved"},
]
RULINGS = [{"task": "gamma", "accept": True, "reason": "false positive", "at": "2026-09-02"}]


def older_scheme(root, phase="done", name="old-epic"):
    d = root / phase / name
    d.mkdir(parents=True)
    readme = fm(title="Older epic", blockers=[], stage="review", owner="", repos=[])
    (d / "README.md").write_text(readme + OLD_README_BODY)
    (d / "design.md").write_text(
        "# Older epic design\n\n## Summary\n\nOld summary.\n\n## Decisions\n\n### D1: Old\n\n"
        "Old why.\n\n## Contracts\n\n- contract one\n"
    )
    old_keys = dict(
        title="Gamma",
        status="done",
        repo="workbench",
        owns=["g.py"],
        uses=["u.py"],
        estimate="30",
        actual="20",
        worktree="old-epic--gamma",
        branch="old-epic--gamma",
        run="2",
        provides=["thing"],
        acs_for_audit=["AC1"],
        process_gaps=["gap"],
        verify="make test",
        verified_head="fff000",
    )
    p = d / "tasks" / "gamma.md"
    p.parent.mkdir()
    p.write_text(
        fm(**old_keys)
        + task_body("Gamma", "\n## Ruling\n\nAccepted on appeal.\n\n## Resolution\n\nFixed.\n")
    )
    (d / "approvals.json").write_text(json.dumps(APPROVALS, indent=2))
    (d / "rulings.json").write_text(json.dumps(RULINGS, indent=2))
    (d / "record.md").write_text("# Older epic record\n\n## Summary\n\nOld record.\n")
    return d


def todo_epic(root, name="todo-epic"):
    d = root / "todo" / name
    d.mkdir(parents=True)
    readme = fm(title="Todo epic", blockers=[], stage="build", owner="", repos=[], created="x")
    (d / "README.md").write_text(
        readme + "\n# Todo epic\n\n## Project brief\n\nWhat: later work\n\n## Goals\n\n- G\n"
    )
    return d


def in_progress_epic(root, name="ip-epic"):
    d = root / "in-progress" / name
    d.mkdir(parents=True)
    readme = fm(title="Running epic", blockers=[], stage="build", owner="Tess", repos=[])
    (d / "README.md").write_text(readme + "\n# Running epic\n\n## Goals\n\n- Run\n")
    write_task(d, "c-last", "Last", depends_on=["b-mid"], status="todo")
    write_task(d, "a-first", "First", status="done", verified_head="111")
    write_task(d, "b-mid", "Mid", depends_on=["a-first"], status="in-progress")
    return d


@pytest.fixture
def plans(tmp_path):
    repo = init_repo(tmp_path / "repo")
    root = repo / "docs" / "plans"
    current_scheme(root)
    older_scheme(root)
    todo_epic(root)
    in_progress_epic(root)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "old epics")
    return repo, root


def migrate(root, *args, cwd=None):
    return cli("migrate", *args, "--root", root, cwd=cwd)


def h2s(text):
    return re.findall(r"^## (.+?)\s*$", text, re.M)


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, name
    return m.group(1)


def template_h2(name):
    return h2s((SCRIPT.parents[1] / "templates" / name).read_text())


# ---------------------------------------------------------------- the run


def test_migrate_all_keeps_phases_and_commits_once_per_plan(plans):
    repo, root = plans
    r = migrate(root, "--all")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [
        "todo-epic: migrated (0 steps)",
        "ip-epic: migrated (3 steps)",
        "cur-epic: migrated (2 steps, retro.md)",
        "old-epic: migrated (1 steps, retro.md)",
    ]
    for phase, name in (
        ("done", "cur-epic"),
        ("done", "old-epic"),
        ("in-progress", "ip-epic"),
        ("todo", "todo-epic"),
    ):
        d = root / phase / name
        assert (d / "plan.md").is_file(), name
        names = {p.name for p in d.iterdir()}  # exact case: the disk may ignore case
        for old in OLD_FILES:
            assert old not in names, (name, old)
    assert (root / "done" / "cur-epic" / "close.json").is_file()
    log = git(repo, "log", "--format=%s", "-4").stdout.split("\n")
    assert sorted(x for x in log if x) == sorted(
        f"chore(ticket): {n} migrate" for n in ("cur-epic", "old-epic", "ip-epic", "todo-epic")
    )
    for n in range(4):
        files = git(repo, "show", "--name-only", "--format=", f"HEAD~{n}").stdout.split()
        plan = git(repo, "log", "-1", "--format=%s", f"HEAD~{n}").stdout.split()[1]
        assert files and all(f"/{plan}/" in f for f in files), (plan, files)
    assert git(repo, "status", "--porcelain").stdout == ""
    tracked = git(repo, "ls-files", "docs").stdout.split()
    assert not [f for f in tracked if f.endswith(("README.md", "RETRO.md", "record.md"))]
    assert "docs/plans/done/cur-epic/close.json" in tracked


def test_second_run_has_nothing_to_change(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    r = migrate(root, "--all")
    assert r.returncode == 0 and r.stdout.strip() == "migrate: nothing to change"


def test_plan_dirs_holding_plan_md_are_untouched(plans):
    repo, root = plans
    new = root / "todo" / "fresh"
    new.mkdir()
    text = fm(title="Fresh", repos=[], created="2026-10-31", owner="", rung="") + "\n# Fresh\n"
    (new / "plan.md").write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "fresh")
    assert migrate(root, "--all").returncode == 0
    assert (new / "plan.md").read_text() == text
    assert sorted(p.name for p in new.iterdir()) == ["plan.md"]


def test_migrate_one_epic(plans):
    repo, root = plans
    r = migrate(root, "todo-epic")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "todo-epic: migrated (0 steps)"
    assert last_subject(repo) == "chore(ticket): todo-epic migrate"
    assert (root / "done" / "cur-epic" / "README.md").is_file()
    r = migrate(root, "todo-epic")
    assert r.returncode == 0 and r.stdout.strip() == "migrate: nothing to change"
    assert migrate(root, "ghost").returncode == 1


def test_migrate_needs_one_epic_or_all(plans):
    _, root = plans
    r = migrate(root)
    assert r.returncode == 1 and "migrate needs <epic> or --all" in r.stderr


def test_after_migration_the_plan_commands_work(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    r = cli("path", "cur-epic", "plan", "--root", root)
    assert r.returncode == 0, r.stderr
    r = cli("check", "--title", "Something else", "--root", root)
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------- plan.md


def test_plan_md_follows_the_template_and_the_mapping(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    p = root / "done" / "cur-epic" / "plan.md"
    text = p.read_text()
    m = meta(p)
    assert list(m) == ["title", "repos", "created", "owner", "rung"]
    assert m == {
        "title": "Current epic",
        "repos": ["workbench"],
        "created": "2026-10-01",
        "owner": "Tess",
        "rung": "1",
    }
    assert h2s(text) == template_h2("plan.md") + ["Migrated notes"]
    assert re.findall(r"^# (.+)$", text, re.M) == ["Current epic"]
    what = section(text, "What and why")
    for line in ("What: a widget", "How: with a tool", "Why: users asked", "It spans two lines."):
        assert line in what
    ladder = section(text, "Scope ladder")
    assert "### Rung 1: agreed scope (migrated)" in ladder
    assert "- 1.1: Goal one\n  - nested detail\n- 1.2: Goal two" in ladder
    assert "migrated" in section(text, "Agreed scope").lower()
    assert "- Not this" in section(text, "Non-goals")
    decisions = section(text, "Decisions")
    assert "### D1: Use a tool" in decisions and "Because. (my call)" in decisions
    assert "- Q1: Which? [answer: this one]" in section(text, "Open questions")
    research = section(text, "Research")
    assert "| docs | ran |" in research and "- finding one - src - alpha" in research
    assert "- deleting the old file" in section(text, "Irreversible operations")
    notes = section(text, "Migrated notes")
    for heading in (
        "### README.md: Review",
        "### design.md: Summary",
        "### design.md: Intent and why",
        "### design.md: Goals",
        "### design.md: Non-goals",
        "### design.md: Anti-goals",
        "### design.md: Constraints",
        "### design.md: Decision coverage",
        "### design.md: Review focus",
        "### design.md: Left to the builder",
        "### design.md: Assumptions and unknown facts",
    ):
        assert heading in notes, heading
    assert "Verdict: pass (2026-10-02)" in notes


def test_older_scheme_time_dropped_approvals_and_extra_sections_kept(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    text = (root / "done" / "old-epic" / "plan.md").read_text()
    assert "## Time" not in text and "Estimate: 100 min" not in text
    notes = section(text, "Migrated notes")
    assert "### design.md: Contracts" in notes and "- contract one" in notes
    assert "### approvals.json" in notes
    assert "- A1: Approve one [decisions: D1] [tasks: gamma]" in notes
    assert "- A2: Approve two [status: approved]" in notes
    assert meta(root / "done" / "old-epic" / "plan.md")["created"] == ""


def test_todo_plan_is_not_agreed_and_cannot_be_claimed(plans):
    repo, root = plans
    assert migrate(root, "--all").returncode == 0
    d = root / "todo" / "todo-epic"
    assert meta(d / "plan.md")["rung"] == ""
    assert section((d / "plan.md").read_text(), "Agreed scope").strip() == "not agreed yet"
    assert not (d / "implementation-plan.md").exists() and not (d / "retro.md").exists()
    r = cli("move", "todo-epic", "in-progress", "--root", root)
    assert r.returncode == 1 and "has no agreed rung" in r.stderr
    assert meta(root / "in-progress" / "ip-epic" / "plan.md")["rung"] == "1"


# ---------------------------------------------------------------- implementation-plan.md


def test_implementation_plan_steps_in_dependency_order(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    text = (root / "in-progress" / "ip-epic" / "implementation-plan.md").read_text()
    assert text.splitlines()[0] == "# Running epic implementation plan"
    assert h2s(text) == [
        "Agreed rung",
        "Approach",
        "Chunk 1: migrated tasks (model: sonnet)",
        "Files to delete",
        "Final verify",
        "After merge",
    ]
    steps = re.findall(r"^### (S\d+: .+)$", text, re.M)
    assert steps == ["S1: First", "S2: Mid", "S3: Last"]
    s1 = text[text.index("### S1: First") : text.index("### S2: Mid")]
    assert "- Status: done" in s1 and "- Verified head: 111" in s1
    assert "- Files: none" in s1  # files frontmatter was empty
    s2 = text[text.index("### S2: Mid") : text.index("### S3: Last")]
    assert "- Status: in-progress" in s2 and "- Verified head: none" in s2


def test_steps_carry_fields_and_every_body_section_one_level_deeper(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    text = (root / "done" / "cur-epic" / "implementation-plan.md").read_text()
    assert "## Chunk 1: migrated tasks (model: opus)" in text
    assert re.findall(r"^### (S\d+: .+)$", text, re.M) == ["S1: Beta", "S2: Alpha"]
    beta = text[text.index("### S1: Beta") : text.index("### S2: Alpha")]
    for line in (
        "- Status: done",
        "- Files: `b.py`, `c.py`",
        "- Verify: `pytest -q`",
        "- Verified head: def456",
        "#### Requirement",
        "Do Beta.",
        "#### Acceptance conditions",
        "- AC1: Beta works [evidence: test:t.py::test_beta]",
        "#### Files",
        "#### Steps",
        "#### Notes",
        "Note for Beta.",
    ):
        assert line in beta, line
    assert "# Beta\n" not in beta
    for gone in ("points", "expected_minutes", "actual_tokens"):
        assert gone not in text


def test_older_task_keys_and_rulings(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    text = (root / "done" / "old-epic" / "implementation-plan.md").read_text()
    gamma = text[text.index("### S1: Gamma") :]
    assert "- Files: `g.py`, `u.py`" in gamma
    assert "- Verify: `make test`" in gamma
    assert "#### Ruling" in gamma and "Accepted on appeal." in gamma
    assert "#### Resolution" in gamma and "Fixed." in gamma
    for gone in ("estimate", "worktree", "acs_for_audit", "process_gaps", "provides"):
        assert gone not in text, gone
    assert h2s(text)[-1] == "Rulings (migrated)"
    rulings = section(text, "Rulings (migrated)")
    assert "- gamma: accept true, at 2026-09-02: false positive" in rulings


# ---------------------------------------------------------------- retro.md


def test_retro_md_from_retro_and_record(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    text = (root / "done" / "cur-epic" / "retro.md").read_text()
    assert text.splitlines()[0] == "# Current epic retro"
    assert h2s(text) == template_h2("retro.md") + ["Delivery record (migrated)"]
    assert "retro:generated" not in text and "MdAPE" not in text and "| Alpha | 3 |" not in text
    well = section(text, "What went well")
    assert "- Fast reviews" in well and "- Clear plan" in well
    wrong = section(text, "What went wrong or could improve")
    assert "- Slow verify" in wrong
    assert "Clear plan" not in wrong
    recs = section(text, "Recommendations")
    assert "- Code:\n  - tidy the helper" in recs and "  - run less" in recs
    record = section(text, "Delivery record (migrated)")
    assert "### Asked" in record and "Asked for a widget." in record
    assert "Shipped the widget." in record and "# Current epic record" not in record


def test_retro_md_from_record_only(plans):
    _, root = plans
    assert migrate(root, "--all").returncode == 0
    text = (root / "done" / "old-epic" / "retro.md").read_text()
    assert h2s(text) == template_h2("retro.md") + ["Delivery record (migrated)"]
    assert "Old record." in section(text, "Delivery record (migrated)")
    for name in ("What went well", "What went wrong or could improve", "Recommendations"):
        assert section(text, name).strip(), name


def test_nothing_is_lost(plans):
    _, root = plans
    sources = {}
    for d in (root / "done" / "cur-epic", root / "done" / "old-epic"):
        texts = [p.read_text() for p in d.rglob("*.md")]
        sources[d] = texts
    assert migrate(root, "--all").returncode == 0
    for d, texts in sources.items():
        out = "\n".join(p.read_text() for p in d.glob("*.md"))
        for text in texts:
            body = ticket.load(text, "x").body if text.startswith("---") else text
            body = re.sub(r"<!-- retro:generated:begin -->.*?:end -->", "", body, flags=re.S)
            for line in body.splitlines():
                s = line.strip()
                if not s or s.startswith("#") or s.startswith("<!--") or "|---" in s:
                    continue
                if "Estimate: 100 min" in s:
                    continue  # README Time is retired
                if s.startswith("|") and s.endswith("|"):  # Retro table rows split into cells
                    cells = [c.strip() for c in s.strip("|").split("|")]
                    for c in cells:
                        if c and c not in ("Went well", "Went bad / could be improved"):
                            assert c in out, (d.name, c)
                    continue
                s = re.sub(r"^- ", "", s)
                assert s in out, (d.name, s)


# ---------------------------------------------------------------- validation and dry run


def test_unparseable_file_anywhere_refuses_and_writes_nothing(plans):
    repo, root = plans
    (root / "done" / "cur-epic" / "tasks" / "alpha.md").write_text("---\na:\n  b: 1\n---\n")
    (root / "done" / "old-epic" / "rulings.json").write_text("{not json")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "broken")
    head = git(repo, "rev-parse", "HEAD").stdout
    r = migrate(root, "--all")
    assert r.returncode == 1
    assert "alpha.md:2: unsupported frontmatter" in r.stderr
    assert "rulings.json" in r.stderr
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert git(repo, "status", "--porcelain").stdout == ""
    assert not list(root.rglob("plan.md"))


def test_dependency_cycle_refuses(plans):
    repo, root = plans
    d = root / "in-progress" / "ip-epic" / "tasks" / "a-first.md"
    doc = ticket.load(d.read_text(), d)
    doc.meta["depends_on"] = ["c-last"]
    d.write_text(ticket.dump(doc))
    r = migrate(root, "--all")
    assert r.returncode == 1 and "dependency cycle" in r.stderr and "ip-epic" in r.stderr
    assert not list(root.rglob("plan.md"))


def test_dir_without_readme_or_plan_refuses(plans):
    _, root = plans
    (root / "todo" / "empty").mkdir()
    r = migrate(root, "--all")
    assert r.returncode == 1 and "empty" in r.stderr and "no README.md" in r.stderr


def test_dry_run_writes_nothing_and_lists_files(plans):
    repo, root = plans
    head = git(repo, "rev-parse", "HEAD").stdout
    r = migrate(root, "--all", "--dry-run")
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert (
        "cur-epic: would write plan.md, implementation-plan.md, retro.md; would remove "
        "README.md, RETRO.md, design.md, record.md, tasks/" in out
    )
    assert "todo-epic: would write plan.md; would remove README.md" in out
    assert "approvals.json" in out.split("old-epic:")[1].splitlines()[0]
    assert git(repo, "rev-parse", "HEAD").stdout == head
    assert git(repo, "status", "--porcelain").stdout == ""
    assert not list(root.rglob("plan.md"))


def test_dry_run_runs_in_a_linked_worktree_and_outside_git(plans, tmp_path):
    repo, root = plans
    side = tmp_path / "side"
    git(repo, "worktree", "add", "-q", "-b", "side", str(side))
    r = migrate(side / "docs" / "plans", "--all", "--dry-run")
    assert r.returncode == 0, r.stderr
    r = migrate(side / "docs" / "plans", "--all")
    assert r.returncode == 1 and "main checkout" in r.stderr
    plain = tmp_path / "plain" / "plans"
    todo_epic(plain)
    r = migrate(plain, "--all", "--dry-run")
    assert r.returncode == 0 and "todo-epic: would write plan.md" in r.stdout
    r = migrate(plain, "--all")
    assert r.returncode == 0 and (plain / "todo" / "todo-epic" / "plan.md").is_file()
    assert not (plain / "todo" / "todo-epic" / "README.md").exists()


def test_old_epic_refusal_points_at_migrate(plans):
    _, root = plans
    r = cli("check", "--title", "X", "--root", root)
    assert r.returncode == 1 and "run ticket.py migrate --all" in r.stderr
    assert "migrate" in cli("--help").stdout
