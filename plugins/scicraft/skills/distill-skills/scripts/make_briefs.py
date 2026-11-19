#!/usr/bin/env python3
"""Write one build brief per skill (BRIEFS/W_<skill>.md) from a JSON spec and a brief template.

The spec (see assets/skill_spec.example.json) names the package, its plugins and, per skill:
plugin, scope, must (what it must contain), primary findings codes (read fully), secondary
"CODE: what to take" entries (read the named parts), existing material to port, and notes
(decisions already made). A findings code resolves to the single file FINDINGS/<CODE>_*.md.
The template (default assets/build_brief.md) uses {placeholders}; every brief also lists all
other skills as siblings, so each writer points to a neighbor instead of repeating it.

Usage:
    python3 make_briefs.py SPEC.json [--template assets/build_brief.md] [--only name1,name2] [--dry-run]

Exit code 1 when a findings code matches no file or more than one, or a placeholder is unfilled.
Standard library only.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find(findings: str, code: str) -> str:
    hits = glob.glob(f"{findings}/{code}_*.md")
    if len(hits) != 1:
        raise SystemExit(f"findings code {code}: expected one file {findings}/{code}_*.md, found {len(hits)}")
    return hits[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("spec", type=Path)
    ap.add_argument("--template", type=Path, default=HERE.parent / "assets" / "build_brief.md")
    ap.add_argument("--only", default="", help="comma-separated skill names to (re)write")
    ap.add_argument("--dry-run", action="store_true", help="check the spec and print what would be written")
    a = ap.parse_args()
    spec = json.loads(a.spec.read_text())
    tpl = a.template.read_text()
    P, plugins, skills = spec["paths"], spec["plugins"], spec["skills"]
    only = [x for x in a.only.split(",") if x]
    out = Path(P["briefs"])
    names = list(skills)
    written = []
    for name, s in skills.items():
        if only and name not in only:
            continue
        pl = plugins[s["plugin"]]
        folder = f"{pl['root']}/{name}"
        gate = P["gate"].format(folder=folder, terms=pl["terms"]) + pl.get("gate_extra", "")
        fields = dict(
            package=spec["package"], mission=spec["mission"], standard=spec["standard"],
            lead_reader=spec["lead_reader"], contract=P["contract"], model_skill=P["model_skill"],
            eval_model=P["eval_model"], name=name, plugin=s["plugin"], folder=folder, scope=s["scope"],
            must=s["must"], notes=s.get("notes", "none"), gate=gate,
            build_note=f"{P['build_notes']}/{name}.md",
            primary="\n".join(f"- `{find(P['findings'], c)}`" for c in s.get("primary", []))
                    or "- none; see the material to port",
            secondary="\n".join(f"- `{find(P['findings'], x.split(':')[0].strip())}`: {x.split(':', 1)[1].strip()}"
                                for x in s.get("secondary", [])) or "- none",
            existing="\n".join(f"- {e}" for e in s.get("existing", [])) or "- none",
            siblings=", ".join(f"`{n}`" for n in names if n != name))
        text = tpl.format(**fields)
        left = re.findall(r"\{[a-z_]+\}", text)
        if left:
            raise SystemExit(f"{name}: unfilled placeholders {sorted(set(left))}")
        target = out / f"W_{name}.md"
        if not a.dry_run:
            out.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        written.append(str(target))
    print(("would write " if a.dry_run else "wrote ") + f"{len(written)} brief(s):")
    for w in written:
        print("  " + w)
    print('Launch line per brief: "Read your full assignment at <brief> and carry it out exactly."')
    return 0


if __name__ == "__main__":
    sys.exit(main())
