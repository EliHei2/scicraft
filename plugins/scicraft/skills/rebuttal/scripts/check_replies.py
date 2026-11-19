#!/usr/bin/env python3
"""Check reply texts before they are posted: length per comment, banned strings, punctuation in our sentences,
quotations against their sources, and colored MathJax phrases.

    python3 check_replies.py replies.md --sources reviews.md paper.txt guideline.txt
    python3 check_replies.py replies.md --limit 5000 --ban banned.txt --refs refs.json --bytes

The replies file holds one block per comment. A block starts with a header line
    <<<<< key | title | readers >>>>>
(only the key is required) and runs to the next header. A file with no header line is checked as one block. Everything between headers is the text exactly as it is pasted.

Checks, per block:
  length       characters as the platform counts them (the block joined with newlines, outer blank lines removed);
               line-reference tokens such as [[BENCH]] or the bracket form used by resolve_lines.py are replaced from
               --refs first, and an unknown token counts as nine characters. --bytes counts UTF-8 bytes instead.
  banned       every regex in --ban (one per line, # starts a comment) plus the defaults below; table rule lines
               and quoted reviewer lines (starting with >) are exempt.
  punctuation  an em dash, en dash or spaced double hyphen, a semicolon, or a colon inside one of our sentences
               (headings, table rows, quoted lines and the lines under a Location heading are exempt). Turn off with --allow-punct.
  counts       phrases that count what failed ("N of them", "all but", "except") are listed as warnings.
  quotes       every "double-quoted" passage of five or more characters, and every quoted line (>), must occur
               verbatim in one of the --sources files after whitespace and curly quotes are normalized; an
               ellipsis splits a quote into parts that are checked one by one. Case is ignored, so a quote may start
               lower-case inside our sentence; check capitals by eye.
  color       every $\\color{c}{\\textsf{...}}$ phrase is listed with its length (MathJax boxes do not wrap).

Exit code 1 when a block is over the limit, a banned string or a punctuation fault is found, or a quote is not found.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADER = re.compile(r"^<<<<<\s*(.*?)\s*>>>>>\s*$")
TOKEN = re.compile(r"⟦([A-Z0-9_]+)⟧|\[\[([A-Z0-9_]+)\]\]")
MAC = re.compile(r"\$\\color\{(\w+)\}\{\\textsf\{(.*?)\}\}\$")
TABLE_RULE = re.compile(r"^\s*\|[-:| ]+\|\s*$")
DEFAULT_BAN = ["\u2014", "\u2013", r" -{2,3} "]
COUNTS = [r"\b(two|three|four|five|six|seven|eight|nine|ten|\d+) of them\b", r"\ball but\b", r"\bexcept\b",
          r"\b\d+ of the \d+\b"]


def blocks(path: Path) -> dict:
    out, key = {}, None
    for ln in path.read_text(encoding="utf-8").split("\n"):
        m = HEADER.match(ln)
        if m:
            key = m.group(1).split("|")[0].strip()
            out[key] = []
        elif key is not None:
            out[key].append(ln)
    for k, v in out.items():
        while v and not v[-1].strip():
            v.pop()
        while v and not v[0].strip():
            v.pop(0)
    return {k: "\n".join(v) for k, v in out.items()}


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def load_bans(path: str | None) -> list:
    pats = list(DEFAULT_BAN)
    if path:
        for ln in Path(path).read_text(encoding="utf-8").split("\n"):
            ln = ln.split(" #")[0].rstrip() if not ln.startswith("#") else ""
            if ln.strip():
                pats.append(ln.strip())
    return pats


def our_lines(text: str):
    """(line number, line) of the lines written by us: no quoted reviewer lines, no table rules."""
    loc = False
    for i, ln in enumerate(text.split("\n"), 1):
        s = ln.strip()
        if s.startswith("#"):
            loc = "location" in s.lower()
        if s.startswith(">") or TABLE_RULE.match(s):
            continue
        yield i, ln, loc


def punct_faults(line: str) -> list:
    s = line.strip()
    if not s or s.startswith("#") or s.startswith("|"):
        return []
    s = MAC.sub("X", re.sub(r"\$[^$]*\$", "X", s))           # math is exempt
    s = re.sub(r"https?://\S+", "URL", s)
    out = []
    if ";" in s:
        out.append("semicolon")
    for m in re.finditer(r":", s):
        before, after = s[:m.start()], s[m.end():]
        if re.search(r"\d$", before) and re.match(r"\d", after):   # ratios and times
            continue
        if not after.strip():                                       # a colon that ends the line opens a list or table
            continue
        if re.fullmatch(r"\**[^.!?]{0,40}\**", before.strip()) and before.strip().endswith("**"):
            continue                                                # a bold run-in label such as **W1:**
        out.append("colon inside a sentence")
        break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("replies", help="file of reply blocks")
    ap.add_argument("--sources", nargs="*", default=[], help="text files that quotations must come from")
    ap.add_argument("--limit", type=int, default=5000, help="characters per comment (default 5000)")
    ap.add_argument("--bytes", action="store_true", help="count UTF-8 bytes instead of characters")
    ap.add_argument("--ban", help="file of banned regexes, one per line")
    ap.add_argument("--refs", help="JSON of line-reference tokens to their resolved text")
    ap.add_argument("--allow-punct", action="store_true", help="skip the semicolon, colon and dash checks")
    a = ap.parse_args()

    refs = json.loads(Path(a.refs).read_text()) if a.refs else {}
    bans = [re.compile(p) for p in load_bans(a.ban)]
    if a.allow_punct:
        bans = [b for b in bans if b.pattern not in DEFAULT_BAN]
    src = [norm(Path(p).read_text(encoding="utf-8", errors="replace")).lower() for p in a.sources]
    texts = blocks(Path(a.replies))
    if not texts:                                   # a file without headers (a journal letter) is one block
        texts = {Path(a.replies).stem: Path(a.replies).read_text(encoding="utf-8").strip("\n")}
    bad = 0
    for key, t in texts.items():
        unknown = sorted({m.group(1) or m.group(2) for m in TOKEN.finditer(t)} - set(refs))
        resolved = TOKEN.sub(lambda m: refs.get(m.group(1) or m.group(2), "X" * 9), t)
        n = len(resolved.encode("utf-8")) if a.bytes else len(resolved)
        unit = "bytes" if a.bytes else "characters"
        state = f"room {a.limit - n}" if n <= a.limit else f"OVER by {n - a.limit}"
        print(f"{key}: {n} {unit} of {a.limit}, {state}" + (f"; unresolved tokens {', '.join(unknown)}" if unknown else ""))
        bad += n > a.limit
        for i, ln, loc in our_lines(t):
            for b in bans:
                for m in b.finditer(ln):
                    print(f"   line {i} BANNED {b.pattern!r}: ...{ln[max(0, m.start() - 40):m.end() + 30]}...")
                    bad += 1
            if not a.allow_punct and not loc:            # location lists ("Figure 3; p. 6") are exempt
                for f in punct_faults(ln):
                    print(f"   line {i} PUNCT {f}: {ln.strip()[:110]}")
                    bad += 1
            for c in COUNTS:
                for m in re.finditer(c, ln, re.I):
                    print(f"   line {i} warn, counts what failed? ...{ln[max(0, m.start() - 40):m.end() + 40]}...")
        if src:
            plain = MAC.sub(lambda m: m.group(2), t).replace("**", "").replace("*", "")
            quotes = re.findall(r'"([^"\n]{5,})"', norm(plain))
            for ln in plain.split("\n"):
                s = ln.strip()
                if s.startswith(">"):
                    q = re.sub(r"^>\s*", "", s)
                    q = re.sub(r"^[A-Z]\d+[.:]\s*", "", q).strip().strip('"').strip()
                    if len(q) >= 5:
                        quotes.append(q)
            seen = set()
            for q in quotes:
                if norm(q).lower() in seen:
                    continue
                seen.add(norm(q).lower())
                for part in [x.strip(" .,") for x in re.split(r"…|\.\.\.|\[\.\.\.\]", norm(q)) if x.strip(" .,")]:
                    if len(part) >= 5 and not any(part.lower() in s for s in src):
                        print(f"   QUOTE NOT FOUND: {part[:100]!r}")
                        bad += 1
        for m in MAC.finditer(t):
            print(f"   color {m.group(1):10s} {len(m.group(2)):3d} characters: {m.group(2)}")
    print(f"{len(texts)} blocks checked; {'no faults' if not bad else str(bad) + ' faults'}"
          + ("" if src else "; quotations not checked (no --sources)"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
