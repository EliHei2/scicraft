#!/usr/bin/env python3
"""Plan mining slices from a digest folder: group chunks by source, pack them under a size budget per miner.

A source is one project's prompt history (history/history__<project>_NNN.md) or one session
(sessions/<project>/<session8>_NNN.md). A source larger than the budget is split into parts of
consecutive chunks ("part 2 of 4"); smaller sources of the same kind and project are packed together.
The output is a Markdown table to paste into the plan, plus optional JSON for a brief generator.

Usage:
    python3 plan_slices.py DIGEST_DIR [--budget-kb 420] [--json slices.json] [--min-kb 0]

The 420 KB default is the largest slice one miner read fully in the build this skill came from
(seven 60 KB chunks). Sources under --min-kb are listed as skipped, never dropped silently.
Standard library only. Exit code 1 when the folder holds no digest chunks.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CHUNK_RE = re.compile(r"^(?P<stem>.+)_(?P<idx>\d{3})\.md$")


def sources(root: Path) -> list[dict]:
    found: dict[tuple, dict] = {}
    for f in sorted(root.rglob("*.md")):
        m = CHUNK_RE.match(f.name)
        if not m:
            continue
        rel = f.relative_to(root)
        if rel.parts[0] == "history":
            kind, project = "history", m.group("stem").replace("history__", "", 1)
        elif rel.parts[0] == "sessions" and len(rel.parts) >= 3:
            kind, project = "session", rel.parts[1]
        else:
            continue
        key = (kind, project, m.group("stem"))
        s = found.setdefault(key, dict(kind=kind, project=project, stem=m.group("stem"), files=[], kb=0.0))
        s["files"].append((int(m.group("idx")), str(rel), f.stat().st_size / 1024))
    out = []
    for s in found.values():
        s["files"].sort()
        s["kb"] = sum(k for _, _, k in s["files"])
        out.append(s)
    return sorted(out, key=lambda s: (s["kind"], s["project"], s["stem"]))


def split(s: dict, budget: float) -> list[dict]:
    if s["kb"] <= budget:
        return [dict(s, part="")]
    parts, cur, size = [], [], 0.0
    for item in s["files"]:
        if cur and size + item[2] > budget:
            parts.append(cur)
            cur, size = [], 0.0
        cur.append(item)
        size += item[2]
    if cur:
        parts.append(cur)
    if len(parts) == 1:
        return [dict(s, part="")]
    return [dict(s, files=p, kb=sum(k for _, _, k in p), part=f"part {i} of {len(parts)}")
            for i, p in enumerate(parts, 1)]


def pack(units: list[dict], budget: float) -> list[list[dict]]:
    slices: list[list[dict]] = []
    for u in units:
        last = slices[-1] if slices else None
        if (last and not u["part"] and not last[0]["part"] and last[0]["kind"] == u["kind"]
                and last[0]["project"] == u["project"] and sum(x["kb"] for x in last) + u["kb"] <= budget):
            last.append(u)
        else:
            slices.append([u])
    return slices


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("digest_dir", type=Path)
    ap.add_argument("--budget-kb", type=float, default=420, help="most KB one miner reads fully (default 420)")
    ap.add_argument("--min-kb", type=float, default=0, help="list sources smaller than this as skipped")
    ap.add_argument("--json", type=Path, help="also write the plan as JSON")
    a = ap.parse_args()
    srcs = sources(a.digest_dir)
    if not srcs:
        print(f"no digest chunks (name_NNN.md under history/ or sessions/) in {a.digest_dir}", file=sys.stderr)
        return 1
    skipped = [s for s in srcs if s["kb"] < a.min_kb]
    units = [u for s in srcs if s["kb"] >= a.min_kb for u in split(s, a.budget_kb)]
    plan = pack(units, a.budget_kb)
    rows = []
    print("| slice | kind | project | sources | files | KB |")
    print("|---|---|---|---|---|---|")
    for i, sl in enumerate(plan, 1):
        sid = ("H" if sl[0]["kind"] == "history" else "S") + str(i)
        names = ", ".join(u["stem"] + (f" ({u['part']})" if u["part"] else "") for u in sl)
        files = [f for u in sl for _, f, _ in u["files"]]
        kb = sum(u["kb"] for u in sl)
        print(f"| {sid} | {sl[0]['kind']} | {sl[0]['project']} | {names} | {len(files)} | {kb:.0f} |")
        rows.append(dict(slice=sid, kind=sl[0]["kind"], project=sl[0]["project"], files=files, kb=round(kb, 1)))
    total = sum(s["kb"] for s in srcs)
    print(f"\n{len(plan)} slice(s) from {len(srcs)} source(s), {total:.0f} KB in all, budget {a.budget_kb:g} KB.")
    if skipped:
        print(f"skipped below {a.min_kb:g} KB: " + ", ".join(f"{s['stem']} ({s['kb']:.0f} KB)" for s in skipped))
    print("Memory notes, repositories and existing skills are not in digests: plan those slices by hand.")
    if a.json:
        a.json.write_text(json.dumps(dict(budget_kb=a.budget_kb, slices=rows,
                                          skipped=[s["stem"] for s in skipped]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
