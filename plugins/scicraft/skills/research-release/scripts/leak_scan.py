#!/usr/bin/env python3
"""Scan a folder for things that must not be published. Run it before every push, upload or deploy.

    python3 leak_scan.py <folder> [--git] [--style] [--private FILE] [--forbid FILE ...] [--allow REGEX ...]
                                  [--skip CLASS ...]

ERROR hits make the exit code 1. WARN hits are for a person to read and decide.

  ERROR  home and cluster paths, scheduler directives, review-process words, assistant traces (CLAUDE.md, .claude/,
         Co-Authored-By lines), access tokens and private keys, every pattern in --private, the content of every
         --forbid file (text or binary; the value is never printed)
  WARN   leftovers (TODO, FIXME, XXX, HACK), e-mail addresses, claim words (state of the art, outperform, SOTA),
         metadata inside images (EXIF, XMP, text chunks), and with --git every commit author

  --git      also read commit messages and authors of the git repository at <folder> (all branches)
  --style    also flag wording a release should not use (prose files and notebook markdown cells only)
  --private  a file with extra ERROR patterns, one regular expression per line, # for comments. It holds the
             project's own names (people, in-house sample ids, run names, internal hosts) and never leaves the
             machine; keep it outside the repository you scan
  --forbid   a file whose content must not appear anywhere (a password, a deploy secret)
  --allow    drop findings whose matched text fits this expression (an address the page means to show)
  --skip     drop a whole ERROR class by name, e.g. --skip "assistant trace" when the release is itself a package
             of agent skills that must name the assistant

Text files are read whole. Notebooks are read cell by cell, outputs included. Images are checked for metadata
(needs Pillow; without it the check is skipped and said so). Other binary files are checked by name and for
--forbid content only. Nothing is sent anywhere. Standard library only, Pillow optional.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ERROR = {
    "home path": r"/Users/[A-Za-z0-9._-]+|/home/[a-z][A-Za-z0-9._-]+|[A-Za-z]:\\\\Users\\\\",
    "cluster path": r"(?<![A-Za-z0-9])/(?:mnt|scratch|gpfs|lustre|omics|cluster|nfs|work|project|projects)/[A-Za-z0-9._-]+",
    "scheduler": r"#BSUB|#SBATCH|#PBS\b|^#\$ ",
    "review process": r"\brebuttal\b|\breviewers?\b|OpenReview|\barea chair\b",
    "assistant trace": r"CLAUDE\.md|\.claude/|\bClaude\b|\bAnthropic\b|Co-Authored-By|Generated with|claude\.ai",
    "secret": r"\bhf_[A-Za-z0-9]{30,}|\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"
              r"|-----BEGIN [A-Z ]*PRIVATE KEY|\bsk-[A-Za-z0-9_-]{20,}|\bAKIA[0-9A-Z]{16}\b",
}
WARN = {
    "leftover": r"\bTODO\b|\bFIXME\b|\bXXX\b|\bHACK\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b",
    "claim word": r"state[- ]of[- ]the[- ]art|\boutperform\w*|\bSOTA\b",
}
STYLE = {
    "word": r"\b(powerful|seamless(ly)?|cutting[- ]edge|unlock(s|ing)?|leverag(e|es|ing)|comprehensive|robust(ly)?"
            r"|effortless(ly)?|blazing|supercharge)\b",
    "dash or dot": "—| · ",
    "exclamation": r"[A-Za-z]!(\s|$)",
}
EMAIL_OK = re.compile(r"noreply@github\.com|@users\.noreply\.github\.com|git@github\.com|@example\.(com|org)", re.I)
PROSE = {".md", ".rst", ".txt"}
TEXT = PROSE | {".py", ".toml", ".yaml", ".yml", ".json", ".cfg", ".ini", ".sh", ".html", ".htm", ".css", ".js",
                ".mjs", ".cff", ".csv", ".tsv", ".ipynb", ".in", ".svg", ".xml", ".map", ".tex", ".bib", ".r", ".R", ""}
IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", ".venv", "_venv", "venv"}
MAX_BYTES = 30_000_000


def chunks(path: Path):
    """Yield (label, text, is_prose) pieces of one file."""
    if path.suffix == ".ipynb":
        try:
            nb = json.loads(path.read_text(errors="replace"))
        except json.JSONDecodeError:
            yield "unreadable notebook", "", False
            return
        for i, cell in enumerate(nb.get("cells", [])):
            src = cell.get("source", [])
            yield f"cell {i}", "".join(src) if isinstance(src, list) else src, cell.get("cell_type") == "markdown"
            for out in cell.get("outputs", []):
                text = "".join(out.get("text", [])) + "".join(out.get("data", {}).get("text/plain", []))
                text += "\n".join(out.get("traceback", []))
                if text:
                    yield f"cell {i} output", text, False
    else:
        yield "", path.read_text(errors="replace"), path.suffix in PROSE


def image_metadata(path: Path):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            keys = [k for k in im.info if k.lower() in ("exif", "xmp", "xml:com.adobe.xmp", "comment", "software",
                                                       "description", "author") and im.info[k]]
            return keys
    except Exception:
        return []


def shown(kind: str, rx, line: str) -> str:
    """The line as printed: a secret is cut to its first four characters so the report never repeats it."""
    if kind.endswith("secret"):
        line = rx.sub(lambda m: m.group(0)[:4] + "...[masked]", line)
    return line.strip()[:160]


def allowed(text: str, allow) -> bool:
    return any(a.search(text) for a in allow)


def hit(rx, text: str, allow) -> bool:
    """True when some match of rx in text is not covered by --allow."""
    return any(not allowed(m.group(0), allow) for m in rx.finditer(text))


def scan(root: Path, err: dict, style: bool, allow, forbid):
    warn = {k: re.compile(v) for k, v in WARN.items()}
    sty = {k: re.compile(v, re.I) for k, v in STYLE.items()} if style else {}
    hits, no_pil, n_files = [], False, 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or not path.is_file():
            continue
        n_files += 1
        for kind, rx in err.items():
            if hit(rx, str(rel), allow):
                hits.append(("ERROR", kind, str(rel), "", "file name"))
        if forbid:
            raw = path.read_bytes() if path.stat().st_size <= MAX_BYTES * 10 else b""
            for name, secret in forbid:
                if secret in raw:
                    hits.append(("ERROR", "forbidden content", str(rel), "", f"holds the content of {name}"))
        ext = path.suffix.lower() if path.suffix not in (".R",) else ".r"
        if ext in IMAGE:
            keys = image_metadata(path)
            if keys is None:
                no_pil = True
            elif keys:
                hits.append(("WARN", "image metadata", str(rel), "", ", ".join(keys)))
            continue
        if ext not in TEXT or path.stat().st_size > MAX_BYTES:
            continue
        for label, text, prose in chunks(path):
            for n, line in enumerate(text.splitlines(), 1):
                where = f"{label} line {n}" if label else f"line {n}"
                for kind, rx in err.items():
                    if hit(rx, line, allow):
                        hits.append(("ERROR", kind, str(rel), where, shown(kind, rx, line)))
                for kind, rx in warn.items():
                    bad = [m.group(0) for m in rx.finditer(line) if not allowed(m.group(0), allow)
                           and not (kind == "email" and EMAIL_OK.search(m.group(0)))]
                    if bad:
                        hits.append(("WARN", kind, str(rel), where, line.strip()[:160]))
                if prose:
                    for kind, rx in sty.items():
                        if rx.search(line):
                            hits.append(("WARN", "style: " + kind, str(rel), where, line.strip()[:160]))
    return hits, no_pil, n_files


def scan_git(root: Path, err: dict, allow):
    out = subprocess.run(["git", "-C", str(root), "log", "--all", "--format=%h%x09%an <%ae>%x09%s%x09%b%x1e"],
                         capture_output=True, text=True)
    if out.returncode:
        return [("ERROR", "git", ".", "", "not a git repository or git log failed")]
    hits, authors = [], set()
    for rec in out.stdout.split("\x1e"):
        rec = rec.strip()
        if not rec:
            continue
        sha, author, *rest = rec.split("\t")
        authors.add(author)
        text = " ".join(rest)
        for kind, rx in err.items():
            for s in (text, author):
                if hit(rx, s, allow):
                    hits.append(("ERROR", "commit: " + kind, sha, "", shown(kind, rx, author + " | " + text)))
                    break
    hits += [("WARN", "commit author", ".", "", a) for a in sorted(authors)]
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--git", action="store_true")
    ap.add_argument("--style", action="store_true")
    ap.add_argument("--private", type=Path)
    ap.add_argument("--forbid", action="append", default=[], type=Path)
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--skip", action="append", default=[])
    a = ap.parse_args()
    if not a.folder.is_dir():
        print(f"no such folder: {a.folder}")
        return 2
    patterns = {k: v for k, v in ERROR.items() if k not in a.skip}
    unknown = [s for s in a.skip if s not in ERROR]
    if unknown:
        print(f"unknown class for --skip: {', '.join(unknown)} (known: {', '.join(ERROR)})")
        return 2
    if a.private:
        if not a.private.is_file():
            print(f"no such private pattern file: {a.private}")
            return 2
        lines = [s.strip() for s in a.private.read_text().splitlines() if s.strip() and not s.lstrip().startswith("#")]
        # a leading (?i) becomes a scoped (?i:...) group so that one line's flag does not leak into the others
        lines = [f"(?i:{s[4:]})" if s.startswith("(?i)") else f"(?:{s})" for s in lines]
        if lines:
            patterns["private list"] = "|".join(lines)
    err = {k: re.compile(v, re.M) for k, v in patterns.items()}
    allow = [re.compile(x) for x in a.allow]
    forbid = []
    for f in a.forbid:
        if not f.is_file():
            print(f"no such forbid file: {f}")
            return 2
        secret = f.read_bytes().strip()
        if secret:
            forbid.append((f.name, secret))
    hits, no_pil, n_files = scan(a.folder, err, a.style, allow, forbid)
    if a.git:
        hits += scan_git(a.folder, err, allow)
    print(f"{n_files} files scanned in {a.folder}; ERROR classes: {', '.join(err)}")
    if no_pil:
        print("note: Pillow is not installed, so image metadata was not checked (pip install pillow)")
    for level in ("ERROR", "WARN"):
        rows = [h for h in hits if h[0] == level]
        if rows:
            print(f"== {level} ({len(rows)})")
        for _, kind, rel, where, line in rows:
            print(f"  [{kind}] {rel}" + (f" ({where})" if where else "") + f": {line}")
    n_err = sum(h[0] == "ERROR" for h in hits)
    print(f"\n{a.folder}: {n_err} errors, {len(hits) - n_err} warnings")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
