#!/usr/bin/env python3
"""Build a Jupyter notebook from a percent-format Python source, as the paper build or the tutorial build.

    python3 nb_build.py nb_<topic>.py --out paper/<topic>.ipynb
    python3 nb_build.py nb_<topic>.py --out tutorials/<topic>.ipynb --tutorial
    python3 nb_build.py --self-test

Cells are separated by lines that start with `# %%`. A `# %% [markdown]` cell has its leading `# ` stripped. A
code cell header may carry `tags=["a", "b"]`, written to the cell metadata.

Flags are top-level lines of the form `PAPER_<NAME> = True|False` (inputs taken from the paper: canonical result
values, the paper's labels and thresholds) and `RUN_<NAME> = True|False` (the reader runs the method). The paper
build writes the source as it is. The tutorial build sets every `PAPER_*` flag to False and every `RUN_*` flag to
True, then asserts that no `PAPER_*` flag is still True, so a tutorial never shows paper values it did not compute.
Write the flag comments so they read true in both builds ("True uses the paper's thresholds").

Exit 0 on success, 1 when the tutorial assertion fails or the source has no cells, 2 on bad arguments.
Standard library only; output layout matches what nbformat writes (nbformat 4.5, indent 1).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

PAPER_FLAG = re.compile(r"^(PAPER_[A-Z0-9_]+)(\s*=\s*)(True|False)\b", re.M)
RUN_FLAG = re.compile(r"^(RUN_[A-Z0-9_]+)(\s*=\s*)(True|False)\b", re.M)


def to_tutorial(source: str) -> str:
    source = PAPER_FLAG.sub(lambda m: m.group(1) + m.group(2) + "False", source)
    source = RUN_FLAG.sub(lambda m: m.group(1) + m.group(2) + "True", source)
    still_on = [m.group(1) for m in PAPER_FLAG.finditer(source) if m.group(3) == "True"]
    if still_on:
        raise AssertionError("paper-only inputs still on: " + ", ".join(still_on))
    return source


def lines_of(text: str) -> list:
    """Notebook JSON stores cell source as a list of lines, each but the last ending in a newline."""
    return text.splitlines(keepends=True)


def build_cells(source: str) -> list:
    cells = []
    for block in re.split(r"^# %%", source.strip(), flags=re.M):
        if not block.strip():
            continue
        header, _, body = block.partition("\n")
        body = body.strip("\n")
        if "[markdown]" in header:
            text = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in body.splitlines())
            cells.append({"cell_type": "markdown", "metadata": {}, "source": lines_of(text)})
        else:
            meta = {}
            tags = re.search(r"tags=(\[.*\])", header)
            if tags:
                meta["tags"] = json.loads(tags.group(1))
            cells.append({"cell_type": "code", "execution_count": None, "metadata": meta,
                          "outputs": [], "source": lines_of(body)})
    for i, cell in enumerate(cells):
        cell["id"] = f"cell-{i:03d}"
    return cells


def build(source: str, out: Path, tutorial: bool) -> dict:
    if tutorial:
        source = to_tutorial(source)
    cells = build_cells(source)
    if not cells:
        raise ValueError("no cells found (cells start with '# %%')")
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(nb, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    flags = PAPER_FLAG.findall(source) + RUN_FLAG.findall(source)
    on = [name for name, _, value in flags if value == "True"]
    print(f"{out}: {len(cells)} cells ({sum(c['cell_type'] == 'code' for c in cells)} code), "
          f"{'tutorial' if tutorial else 'paper'} build, flags on: {', '.join(on) or 'none'}")
    return nb


SAMPLE = '''# %% [markdown]
# # Does the method recover the held-out labels?
# Run time: about 3 minutes on one GPU.

# %% tags=["parameters"]
RUN_METHOD = False  # True runs the method; False loads the released predictions
PAPER_THRESHOLDS = True  # True uses the thresholds printed in the paper

# %%
print(RUN_METHOD, PAPER_THRESHOLDS)
'''


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        src = SAMPLE
        paper = build(src, Path(tmp) / "paper.ipynb", tutorial=False)
        tut = build(src, Path(tmp) / "tutorial.ipynb", tutorial=True)
        assert [c["cell_type"] for c in paper["cells"]] == ["markdown", "code", "code"]
        assert paper["cells"][1]["metadata"]["tags"] == ["parameters"]
        assert paper["cells"][0]["source"][0] == "# Does the method recover the held-out labels?\n"
        code = "".join(tut["cells"][1]["source"])
        assert "RUN_METHOD = True" in code and "PAPER_THRESHOLDS = False" in code
        assert "PAPER_THRESHOLDS = True" in "".join(paper["cells"][1]["source"])
        json.loads((Path(tmp) / "tutorial.ipynb").read_text())
        assert to_tutorial("x = 1\n  PAPER_Y = True\n") == "x = 1\n  PAPER_Y = True\n"  # indented: not a flag
    print("self-test passed")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", nargs="?", type=Path, help="percent-format Python source (nb_<topic>.py)")
    ap.add_argument("--out", type=Path, help="notebook to write (.ipynb)")
    ap.add_argument("--tutorial", action="store_true", help="tutorial build: PAPER_* off, RUN_* on, asserted")
    ap.add_argument("--self-test", action="store_true", help="build a sample source both ways and check it")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.source or not args.out:
        ap.error("source and --out are required")
    try:
        build(args.source.read_text(encoding="utf-8"), args.out, args.tutorial)
    except (AssertionError, ValueError) as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
