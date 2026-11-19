#!/usr/bin/env python3
"""List every top-level entry of a cluttered project folder as a triage table. Moves nothing.

For each file or folder directly under ROOT it reports size, file count, last change, whether git
tracks anything in it, and a suggested class:

  KEEP?         named in the project's code (the live chain), tracked by git, a known project
                file, or the newest of a run of dated siblings
  ARCHIVE?      an older sibling in a run of dated or numbered entries (name_20260314_074730,
                "name 2.zip", name_v3, name2 beside name)
  DELETE?       a smoke test, check, tmp or probe output; an empty folder; build debris; a virtual env
  VERIFY-FIRST  a single file of 1 GB or more, or a lone archive file: find the authoritative copy first
  UNSORTED      none of the above: a person decides

The classes are suggestions from names, sizes and dates only. The person who owns the project
decides every row; nothing is moved or deleted by this script. Write the table into a file
(for example docs/FOLDER_TRIAGE.md), fill the Decision column, then act with archive.py.

Usage:
  python3 triage.py ROOT [--out docs/FOLDER_TRIAGE.md] [--no-size] [--big-gb 1]

Standard library only (git is used when ROOT is inside a repository). Python 3.9 or later.
Exit 0 after writing the table; 1 when ROOT is not a folder.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

STAMP = re.compile(r"^(?P<stem>.+?)[ _.-]?(?P<stamp>(?:19|20)\d{6}(?:[_-]?\d{4,6})?|(?<= )\d{1,2}|\(\d+\)|v\d{1,2})"
                   r"(?P<tail>[_-][A-Za-z].*)?(?P<ext>\.[A-Za-z][A-Za-z0-9.]*)?$")
TRAILING_DIGIT = re.compile(r"^(?P<stem>.*\D)\d{1,2}$")
THROWAWAY = re.compile(r"(smoke|tmp|temp|scratch|check|probe|debug|test\d*$|_test|submit_test|sanity|try\d*|draft_old)", re.I)
DEBRIS = re.compile(r"(\.aux|\.log|\.out|\.toc|\.bbl|\.blg|\.fls|\.fdb_latexmk|\.synctex\.gz|\.pyc|\.DS_Store|__pycache__|\.ipynb_checkpoints|\.pytest_cache)$")
VENV = re.compile(r"^(\.?venv\w*|env|\.conda|\.pixi)$")
ARCHIVE = re.compile(r"\.(zip|tar|tgz|tar\.gz|tar\.bz2|7z|rar)$", re.I)
CODE_EXT = (".py", ".sh", ".R", ".r", ".jl", ".ipynb", ".yaml", ".yml", ".toml", ".json", ".env", ".cfg", ".mk", "Makefile", ".smk", ".nf")
PROJECT_FILES = {"README.md", "CLAUDE.md", "AGENTS.md", "STATUS.md", "PROVENANCE.md", "RUN_MAP.md", "DECISIONS.md",
                 "LICENSE", "pyproject.toml", "setup.py", "environment.yml", "pixi.toml", "pixi.lock", ".gitignore",
                 "CHANGELOG.md", "CITATION.cff", "Makefile", "src", "tests", "configs", "scripts", "docs", "guidelines",
                 "experiments", "reference", ".git"}


def measure(p: Path, do_size: bool):
    """Bytes and file count, never following symbolic links."""
    if p.is_symlink():
        return 0, 0
    if p.is_file():
        return p.stat().st_size, 1
    if not do_size:
        return -1, -1
    total = files = 0
    for dirpath, dirnames, filenames in os.walk(p, followlinks=False):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
                    files += 1
            except OSError:
                pass
    return total, files


def human(n: int) -> str:
    if n < 0:
        return "?"
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return str(n)


def tracked_names(root: Path) -> set:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "--full-name", "."],
                             capture_output=True, text=True, check=True).stdout
        top = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-prefix"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return set()
    names = set()
    for line in out.splitlines():
        rel = line[len(top):] if top and line.startswith(top) else line
        names.add(rel.split("/", 1)[0])
    return names


def code_refs(root: Path, dirs) -> dict:
    """Map each top-level entry name to the code files that mention it (the live chain)."""
    texts = []
    for d in dirs:
        base = root / d
        if not base.is_dir() or base.is_symlink():
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = [x for x in dirnames if not x.startswith(".") and x != "__pycache__"]
            for f in filenames:
                if f.endswith(CODE_EXT):
                    fp = Path(dirpath) / f
                    try:
                        if fp.stat().st_size < 2_000_000:
                            texts.append((str(fp.relative_to(root)), fp.read_text(encoding="utf-8", errors="ignore")))
                    except OSError:
                        pass
    return {"_texts": texts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, help="write the Markdown table here (default: print it)")
    ap.add_argument("--no-size", action="store_true", help="skip walking folders (fast on very large trees)")
    ap.add_argument("--refs", nargs="*", default=["scripts", "src", "code", "configs", "experiments", "notebooks", "workflow"],
                    help="folders whose code is searched for entry names (default: scripts src code configs experiments notebooks workflow)")
    ap.add_argument("--big-gb", type=float, default=1.0, help="size from which a file or archive is VERIFY-FIRST (default 1)")
    a = ap.parse_args()
    root = a.root.expanduser().resolve()
    if not root.is_dir():
        print(f"not a folder: {root}", file=sys.stderr)
        return 1

    tracked = tracked_names(root)
    entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    rows = []
    for p in entries:
        size, nfiles = measure(p, not a.no_size)
        mtime = dt.datetime.fromtimestamp(p.lstat().st_mtime)
        rows.append({"p": p, "name": p.name, "size": size, "files": nfiles, "mtime": mtime,
                     "kind": "link" if p.is_symlink() else ("dir" if p.is_dir() else "file"),
                     "cls": None, "why": ""})

    # runs of dated or numbered siblings: newest is KEEP?, the rest ARCHIVE?
    groups = defaultdict(list)
    names = {r["name"] for r in rows}
    for r in rows:
        if THROWAWAY.search(r["name"]) or DEBRIS.search(r["name"]):
            continue  # a smoke test never stands as the newest of a family
        m = STAMP.match(r["name"])
        if m:
            groups[(m.group("stem").rstrip(" _-.") + (m.group("ext") or ""), r["kind"])].append(r)
            continue
        m = TRAILING_DIGIT.match(r["name"])  # sweep_clean2 beside sweep_clean
        if m and m.group("stem") in names:
            groups[(m.group("stem"), r["kind"])].append(r)
    for (stem, _), members in groups.items():
        base = [r for r in rows if r["name"] == stem]
        family = members + base
        if len(family) < 2:
            continue
        family.sort(key=lambda r: r["mtime"])
        for r in family[:-1]:
            r["cls"], r["why"] = "ARCHIVE?", f"older of {len(family)} siblings named {stem}*"
        family[-1]["cls"], family[-1]["why"] = "KEEP?", f"newest of {len(family)} siblings named {stem}*"

    texts = code_refs(root, a.refs)["_texts"]
    big = int(a.big_gb * 1024 ** 3)
    for r in rows:
        name, p = r["name"], r["p"]
        users = [f for f, t in texts if re.search(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])", t)]
        if users and name not in PROJECT_FILES:
            r["cls"], r["why"] = "KEEP?", "named in " + ", ".join(users[:3]) + (" ..." if len(users) > 3 else "")
            continue
        if name in tracked or name in PROJECT_FILES:
            r["cls"], r["why"] = "KEEP?", "tracked by git" if name in tracked else "project file or folder"
        elif r["kind"] == "link":
            r["cls"], r["why"] = "KEEP?", f"symbolic link to {os.readlink(p)}"
        elif r["kind"] == "file" and r["size"] >= big:
            r["cls"], r["why"] = "VERIFY-FIRST", "large; confirm the authoritative copy (cmp or sha256) before any delete"
        elif ARCHIVE.search(name) and r["cls"] is None:
            r["cls"], r["why"] = "VERIFY-FIRST", "archive file; may mirror raw inputs: compare with its source by checksum first"
        elif VENV.match(name) or DEBRIS.search(name):
            r["cls"], r["why"] = "DELETE?", "regenerable environment or build debris"
        elif THROWAWAY.search(name):
            r["cls"], r["why"] = "DELETE?", "name says smoke test, check, tmp or probe"
        elif r["kind"] == "dir" and r["files"] == 0:
            r["cls"], r["why"] = "DELETE?", "empty folder"
        elif r["cls"] is None:
            r["cls"], r["why"] = "UNSORTED", ""

    order = ["VERIFY-FIRST", "KEEP?", "ARCHIVE?", "DELETE?", "UNSORTED"]
    total = sum(r["size"] for r in rows if r["size"] > 0)
    lines = [f"# Folder triage: {root.name}", "",
             f"{len(rows)} entries, {human(total)} on {dt.date.today().isoformat()}. Classes are suggestions from names, "
             "sizes and dates; nothing has been moved. Fill Decision (KEEP, ARCHIVE, DELETE, OUT OF SCOPE) "
             "for every row before acting.", ""]
    for cls in order:
        sel = sorted((r for r in rows if r["cls"] == cls), key=lambda r: -r["size"])
        if not sel:
            continue
        lines += [f"## {cls} ({len(sel)})", "", "| Entry | Kind | Size | Files | Last change | Why suggested | Decision |",
                  "|---|---|---|---|---|---|---|"]
        for r in sel:
            files = "?" if r["files"] < 0 else str(r["files"])
            lines.append(f"| `{r['name']}` | {r['kind']} | {human(r['size'])} | {files} | "
                         f"{r['mtime']:%Y-%m-%d} | {r['why']} | |")
        lines.append("")
    text = "\n".join(lines)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)
    counts = {c: sum(1 for r in rows if r["cls"] == c) for c in order}
    print("triage: " + ", ".join(f"{c} {n}" for c, n in counts.items()) + "; nothing moved", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
