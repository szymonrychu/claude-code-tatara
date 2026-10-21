#!/usr/bin/env python3
"""List all open PRs/MRs for a single code/ repo, classified by merge readiness.

Status codes:
  G - ready to merge
  C - conflicted
  R - pipeline/checks failed

Sorted oldest to newest. Exit 1 when any PR/MR is C or R.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

import common  # noqa: E402
import scm  # noqa: E402

DESC_TRUNC_LEN = 200


def classify(item: dict) -> str:
    """C over R over G, from an Adapter.list_open() item."""
    if item["mergeable"] == "conflict":
        return "C"
    if item["checks"] == "failed":
        return "R"
    return "G"


def truncate_description(body: str | None) -> str:
    body = (body or "").strip()
    if len(body) > DESC_TRUNC_LEN:
        return body[:DESC_TRUNC_LEN].rstrip() + "..."
    return body


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="submodule repo name")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        adapter = scm.adapter_for(args.repo)
        if adapter is None:
            print(f"local-only: no PR/MR host for {scm.origin_url(args.repo)}")
            sys.exit(0)
        items = adapter.list_open()
    except scm.HostMapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    except common.RepoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"{'URL':<60} {'ST':<4} DESCRIPTION")
    print(f"{'-' * 60} {'-' * 4} {'-' * 40}")
    any_bad = False
    for item in sorted(items, key=lambda i: i["created"]):
        status = classify(item)
        any_bad = any_bad or status in ("C", "R")
        print(f"{item['url']:<60} {status:<4} {truncate_description(item['body'])}")
    sys.exit(1 if any_bad else 0)


if __name__ == "__main__":
    main()
