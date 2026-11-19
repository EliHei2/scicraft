#!/usr/bin/env python3
"""List what the figure repository's documents owe: the input to a deferred doc sync.

Suggested, not yet tested in real work: the practice (a Synced flag per panel, swept on
request) is the author's; this scanner is an addition that automates the listing.

Reads PANEL_MAP.md and PROVENANCE.md at the repository root (layout in assets/repo/) and
reports:
  * panel rows whose Script or Output path does not exist on disk;
  * rows with Status draft, and rows with Synced "-" (the sync is owed);
  * panel, supplement and composer scripts under code/ that PANEL_MAP.md never names
    (in a row or in a generation block);
  * files under data/ that no PROVENANCE.md row names.

PANEL_MAP rows are markdown table rows whose header contains Script, Output, Status and
Synced columns. An Output cell may use a brace list: figures/f3/panels/a.{pdf,png}.

    python docs_status.py --repo .

Exit 1 if a named path is missing or a script or data file is undocumented. Owed syncs and
drafts are listed without failing. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CODE_RE = re.compile(r"`([^`]+)`")


def tables(md: str) -> list[tuple[list[str], list[list[str]]]]:
    out, header, rows = [], None, []
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if header:
                out.append((header, rows))
            header, rows = None, []
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
        elif not set("".join(cells)) <= set("-: "):
            rows.append(cells)
    if header:
        out.append((header, rows))
    return out


def expand(path: str) -> list[str]:
    m = re.search(r"\{([^}]+)\}", path)
    if not m:
        return [path]
    return [path[:m.start()] + alt + path[m.end():] for alt in m.group(1).split(",")]


def paths_in(cell: str) -> list[str]:
    found = CODE_RE.findall(cell) or [cell]
    return [p.strip() for p in found if "/" in p and " " not in p.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description="List undocumented scripts, missing outputs and owed doc syncs.")
    ap.add_argument("--repo", type=Path, default=Path("."), help="figure repository root")
    ap.add_argument("--code", default="code", help="folder holding panel scripts (default code)")
    ap.add_argument("--data", default="data", help="folder holding render inputs (default data)")
    a = ap.parse_args()
    repo = a.repo.resolve()
    pm, pv = repo / "PANEL_MAP.md", repo / "PROVENANCE.md"
    if not pm.is_file():
        sys.exit(f"no PANEL_MAP.md in {repo}")

    problems, owed, drafts, named = [], [], [], set()
    pm_text = pm.read_text()
    for header, rows in tables(pm_text):
        if not {"script", "output", "status", "synced"} <= set(header):
            continue
        ix = {h: i for i, h in enumerate(header)}
        for r in rows:
            if len(r) < len(header):
                continue
            panel = r[0]
            for col in ("script", "output"):
                for p in paths_in(r[ix[col]]):
                    for q in expand(p):
                        named.add(q)
                        if not (repo / q).exists():
                            problems.append(f"{panel}: {col} {q} does not exist")
            if r[ix["synced"]].strip() in ("-", "–", ""):
                owed.append(panel)
            if r[ix["status"]].strip().lower() == "draft":
                drafts.append(panel)

    code = repo / a.code
    if code.is_dir():
        for f in sorted(code.rglob("*.py")):
            n = f.name
            if "archive" in f.parts or "_prep" in f.parts or n.startswith(("_mockup", "_scratch")):
                continue
            if n.startswith(("panel_", "supp", "_compose")) and str(f.relative_to(repo)) not in pm_text:
                problems.append(f"script {f.relative_to(repo)} is not named in PANEL_MAP.md")

    data = repo / a.data
    if data.is_dir():
        prov = pv.read_text() if pv.is_file() else ""
        for f in sorted(p for p in data.rglob("*") if p.is_file() and not p.name.startswith(".")):
            rel = str(f.relative_to(repo))
            if rel not in prov and f.name not in prov:
                problems.append(f"data file {rel} has no PROVENANCE.md row")

    for p in problems:
        print(f"PROBLEM  {p}")
    print(f"sync owed (Synced = -): {', '.join(owed) or 'none'}")
    print(f"draft panels: {', '.join(drafts) or 'none'}")
    print("docs status passed" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
