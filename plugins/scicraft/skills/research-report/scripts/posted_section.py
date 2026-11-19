#!/usr/bin/env python3
"""Generate the "replies as posted" section of an internal report from the paste-ready reply files.

When an internal report records a rebuttal or a reply to co-authors, the replies are inserted as posted, generated
from the files that were pasted (for example the <key>.md files written by the rebuttal skill's preview_replies.py),
never copied by hand. Re-run after every change to the replies, so the report and the posted text cannot drift.

    python3 posted_section.py "General response=out/general.md" "Reviewer R1=out/R1.md" --insert code/report.html
    python3 posted_section.py "Reply to the co-authors=reply.md" --format tex --insert report/main.tex
    python3 posted_section.py "Reply=reply.md" --out posted.html        # write the fragment alone
    python3 posted_section.py --self-test

Each part is TITLE=FILE, in the order the section shows them. Markdown subset read: #, ## and ### headers,
**bold**, *italic*, "- " bullets, pipe tables, $inline$ and $$display$$ math (kept as TeX).

--format html (default) writes a collapsed appendix block, <details id="posted">, with each reply inside a
<blockquote>, so check_report.py skips banned words in text that must stay as posted. Math becomes \\( \\) and
\\[ \\], which build_report.py pre-renders. --format tex writes a \\section with \\subsection* per part; bullets
and table rows become paragraphs, so a docx converter that cannot read list or tabular environments still works.

--insert FILE replaces what lies between the two marker lines and leaves the rest of FILE byte-identical:
    html:  <!-- posted-replies:start -->   ...   <!-- posted-replies:end -->
    tex:   % posted-replies:start          ...   % posted-replies:end
It fails when the markers are missing or appear more than once.

Standard library only, Python 3.9+. Exit 0 on success, 1 on a missing file or marker, 2 on a failed self-test.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

MARKERS = {
    "html": ("<!-- posted-replies:start -->", "<!-- posted-replies:end -->"),
    "tex": ("% posted-replies:start", "% posted-replies:end"),
}
MATH = re.compile(r"(\$[^$\n]+\$)")
TABLE_RULE = re.compile(r"^\|\s*:?-{2,}")


# ---------- inline text ----------

def inline_html(s: str) -> str:
    out = []
    for i, piece in enumerate(MATH.split(s)):
        if i % 2:
            out.append(r"\(" + html.escape(piece[1:-1], quote=False) + r"\)")
            continue
        p = html.escape(piece, quote=False)
        p = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", p)
        p = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<i>\1</i>", p)
        out.append(p)
    return "".join(out)


def inline_tex(s: str) -> str:
    out = []
    for i, piece in enumerate(MATH.split(s)):
        if i % 2:
            out.append(piece)
            continue
        p = piece.replace("\\", r"\textbackslash{}")
        for ch in "%&#_{}":
            p = p.replace(ch, "\\" + ch)
        p = p.replace("\\textbackslash\\{\\}", r"\textbackslash{}")
        for u, t in (("\u2212", "$-$"), ("\u2264", r"$\leq$"), ("\u2265", r"$\geq$"), ("\u00d7", r"$\times$"),
                     ("\u00b5", r"$\mu$")):
            p = p.replace(u, t)
        p = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", p)
        p = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"\\emph{\1}", p)
        out.append(p)
    return "".join(out)


# ---------- block conversion ----------

def convert(md: str, fmt: str) -> str:
    inl = inline_html if fmt == "html" else inline_tex
    lines, out, para, items = md.splitlines(), [], [], []

    def flush_para():
        if para:
            txt = inl(" ".join(x.strip() for x in para))
            out.append(f"<p>{txt}</p>" if fmt == "html" else txt + "\n")
            para.clear()

    def flush_items():
        if items:
            if fmt == "html":
                out.append("<ul>" + "".join(f"<li>{inl(x)}</li>" for x in items) + "</ul>")
            else:
                out.extend(r"\textbullet{} " + inl(x) + "\n" for x in items)
            items.clear()

    def flush():
        flush_para()
        flush_items()

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not TABLE_RULE.match(lines[i]):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[1:]
            if fmt == "html":
                th = "".join(f"<th>{inl(c)}</th>" for c in head)
                tb = "".join("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in r) + "</tr>" for r in body)
                out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>")
            else:
                for r in body:
                    cells = "; ".join(f"{h} {v}" for h, v in zip(head[1:], r[1:]))
                    out.append(r"\textbullet{} " + inl(f"**{r[0]}**: " + cells) + "\n")
            continue
        d = re.match(r"^\$\$(.+)\$\$([,.;]?)\s*$", ln.strip())
        if d:
            flush()
            body = d.group(1) + d.group(2)
            if fmt == "html":
                out.append(r"<p>\[" + html.escape(body, quote=False) + r"\]</p>")
            elif len(body) > 170:  # a long display equation is scaled to the line width
                out.append("\\[\\resizebox{\\linewidth}{!}{$\\displaystyle " + body + "$}\\]\n")
            else:
                out.append("\\[" + body + "\\]\n")
            i += 1
            continue
        m = re.match(r"^#{1,3}\s+(.*)", ln)
        if m:
            flush()
            out.append(f"<h4>{inl(m.group(1))}</h4>" if fmt == "html"
                       else r"\subsubsection*{" + inl(m.group(1)) + "}\n")
        elif re.match(r"^\s*-\s+", ln):
            flush_para()
            items.append(re.sub(r"^\s*-\s+", "", ln))
        elif not ln.strip():
            flush()
        else:
            flush_items()
            para.append(ln)
        i += 1
    flush()
    return "\n".join(out)


def section(parts, fmt: str, heading: str, note: str) -> str:
    if fmt == "html":
        body = [f'<details id="posted"><summary>{html.escape(heading)}</summary>',
                f"<p>{html.escape(note)}</p>"]
        for title, md in parts:
            body += [f"<h3>{html.escape(title)}</h3>", "<blockquote>", convert(md, fmt), "</blockquote>"]
        body.append("</details>")
    else:
        body = [r"\section{" + inline_tex(heading) + r"}\label{sec:posted}", inline_tex(note), ""]
        for title, md in parts:
            body += [r"\subsection*{" + inline_tex(title) + "}", convert(md, fmt), ""]
    return "\n".join(body) + "\n"


def insert(target: str, block: str, fmt: str) -> str:
    start, end = MARKERS[fmt]
    if target.count(start) != 1 or target.count(end) != 1:
        raise ValueError(f"need exactly one '{start}' and one '{end}' line")
    a = target.index(start) + len(start)
    b = target.index(end)
    if b < a:
        raise ValueError("the end marker comes before the start marker")
    return target[:a] + "\n" + block + target[b:]


# ---------- self-test ----------

def self_test() -> int:
    md = ("## Point 1\nThe gap is **1.5 points** at *3 seeds*; see $\\Delta = 1.5$.\n\n"
          "- first item with 10_000 steps\n- second & last\n\n"
          "| Model | Error | Seeds |\n|---|---|---|\n| A | 0.12 | 3 |\n\n$$x^2 + y^2 = z^2$$.\n")
    parts = [("Reviewer R1", md)]
    h = section(parts, "html", "Replies as posted", "As posted on [date].")
    t = section(parts, "tex", "Replies as posted", "As posted on [date].")
    checks = [
        ("html bold", "<b>1.5 points</b>" in h),
        ("html italic", "<i>3 seeds</i>" in h),
        ("html inline math", r"\(\Delta = 1.5\)" in h),
        ("html display math", r"\[x^2 + y^2 = z^2.\]" in h),
        ("html list", "<ul><li>first item with 10_000 steps</li><li>second &amp; last</li></ul>" in h),
        ("html table", "<th>Error</th>" in h and "<td>0.12</td>" in h),
        ("html quoted", h.count("<blockquote>") == 1),
        ("tex escapes", r"10\_000" in t and r"second \& last" in t),
        ("tex math kept", r"$\Delta = 1.5$" in t),
        ("tex table row", r"\textbf{A}: Error 0.12; Seeds 3" in t),
        ("tex section", r"\section{Replies as posted}\label{sec:posted}" in t),
    ]
    page = "<main>\nA\n<!-- posted-replies:start -->\nold text\n<!-- posted-replies:end -->\nZ\n</main>\n"
    once = insert(page, h, "html")
    twice = insert(once, h, "html")
    checks += [("insert replaces", "old text" not in once and h in once),
               ("insert idempotent", once == twice),
               ("insert keeps rest", once.startswith("<main>\nA\n") and once.endswith("<!-- posted-replies:end -->\nZ\n</main>\n"))]
    try:
        insert("no markers", h, "html")
        checks.append(("missing marker fails", False))
    except ValueError:
        checks.append(("missing marker fails", True))
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(("PASS " if ok else "FAIL ") + n)
    print(f"self-test: {len(checks) - len(bad)} of {len(checks)} passed")
    return 2 if bad else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="*", help='TITLE=FILE, one per reply, in display order')
    ap.add_argument("--format", choices=("html", "tex"), default="html")
    ap.add_argument("--heading", default="Replies as posted", help="section heading")
    ap.add_argument("--note", default="The replies as posted. Table, figure and appendix numbers refer to the "
                                      "revised paper, not to this report.", help="one line under the heading")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--insert", type=Path, help="report source to update between the marker lines")
    g.add_argument("--out", type=Path, help="write the fragment to this file")
    ap.add_argument("--self-test", action="store_true", help="run the built-in checks and exit")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())
    if not a.parts:
        ap.error("give at least one TITLE=FILE part (or --self-test)")
    parts = []
    for p in a.parts:
        if "=" not in p:
            ap.error(f"part '{p}' is not TITLE=FILE")
        title, f = p.split("=", 1)
        path = Path(f)
        if not path.is_file():
            print(f"FAILED: reply file not found: {path}", file=sys.stderr)
            sys.exit(1)
        parts.append((title.strip(), path.read_text(encoding="utf-8")))
    block = section(parts, a.format, a.heading, a.note)
    if a.insert:
        try:
            new = insert(a.insert.read_text(encoding="utf-8"), block, a.format)
        except (OSError, ValueError) as e:
            print(f"FAILED: {a.insert}: {e}", file=sys.stderr)
            sys.exit(1)
        a.insert.write_text(new, encoding="utf-8")
        print(f"updated {a.insert}: {len(parts)} replies between the markers")
    elif a.out:
        a.out.write_text(block, encoding="utf-8")
        print(f"wrote {a.out}: {len(parts)} replies")
    else:
        sys.stdout.write(block)


if __name__ == "__main__":
    main()
