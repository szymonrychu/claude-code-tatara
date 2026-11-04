#!/usr/bin/env bash
# Create (or reuse) the pill render venv and print its python path.
#
# Usage: setup_venv.sh [VENV_DIR]
# VENV_DIR defaults to $PILL_VENV, else <workbench scratchpad>/pill/venv
# (workbench.py scratchpad pill). Installs the pinned pure-pip stack from
# requirements.txt: no pandoc, typst, LaTeX, chromium or pango needed.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv="${1:-${PILL_VENV:-}}"
if [ -z "$venv" ]; then
  scratch="$(python3 "$here/../../../scripts/lib/workbench.py" scratchpad pill)"
  venv="$scratch/venv"
fi

if [ ! -x "$venv/bin/python" ]; then
  python3 -m venv "$venv" >&2
fi
"$venv/bin/python" -m pip install --quiet --disable-pip-version-check -r "$here/requirements.txt" >&2
"$venv/bin/python" -c "import markdown, xhtml2pdf, svglib, reportlab" >&2
echo "$venv/bin/python"
