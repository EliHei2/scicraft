#!/usr/bin/env python3
"""Write a Jupyter notebook from a list of cells, so the notebook is never edited by hand.

  build_notebook.py CELLS.py --out <pkg>.ipynb [--accelerator GPU --gpu-type T4]
  build_notebook.py CELLS.py --out run_full.ipynb --replace "QUICK = True" "QUICK = False"
  build_notebook.py --self-test

CELLS.py is a Python file that defines CELLS, a list of ("md" | "code", source) pairs, for example

  CELLS = [
      ("md", "## 1. Parameters"),
      ("code", 'QUICK = True\\ncfg = preset("quick" if QUICK else "full")'),
      ("md", "## 2. Data"),
      ("code", 'with section("data", st) as s:\\n    s.update(pkg.data.build(cfg, st))'),
  ]

Markdown cells hold section titles; code cells hold one call into the package each. --replace OLD NEW
(repeatable) substitutes text in code cells, the way a full-run script derives its notebook from the
one that is shipped; each OLD must occur at least once or the build fails. --accelerator and
--gpu-type write the hosted service's metadata so the notebook opens ready to run there. The output
is nbformat 4 JSON written with the standard library; no cell carries outputs. Regenerate after
every package change, and list a derived notebook in .gitignore.

Exits 1 when CELLS is missing or malformed, or a --replace text is not found.
"""
from __future__ import annotations

import argparse
import json
import runpy
import sys
import tempfile
from pathlib import Path


def _lines(src: str) -> list:
    parts = src.split("\n")
    return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def build(cells: list, replace: list = (), accelerator: str | None = None, gpu_type: str | None = None) -> dict:
    if not isinstance(cells, list) or not cells:
        raise ValueError("CELLS must be a non-empty list of (kind, source) pairs")
    hits = {old: 0 for old, _ in replace}
    out = []
    for n, cell in enumerate(cells):
        if not (isinstance(cell, (list, tuple)) and len(cell) == 2 and cell[0] in ("md", "code")
                and isinstance(cell[1], str)):
            raise ValueError(f"cell {n}: expected ('md' or 'code', source string), got {cell!r}")
        kind, src = cell
        if kind == "code":
            for old, new in replace:
                hits[old] += src.count(old)
                src = src.replace(old, new)
            out.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
                        "source": _lines(src)})
        else:
            out.append({"cell_type": "markdown", "metadata": {}, "source": _lines(src)})
    missing = [old for old, k in hits.items() if k == 0]
    if missing:
        raise ValueError(f"--replace text not found in any code cell: {missing}")
    meta = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"}}
    if accelerator:
        meta["accelerator"] = accelerator
    if gpu_type:
        meta["colab"] = {"provenance": [], "gpuType": gpu_type}
    return {"cells": out, "metadata": meta, "nbformat": 4, "nbformat_minor": 5}


def write(nb: dict, path: Path) -> None:
    for k, c in enumerate(nb["cells"]):
        c["id"] = f"cell-{k:03d}"  # stable ids keep diffs of a regenerated notebook small
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> int:
    cells = [("md", "## 1. Parameters"), ("code", "QUICK = True\nprint(QUICK)"), ("md", "## 2. Run"),
             ("code", "x = 1")]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "nb.ipynb"
        write(build(cells, [("QUICK = True", "QUICK = False")], "GPU", "T4"), p)
        nb = json.loads(p.read_text(encoding="utf-8"))
        checks = {
            "four cells, kinds kept": [c["cell_type"] for c in nb["cells"]] == ["markdown", "code", "markdown", "code"],
            "substitution applied": "".join(nb["cells"][1]["source"]) == "QUICK = False\nprint(QUICK)",
            "no outputs": all(c.get("outputs", []) == [] for c in nb["cells"]),
            "host metadata": nb["metadata"].get("accelerator") == "GPU" and nb["metadata"]["colab"]["gpuType"] == "T4",
            "nbformat 4.5 with cell ids": nb["nbformat"] == 4 and all("id" in c for c in nb["cells"]),
        }
        try:
            build(cells, [("NOT THERE", "x")])
            checks["missing replace text fails"] = False
        except ValueError:
            checks["missing replace text fails"] = True
        try:
            build([("python", "x")])
            checks["bad cell kind fails"] = False
        except ValueError:
            checks["bad cell kind fails"] = True
    for name, ok in checks.items():
        print(("ok    " if ok else "FAIL  ") + name)
    bad = sum(not v for v in checks.values())
    print(f"{len(checks) - bad} of {len(checks)} checks passed")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cells", nargs="?", type=Path, help="Python file that defines CELLS")
    ap.add_argument("--out", type=Path, help="notebook to write")
    ap.add_argument("--replace", nargs=2, action="append", default=[], metavar=("OLD", "NEW"),
                    help="substitute text in code cells (repeatable)")
    ap.add_argument("--accelerator", help="hosted-notebook accelerator metadata, e.g. GPU")
    ap.add_argument("--gpu-type", help="hosted-notebook GPU type metadata, e.g. T4")
    ap.add_argument("--self-test", action="store_true", help="build a toy notebook and check it")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.cells or not a.out:
        ap.error("CELLS.py and --out are required (or --self-test)")
    try:
        cells = runpy.run_path(str(a.cells)).get("CELLS")
        nb = build(cells, [tuple(r) for r in a.replace], a.accelerator, a.gpu_type)
    except (ValueError, OSError, SyntaxError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    write(nb, a.out)
    n_code = sum(c["cell_type"] == "code" for c in nb["cells"])
    print(f"wrote {a.out}: {len(nb['cells'])} cells ({n_code} code), {len(a.replace)} substitution(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
