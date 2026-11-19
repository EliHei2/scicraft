#!/usr/bin/env python3
"""Strip notebook outputs down to what a reader needs: stdout text, tables and images.

    python3 clean_notebook_outputs.py <notebook.ipynb> [...] [--check]

Drops stderr streams (progress bars, warnings), error tracebacks, execution counts, widget state and the
collapsed/scrolled cell flags. Keeps stdout and the text/plain, text/html, image/png, image/jpeg and image/svg+xml
parts of results. With --check nothing is written and the exit code is 1 when a notebook would change, so it can
run as a pre-commit hook or a release gate.

Standard library only (the notebook is written back with indent 1 and sorted keys, as nbformat writes it).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KEEP_STREAM_NAMES = {"stdout"}
KEEP_DATA_KEYS = {"text/plain", "text/html", "image/png", "image/jpeg", "image/svg+xml"}


def keep_output(output: dict) -> bool:
    kind = output.get("output_type")
    if kind == "stream":
        return output.get("name") in KEEP_STREAM_NAMES
    if kind in ("execute_result", "display_data"):
        data = {k: v for k, v in output.get("data", {}).items() if k in KEEP_DATA_KEYS}
        if not data:
            return False
        output["data"] = data
        output["metadata"] = {}
        if kind == "execute_result":
            output["execution_count"] = None
        return True
    return False  # "error" outputs (tracebacks)


def clean(nb: dict) -> dict:
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        cell["execution_count"] = None
        cell["outputs"] = [o for o in cell.get("outputs", []) if keep_output(o)]
        cell.get("metadata", {}).pop("collapsed", None)
        cell.get("metadata", {}).pop("scrolled", None)
    nb.get("metadata", {}).pop("widgets", None)
    return nb


def dump(nb: dict) -> str:
    return json.dumps(nb, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notebooks", nargs="+", type=Path)
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if a notebook would change")
    a = ap.parse_args()
    changed = 0
    for path in a.notebooks:
        before = path.read_text(encoding="utf-8")
        after = dump(clean(json.loads(before)))
        if json.loads(before) != json.loads(after):
            changed += 1
            print(f"{'would clean' if a.check else 'cleaned'}: {path}")
            if not a.check:
                path.write_text(after, encoding="utf-8")
        else:
            print(f"clean already: {path}")
    print(f"{len(a.notebooks)} notebook(s), {changed} {'to clean' if a.check else 'cleaned'}")
    return 1 if a.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
