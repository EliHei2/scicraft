#!/usr/bin/env python3
"""Count what the package holds: skills, lines, reference files, scripts, assets, eval cases and graders.

Usage:
    python3 tools/stats.py            # table on stdout
    python3 tools/stats.py --json     # machine-readable
    python3 tools/stats.py --extra ../other-package/plugins   # count another plugin folder too

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = {".py", ".js", ".mjs", ".sh"}


def count(plugin_dir: Path) -> dict:
    d = dict(skills=0, skill_md_lines=0, reference_files=0, reference_lines=0, scripts=0, script_lines=0,
             assets=0, eval_cases=0, graders=0, words=0)
    for skill in sorted(p.parent for p in plugin_dir.glob("skills/*/SKILL.md")):
        d["skills"] += 1
        text = (skill / "SKILL.md").read_text(errors="replace")
        d["skill_md_lines"] += len(text.splitlines())
        d["words"] += len(text.split())
        for f in skill.rglob("*"):
            if not f.is_file() or "__pycache__" in f.parts or f.name == ".DS_Store":
                continue
            rel = f.relative_to(skill).parts
            if rel[0] == "references" and f.suffix == ".md":
                t = f.read_text(errors="replace")
                d["reference_files"] += 1
                d["reference_lines"] += len(t.splitlines())
                d["words"] += len(t.split())
            elif rel[0] == "scripts" and f.suffix in CODE:
                d["scripts"] += 1
                d["script_lines"] += len(f.read_text(errors="replace").splitlines())
            elif rel[0] == "assets":
                d["assets"] += 1
            elif rel[0] == "evals" and f.name == "case.yaml":
                d["eval_cases"] += 1
            elif rel[0] == "evals" and f.parent.name == "graders":
                d["graders"] += 1
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--extra", type=Path, action="append", default=[], help="another plugins/ folder to include")
    a = ap.parse_args()
    rows = {}
    for base in [ROOT / "plugins", *a.extra]:
        for p in sorted(q for q in base.iterdir() if q.is_dir()):
            c = count(p)
            if c["skills"]:
                rows[p.name] = c
    total = {k: sum(r[k] for r in rows.values()) for k in next(iter(rows.values()))} if rows else {}
    if a.json:
        print(json.dumps({"plugins": rows, "total": total}, indent=2))
        return 0
    cols = ["skills", "skill_md_lines", "reference_files", "scripts", "script_lines", "assets", "eval_cases", "graders", "words"]
    print(f"{'plugin':16s}" + "".join(f"{c:>16s}" for c in cols))
    for name, r in list(rows.items()) + [("TOTAL", total)]:
        print(f"{name:16s}" + "".join(f"{r.get(c, 0):>16,d}" for c in cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
