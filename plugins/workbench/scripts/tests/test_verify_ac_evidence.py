"""verify-task --ac-evidence: a renamed test resolves by evidence, then exact, then substring."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verify_task as base  # noqa: E402
from test_verify_task import (  # noqa: E402
    ac,
    branch,
    by_id,
    commit,
    stub_bin,
    verify,
)

repo = base.repo
PY = "def test_parses_input_strictly():\n    pass\n\n\ndef test_other():\n    pass\n"


def run(repo, tmp_path, monkeypatch, acs, evidence=None, files=None):
    stub_bin(tmp_path, monkeypatch, ["pytest", "node"])
    branch(repo)
    commit(repo, {"src/a.py": "1\n", **(files if files is not None else {"tests/test_a.py": PY})})
    extra = []
    if evidence is not None:
        f = tmp_path / "ace.json"
        f.write_text(json.dumps(evidence))
        extra = ["--ac-evidence", str(f)]
    return by_id(verify(repo, "true", "--no-triage", *extra, acs=acs))


def test_ac_evidence_entry_resolves_a_renamed_test(repo, tmp_path, monkeypatch):
    got = run(
        repo, tmp_path, monkeypatch,
        [ac("A1", "x", "test", "tests/test_a.py::test_old_name")],
        evidence={"A1": "tests/test_a.py::test_other"},
    )  # fmt: skip
    a = got["A1"]
    assert a["met"] is True and "refMissing" not in a
    assert a["matchedBy"] == "acEvidence" and a["resolvedRef"] == "tests/test_a.py::test_other"


def test_ac_evidence_naming_a_missing_test_falls_back_to_exact(repo, tmp_path, monkeypatch):
    got = run(
        repo, tmp_path, monkeypatch,
        [ac("A1", "x", "test", "tests/test_a.py::test_other")],
        evidence={"A1": "tests/test_a.py::test_nope"},
    )  # fmt: skip
    assert got["A1"]["met"] is True and got["A1"]["matchedBy"] == "exact"
    assert got["A1"]["resolvedRef"] == "tests/test_a.py::test_other"


def test_single_substring_candidate_resolves_and_is_marked(repo, tmp_path, monkeypatch):
    got = run(
        repo, tmp_path, monkeypatch, [ac("A1", "x", "test", "tests/test_a.py::test_parses_input")]
    )
    a = got["A1"]
    assert a["met"] is True and a["matchedBy"] == "substring"
    assert a["resolvedRef"] == "tests/test_a.py::test_parses_input_strictly"


def test_ref_name_containing_the_real_name_is_a_substring_match(repo, tmp_path, monkeypatch):
    got = run(
        repo, tmp_path, monkeypatch, [ac("A1", "x", "test", "tests/test_a.py::test_other_extended")]
    )
    assert got["A1"]["matchedBy"] == "substring"
    assert got["A1"]["resolvedRef"] == "tests/test_a.py::test_other"


def test_ambiguous_substring_stays_ref_missing(repo, tmp_path, monkeypatch):
    files = {
        "tests/test_a.py": "def test_parses_a():\n    pass\n\n\ndef test_parses_b():\n    pass\n"
    }
    got = run(
        repo,
        tmp_path,
        monkeypatch,
        [ac("A1", "x", "test", "tests/test_a.py::test_parses")],
        files=files,
    )
    assert got["A1"]["met"] is False and got["A1"]["refMissing"] is True


def test_zero_substring_candidates_stay_ref_missing(repo, tmp_path, monkeypatch):
    got = run(
        repo, tmp_path, monkeypatch, [ac("A1", "x", "test", "tests/test_a.py::test_unrelated")]
    )
    assert got["A1"]["met"] is False and got["A1"]["refMissing"] is True
    assert "matchedBy" not in got["A1"]


def test_exact_ref_is_matched_by_exact(repo, tmp_path, monkeypatch):
    got = run(repo, tmp_path, monkeypatch, [ac("A1", "x", "test", "tests/test_a.py::test_other")])
    assert got["A1"]["matchedBy"] == "exact"
    assert got["A1"]["resolvedRef"] == "tests/test_a.py::test_other"


def test_substring_looks_only_inside_the_refs_file(repo, tmp_path, monkeypatch):
    files = {"tests/test_a.py": PY, "tests/test_b.py": "def test_unrelated_thing():\n    pass\n"}
    got = run(
        repo,
        tmp_path,
        monkeypatch,
        [ac("A1", "x", "test", "tests/test_b.py::test_parses_input")],
        files=files,
    )
    assert got["A1"]["refMissing"] is True


def test_js_substring_candidate(repo, tmp_path, monkeypatch):
    files = {"tests/a.test.mjs": "test('ac-evidence-resolves-renames', () => {})\n"}
    got = run(
        repo,
        tmp_path,
        monkeypatch,
        [ac("A1", "x", "test", "tests/a.test.mjs::ac-evidence")],
        files=files,
    )
    assert got["A1"]["matchedBy"] == "substring"
    assert got["A1"]["resolvedRef"] == "tests/a.test.mjs::ac-evidence-resolves-renames"


def test_acs_without_evidence_flag_still_work(repo, tmp_path, monkeypatch):
    got = run(repo, tmp_path, monkeypatch, [ac("A1", "x", "test", "tests/test_a.py::test_other")])
    assert got["A1"]["met"] is True


def test_resolution_order_and_matched_by(repo, tmp_path, monkeypatch):
    # acEvidence beats an exact ref that also exists; exact beats substring.
    got = run(
        repo, tmp_path, monkeypatch,
        [
            ac("A1", "x", "test", "tests/test_a.py::test_other"),
            ac("A2", "x", "test", "tests/test_a.py::test_other"),
            ac("A3", "x", "test", "tests/test_a.py::test_parses_input"),
        ],
        evidence={
            "A1": "tests/test_a.py::test_parses_input_strictly",
            "A3": "tests/test_a.py::test_nope",
        },
    )  # fmt: skip
    assert got["A1"]["matchedBy"] == "acEvidence"
    assert got["A1"]["resolvedRef"] == "tests/test_a.py::test_parses_input_strictly"
    assert got["A2"]["matchedBy"] == "exact"
    assert got["A3"]["matchedBy"] == "substring"


def test_renamed_tests_fixture_has_no_ref_missing(repo, tmp_path, monkeypatch):
    # Modelled on harness-config-migrate#1: several refs name tests later renamed.
    files = {
        "tests/test_m.py": (
            "def test_migrates_config_files():\n    pass\n\n\n"
            "def test_rejects_unknown_harness():\n    pass\n\n\n"
            "def test_writes_backup_before_migrating():\n    pass\n"
        )
    }
    got = run(
        repo, tmp_path, monkeypatch,
        [
            ac("AC3", "x", "test", "tests/test_m.py::test_migrate_config"),
            ac("AC4", "x", "test", "tests/test_m.py::test_unknown_harness_error"),
            ac("AC5", "x", "test", "tests/test_m.py::test_backup"),
        ],
        evidence={
            "AC3": "tests/test_m.py::test_migrates_config_files",
            "AC4": "tests/test_m.py::test_rejects_unknown_harness",
            "AC5": "tests/test_m.py::test_writes_backup_before_migrating",
        },
        files=files,
    )  # fmt: skip
    assert all("refMissing" not in a and a["met"] for a in got.values()), got
    assert got["AC4"]["matchedBy"] == "acEvidence" and got["AC5"]["matchedBy"] == "acEvidence"
