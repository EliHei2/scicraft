#!/usr/bin/env python3
"""Draw the reply texts the way a Markdown review platform shows them, and write the paste-ready files.

    python3 preview_replies.py replies.md out/
    python3 preview_replies.py replies.md out/ --fold R2=followup_R2.md --limit 5000 --docx "round 2 texts.docx"

Input: the same block file as check_replies.py. Each block header is
    <<<<< key | title | readers >>>>>
for example  <<<<< R2 | Response to Reviewer R2 | everyone >>>>>  or  <<<<< AC | Note to the Area Chair | Area Chairs and Program Chairs >>>>>.
Output in out/:
  <key>.md       each text exactly as it is pasted (one file per comment)
  preview.html   white cards on light grey: title, readers and character count, a copy button, then the rendered
                 Markdown. A reviewer's message given with --fold key=file is shown folded above the reply to it.
                 Colored MathJax phrases $\\color{c}{\\textsf{...}}$ are drawn as colored text that does not wrap.
  --docx FILE    a Word file holding the Markdown source as plain text, one paragraph per line, for co-authors who
                 edit and paste from it (needs python-docx).
Rendering follows CommonMark with tables, with raw HTML off and single line breaks ignored, which is how one
platform behaved in late 2026; check the venue's own preview before posting, because renderers differ.

Needs markdown-it-py (pip install markdown-it-py); python-docx only for --docx. Exit code 1 when a block is over
--limit.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover
    sys.exit("preview_replies.py needs markdown-it-py: pip install markdown-it-py")

HEADER = re.compile(r"^<<<<<\s*(.*?)\s*>>>>>\s*$")
MAC = re.compile(r"\$\\color\{(\w+)\}\{\\textsf\{(.*?)\}\}\$")
CSS = """
body{background:#f5f5f5;font-family:"Noto Sans","Helvetica Neue",Helvetica,Arial,sans-serif;font-size:13.5px;line-height:1.5;color:#2c3a4a;margin:0;padding:24px 16px}
.note{background:#fff;border:1px solid #ddd;border-radius:2px;max-width:860px;margin:0 auto 22px;padding:14px 18px 10px}
.head{font-weight:700;font-size:15px;color:#3e6775}.meta{color:#8c1b13;font-size:11.5px;margin:2px 0 10px}.meta a{color:#3e6775}
.over{color:#c00;font-weight:700}
.fold summary{cursor:pointer;list-style:none}.fold summary::-webkit-details-marker{display:none}.fold .hint{color:#888;font-size:11.5px;margin-left:10px}.fold[open] summary{margin-bottom:10px}
.body p{margin:0 0 10px}.body blockquote{border-left:4px solid #ddd;margin:10px 0;padding:2px 12px;color:#666}.body blockquote p{margin:0}
.body table{border-collapse:collapse;margin:8px 0 12px;font-size:12.5px;display:block;overflow-x:auto;max-width:100%}.body th,.body td{border:1px solid #ddd;padding:4px 9px;text-align:left;vertical-align:top}.body th{background:#fafafa}
.body .mj{white-space:nowrap}
.body ol,.body ul{margin:0 0 10px 0;padding-left:26px}.body li{margin-bottom:6px}
@media print{body{background:#fff;padding:0}.note{border-color:#ccc}}
"""
JS = """
var SRC=JSON.parse(document.getElementById('src').textContent);
document.querySelectorAll('[data-copy]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();var x=SRC[a.getAttribute('data-copy')],l=a.textContent;
var done=function(){a.textContent='copied';setTimeout(function(){a.textContent=l;},1500);};
var fb=function(){var ta=document.createElement('textarea');ta.value=x;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(err){}ta.remove();};
if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(x).then(done,fb);else fb();});});
"""


def read_blocks(path: Path):
    blocks, key = {}, None
    for ln in path.read_text(encoding="utf-8").split("\n"):
        m = HEADER.match(ln)
        if m:
            parts = [p.strip() for p in m.group(1).split("|")]
            key = parts[0]
            blocks[key] = {"title": parts[1] if len(parts) > 1 else key,
                           "readers": parts[2] if len(parts) > 2 else "", "lines": []}
        elif key is not None:
            blocks[key]["lines"].append(ln)
    for b in blocks.values():
        b["text"] = "\n".join(b.pop("lines")).strip("\n")
    return blocks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("replies")
    ap.add_argument("out")
    ap.add_argument("--fold", action="append", default=[], help="key=file: a reviewer message shown folded above that reply")
    ap.add_argument("--limit", type=int, default=5000, help="characters per comment (default 5000)")
    ap.add_argument("--docx", help="also write a Word file with the Markdown source as plain text")
    ap.add_argument("--title", default="Reply preview", help="page title")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    blocks = read_blocks(Path(a.replies))
    folds = dict(f.split("=", 1) for f in a.fold)
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "breaks": False}).enable("table")
    render = lambda s: MAC.sub(r'<span class="mj" style="color:\1">\2</span>', md.render(s))  # noqa: E731
    esc = lambda s: html.escape(s, quote=True)  # noqa: E731
    cards, over = [], 0
    for key, b in blocks.items():
        n = len(b["text"])
        over += n > a.limit
        (out / f"{key}.md").write_text(b["text"] + "\n", encoding="utf-8")
        print(f"{key:8s} {n:5d} characters" + ("  OVER" if n > a.limit else ""))
        if key in folds:
            msg = Path(folds[key]).read_text(encoding="utf-8").strip()
            cards.append(f'<details class="note fold"><summary><span class="head">Message this replies to</span>'
                         f'<span class="hint">click to show or hide</span></summary><div class="body">{render(msg)}</div></details>')
        count = f'<span class="over">{n:,} of {a.limit:,} characters</span>' if n > a.limit else f"{n:,} of {a.limit:,} characters"
        readers = f"readers: {esc(b['readers'])} &middot; " if b["readers"] else ""
        cards.append(f'<div class="note"><div class="head">{esc(b["title"])}</div><div class="meta">{readers}{count} &middot; '
                     f'<a href="#" data-copy="{esc(key)}">copy Markdown</a></div><div class="body">{render(b["text"])}</div></div>')
    src = json.dumps({k: b["text"] for k, b in blocks.items()}).replace("</", "<\\/")
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(a.title)}</title><style>{CSS}</style></head><body>{"".join(cards)}'
            f'<script type="application/json" id="src">{src}</script><script>{JS}</script></body></html>')
    (out / "preview.html").write_text(page, encoding="utf-8")
    if a.docx:
        try:
            from docx import Document
            from docx.shared import Pt
        except ImportError:
            sys.exit("--docx needs python-docx: pip install python-docx")
        doc = Document()
        doc.styles["Normal"].font.name = "Arial"
        doc.styles["Normal"].font.size = Pt(10.5)
        doc.styles["Normal"].paragraph_format.space_after = Pt(0)
        for key, b in blocks.items():
            doc.add_heading(f"{b['title']}" + (f" (readers: {b['readers']})" if b["readers"] else "") + f", {len(b['text']):,} characters", 1)
            for ln in b["text"].split("\n"):
                doc.add_paragraph(ln)
        doc.save(out / a.docx)
    print("wrote", out)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
