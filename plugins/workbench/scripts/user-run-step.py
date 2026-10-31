#!/usr/bin/env python3
"""User-run step: check before, hand the user one command, parse the result back.

prepare <spec>  run each `pre` check, print PRE lines, then `! <command>` when all pass.
check <spec>    run each `post` check, match `expect` against combined output.

Spec is JSON: {name, command, pre: [cmd], post: [cmd], expect: <regex>}.
Checks must be read-only; a mutating check is rejected (exit 2) before anything runs.
"""

import argparse
import json
import re
import subprocess
import sys

TAIL = 20
# Redirects that write nothing: to /dev/null, or fd duplication like 2>&1.
SAFE_REDIRECT = re.compile(r"(?:&>|\d*>)\s*(?:/dev/null|&\d)(?![\w/.])")
MUTATING = re.compile(r">|\bsudo\b|\brm |\btee |\bdd ")
TIMEOUT = 300


def load(path):
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    for key in ("command", "pre", "post", "expect"):
        spec.setdefault(key, "" if key in ("command", "expect") else [])
    return spec


def reject_mutating(checks):
    bad = [c for c in checks if MUTATING.search(SAFE_REDIRECT.sub(" ", c))]
    for c in bad:
        print(f"REJECT not read-only: {c}", file=sys.stderr)
    return bool(bad)


def run_check(cmd):
    try:
        p = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {TIMEOUT}s\n"
    return p.returncode, p.stdout + p.stderr


def prepare(spec):
    if reject_mutating(spec["pre"]):
        return 2
    failed = False
    for cmd in spec["pre"]:
        code, _ = run_check(cmd)
        if code == 0:
            print(f"PRE ok {cmd}")
        else:
            print(f"PRE FAIL {cmd} exit {code}")
            failed = True
    if failed:
        return 1
    print(f"! {spec['command']}")
    return 0


def check(spec):
    if reject_mutating(spec["post"]):
        return 2
    out, reason = "", None
    for cmd in spec["post"]:
        code, text = run_check(cmd)
        out += text
        if code != 0 and reason is None:
            reason = f"check exited {code}: {cmd}"
    try:
        matched = re.search(spec["expect"], out, re.M) if spec["expect"] else True
    except re.error as exc:
        print(f"REJECT bad expect regex: {exc}", file=sys.stderr)
        return 2
    if reason is None and not matched:
        reason = f"expect /{spec['expect']}/ not found in output"
    print("RESULT pass" if reason is None else f"RESULT fail: {reason}")
    print("\n".join(out.splitlines()[-TAIL:]))
    return 0 if reason is None else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("action", choices=["prepare", "check"])
    ap.add_argument("spec")
    args = ap.parse_args(argv)
    spec = load(args.spec)
    return prepare(spec) if args.action == "prepare" else check(spec)


if __name__ == "__main__":
    sys.exit(main())
