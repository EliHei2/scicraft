"""Shared text preparation for the humanizer scripts. Standard library only, Python 3.9 or later.

Turns a .tex, .md or plain-text file into prose lines (line numbers kept) so that counts and diffs see the
sentences a reader sees: TeX comments, math, citation and label commands, Markdown code and link targets are
removed. Imported by frame_density.py and preserve_diff.py. Run on its own
(`python3 textprep.py FILE`) it prints the prose lines those scripts count.
"""
from __future__ import annotations

import re
from pathlib import Path

TEX_COMMENT = re.compile(r"(?<!\\)%.*$")
TEX_DISPLAY_ENVS = ("equation", "align", "gather", "multline", "eqnarray", "displaymath", "math", "verbatim",
                    "lstlisting", "minted", "tikzpicture", "tabular")
TEX_BEGIN = re.compile(r"\\begin\{(%s)\*?\}" % "|".join(TEX_DISPLAY_ENVS))
TEX_END = re.compile(r"\\end\{(%s)\*?\}" % "|".join(TEX_DISPLAY_ENVS))
TEX_REFCMD = re.compile(r"\\(?:cite\w*|ref|eqref|cref|Cref|autoref|pageref|label|url|href|includegraphics)\*?"
                        r"(?:\[[^\]]*\])*\{[^}]*\}")
TEX_INLINE_MATH = re.compile(r"\$[^$]*\$|\\\([^)]*\\\)")
MD_INLINE_CODE = re.compile(r"`[^`]*`")
MD_LINK_TARGET = re.compile(r"\]\([^)]*\)")
URL = re.compile(r"https?://\S+")


def detect_format(path: Path, fmt: str = "auto") -> str:
    if fmt != "auto":
        return fmt
    ext = path.suffix.lower()
    if ext in (".tex", ".sty", ".cls"):
        return "tex"
    if ext in (".md", ".markdown", ".rmd", ".qmd"):
        return "md"
    if ext in (".html", ".htm"):
        return "html"
    return "txt"


def strip_tex_comments(text: str) -> str:
    return "\n".join(TEX_COMMENT.sub("", line) for line in text.splitlines())


def prose_lines(text: str, fmt: str):
    """Yield (line number, prose) with code, math and reference commands blanked out."""
    in_env = in_fence = in_display = False
    for i, line in enumerate(text.splitlines(), 1):
        if fmt == "tex":
            line = TEX_COMMENT.sub("", line)
            if in_env:
                if TEX_END.search(line):
                    in_env = False
                continue
            if TEX_BEGIN.search(line):
                in_env = not TEX_END.search(line)
                continue
            if "\\[" in line and "\\]" not in line:
                in_display = True
                continue
            if in_display:
                if "\\]" in line:
                    in_display = False
                continue
            line = re.sub(r"\\\[.*?\\\]", " ", line)
            line = TEX_REFCMD.sub(" ", line)
            line = TEX_INLINE_MATH.sub(" ", line)
        elif fmt == "md":
            s = line.strip()
            if s.startswith("```") or s.startswith("~~~"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = MD_INLINE_CODE.sub(" ", line)
            line = MD_LINK_TARGET.sub("]", line)
        elif fmt == "html":
            line = re.sub(r"<[^>]+>", " ", line)
        line = URL.sub(" ", line)
        yield i, line


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*|\d+(?:\.\d+)?", text))


def sentences(text: str) -> list:
    flat = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\\$])", flat)
    return [p.strip() for p in parts if len(p.strip().split()) >= 4]


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Print the prose lines that frame_density.py and preserve_diff.py "
                                             "count, so you can see what was stripped.")
    ap.add_argument("file", type=Path)
    ap.add_argument("--format", default="auto", choices=["auto", "tex", "md", "txt", "html"])
    a = ap.parse_args()
    fmt = detect_format(a.file, a.format)
    lines = list(prose_lines(a.file.read_text(encoding="utf-8", errors="replace"), fmt))
    for i, t in lines:
        if t.strip():
            print(f"{i:>5}  {t}")
    print(f"\n{fmt}: {words(chr(10).join(t for _, t in lines))} words of prose")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
