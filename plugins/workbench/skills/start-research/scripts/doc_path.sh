#!/usr/bin/env bash
# doc_path.sh <kind> <topic>: print (and create the dir of) the dated doc path.
# kinds: design, plan, record (.md), tasks, approvals (.json) under docs/plans; research under docs/research.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=SCRIPTDIR/../../_lib/common.sh
source "$SCRIPT_DIR/../../_lib/common.sh"

USAGE="usage: doc_path.sh <design|plan|tasks|approvals|record|research> <topic>"
KIND="${1-}"
TOPIC="${2-}"

case "$KIND" in
  design|plan|record) ext=md; sub=plans ;;
  tasks|approvals) ext=json; sub=plans ;;
  research) ext=md; sub=research ;;
  *) log_err "$USAGE"; exit 1 ;;
esac

if [ -z "$TOPIC" ]; then
  log_err "$USAGE"
  exit 1
fi

slug="$(slugify "$TOPIC")"
if [ -z "$slug" ]; then
  log_err "topic produced an empty slug: $TOPIC"
  log_err "$USAGE"
  exit 1
fi

root="$(docs_root)" || exit 1
dir="$root/docs/$sub"
mkdir -p "$dir" || { log_err "could not create dir: $dir"; exit 1; }

if [ "$KIND" = research ]; then
  echo "$dir/$(date +%F)-$slug.$ext"
else
  echo "$dir/$(date +%F)-$slug-$KIND.$ext"
fi
