#!/usr/bin/env python3
"""Coverage audit of a skill package against its findings: write one auditor brief per findings file, then aggregate.

  write      BRIEFS/C_<code>.md for every FINDINGS/<code>_*.md (the code is the part before the first "_").
  aggregate  read COVERAGE/<code>.md files written by the auditors, count COVERED / PARTIAL / MISSING /
             EXCLUDED rows, compute the covered share of in-scope items (excluded rows left out), and
             collect the proposed additions per skill into COVERAGE/_additions_<skill>.md plus
             COVERAGE/_SUMMARY.md. Findings files without a coverage file are listed as not audited.
             Every "## Contradictions and leaks" section is collected into COVERAGE/_CONFLICTS.md, one
             line per bullet with its source, for the one reconciler who settles them before repair.

Usage:
    python3 coverage.py write --findings DIR --briefs DIR --coverage DIR --package-root DIR [--package-root DIR ...]
                              --contract FILE --package NAME --requirement TEXT [--skip G1,X9]
    python3 coverage.py aggregate --findings DIR --coverage DIR [--skip G1,X9]

The brief template is assets/coverage_brief.md (override with --template). Standard library only.
Exit code 1 when nothing was found to write or aggregate.
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROW = re.compile(r"^\|\s*([A-Za-z][\w.-]*)\s*\|\s*(COVERED|PARTIAL|MISSING|EXCLUDED)\b", re.M)


def codes(findings: Path, skip: tuple) -> dict:
    out = {}
    for f in sorted(findings.glob("*.md")):
        code = f.stem.split("_")[0]
        if code not in skip:
            out[code] = f
    return out


def write(a) -> int:
    tpl = a.template.read_text()
    found = codes(a.findings, a.skip)
    if not found:
        print(f"no findings files in {a.findings}", file=sys.stderr)
        return 1
    a.briefs.mkdir(parents=True, exist_ok=True)
    roots = ", ".join(f"`{r}`" for r in a.package_root)
    for code, f in found.items():
        text = tpl.format(package=a.package, requirement=a.requirement, findings_file=f, package_roots=roots,
                          contract=a.contract, out_file=a.coverage / f"{code}.md", code=code)
        (a.briefs / f"C_{code}.md").write_text(text)
    print(f"{len(found)} coverage briefs written to {a.briefs}")
    print('Launch one fresh agent per brief: "Read your full assignment at <brief> and carry it out exactly."')
    return 0


def aggregate(a) -> int:
    tot = collections.Counter()
    per_skill = collections.defaultdict(list)
    per_file = []
    conflicts = []
    files = [f for f in sorted(a.coverage.glob("*.md")) if not f.name.startswith("_")]
    if not files:
        print(f"no coverage files in {a.coverage}", file=sys.stderr)
        return 1
    for f in files:
        t = f.read_text(errors="replace")
        code = f.stem
        c = collections.Counter(m.group(2) for m in ROW.finditer(t))
        tot.update(c)
        per_file.append((code, c))
        add = t.split("## Additions", 1)[1].split("## Contradictions", 1)[0] if "## Additions" in t else ""
        for block in re.split(r"(?m)^### ", add)[1:]:
            head, _, body = block.partition("\n")
            skill = head.split("/")[0].strip().strip("`")
            if body.strip():
                per_skill[skill].append(f"<!-- from {code}: {head.strip()} -->\n{body.strip()}\n")
        if "## Contradictions" in t:
            sec = re.split(r"(?m)^## ", t.split("## Contradictions", 1)[1])[0]
            for line in sec.splitlines()[1:]:
                s = line.strip()
                if s.startswith(("-", "*")) and len(s.lstrip("-* ").strip()) > 0:
                    if s.lstrip("-* ").strip().lower().rstrip(".") not in ("none", "n/a"):
                        conflicts.append(f"- [{code}] {s.lstrip('-* ').strip()}")
    done = tot["COVERED"] + tot["PARTIAL"] + tot["MISSING"]
    pct = 100 * tot["COVERED"] / done if done else 0
    lines = ["# Coverage summary", "",
             f"covered {tot['COVERED']}, partial {tot['PARTIAL']}, missing {tot['MISSING']}, "
             f"excluded {tot['EXCLUDED']}; covered share of in-scope items: {pct:.1f}%", "",
             "| findings | covered | partial | missing | excluded |", "|---|---|---|---|---|"]
    for code, c in per_file:
        lines.append(f"| {code} | {c['COVERED']} | {c['PARTIAL']} | {c['MISSING']} | {c['EXCLUDED']} |")
    empty = [code for code, c in per_file if not sum(c.values())]
    audited = {code for code, _ in per_file}
    missing = [code for code in codes(a.findings, a.skip) if code not in audited] if a.findings else []
    lines.append("")
    if empty:
        lines.append("coverage files with no item rows (auditor died or ignored the format): " + ", ".join(empty))
    if missing:
        lines.append("findings files never audited: " + ", ".join(missing))
    lines += ["", "## Additions per skill", ""]
    for skill, blocks in sorted(per_skill.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- {skill}: {len(blocks)} addition block(s), in `_additions_{skill}.md`")
        (a.coverage / f"_additions_{skill}.md").write_text(f"# Additions proposed for {skill}\n\n" + "\n".join(blocks))
    lines += ["", f"contradictions and leaks reported: {len(conflicts)}, in `_CONFLICTS.md` "
              "(settle them all in one reconciliation before any gap fill)"]
    (a.coverage / "_CONFLICTS.md").write_text(
        "# Contradictions and leaks reported by the auditors\n\n"
        "One ruling per contradiction, applied to every skill it names, before any gap-fill agent starts.\n\n"
        + ("\n".join(conflicts) if conflicts else "(none reported)") + "\n")
    (a.coverage / "_SUMMARY.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:60]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="write one auditor brief per findings file")
    w.add_argument("--findings", type=Path, required=True)
    w.add_argument("--briefs", type=Path, required=True)
    w.add_argument("--coverage", type=Path, required=True, help="folder the auditors write into")
    w.add_argument("--package-root", type=Path, action="append", required=True)
    w.add_argument("--contract", type=Path, required=True)
    w.add_argument("--package", required=True, help="package name")
    w.add_argument("--requirement", required=True, help="the author's coverage requirement, in their words")
    w.add_argument("--template", type=Path, default=HERE.parent / "assets" / "coverage_brief.md")
    g = sub.add_parser("aggregate", help="count statuses and collect additions per skill")
    g.add_argument("--coverage", type=Path, required=True)
    g.add_argument("--findings", type=Path, help="to list findings files that were never audited")
    for p in (w, g):
        p.add_argument("--skip", default="", help="comma-separated findings codes to leave out")
    a = ap.parse_args()
    a.skip = tuple(x for x in a.skip.split(",") if x)
    return write(a) if a.cmd == "write" else aggregate(a)


if __name__ == "__main__":
    sys.exit(main())
