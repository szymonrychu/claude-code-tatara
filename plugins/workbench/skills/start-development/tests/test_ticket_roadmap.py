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
    """tasks: (name, status, files)"""
    d = root / phase / slug
    (d / "tasks").mkdir(parents=True)
    bl = "[" + ", ".join(blockers) + "]"
    (d / "README.md").write_text(f"---\ntitle: {slug}\nblockers: {bl}\nstage: {stage}\n---\n")
    for name, status, files in tasks:
        fl = "[" + ", ".join(files) + "]"
        (d / "tasks" / f"{name}.md").write_text(
            f"---\ntitle: {name}\nstatus: {status}\nfiles: {fl}\n---\nb\n"
        )


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


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
        tasks=[("t1", "done", ["x.py"]), ("t2", "todo", ["y.py"])],
    )
    epic(root, "next", blockers=["base"], tasks=[("n1", "todo", ["z.py"])])
    epic(root, "free", tasks=[("f1", "todo", ["w.py"])])
    out = lines(roadmap(root))
    assert "base in-progress/review 1/2 tasks blockers= running" in out
    assert "next todo 0/1 tasks blockers=base waiting on base" in out
    assert "free todo 0/1 tasks blockers= runnable" in out
    assert "next <- base" in out
    assert out[-1] == "runnable: free"


def test_source_overlap_not_runnable(root):
    epic(
        root,
        "busy",
        "in-progress",
        tasks=[("b1", "todo", ["src/a.py"]), ("b2", "done", ["src/old.py"])],
    )
    epic(root, "clash", tasks=[("c1", "todo", ["src/a.py"])])
    epic(root, "donefile", tasks=[("d1", "todo", ["src/old.py"])])
    out = lines(roadmap(root))
    assert any(ln.startswith("clash todo") and ln.endswith("overlaps busy: src/a.py") for ln in out)
    assert any(ln.startswith("donefile todo") and ln.endswith("runnable") for ln in out)
    assert out[-1] == "runnable: donefile"


def test_doc_overlap_runnable(root):
    epic(root, "busy", "in-progress", tasks=[("b1", "todo", ["docs/README.md"])])
    epic(root, "other", tasks=[("c1", "todo", ["docs/README.md"])])
    out = lines(roadmap(root))
    assert out[-1] == "runnable: other"


def test_mutual_overlap_first_only(root):
    epic(root, "aaa", tasks=[("a1", "todo", ["s.py"])])
    epic(root, "bbb", tasks=[("b1", "todo", ["s.py"])])
    out = lines(roadmap(root))
    assert any(ln.startswith("aaa ") and ln.endswith("overlaps bbb: s.py") for ln in out)
    assert any(ln.startswith("bbb ") and ln.endswith("overlaps aaa: s.py") for ln in out)
    assert out[-1] == "runnable: aaa"


def test_json_output(root):
    epic(root, "free", tasks=[("f1", "todo", ["w.py"])])
    epic(root, "late", blockers=["free"], tasks=[])
    data = json.loads(roadmap(root, "--json").stdout)
    assert data["runnable"] == ["free"]
    assert data["edges"] == [["late", "free"]]
    e = {x["epic"]: x for x in data["epics"]}
    assert e["free"]["state"] == "runnable"
    assert e["late"]["state"] == "waiting on free"


def _mk(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_roadmap_open_files_drops_merged(tmp_path):
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-b", "main")
    git(r, "config", "user.email", "t@t")
    git(r, "config", "user.name", "t")
    plans = r / "docs" / "plans"
    readme = "---\ntitle: {}\nblockers: []\nstage: build\n---\n"
    _mk(plans / "in-progress" / "busy" / "README.md", readme.format("busy"))
    _mk(
        plans / "in-progress" / "busy" / "tasks" / "b1.md",
        "---\ntitle: b1\nstatus: in-progress\nrepo: proj\nbranch: busy--b1\n"
        "files: [src/a.py]\n---\nb\n",
    )
    _mk(plans / "todo" / "next" / "README.md", readme.format("next"))
    _mk(
        plans / "todo" / "next" / "tasks" / "n1.md",
        "---\ntitle: n1\nstatus: todo\nfiles: [src/a.py]\n---\nb\n",
    )
    git(r, "add", ".")
    git(r, "commit", "-m", "init")
    out = roadmap(plans)
    assert "overlaps busy: src/a.py" in out.stdout, out.stdout + out.stderr
    git(r, "branch", "busy--b1")  # merged: the branch tip is already in main
    out = roadmap(plans)
    assert out.stdout.splitlines()[-1] == "runnable: next", out.stdout + out.stderr
