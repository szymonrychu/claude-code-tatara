import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "investigation.py"


def _load():
    spec = importlib.util.spec_from_file_location("investigation", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_slugify_normalizes():
    inv = _load()
    assert inv.slugify("Memory OOM  spike!") == "memory-oom-spike"
    assert inv.slugify("--Already-Slug--") == "already-slug"


def test_report_path_composes():
    inv = _load()
    p = inv.report_path("memory-oom", "2026-07-11", Path("/x"))
    assert p == Path("/x/2026-07-11-memory-oom.md")


def test_init_writes_report(tmp_path):
    inv = _load()
    p = inv.init("memory-oom", "2026-07-11", tmp_path)
    assert p.exists()
    body = p.read_text()
    assert "# Grafana investigation: memory-oom" in body
    assert "**Date:** 2026-07-11" in body
    assert "## Plan" in body
    assert "## Phase 1" in body
    assert "## Final review" in body


def test_init_refuses_clobber(tmp_path):
    inv = _load()
    inv.init("dup", "2026-07-11", tmp_path)
    with pytest.raises(FileExistsError):
        inv.init("dup", "2026-07-11", tmp_path)


def test_append_adds_step_under_phase(tmp_path):
    inv = _load()
    p = inv.init("lat", "2026-07-11", tmp_path)
    inv.append_step(
        p,
        1,
        "golden-signals",
        "query_prometheus",
        "rate(http_requests_total[5m])",
        "error rate 12% on chat",
        "2026-07-11T10:00:00Z",
    )
    body = p.read_text()
    assert "- **[2026-07-11T10:00:00Z] golden-signals** via `query_prometheus`" in body
    assert "  - query: `rate(http_requests_total[5m])`" in body
    assert "  - finding: error rate 12% on chat" in body
    # step lands before Final review
    assert body.index("finding: error rate") < body.index("## Final review")


def test_append_creates_missing_phase_heading(tmp_path):
    inv = _load()
    p = inv.init("lat", "2026-07-11", tmp_path)
    inv.append_step(
        p,
        3,
        "use",
        "query_prometheus",
        "container_memory_working_set_bytes",
        "mem 95% on operator pod",
        "2026-07-11T10:05:00Z",
    )
    body = p.read_text()
    assert "## Phase 3" in body
    assert body.index("## Phase 3") < body.index("mem 95%")
    assert body.index("mem 95%") < body.index("## Final review")


def test_append_distinguishes_prefix_collision_phases(tmp_path):
    inv = _load()
    p = inv.init("collide", "2026-07-11", tmp_path)
    inv.append_step(
        p,
        21,
        "s21",
        "query_prometheus",
        "q21",
        "finding-21",
        "2026-07-11T10:00:00Z",
    )
    inv.append_step(
        p,
        2,
        "s2",
        "query_prometheus",
        "q2",
        "finding-2",
        "2026-07-11T10:01:00Z",
    )
    body = p.read_text()
    # both headings exist as distinct whole-line headings
    assert re.search(r"^## Phase 21$", body, re.M)
    assert re.search(r"^## Phase 2$", body, re.M)

    heading2 = re.search(r"^## Phase 2$", body, re.M)
    heading21 = re.search(r"^## Phase 21$", body, re.M)
    idx_finding2 = body.index("finding-2\n")
    idx_finding21 = body.index("finding-21\n")

    # finding-2 must be filed after "## Phase 2" heading and before the next
    # top-level heading that follows it (not spliced under "## Phase 21")
    assert idx_finding2 > heading2.end()
    next_heading_after_2 = re.search(r"\n## ", body[heading2.end() :])
    boundary = heading2.end() + next_heading_after_2.start() if next_heading_after_2 else len(body)
    assert idx_finding2 < boundary

    # finding-21 must be filed under "## Phase 21", not under "## Phase 2"
    assert idx_finding21 > heading21.end()


def test_parse_claim_splits_on_double_colon():
    inv = _load()
    assert inv.parse_claim("root cause is OOM::query_prometheus mem 95%") == (
        "root cause is OOM",
        "query_prometheus mem 95%",
    )
    assert inv.parse_claim("unbacked claim") == ("unbacked claim", "")


def test_finalize_lists_claims_and_flags_missing(tmp_path):
    inv = _load()
    p = inv.init("oom", "2026-07-11", tmp_path)
    inv.finalize(
        p,
        [
            ("operator pod OOMed", "query_prometheus working_set 95%"),
            ("caused by leak in cache", ""),
        ],
    )
    body = p.read_text()
    assert "1. operator pod OOMed" in body
    assert "evidence: query_prometheus working_set 95%" in body
    assert "[!] 2. caused by leak in cache" in body
    assert "EVIDENCE MISSING" in body


def test_finalize_replaces_placeholder(tmp_path):
    inv = _load()
    p = inv.init("oom", "2026-07-11", tmp_path)
    inv.finalize(p, [("x", "y")])
    body = p.read_text()
    assert "Populated by" not in body  # placeholder gone
    assert body.count("## Final review") == 1


def test_cli_init_append_finalize(tmp_path):
    def run(*args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=True,
        )

    out = run("init", "cli-smoke", "--date", "2026-07-11", "--base", str(tmp_path))
    path = out.stdout.strip()
    assert Path(path).exists()
    run(
        "append",
        path,
        "--phase",
        "1",
        "--stage",
        "scope",
        "--tool",
        "list_datasources",
        "--query",
        "n/a",
        "--finding",
        "prom uid=abc",
        "--ts",
        "2026-07-11T10:00:00Z",
    )
    run("finalize", path, "--claim", "prom exists::list_datasources uid=abc")
    body = Path(path).read_text()
    assert "scope" in body and "1. prom exists" in body


def test_default_base_resolves_against_workbench_root(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    (root / "code").mkdir(parents=True)
    (root / ".gitmodules").write_text("")
    sub = root / "deep" / "dir"
    sub.mkdir(parents=True)
    monkeypatch.setenv("WORKBENCH_ROOT", str(root))
    monkeypatch.chdir(sub)
    inv = _load()
    assert inv.default_base() == root / "docs" / "grafana-investigations"


def test_default_base_falls_back_to_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("WORKBENCH_ROOT", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    inv = _load()
    assert inv.default_base() == tmp_path / "docs" / "grafana-investigations"


def test_skill_is_generic():
    # Forbidden words are built at run time so this file does not trip the
    # personal-term lint it is asserting against.
    words = ["home" + "lab", "har" + "bor", "tat" + "ara", "RTL" + "8156B", "47d" + "28x2"]
    skill_dir = SCRIPT.parents[1]
    for f in skill_dir.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".py") and f != Path(__file__).resolve():
            text = f.read_text().lower()
            for w in words:
                assert w.lower() not in text, (f, w)
    skill = (skill_dir / "SKILL.md").read_text()
    assert "${CLAUDE_PLUGIN_ROOT}/skills/grafana-debugging-start/scripts/investigation.py" in skill
    assert "references/<project>-topology.md" in skill
