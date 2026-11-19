#!/usr/bin/env python3
"""Create the folder tree and the starting documents of a research project.

Writes into TARGET (created if missing):
  the tree for the chosen layout, one line per directory (printed, and written into the
  index file and README); the index file for agents (CLAUDE.md by default), README.md with
  the table of which file owns which question; the four governing documents NARRATIVE.md,
  GOALS.md, GUARDRAILS.md and GUIDELINES.md; the knowledge base docs/kb/ (README.md, INDEX.md
  and a first entry); .gitignore with a reason per block, PROVENANCE.md, STATUS.md,
  DECISIONS.md, RUN_MAP.md, experiments/EXPERIMENTS.md, guidelines/WORKFLOW.md,
  configs/paths.env, data/README.md, scripts/sync.sh; for the research layout also SPEC.md,
  DESIGN.md, NOTES.md, the results
  contract (guidelines/RESULTS.md, results/runs/, results/cache/, results/aggregate/,
  results/archived/), src/<pkg>/settings.py (one Config with presets) and src/<pkg>/store.py
  (a copy of results_store.py) with tests/test_store.py; for the driver layout also UPSTREAM_COMMIT.

Raw stores are linked, never copied: each --raw NAME=PATH makes data/raw/NAME a symbolic link
to PATH and adds a row to PROVENANCE.md.

Existing files are never overwritten unless --force is given; skipped files are listed.
Git is not initialized: branches, commits and remotes belong to the research-code skill.

Layouts:
  research  a project that owns its method code (src/, tests/) and its experiments
  driver    heavy runs of someone else's package at a pinned commit: no package source,
            patches/, vendor/, UPSTREAM_COMMIT

Examples:
  python3 scaffold.py ~/projects/tab-pretrain --name "Tabular pretraining" --package tabpre \\
      --raw openml=/mnt/store/openml --remote me@gpu-box:/work/tab-pretrain/
  python3 scaffold.py ./run-upstream --layout driver --dry-run

Standard library only; Python 3.9 or later. Exit 0 when the tree and files are in place and
the checks pass (index file at most 500 words and naming the four governing documents,
data/ and results/ ignored), 1 otherwise. Afterwards fill the [bracketed] placeholders and run
doctor.py on the project.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "assets" / "templates"

# (path, one-line purpose, tracked by git?)
LAYOUTS = {
    "research": [
        ("src/{pkg}/", "the method; each module's first line says what it implements", True),
        ("configs/", "small declarative configs; paths.env holds every path once", True),
        ("scripts/", "thin entry points (run, submit, preflight, sync); no logic that belongs in src", True),
        ("experiments/", "campaign configs and EXPERIMENTS.md, the lab notebook (failures kept)", True),
        ("tests/", "fast CPU tests with small committed baselines", True),
        ("docs/", "reference documents: paper-to-code map, data availability", True),
        ("docs/kb/", "the knowledge base: INDEX.md first, one topic per entry, archive/ for superseded", True),
        ("guidelines/", "topic files of GUIDELINES.md (WORKFLOW.md first)", True),
        ("reference/", "frozen baselines and contract files, tracked, checked by md5", True),
        ("data/raw/", "symbolic links to raw stores outside the project (ignored)", False),
        ("data/", "small copied inputs, one PROVENANCE.md row each (ignored)", False),
        ("results/runs/", "one root per run profile: config.json first, manifest.json last (ignored)", False),
        ("results/cache/", "downloads that must survive restarts (ignored)", False),
        ("results/aggregate/", "cross-run tables that feed the paper (ignored)", False),
        ("results/archived/", "superseded outputs under <date>_<reason>/ with MANIFEST.tsv (ignored)", False),
        ("scratch/", "smoke profile and throwaway checks, never cited (ignored)", False),
        ("_attic/", "superseded drafts, never built and never cited (ignored)", False),
    ],
    "driver": [
        ("configs/", "one <run>.env per run: paths, budgets, resources; paths.env holds paths once", True),
        ("scripts/", "preflight, plan, run, validate, track: entry points of the run", True),
        ("scripts/lib/", "sourced helpers and workers", True),
        ("patches/", "the upstream changes this driver needs, as numbered .patch files", True),
        ("vendor/", "third-party code copied in, each with a PROVENANCE.md row", True),
        ("docs/", "numbered docs read in order (00_overview.md first)", True),
        ("docs/kb/", "the knowledge base: INDEX.md first, one topic per entry, archive/ for superseded", True),
        ("guidelines/", "topic files of GUIDELINES.md (WORKFLOW.md first)", True),
        ("experiments/", "EXPERIMENTS.md, the lab notebook (failures kept)", True),
        ("reference/", "frozen baselines, tracked, checked by md5", True),
        ("data/raw/", "symbolic links to raw stores outside the project (ignored)", False),
        ("data/", "small copied inputs, one PROVENANCE.md row each (ignored)", False),
        ("results/runs/", "one folder per <unit>/<variant>/ with manifest.json (ignored)", False),
        ("results/archived/", "superseded outputs under <date>_<reason>/ with MANIFEST.tsv (ignored)", False),
        ("scratch/", "smoke tests and calibration runs, never cited (ignored)", False),
    ],
}

# (template file, destination, layouts it belongs to)
FILES = [
    ("CLAUDE.md", "{index}", ("research", "driver")),
    ("README.md", "README.md", ("research", "driver")),
    ("NARRATIVE.md", "NARRATIVE.md", ("research", "driver")),
    ("GOALS.md", "GOALS.md", ("research", "driver")),
    ("GUARDRAILS.md", "GUARDRAILS.md", ("research", "driver")),
    ("GUIDELINES.md", "GUIDELINES.md", ("research", "driver")),
    ("kb_README.md", "docs/kb/README.md", ("research", "driver")),
    ("kb_INDEX.md", "docs/kb/INDEX.md", ("research", "driver")),
    ("kb_entry.md", "docs/kb/00_overview.md", ("research", "driver")),
    ("gitignore.txt", ".gitignore", ("research", "driver")),
    ("PROVENANCE.md", "PROVENANCE.md", ("research", "driver")),
    ("STATUS.md", "STATUS.md", ("research", "driver")),
    ("DECISIONS.md", "DECISIONS.md", ("research", "driver")),
    ("RUN_MAP.md", "RUN_MAP.md", ("research", "driver")),
    ("EXPERIMENTS.md", "experiments/EXPERIMENTS.md", ("research", "driver")),
    ("WORKFLOW.md", "guidelines/WORKFLOW.md", ("research", "driver")),
    ("paths.env", "configs/paths.env", ("research", "driver")),
    ("data_README.md", "data/README.md", ("research", "driver")),
    ("SPEC.md", "SPEC.md", ("research",)),
    ("DESIGN.md", "DESIGN.md", ("research",)),
    ("NOTES.md", "NOTES.md", ("research",)),
    ("RESULTS.md", "guidelines/RESULTS.md", ("research",)),
    ("settings.py", "src/{pkg}/settings.py", ("research",)),
    ("UPSTREAM_COMMIT", "UPSTREAM_COMMIT", ("driver",)),
]

GOVERNING = ["NARRATIVE.md", "GOALS.md", "GUARDRAILS.md", "GUIDELINES.md"]
COMMON_ROOT = [("{index}", "entry for agents: reading order, contract, guardrails by id, pointers"),
               ("README.md", "what it is, install, 60-second version, layout, which file owns which question"),
               ("NARRATIVE.md", "the argument: why this project, why this way, what a win looks like"),
               ("GOALS.md", "the targets: long goals, the active short goal with its checks, non-goals"),
               ("GUARDRAILS.md", "the invariants: rules with ids, what each prevents, how each is checked"),
               ("GUIDELINES.md", "the conventions: the bar, defaults, the definition of done"),
               ("STATUS.md", "each component R/A/E with where it lives; blocked; next; dated"),
               ("RUN_MAP.md", "one row per run: config, output, status, Synced"),
               ("DECISIONS.md", "one line per choice, superseded rows kept"),
               ("PROVENANCE.md", "one row per linked store, copied file, borrowed code")]
ROOT_FILES = {
    "research": COMMON_ROOT + [("SPEC.md", "the author's inputs verbatim, the goal part named; frozen"),
                               ("DESIGN.md", "the science as built: object of study, choices with reasons"),
                               ("NOTES.md", "environment, verified APIs, gotchas, deviations, decisions, runtimes")],
    "driver": COMMON_ROOT + [("UPSTREAM_COMMIT", "branch and commit of the code that runs")],
}


# (file, the question it owns, layouts it belongs to)
OWNERS = [
    ("NARRATIVE.md", "why this project, why this way, what a win looks like", ("research", "driver")),
    ("GOALS.md", "the long goals, the active short goal, the non-goals", ("research", "driver")),
    ("GUARDRAILS.md", "what must never happen", ("research", "driver")),
    ("GUIDELINES.md", "how work is normally done, and what \"done\" means", ("research", "driver")),
    ("{index}", "where everything is, and the reading order for an agent", ("research", "driver")),
    ("docs/kb/INDEX.md", "what we know about the field, the data and the methods, and how we know it",
     ("research", "driver")),
    ("SPEC.md", "what the author asked for, verbatim and frozen", ("research",)),
    ("DESIGN.md", "what is built and why, with every setting that is safe to tune", ("research",)),
    ("NOTES.md", "what was verified on this machine: versions, APIs, runtimes", ("research",)),
    ("UPSTREAM_COMMIT", "which upstream code runs", ("driver",)),
    ("STATUS.md", "what works, what is blocked, what is next", ("research", "driver")),
    ("DECISIONS.md", "what was chosen, when and why", ("research", "driver")),
    ("experiments/EXPERIMENTS.md", "what was tried and what happened", ("research", "driver")),
    ("RUN_MAP.md", "which run produced what", ("research", "driver")),
    ("PROVENANCE.md", "where each input came from", ("research", "driver")),
]


def owners_table(layout: str, index: str) -> str:
    rows = ["| File | Owns the question |", "|---|---|"]
    rows += [f"| `{f.format(index=index)}` | {q} |" for f, q, layouts in OWNERS if layout in layouts]
    return "\n".join(rows)


def tree_text(layout: str, pkg: str, index: str) -> str:
    rows = [(p.format(pkg=pkg), d) for p, d, _ in LAYOUTS[layout]]
    rows += [(f.format(index=index), d) for f, d in ROOT_FILES[layout]]
    width = max(len(p) for p, _ in rows) + 2
    return "\n".join(f"{p:<{width}}{d}" for p, d in rows)


def fill(text: str, values: dict) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", type=Path, help="project folder to create or fill")
    ap.add_argument("--name", help="project name for the documents (default: folder name)")
    ap.add_argument("--package", help="import name of the package under src/ (default: from the folder name)")
    ap.add_argument("--layout", choices=sorted(LAYOUTS), default="research")
    ap.add_argument("--index-name", default="CLAUDE.md", help="file name of the agent index (e.g. AGENTS.md)")
    ap.add_argument("--raw", action="append", default=[], metavar="NAME=PATH",
                    help="link a raw store as data/raw/NAME (repeatable)")
    ap.add_argument("--remote", default="[user@host:/absolute/path/of/project/]",
                    help="remote copy of the code, written into configs/paths.env")
    ap.add_argument("--force", action="store_true", help="overwrite files that already exist")
    ap.add_argument("--dry-run", action="store_true", help="print what would be created and stop")
    a = ap.parse_args()

    target = a.target.expanduser().resolve()
    name = a.name or target.name
    pkg = a.package or re.sub(r"\W+", "_", target.name.lower()).strip("_") or "pkg"
    if not pkg.isidentifier():
        pkg = "pkg_" + pkg
    today = dt.date.today().isoformat()
    tree = tree_text(a.layout, pkg, a.index_name)
    extra = ("- The author's inputs, verbatim and frozen: `SPEC.md`; the science as built: `DESIGN.md`\n"
             "- Environment, verified APIs, deviations from papers, runtimes: `NOTES.md`\n"
             "- What every run writes, and where: `guidelines/RESULTS.md`; every setting: `src/{pkg}/settings.py`\n"
             "- A fresh session resumes from `NOTES.md` and `STATUS.md`.\n").format(pkg=pkg) if a.layout == "research" else ""
    values = {"INDEX": a.index_name, "NAME": name, "PKG": pkg, "DATE": today, "TREE": tree, "REMOTE": a.remote,
              "EXTRA_POINTERS": extra, "OWNERS": owners_table(a.layout, a.index_name)}

    print(f"scaffold: layout {a.layout} into {target}\n")
    print(tree + "\n")
    if a.dry_run:
        print("dry run: nothing written")
        return 0

    made, skipped, problems = [], [], []
    for p, _, _ in LAYOUTS[a.layout]:
        d = target / p.format(pkg=pkg)
        d.mkdir(parents=True, exist_ok=True)
        made.append(str(d.relative_to(target)) + "/")

    for tpl, dest, layouts in FILES:
        if a.layout not in layouts:
            continue
        out = target / dest.format(index=a.index_name, pkg=pkg)
        if out.exists() and not a.force:
            skipped.append(str(out.relative_to(target)))
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(fill((TEMPLATES / tpl).read_text(encoding="utf-8"), values), encoding="utf-8")
        made.append(str(out.relative_to(target)))

    sync_dst = target / "scripts" / "sync.sh"
    if sync_dst.exists() and not a.force:
        skipped.append("scripts/sync.sh")
    else:
        shutil.copyfile(HERE / "sync.sh", sync_dst)
        sync_dst.chmod(0o755)
        made.append("scripts/sync.sh")

    if a.layout == "research":
        store_dst = target / "src" / pkg / "store.py"
        if store_dst.exists() and not a.force:
            skipped.append(str(store_dst.relative_to(target)))
        else:
            shutil.copyfile(HERE / "results_store.py", store_dst)
            made.append(str(store_dst.relative_to(target)))
        test_dst = target / "tests" / "test_store.py"
        if test_dst.exists() and not a.force:
            skipped.append("tests/test_store.py")
        else:
            test_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(HERE / "test_store.py", test_dst)
            made.append("tests/test_store.py")
        init = target / "src" / pkg / "__init__.py"
        if not init.exists():
            init.write_text(f'"""{name}: [one line on what this package implements]."""\n', encoding="utf-8")
            made.append(str(init.relative_to(target)))

    prov = target / "PROVENANCE.md"
    for spec in a.raw:
        if "=" not in spec:
            problems.append(f"--raw {spec}: expected NAME=PATH")
            continue
        rname, rpath = spec.split("=", 1)
        src = Path(rpath).expanduser()
        link = target / "data" / "raw" / rname
        if link.is_symlink() or link.exists():
            skipped.append(f"data/raw/{rname}")
            continue
        os.symlink(src, link)
        if src.exists():
            mtime = dt.datetime.fromtimestamp(src.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            note = ""
        else:
            mtime, note = "-", "target missing when linked"
            problems.append(f"data/raw/{rname} points to {src}, which does not exist here (dangling link)")
        row = f"| `data/raw/{rname}` | `{src}` | {mtime} | {today} | {note} |\n"
        text = prov.read_text(encoding="utf-8")
        anchor = "| Link | Target | Target mtime | Linked on | Notes |\n|---|---|---|---|---|\n"
        if anchor in text:
            text = text.replace(anchor, anchor + row, 1)
        else:
            text += "\n" + row
        prov.write_text(text, encoding="utf-8")
        made.append(f"data/raw/{rname} -> {src}")

    # checks
    index = target / a.index_name
    words = len(re.sub(r"```.*?```", " ", index.read_text(encoding="utf-8"), flags=re.S).split())
    if words > 500:
        problems.append(f"{a.index_name} has {words} words outside code blocks; keep it at most 500")
    index_text = index.read_text(encoding="utf-8")
    for g in GOVERNING:
        if not (target / g).exists():
            problems.append(f"governing document missing: {g}")
        if g not in index_text:
            problems.append(f"{a.index_name} does not name {g}")
    if "Owns the question" not in (target / "README.md").read_text(encoding="utf-8"):
        problems.append("README.md has no table of which file owns which question (an older README was kept)")
    ign = (target / ".gitignore").read_text(encoding="utf-8")
    for must in ("/data/*", "/results/", "/scratch/"):
        if must not in ign:
            problems.append(f".gitignore lacks {must}")
    if a.layout == "research":
        for must in ("guidelines/RESULTS.md", f"src/{pkg}/settings.py", f"src/{pkg}/store.py", "results/runs"):
            if not (target / must).exists():
                problems.append(f"results contract incomplete: {must} missing")

    print(f"created {len(made)}:")
    for m in made:
        print("  +", m)
    if skipped:
        print(f"kept existing {len(skipped)} (use --force to overwrite):")
        for s in skipped:
            print("  =", s)
    print(f"checked: {a.index_name} {words} words (limit 500) and names the four governing documents; "
          f".gitignore ignores data/, results/, scratch/"
          + ("; results contract files in place" if a.layout == "research" else ""))
    for p in problems:
        print("PROBLEM:", p)
    left = 0
    for m in made:  # only the files written now; never walk into linked raw stores
        f = target / m
        if f.name in ("store.py", "test_store.py"):  # copied verbatim; their brackets are code
            continue
        if f.is_file() and not f.is_symlink() and "[" in f.read_text(encoding="utf-8", errors="ignore"):
            left += 1
    print(f"next: fill the [bracketed] placeholders ({left} of the files written now have some), run doctor.py on "
          f"the project, then set up git with the research-code skill")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
