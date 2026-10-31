#!/usr/bin/env bash
# doc_path.sh research <topic>: print (and create the dir of) the dated research brief path
# under docs/research.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=SCRIPTDIR/../../_lib/common.sh
source "$SCRIPT_DIR/../../_lib/common.sh"

USAGE="usage: doc_path.sh research <topic>"
KIND="${1-}"
TOPIC="${2-}"

if [ "$KIND" != research ]; then
  log_err "$USAGE"
  exit 1
fi

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
dir="$root/docs/research"
mkdir -p "$dir" || { log_err "could not create dir: $dir"; exit 1; }

echo "$dir/$(date +%F)-$slug.md"
