#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=SCRIPTDIR/../../_lib/common.sh
source "$SCRIPT_DIR/../../_lib/common.sh"

REPOS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repos)
      REPOS="$2"
      shift 2
      ;;
    --repos=*)
      REPOS="${1#--repos=}"
      shift
      ;;
    *)
      log_err "unknown argument: $1"
      exit 1
      ;;
  esac
done

if [ -z "$REPOS" ]; then
  REPOS="$(all_repos | tr '\n' ',' | sed 's/,$//')"
fi

OLD_IFS="$IFS"
IFS=','
# shellcheck disable=SC2086
set -- $REPOS
IFS="$OLD_IFS"

for name in "$@"; do
  [ -z "$name" ] && continue

  if ! path="$(resolve_repo "$name" 2>&1)"; then
    report_add "$name" failed "$path"
    continue
  fi

  branch="$(tracked_branch "$name")"

  if ! old_sha="$(git -C "$path" rev-parse --short HEAD 2>&1)"; then
    report_add "$name" failed "not a git checkout: $old_sha"
    continue
  fi

  if ! fetch_out="$(git -C "$path" fetch origin 2>&1)"; then
    report_add "$name" failed "fetch failed: $fetch_out"
    continue
  fi

  if ! merge_out="$(git -C "$path" merge --ff-only "origin/$branch" 2>&1)"; then
    report_add "$name" failed "non-fast-forward: $merge_out"
    continue
  fi

  new_sha="$(git -C "$path" rev-parse --short HEAD 2>&1)"
  if [ "$old_sha" = "$new_sha" ]; then
    report_add "$name" ok "up to date ($old_sha)"
  else
    report_add "$name" ok "$old_sha -> $new_sha"
  fi
done

report_print

if report_failed; then
  exit 1
fi
exit 0
