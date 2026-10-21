#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=SCRIPTDIR/../../_lib/common.sh
source "$SCRIPT_DIR/../../_lib/common.sh"

usage() {
  echo "usage: push.sh --branch <branch> [--repos a,b]" >&2
  exit 2
}

BRANCH=""
REPOS_ARG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --repos)
      REPOS_ARG="$2"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

[ -z "$BRANCH" ] && usage

if [ -n "$REPOS_ARG" ]; then
  REPOS="$(echo "$REPOS_ARG" | tr ',' '\n')"
else
  REPOS="$(all_repos)" || {
    log_err "failed to list repos"
    exit 1
  }
fi

for repo in $REPOS; do
  path="$(worktree_path "$BRANCH" "$repo")"
  if ! git -C "$path" rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    report_add "$repo" failed "no worktree at $path"
    continue
  fi

  push_err="$(git -C "$path" push -u origin "$BRANCH" 2>&1 1>/dev/null)"
  push_status=$?
  if [ "$push_status" -ne 0 ]; then
    report_add "$repo" failed "$push_err"
  else
    report_add "$repo" ok "pushed $BRANCH to origin"
  fi
done

report_print
if report_failed; then
  exit 1
fi
exit 0
