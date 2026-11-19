#!/usr/bin/env python3
"""Extract the paragraphs, comments and image references of a .docx to TSV without executing anything.

A .docx is a ZIP of XML files. This script reads `word/document.xml`, `word/comments.xml` and the
relationship file with `zipfile` and ElementTree only: no macro runs, no Word, no third-party parser.
Run it under `python3 -I` on a copy of the file, so nothing in the download's folder can shadow a module.

Output (one TSV, header first), one row per paragraph and per comment:
    kind      para | comment
    index     paragraph number in the body (0-based), or the comment id
    style     the paragraph style id (Heading1, Caption, ...), empty for a comment
    anchor    for a comment: the index of the paragraph where the comment starts
    images    media files the paragraph shows (word/media/...), separated by commas
    text      the text, tabs and line breaks folded to spaces

Grep the TSV for the claim. Reviewer comments name a claim as often as the text does, and the `images`
column ties each legend paragraph to the panel it sits beside.

Standard library only. Python 3.9 or later.

Examples:
    python3 -I docx_paras.py copy/manuscript.docx > paras.tsv
    python3 -I docx_paras.py copy/manuscript.docx --only comment
    python3 -I docx_paras.py --self-test

Exit status: 0 on success, 2 when the file is missing or is not a .docx.
"""
import argparse
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
V = "urn:schemas-microsoft-com:vml"


def q(ns, tag):
    return f"{{{ns}}}{tag}"


def clean(s):
    return " ".join(s.replace("\t", " ").split())


def para_text(p):
    out = []
    for el in p.iter():
        if el.tag == q(W, "t"):
            out.append(el.text or "")
        elif el.tag in (q(W, "tab"), q(W, "br"), q(W, "cr")):
            out.append(" ")
    return clean("".join(out))


def rels(z):
    try:
        root = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    except KeyError:
        return {}
    return {r.get("Id"): r.get("Target", "") for r in root.iter(q(REL, "Relationship"))}


def para_images(p, relmap):
    ids = [b.get(q(R, "embed")) for b in p.iter(q(A, "blip"))]
    ids += [d.get(q(R, "id")) for d in p.iter(q(V, "imagedata"))]
    out = []
    for i in ids:
        t = relmap.get(i)
        if t:
            t = t.lstrip("/")                      # targets are relative to word/, or absolute from the root
            out.append(t if t.startswith("word/") else "word/" + t)
    return ",".join(out)


def extract(path):
    rows = []
    with zipfile.ZipFile(path) as z:
        doc = ET.fromstring(z.read("word/document.xml"))
        relmap = rels(z)
        body = doc.find(q(W, "body"))
        comment_anchor = {}
        paras = list(body.iter(q(W, "p"))) if body is not None else []
        for i, p in enumerate(paras):
            st = p.find(f"{q(W, 'pPr')}/{q(W, 'pStyle')}")
            style = st.get(q(W, "val")) if st is not None else ""
            for cs in p.iter(q(W, "commentRangeStart")):
                comment_anchor.setdefault(cs.get(q(W, "id")), i)
            for cr in p.iter(q(W, "commentReference")):
                comment_anchor.setdefault(cr.get(q(W, "id")), i)
            rows.append(("para", str(i), style, "", para_images(p, relmap), para_text(p)))
        if "word/comments.xml" in z.namelist():
            croot = ET.fromstring(z.read("word/comments.xml"))
            for c in croot.iter(q(W, "comment")):
                cid = c.get(q(W, "id"))
                text = clean(" ".join(para_text(p) for p in c.iter(q(W, "p"))))
                anchor = comment_anchor.get(cid, "")
                rows.append(("comment", cid, "", str(anchor), "", text))
    return rows


def write_tsv(rows, out, only=None):
    out.write("kind\tindex\tstyle\tanchor\timages\ttext\n")
    for r in rows:
        if only and r[0] != only:
            continue
        out.write("\t".join(r) + "\n")


def _make_sample(path):
    doc = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:a="{A}"><w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Methods</w:t></w:r></w:p>
<w:p><w:commentRangeStart w:id="0"/><w:r><w:t xml:space="preserve">Boundaries use a concave </w:t></w:r>
<w:r><w:t>hull</w:t><w:tab/><w:t>as in tool Y.</w:t></w:r><w:commentRangeEnd w:id="0"/>
<w:r><w:commentReference w:id="0"/></w:r></w:p>
<w:p><w:r><w:drawing><a:graphic><a:graphicData><a:blip r:embed="rId5"/></a:graphicData></a:graphic></w:drawing></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Caption"/></w:pPr><w:r><w:t>Figure 1. Accuracy per task.</w:t></w:r></w:p>
</w:body></w:document>"""
    comments = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:comments xmlns:w="{W}"><w:comment w:id="0" w:author="Reviewer"><w:p><w:r>
<w:t>Is this really the algorithm of tool Y?</w:t></w:r></w:p></w:comment></w:comments>"""
    rel = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL}"><Relationship Id="rId5" Type="image" Target="media/image1.png"/></Relationships>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", doc)
        z.writestr("word/comments.xml", comments)
        z.writestr("word/_rels/document.xml.rels", rel)
        z.writestr("word/media/image1.png", b"\x89PNG")


def self_test():
    import io
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "sample.docx")
        _make_sample(p)
        rows = extract(p)
        paras = [r for r in rows if r[0] == "para"]
        comments = [r for r in rows if r[0] == "comment"]
        assert len(paras) == 4, paras
        assert paras[0][2] == "Heading1", paras[0]
        assert paras[1][5] == "Boundaries use a concave hull as in tool Y.", paras[1][5]
        assert paras[2][4] == "word/media/image1.png", paras[2]
        assert paras[3][2] == "Caption", paras[3]
        assert len(comments) == 1 and comments[0][3] == "1", comments
        assert "algorithm of tool Y" in comments[0][5], comments
        buf = io.StringIO()
        write_tsv(rows, buf, only="comment")
        assert buf.getvalue().count("\n") == 2, buf.getvalue()
    print("self-test passed: 7 checks (styles, runs joined, tab folded, image mapped, caption, "
          "comment anchored, filter)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx", nargs="?", help="a copy of the .docx to read")
    ap.add_argument("--only", choices=["para", "comment"], help="write only paragraphs or only comments")
    ap.add_argument("--self-test", action="store_true", help="build a small .docx, check the output, exit")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.docx:
        ap.error("give a .docx file")
    try:
        rows = extract(a.docx)
    except FileNotFoundError:
        print(f"no such file: {a.docx}", file=sys.stderr)
        return 2
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        print(f"not a readable .docx: {a.docx} ({e})", file=sys.stderr)
        return 2
    write_tsv(rows, sys.stdout, a.only)
    n_p = sum(r[0] == "para" for r in rows)
    n_c = sum(r[0] == "comment" for r in rows)
    print(f"# {n_p} paragraphs, {n_c} comments", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
