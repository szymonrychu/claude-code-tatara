"""triage.py: four Haiku-backed modes, no-call shortcuts, one batched call, log, fallbacks."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import triage  # noqa: E402


class Fake:
    """Fake claude_json runner: records calls, answers with a structured_output envelope."""

    def __init__(self, answer=None, code=0, err="", usage=None):
        self.answer, self.code, self.err, self.usage = answer, code, err, usage or {}
        self.calls = []

    def __call__(self, argv, stdin, env, timeout):
        self.calls.append((argv, stdin))
        env_json = {
            "is_error": False,
            "structured_output": self.answer,
            "modelUsage": {"claude-haiku-5-5": {}},
            "usage": self.usage,
        }
        return self.code, json.dumps(env_json), self.err


def log_lines(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines()]


# ---- tier ----

TIER_IN = {"requirement": "add auth", "files": ["a.py"], "diffstat": "1 file changed"}


def test_tier_returns_classifier_tier(tmp_path):
    fake = Fake({"classifierTier": "panel", "reasons": ["touches auth"]})
    out = triage.tier(TIER_IN, runner=fake)
    assert out == {"classifierTier": "panel", "reasons": ["touches auth"]}
    assert len(fake.calls) == 1
    assert "haiku" in fake.calls[0][0]
    assert "add auth" in fake.calls[0][1]


def test_tier_failure_is_skip_and_says_so():
    out = triage.tier(TIER_IN, runner=Fake(code=1, err="boom"))
    assert out["classifierTier"] == "skip"
    assert any("classifier failed" in r for r in out["reasons"])


def test_tier_schema_mismatch_falls_back_to_skip():
    out = triage.tier(TIER_IN, runner=Fake({"classifierTier": "huge", "reasons": []}))
    assert out["classifierTier"] == "skip"


def test_tier_holds_no_rule_tier_logic():
    assert triage.TIER_ORDER == ["skip", "light", "full", "panel"]
    # the hint is a plain classifier answer: no input field can lower or raise it
    fake = Fake({"classifierTier": "light", "reasons": []})
    assert triage.tier({**TIER_IN, "ruleTier": "panel"}, runner=fake)["classifierTier"] == "light"


# ---- ac-plausible ----


def ac(
    id_,
    kind="test",
    ref="tests/test_login.py::test_login_ok",
    text="login works for valid user",
    met=True,
    snippet="def test_login_ok(): ...",
):
    return {"id": id_, "text": text, "kind": kind, "ref": ref, "snippet": snippet, "met": met}


def test_ac_shortcut_yes_without_call():
    fake = Fake()
    out = triage.ac_plausible(
        [ac("AC1"), ac("AC2", kind="command", ref="pytest login -q")], runner=fake
    )
    assert [o["verdict"] for o in out] == ["yes", "yes"]
    assert fake.calls == []


def test_ac_rest_go_in_one_batched_call_order_kept():
    fake = Fake(
        {
            "results": [
                {"id": "AC2", "verdict": "no", "reason": "unrelated"},
                {"id": "AC4", "verdict": "unsure", "reason": "vague"},
                {"id": "AC3", "verdict": "yes", "reason": "ok"},
            ]
        }
    )
    acs = [
        ac("AC1"),
        ac("AC2", ref="tests/test_zzz.py::test_q"),
        ac("AC3", kind="doc-section", ref="d.md#x"),
        ac("AC4", met=False),
    ]
    out = triage.ac_plausible(acs, runner=fake)
    assert [o["id"] for o in out] == ["AC1", "AC2", "AC3", "AC4"]
    assert [o["verdict"] for o in out] == ["yes", "no", "yes", "unsure"]
    assert len(fake.calls) == 1
    assert "AC1" not in fake.calls[0][1]


def test_ac_missing_answer_for_an_id_is_unsure():
    fake = Fake({"results": []})
    out = triage.ac_plausible([ac("AC9", kind="judgement", ref="")], runner=fake)
    assert out[0]["verdict"] == "unsure"


def test_ac_failure_gives_unsure_but_keeps_shortcuts():
    out = triage.ac_plausible(
        [ac("AC1"), ac("AC2", kind="doc-section", ref="d.md#x")], runner=Fake(code=2, err="x")
    )
    assert out[0]["verdict"] == "yes"
    assert out[1]["verdict"] == "unsure"
    assert "classifier failed" in out[1]["reason"]


def test_ac_empty_input_no_call():
    fake = Fake()
    assert triage.ac_plausible([], runner=fake) == []
    assert fake.calls == []


# ---- parking ----

LINES = [
    {"file": "a.py", "line": 3, "text": "# TODO later"},
    {"file": "a.py", "line": 9, "text": "# note"},
]


def test_parking_returns_flagged_subset_one_call():
    fake = Fake({"lines": [{"index": 0, "reason": "defers work"}]})
    out = triage.parking(LINES, runner=fake)
    assert out == [{"file": "a.py", "line": 3, "text": "# TODO later", "reason": "defers work"}]
    assert len(fake.calls) == 1


def test_parking_failure_is_no_lines():
    assert triage.parking(LINES, runner=Fake(code=1)) == []


def test_parking_failure_says_so_in_reason_attribute_and_wrapper():
    out = triage.parking(LINES, runner=Fake(code=1))
    assert "classifier failed" in out.reason
    wrapped = triage.render("parking", out, with_reason=True)
    assert wrapped["lines"] == [] and "classifier failed" in wrapped["reason"]
    assert triage.render("parking", out, with_reason=False) == []


def test_parking_success_has_no_reason():
    out = triage.parking(LINES, runner=Fake({"lines": [{"index": 0, "reason": "d"}]}))
    assert out.reason is None
    assert triage.render("parking", out, with_reason=True)["reason"] is None


def test_parking_out_of_range_index_ignored():
    fake = Fake({"lines": [{"index": 7, "reason": "x"}]})
    assert triage.parking(LINES, runner=fake) == []


def test_parking_empty_no_call():
    fake = Fake()
    assert triage.parking([], runner=fake) == []
    assert fake.calls == []


# ---- equivalence ----


def f(file, summary, **kw):
    return {"file": file, "summary": summary, **kw}


def test_equivalence_identical_keys_no_call():
    fake = Fake()
    out = triage.equivalence({"prev": [f("a", "x")], "cur": [f("a", "x", sev=1)]}, runner=fake)
    assert out == {"repeated": [{"cur": f("a", "x", sev=1), "prev": f("a", "x")}]}
    assert fake.calls == []


def test_equivalence_remaining_batched_once():
    prev = [f("a", "x"), f("b", "null deref in parse")]
    cur = [f("a", "x"), f("b", "parse can dereference null"), f("c", "new thing")]
    fake = Fake({"pairs": [{"cur": 0, "prev": 0}]})
    out = triage.equivalence({"prev": prev, "cur": cur}, runner=fake)
    assert len(fake.calls) == 1
    assert {"cur": cur[1], "prev": prev[1]} in out["repeated"]
    assert {"cur": cur[0], "prev": prev[0]} in out["repeated"]
    assert len(out["repeated"]) == 2
    assert all(set(r) == {"cur", "prev"} for r in out["repeated"])


def test_equivalence_failure_keeps_key_equality_only():
    prev = [f("a", "x"), f("b", "y")]
    cur = [f("a", "x"), f("b", "y2")]
    out = triage.equivalence({"prev": prev, "cur": cur}, runner=Fake(code=1))
    assert out["repeated"] == [{"cur": cur[0], "prev": prev[0]}]
    assert "key equality only" in out["reason"]


def test_equivalence_success_has_no_reason():
    fake = Fake({"pairs": []})
    data = {"prev": [f("a", "x")], "cur": [f("b", "y")]}
    assert "reason" not in triage.equivalence(data, runner=fake)


def test_equivalence_bad_index_falls_back():
    prev, cur = [f("b", "y")], [f("b", "y2")]
    out = triage.equivalence(
        {"prev": prev, "cur": cur}, runner=Fake({"pairs": [{"cur": 5, "prev": 0}]})
    )
    assert out["repeated"] == []
    assert "key equality only" in out["reason"]


def test_equivalence_nothing_left_no_call():
    fake = Fake()
    assert triage.equivalence({"prev": [], "cur": [f("a", "x")]}, runner=fake) == {"repeated": []}
    assert fake.calls == []


# ---- log ----


def test_log_line_on_call_and_shortcut(tmp_path):
    log = tmp_path / "t.jsonl"
    triage.run(
        "tier", TIER_IN, runner=Fake({"classifierTier": "full", "reasons": ["r"]}), log=str(log)
    )
    triage.run("parking", [], runner=Fake(), log=str(log))
    first, second = log_lines(log)
    assert set(first) == {"ts", "mode", "inputHash", "output", "model", "ms", "error", "usage"}
    assert first["mode"] == "tier" and first["error"] is None
    assert first["output"]["classifierTier"] == "full"
    assert first["model"].startswith("claude-haiku")
    assert second["mode"] == "parking" and second["model"] is None and second["ms"] == 0
    assert first["inputHash"] != second["inputHash"]


def test_log_line_carries_usage(tmp_path):
    log = tmp_path / "t.jsonl"
    usage = {"input_tokens": 12, "output_tokens": 5}
    fake = Fake({"classifierTier": "full", "reasons": ["r"]}, usage=usage)
    triage.run("tier", TIER_IN, runner=fake, log=str(log))
    triage.run("parking", [], runner=Fake(), log=str(log))
    first, second = log_lines(log)
    assert first["usage"]["input_tokens"] == 12 and first["usage"]["output_tokens"] == 5
    assert second["usage"] is None


def test_run_sums_usage_into_the_given_accumulator():
    acc = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
    usage = {"input_tokens": 12, "output_tokens": 5}
    fake = Fake({"classifierTier": "full", "reasons": ["r"]}, usage=usage)
    triage.run("tier", TIER_IN, runner=fake, usage=acc)
    triage.run("tier", TIER_IN, runner=fake, usage=acc)
    triage.run("parking", [], runner=Fake(), usage=acc)
    assert acc == {"calls": 2, "input_tokens": 24, "output_tokens": 10}


def test_log_records_error(tmp_path):
    log = tmp_path / "t.jsonl"
    triage.run("tier", TIER_IN, runner=Fake(code=1, err="boom"), log=str(log))
    (line,) = log_lines(log)
    assert "boom" in line["error"]
    assert line["output"]["classifierTier"] == "skip"


def test_no_log_when_not_given(tmp_path):
    triage.run("parking", [], runner=Fake())
    assert list(tmp_path.iterdir()) == []


# ---- CLI ----


def cli(*args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "triage.py"), *args],
        capture_output=True,
        text=True,
        input=stdin,
    )


def test_cli_exit_zero_with_no_call_mode(tmp_path):
    inp = tmp_path / "in.json"
    inp.write_text("[]")
    log = tmp_path / "l.jsonl"
    r = cli("parking", "--input", str(inp), "--log", str(log))
    assert r.returncode == 0
    assert json.loads(r.stdout) == []
    assert len(log_lines(log)) == 1


def test_cli_reads_stdin_dash():
    r = cli("equivalence", "--input", "-", stdin='{"prev": [], "cur": []}')
    assert r.returncode == 0
    assert json.loads(r.stdout) == {"repeated": []}


def test_cli_bad_json_exit_2(tmp_path):
    inp = tmp_path / "in.json"
    inp.write_text("{nope")
    assert cli("tier", "--input", str(inp)).returncode == 2


@pytest.mark.parametrize("mode", ["tier", "ac-plausible", "parking", "equivalence"])
def test_cli_knows_every_mode(mode):
    assert cli(mode, "--help").returncode == 0


# ---- verify (one call for parking + ac-plausible + tier) ----

V_CANDS = [
    {"file": "a.py", "line": 1, "text": "# later"},
    {"file": "a.py", "line": 2, "text": "# explains"},
]
V_ACS = [{"id": "AC1", "text": "doc", "kind": "judgement", "ref": "", "snippet": "s", "met": None}]


def test_verify_mode_answers_all_three_parts():
    fake = Fake(
        {
            "parking": [{"index": 0, "reason": "defers"}],
            "acs": [{"id": "AC1", "verdict": "no", "reason": "r"}],
            "classifierTier": "panel",
        }
    )
    out = triage.verify({"parking": V_CANDS, "acs": V_ACS, "tier": TIER_IN}, runner=fake, meta={})
    assert len(fake.calls) == 1
    assert out["parking"] == [{**V_CANDS[0], "reason": "defers"}]
    assert out["acs"] == [{"id": "AC1", "verdict": "no", "reason": "r"}]
    assert out["classifierTier"] == "panel" and out["error"] is None


def test_verify_schema_covers_only_present_parts():
    fake = Fake({"classifierTier": "light"})
    out = triage.verify({"tier": TIER_IN}, runner=fake, meta={})
    schema = json.loads(fake.calls[0][0][fake.calls[0][0].index("--json-schema") + 1])
    assert list(schema["properties"]) == ["classifierTier"]
    assert out["parking"] == [] and out["acs"] == []


def test_verify_no_parts_makes_no_call():
    fake = Fake({})
    out = triage.verify({}, runner=fake, meta={})
    assert fake.calls == [] and out["classifierTier"] is None


def test_verify_failure_sets_error_and_flags_nothing():
    fake = Fake(None, code=1, err="boom")
    out = triage.verify({"parking": V_CANDS, "tier": TIER_IN}, runner=fake, meta={})
    assert "classifier failed" in out["error"]
    assert out["parking"] == [] and out["classifierTier"] is None
