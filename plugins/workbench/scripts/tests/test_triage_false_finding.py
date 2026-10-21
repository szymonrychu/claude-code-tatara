"""triage.py false-finding: one batched call, per-finding verdicts, safe side on failure."""

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
import triage  # noqa: E402


class Fake:
    def __init__(self, answer=None, code=0):
        self.answer, self.code, self.calls = answer, code, []

    def __call__(self, argv, stdin, env, timeout):
        self.calls.append((argv, stdin))
        env_json = {
            "is_error": False,
            "structured_output": self.answer,
            "modelUsage": {"claude-haiku-5-5": {}},
            "usage": {},
        }
        return self.code, json.dumps(env_json), ""


FINDINGS = [
    {"file": "a.py", "summary": "claims x is broken"},
    {"file": "b.py", "summary": "missing null check"},
]
VERIFY = {"how": "pytest -q", "exit": 0, "tail": "12 passed"}


def test_false_finding_mode():
    out = triage.false_finding({"findings": FINDINGS, "verification": VERIFY}, runner=Fake(code=1))
    assert [v["verdict"] for v in out["verdicts"]] == ["real", "real"]
    ok = triage.false_finding(
        {"findings": FINDINGS[:1], "verification": VERIFY},
        runner=Fake({"verdicts": [{"index": 0, "verdict": "false", "reason": "r"}]}),
    )
    assert ok["verdicts"] == [{"index": 0, "verdict": "false", "reason": "r"}]


def test_false_finding_verdicts_pass_through():
    fake = Fake(
        {
            "verdicts": [
                {"index": 0, "verdict": "false", "reason": "tail shows pass"},
                {"index": 1, "verdict": "real", "reason": "not covered"},
            ]
        }
    )
    out = triage.false_finding({"findings": FINDINGS, "verification": VERIFY}, runner=fake)
    assert len(fake.calls) == 1
    assert out["verdicts"] == [
        {"index": 0, "verdict": "false", "reason": "tail shows pass"},
        {"index": 1, "verdict": "real", "reason": "not covered"},
    ]


def test_false_finding_missing_verdict_is_real():
    fake = Fake({"verdicts": [{"index": 0, "verdict": "false", "reason": "r"}]})
    out = triage.false_finding({"findings": FINDINGS, "verification": VERIFY}, runner=fake)
    assert [v["verdict"] for v in out["verdicts"]] == ["false", "real"]
    assert [v["index"] for v in out["verdicts"]] == [0, 1]


def test_false_finding_failure_all_real():
    out = triage.false_finding({"findings": FINDINGS, "verification": VERIFY}, runner=Fake(code=1))
    assert [v["verdict"] for v in out["verdicts"]] == ["real", "real"]
    assert all(v["reason"] for v in out["verdicts"])


def test_false_finding_bad_verdict_value_is_real():
    fake = Fake({"verdicts": [{"index": 0, "verdict": "maybe", "reason": "r"}]})
    out = triage.false_finding({"findings": FINDINGS[:1], "verification": VERIFY}, runner=fake)
    assert out["verdicts"][0]["verdict"] == "real"


def test_false_finding_no_findings_no_call():
    fake = Fake()
    out = triage.false_finding({"findings": [], "verification": VERIFY}, runner=fake)
    assert out == {"verdicts": []}
    assert fake.calls == []


def test_false_finding_cli_mode(tmp_path):
    assert "false-finding" in triage.MODES
    p = tmp_path / "in.json"
    p.write_text(json.dumps({"findings": [], "verification": VERIFY}))
    assert triage.main(["false-finding", "--input", str(p)]) == 0
