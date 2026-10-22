#!/usr/bin/env python3
"""Haiku triage for questions rules cannot settle; every mode is at most one batched call.

Modes (input JSON via --input FILE or -, output JSON on stdout, exit 0 on classifier failure):
  tier          {requirement, files, diffstat} -> {classifierTier, reasons[]}
  ac-plausible  [{id, text, kind, ref, snippet, met}] -> [{id, verdict, reason}]
  parking       [{file, line, text}] -> [{file, line, text, reason}]
                (--with-reason: {lines, reason}; reason set when the classifier failed)
  verify        {parking?: [..], acs?: [..], tier?: {..}} -> {parking, acs, classifierTier, error}
                (ONE call covering the parts present; failure: error set, nothing flagged)
  equivalence   {prev: [finding], cur: [finding]} -> {repeated: [{cur, prev}]}
  false-finding {findings: [finding], verification: {how, exit, tail}}
                -> {verdicts: [{index, verdict: false|real, reason}]}; failure: all real

The tier here is a hint only: the rule tier lives in plan-execute, which takes the higher
of the two, so this classifier can only upgrade. Failures fall back to the safe side.
--log appends {ts, mode, inputHash, output, model, ms, error, usage} per invocation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import claude_json  # noqa: E402
from claude_json import ClaudeJsonError  # noqa: E402

TIER_ORDER = ["skip", "light", "full", "panel"]
MODEL = "haiku"
MODES = ("tier", "ac-plausible", "parking", "verify", "equivalence", "false-finding")
GENERIC_TOKENS = {"test", "tests", "py", "js", "mjs", "sh", "the", "and", "for", "with"}


def _ask(prompt: str, schema: dict, runner, meta: dict):
    """One haiku call; fills meta {model, ms, usage}; raises ClaudeJsonError."""
    data, m = claude_json.call_with_meta(prompt, schema, model=MODEL, runner=runner)
    meta.update(model=m["model"], ms=m["ms"], usage=m["usage"])
    return data


def _obj(**props):
    return {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }


def _arr(item):
    return {"type": "array", "items": item}


_STR = {"type": "string"}
_INT = {"type": "integer", "minimum": 0}


def _fail(meta: dict, e: Exception) -> str:
    meta["error"] = str(e)
    return f"classifier failed: {e}"


def tier(data: dict, *, runner=None, meta: dict | None = None) -> dict:
    meta = {} if meta is None else meta
    schema = _obj(classifierTier={"type": "string", "enum": TIER_ORDER}, reasons=_arr(_STR))
    prompt = (
        "Classify how much review this change needs. Tiers, lowest to highest: "
        "skip (trivial, docs or formatting), light (small contained change), "
        "full (logic, several files, behaviour change), panel (security, data loss, "
        "concurrency, migrations, public contracts). Answer with the tier and short reasons.\n\n"
        f"Requirement:\n{data.get('requirement', '')}\n\n"
        f"Files:\n{json.dumps(data.get('files', []))}\n\nDiffstat:\n{data.get('diffstat', '')}\n"
    )
    try:
        out = _ask(prompt, schema, runner, meta)
    except ClaudeJsonError as e:
        return {"classifierTier": "skip", "reasons": [_fail(meta, e) + " (no upgrade)"]}
    return {"classifierTier": out["classifierTier"], "reasons": out["reasons"]}


def _tokens(s: str) -> set:
    return {
        t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) >= 3 and t not in GENERIC_TOKENS
    }


def _shortcut_yes(a: dict) -> bool:
    return (
        a.get("kind") in ("command", "test")
        and a.get("met") is True
        and bool(_tokens(a.get("ref", "")) & _tokens(a.get("text", "")))
    )


def ac_plausible(acs: list, *, runner=None, meta: dict | None = None) -> list:
    meta = {} if meta is None else meta
    verdicts = {
        a["id"]: {
            "id": a["id"],
            "verdict": "yes",
            "reason": "ref marked met and shares tokens with the AC text",
        }
        for a in acs
        if _shortcut_yes(a)
    }
    rest = [a for a in acs if a["id"] not in verdicts]
    if rest:
        schema = _obj(
            results=_arr(
                _obj(
                    id=_STR,
                    verdict={"type": "string", "enum": ["yes", "no", "unsure"]},
                    reason=_STR,
                )
            )
        )
        prompt = (
            "For each acceptance criterion, judge whether the evidence (kind, ref, snippet) "
            "plausibly covers the criterion text. Answer yes, no or unsure with a short reason, "
            "one result per id.\n\n"
            + json.dumps(
                [{k: a.get(k) for k in ("id", "text", "kind", "ref", "snippet")} for a in rest],
                indent=1,
            )
        )
        try:
            got = {r["id"]: r for r in _ask(prompt, schema, runner, meta)["results"]}
            failure = None
        except ClaudeJsonError as e:
            got, failure = {}, _fail(meta, e)
        for a in rest:
            r = got.get(a["id"])
            verdicts[a["id"]] = (
                {"id": a["id"], "verdict": r["verdict"], "reason": r["reason"]}
                if r
                else {
                    "id": a["id"],
                    "verdict": "unsure",
                    "reason": failure or "classifier gave no answer for this AC",
                }
            )
    return [verdicts[a["id"]] for a in acs]


class ParkingResult(list):
    """List of parked lines; `.reason` says why a failed classifier returned nothing."""

    reason: str | None = None


def parking(lines: list, *, runner=None, meta: dict | None = None) -> list:
    meta = {} if meta is None else meta
    if not lines:
        return ParkingResult()
    schema = _obj(lines=_arr(_obj(index=_INT, reason=_STR)))
    numbered = [
        {"index": i, "file": x["file"], "line": x["line"], "text": x["text"]}
        for i, x in enumerate(lines)
    ]
    prompt = (
        "These are lines added in a change (comments, docs, strings). Return only those that "
        "defer, park or postpone work (TODO, later, follow-up, not handled yet, out of scope, "
        "temporary workaround to revisit). Ordinary explanation is not parking. "
        "Give the index and a short reason.\n\n" + json.dumps(numbered, indent=1)
    )
    try:
        got = _ask(prompt, schema, runner, meta)["lines"]
    except ClaudeJsonError as e:
        res = ParkingResult()
        res.reason = f"{_fail(meta, e)}; no lines flagged"
        return res
    out, seen = ParkingResult(), set()
    for g in got:
        i = g["index"]
        if i < len(lines) and i not in seen:
            seen.add(i)
            out.append(
                {**{k: lines[i][k] for k in ("file", "line", "text")}, "reason": g["reason"]}
            )
    return out


_AC_VERDICT = {"type": "string", "enum": ["yes", "no", "unsure"]}


def verify(data: dict, *, runner=None, meta: dict | None = None) -> dict:
    """The parking, ac-plausible and tier questions in ONE haiku call; absent parts cost nothing.

    Returns {parking, acs, classifierTier, error}; classifierTier is None when no tier part was
    sent. On failure error names it, parking and acs are empty and classifierTier is None."""
    meta = {} if meta is None else meta
    cands = data.get("parking") or []
    acs = data.get("acs") or []
    tier_in = data.get("tier")
    shortcut = {
        a["id"]: {"id": a["id"], "verdict": "yes", "reason": "ref marked met and shares tokens"}
        for a in acs
        if _shortcut_yes(a)
    }
    rest = [a for a in acs if a["id"] not in shortcut]
    props, parts = {}, []
    if cands:
        props["parking"] = _arr(_obj(index=_INT, reason=_STR))
        parts.append(
            "PARKING: these are lines added in a change (comments, docs, strings). Return in "
            "`parking` only those that defer, park or postpone work (promises of later work, "
            "unhandled cases, scope disclaimers, temporary workarounds to revisit). Ordinary explanation "
            "is not parking. Give the index and a short reason.\n"
            + json.dumps(
                [
                    {"index": i, "file": x["file"], "line": x["line"], "text": x["text"]}
                    for i, x in enumerate(cands)
                ],
                indent=1,
            )
        )
    if rest:
        props["acs"] = _arr(_obj(id=_STR, verdict=_AC_VERDICT, reason=_STR))
        parts.append(
            "AC PLAUSIBILITY: for each acceptance criterion judge whether the evidence (kind, "
            "ref, snippet) plausibly covers the criterion text. Put one result per id in `acs`: "
            "yes, no or unsure with a short reason.\n"
            + json.dumps(
                [{k: a.get(k) for k in ("id", "text", "kind", "ref", "snippet")} for a in rest],
                indent=1,
            )
        )
    if tier_in is not None:
        props["classifierTier"] = {"type": "string", "enum": TIER_ORDER}
        parts.append(
            "TIER: classify how much review this change needs and put it in `classifierTier`. "
            "Tiers, lowest to highest: skip (trivial, docs or formatting), light (small contained "
            "change), full (logic, several files, behaviour change), panel (security, data loss, "
            "concurrency, migrations, public contracts).\n"
            f"Requirement:\n{tier_in.get('requirement', '')}\n"
            f"Files:\n{json.dumps(tier_in.get('files', []))}\n"
            f"Diffstat:\n{tier_in.get('diffstat', '')}"
        )
    out = {"parking": [], "acs": list(shortcut.values()), "classifierTier": None, "error": None}
    if not props:
        return out
    prompt = "Answer every part below in one structured answer.\n\n" + "\n\n".join(parts)
    schema = _obj(**props)
    try:
        got = _ask(prompt, schema, runner, meta)
    except ClaudeJsonError as e:
        out["error"] = _fail(meta, e)
        return out
    seen = set()
    for g in got.get("parking", []):
        i = g["index"]
        if i < len(cands) and i not in seen:
            seen.add(i)
            out["parking"].append(
                {**{k: cands[i][k] for k in ("file", "line", "text")}, "reason": g["reason"]}
            )
    for g in got.get("acs", []):
        out["acs"].append({"id": g["id"], "verdict": g["verdict"], "reason": g["reason"]})
    out["classifierTier"] = got.get("classifierTier")
    return out


def _key(f: dict) -> tuple:
    return (f.get("file"), f.get("summary"))


def equivalence(data: dict, *, runner=None, meta: dict | None = None) -> dict:
    meta = {} if meta is None else meta
    prev, cur = data.get("prev", []), data.get("cur", [])
    by_key = {}
    for p in prev:
        by_key.setdefault(_key(p), p)
    repeated = [{"cur": c, "prev": by_key[_key(c)]} for c in cur if _key(c) in by_key]
    left_cur = [c for c in cur if _key(c) not in by_key]
    cur_keys = {_key(c) for c in cur}
    left_prev = [p for p in prev if _key(p) not in cur_keys]
    if not left_cur or not left_prev:
        return {"repeated": repeated}
    schema = _obj(pairs=_arr(_obj(cur=_INT, prev=_INT)))
    prompt = (
        "Review findings from two consecutive rounds. List each current finding that reports "
        "the same underlying problem as a previous finding (same defect, same place, reworded). "
        "Different defects are not repeats. Answer with cur and prev indexes.\n\n"
        f"Previous:\n{json.dumps(list(enumerate(left_prev)), indent=1)}\n\n"
        f"Current:\n{json.dumps(list(enumerate(left_cur)), indent=1)}\n"
    )
    try:
        pairs = _ask(prompt, schema, runner, meta)["pairs"]
        if any(p["cur"] >= len(left_cur) or p["prev"] >= len(left_prev) for p in pairs):
            raise ClaudeJsonError("index out of range")
    except ClaudeJsonError as e:
        reason = f"{_fail(meta, e)}; key equality only"
        return {"repeated": repeated, "reason": reason}
    done = set()
    for p in pairs:
        if p["cur"] not in done:
            done.add(p["cur"])
            repeated.append({"cur": left_cur[p["cur"]], "prev": left_prev[p["prev"]]})
    return {"repeated": repeated}


def false_finding(data: dict, *, runner=None, meta: dict | None = None) -> dict:
    """Per-finding verdict: 'false' only when the verification output refutes it."""
    meta = {} if meta is None else meta
    findings = data.get("findings", [])
    if not findings:
        return {"verdicts": []}
    real = lambda i, why: {"index": i, "verdict": "real", "reason": why}  # noqa: E731
    schema = _obj(verdicts=_arr(_obj(index=_INT, verdict={"enum": ["false", "real"]}, reason=_STR)))
    prompt = (
        "A task passed its verification, yet a reviewer left these findings open. For each "
        "finding decide: 'false' only if the verification output below clearly shows the claim "
        "is wrong or already satisfied (or the finding is not a defect at all); 'real' if the "
        "output does not settle it or it may be a genuine defect. When unsure answer real. "
        "Give the index, the verdict and a short reason for every finding.\n\n"
        f"Verification: {json.dumps(data.get('verification', {}), indent=1)}\n\n"
        f"Findings:\n{json.dumps(list(enumerate(findings)), indent=1)}\n"
    )
    try:
        got = _ask(prompt, schema, runner, meta)["verdicts"]
    except ClaudeJsonError as e:
        why = f"{_fail(meta, e)}; treated as real"
        return {"verdicts": [real(i, why) for i in range(len(findings))]}
    by_index = {}
    for g in got:
        if isinstance(g.get("index"), int) and 0 <= g["index"] < len(findings):
            by_index.setdefault(g["index"], g)
    out = []
    for i in range(len(findings)):
        g = by_index.get(i)
        if g and g.get("verdict") in ("false", "real"):
            out.append({"index": i, "verdict": g["verdict"], "reason": g.get("reason") or ""})
        else:
            out.append(real(i, "no usable verdict; treated as real"))
    return {"verdicts": out}


_FUNCS = {
    "tier": tier,
    "ac-plausible": ac_plausible,
    "parking": parking,
    "verify": verify,
    "equivalence": equivalence,
    "false-finding": false_finding,
}


def run(mode: str, data, *, runner=None, log: str | None = None, usage: dict | None = None):
    """Run one mode, append one log line when `log` is given, return the output.

    `usage` ({calls, input_tokens, output_tokens}) accumulates the cost of the call, if one ran."""
    meta: dict = {}
    output = _FUNCS[mode](data, runner=runner, meta=meta)
    if usage is not None and meta.get("usage") is not None:
        usage["calls"] += 1
        for k in ("input_tokens", "output_tokens"):
            usage[k] += meta["usage"].get(k) or 0
    if log:
        line = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": mode,
            "inputHash": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16],
            "output": output,
            "model": meta.get("model"),
            "ms": meta.get("ms", 0),
            "error": meta.get("error"),
            "usage": meta.get("usage"),
        }
        with open(log, "a") as fh:
            fh.write(json.dumps(line) + "\n")
    return output


def render(mode: str, output, *, with_reason: bool = False):
    """Parking is a bare list; with_reason wraps it as {lines, reason} so a failure is visible."""
    if mode == "parking" and with_reason:
        return {"lines": list(output), "reason": output.reason}
    return output


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("mode", choices=MODES)
    ap.add_argument("--input", required=True, help="JSON file, or - for stdin")
    ap.add_argument("--log", help="JSONL file to append one line to")
    ap.add_argument(
        "--with-reason",
        action="store_true",
        help="parking only: print {lines, reason} so a classifier failure is visible",
    )
    args = ap.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        print(f"triage: bad input: {e}", file=sys.stderr)
        return 2
    out = run(args.mode, data, log=args.log)
    print(json.dumps(render(args.mode, out, with_reason=args.with_reason)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
