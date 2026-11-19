#!/usr/bin/env python3
"""List every \\rev{...} passage of a revised paper with its section and the unchanged
text just before it.

Uses: an edit list for a reply letter (what changed, where); a check that every
promised change is marked; moving the revision onto the exact submitted source when
the working folder turns out to hold an older draft.

  extract_rev_passages.py main.tex sections/*.tex -o REV_PASSAGES.md
  extract_rev_passages.py main.tex --macro latest     list \\latest{} passages instead

Needs Python 3.9+ (standard library only).
"""
import argparse
import re
import sys
from pathlib import Path

HEAD = re.compile(r"\\(section|subsection|subsubsection|paragraph|rwpara)\*?\{([^{}]*)\}")


def strip_comments(s):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", l) for l in s.split("\n"))


def spans(s, macro):
    """(start, arg_start, arg_end) of each \\macro{...}, braces balanced."""
    for m in re.finditer(r"\\" + macro + r"\{", s):
        depth, i = 1, m.end()
        while i < len(s) and depth:
            if s[i - 1] != "\\":
                depth += {"{": 1, "}": -1}.get(s[i], 0)
            i += 1
        yield m.start(), m.end(), i - 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--macro", default="rev")
    ap.add_argument("-o", "--out", help="write Markdown here (default: print)")
    a = ap.parse_args()
    out = [f"# \\{a.macro}{{}} passages", ""]
    n = 0
    for name in a.files:
        s = strip_comments(Path(name).read_text(encoding="utf-8", errors="replace"))
        heads = [(m.start(), m.group(2)) for m in HEAD.finditer(s)]
        for start, b, e in spans(s, a.macro):
            sec = next((h for pos, h in reversed(heads) if pos < start), "(before the first heading)")
            anchor = re.sub(r"\s+", " ", s[max(0, start - 220):start]).strip()[-160:]
            line = s.count("\n", 0, start) + 1
            n += 1
            out += [f"## {n}. {name}:{line} :: {sec}", "", f"after: `...{anchor}`", "", "```latex",
                    f"\\{a.macro}{{{s[b:e].strip()}}}", "```", ""]
    text = "\n".join(out)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out} with {n} passages")
    else:
        print(text)
        print(f"{n} passages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
