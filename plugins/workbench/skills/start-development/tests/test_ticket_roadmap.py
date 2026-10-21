"""ticket.py roadmap: epic graph, runnable epics, one status line per epic (D4)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"


def cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
    )


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "plans"
    r.mkdir()
    return r


def epic(root, slug, phase="todo", blockers=(), stage="build", tasks=()):
    """tasks: (name, status, files, estimate)"""
    d = root / phase / slug
    (d / "tasks").mkdir(parents=True)
    bl = "[" + ", ".join(blockers) + "]"
    (d / "README.md").write_text(f"---\ntitle: {slug}\nblockers: {bl}\nstage: {stage}\n---\n")
    for name, status, files, est in tasks:
        fl = "[" + ", ".join(files) + "]"
        (d / "tasks" / f"{name}.md").write_text(
            f"---\ntitle: {name}\nstatus: {status}\nfiles: {fl}\nestimate: {est}\n---\nb\n"
        )


def roadmap(root, *extra):
    return cli("roadmap", "--root", root, *extra)


def lines(r):
    assert r.returncode == 0, r.stderr
    return r.stdout.splitlines()


def test_status_lines_and_runnable(root):
    epic(
        root,
        "base",
        "in-progress",
        stage="review",
        tasks=[("t1", "done", ["x.py"], 10), ("t2", "todo", ["y.py"], 20)],
    )
    epic(root, "next", blockers=["base"], tasks=[("n1", "todo", ["z.py"], 5)])
    epic(root, "free", tasks=[("f1", "todo", ["w.py"], 7)])
    out = lines(roadmap(root))
    assert "base in-progress/review 1/2 tasks est 30m blockers= running" in out
    assert "next todo 0/1 tasks est 5m blockers=base waiting on base" in out
    assert "free todo 0/1 tasks est 7m blockers= runnable" in out
    assert "next <- base" in out
    assert out[-1] == "runnable: free"


def test_source_overlap_not_runnable(root):
    epic(
        root,
        "busy",
        "in-progress",
        tasks=[("b1", "todo", ["src/a.py"], 1), ("b2", "done", ["src/old.py"], 1)],
    )
    epic(root, "clash", tasks=[("c1", "todo", ["src/a.py"], 1)])
    epic(root, "donefile", tasks=[("d1", "todo", ["src/old.py"], 1)])
    out = lines(roadmap(root))
    assert any(ln.startswith("clash todo") and ln.endswith("overlaps busy: src/a.py") for ln in out)
    assert any(ln.startswith("donefile todo") and ln.endswith("runnable") for ln in out)
    assert out[-1] == "runnable: donefile"


def test_doc_overlap_runnable(root):
    epic(root, "busy", "in-progress", tasks=[("b1", "todo", ["docs/README.md"], 1)])
    epic(root, "other", tasks=[("c1", "todo", ["docs/README.md"], 1)])
    out = lines(roadmap(root))
    assert out[-1] == "runnable: other"


def test_mutual_overlap_first_only(root):
    epic(root, "aaa", tasks=[("a1", "todo", ["s.py"], 1)])
    epic(root, "bbb", tasks=[("b1", "todo", ["s.py"], 1)])
    out = lines(roadmap(root))
    assert any(ln.startswith("aaa ") and ln.endswith("overlaps bbb: s.py") for ln in out)
    assert any(ln.startswith("bbb ") and ln.endswith("overlaps aaa: s.py") for ln in out)
    assert out[-1] == "runnable: aaa"


def test_json_output(root):
    epic(root, "free", tasks=[("f1", "todo", ["w.py"], 7)])
    epic(root, "late", blockers=["free"], tasks=[])
    data = json.loads(roadmap(root, "--json").stdout)
    assert data["runnable"] == ["free"]
    assert data["edges"] == [["late", "free"]]
    e = {x["epic"]: x for x in data["epics"]}
    assert e["free"]["state"] == "runnable" and e["free"]["est"] == 7
    assert e["late"]["state"] == "waiting on free"
