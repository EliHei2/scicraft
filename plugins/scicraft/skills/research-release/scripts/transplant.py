#!/usr/bin/env python3
"""Copy the outputs of an executed notebook into a rebuild whose code cells are unchanged.

    python3 transplant.py executed.ipynb rebuilt.ipynb [--out result.ipynb]
    python3 transplant.py --self-test

Use it when only the markdown of a notebook source changed after the notebook was executed, so hours of compute
are not repeated for a typo. Code cells are compared by their exact source text, in order. When every code cell is
identical, the outputs, execution counts and notebook metadata of the executed notebook are copied into the
rebuild, which is written to --out (default: over the rebuild).

When the number of code cells or the text of any code cell differs, nothing is written, every differing cell is
listed, and the exit code is 1: execute the notebook again. Outputs are never copied by position across a changed
cell, because after one inserted cell every later output would land on the wrong code.

Exit 0 on success, 1 when code differs, 2 on bad arguments. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def code_cells(nb: dict) -> list:
    return [c for c in nb["cells"] if c.get("cell_type") == "code"]


def text(cell: dict) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else src


def differences(old: list, new: list) -> list:
    msgs = []
    if len(old) != len(new):
        msgs.append(f"executed notebook has {len(old)} code cells, rebuild has {len(new)}")
    for i, (a, b) in enumerate(zip(old, new)):
        if text(a) != text(b):
            first = (text(b).strip().splitlines() or [""])[0][:70]
            msgs.append(f"code cell {i + 1} changed (rebuild starts: {first!r})")
    return msgs


def transplant(executed: Path, rebuilt: Path, out: Path) -> int:
    old = json.loads(executed.read_text(encoding="utf-8"))
    new = json.loads(rebuilt.read_text(encoding="utf-8"))
    old_code, new_code = code_cells(old), code_cells(new)
    diffs = differences(old_code, new_code)
    if diffs:
        print("FAIL: code cells differ; execute the notebook again. Nothing written.", file=sys.stderr)
        for d in diffs:
            print("  " + d, file=sys.stderr)
        return 1
    for a, b in zip(old_code, new_code):
        b["outputs"], b["execution_count"] = a.get("outputs", []), a.get("execution_count")
    new["metadata"] = old.get("metadata", new.get("metadata", {}))
    out.write_text(json.dumps(new, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n_md = sum(c.get("cell_type") == "markdown" for c in new["cells"])
    print(f"OK: outputs of {len(new_code)} code cells copied into {out} ({n_md} markdown cells from the rebuild)")
    return 0


def _nb(cells: list) -> dict:
    return {"cells": cells, "metadata": {"kernelspec": {"name": "python3"}}, "nbformat": 4, "nbformat_minor": 5}


def _code(src: str, outputs=None, count=None) -> dict:
    return {"cell_type": "code", "source": src, "metadata": {}, "outputs": outputs or [], "execution_count": count}


def self_test() -> int:
    out1 = [{"output_type": "stream", "name": "stdout", "text": "42\n"}]
    executed = _nb([{"cell_type": "markdown", "source": "# Old titel", "metadata": {}},
                    _code("x = 6 * 7", count=1), _code("print(x)", out1, count=2)])
    fixed_typo = _nb([{"cell_type": "markdown", "source": "# Old title", "metadata": {}},
                      _code("x = 6 * 7"), _code("print(x)")])
    inserted = _nb([_code("x = 6 * 7"), _code("x += 1"), _code("print(x)")])
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "exec.ipynb").write_text(json.dumps(executed))
        (t / "typo.ipynb").write_text(json.dumps(fixed_typo))
        (t / "ins.ipynb").write_text(json.dumps(inserted))
        assert transplant(t / "exec.ipynb", t / "typo.ipynb", t / "out.ipynb") == 0
        res = json.loads((t / "out.ipynb").read_text())
        assert res["cells"][0]["source"] == "# Old title"
        assert res["cells"][2]["outputs"] == out1 and res["cells"][2]["execution_count"] == 2
        assert transplant(t / "exec.ipynb", t / "ins.ipynb", t / "out2.ipynb") == 1
        assert not (t / "out2.ipynb").exists()
    print("self-test passed")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("executed", nargs="?", type=Path, help="the notebook that was executed")
    ap.add_argument("rebuilt", nargs="?", type=Path, help="the rebuild from the edited source")
    ap.add_argument("--out", type=Path, help="where to write the result (default: over the rebuild)")
    ap.add_argument("--self-test", action="store_true", help="run on two small synthetic notebooks")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.executed or not args.rebuilt:
        ap.error("executed and rebuilt notebooks are required")
    return transplant(args.executed, args.rebuilt, args.out or args.rebuilt)


if __name__ == "__main__":
    sys.exit(main())
