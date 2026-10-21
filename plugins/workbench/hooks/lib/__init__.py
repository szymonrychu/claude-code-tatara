"""Harness-neutral hook logic shared by the Claude entry scripts and the harness adapter.

This is a regular package (it has this `__init__.py`) on purpose: a regular
package wins over any namespace directory named `lib` elsewhere on `sys.path`,
such as `plugins/workbench/scripts/lib`. Stdlib only, Python 3.9+.
"""
