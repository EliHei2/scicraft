#!/usr/bin/env python3
"""Apply edit pairs to a co-author's Word file and highlight only the words that changed.

    python3 docx_highlight.py IN.docx edits.json OUT.docx
    python3 docx_highlight.py IN.docx edits.json OUT.docx --color green --file main.tex
    python3 docx_highlight.py IN.docx edits.json OUT.docx --all        # replace every occurrence
    python3 docx_highlight.py IN.docx edits.json OUT.docx --dry-run    # report, write nothing
    python3 docx_highlight.py --self-test

edits.json is the same list that changelog.py and the sibling latex-typesetting skill's apply_tex_edits.py read:
    [{"id": "R2.1", "file": "main.tex", "old": "exact text", "new": "replacement"}, ...]
"old" and "new" must be the plain text as it reads in Word (no TeX macros). "file" is optional here; with --file,
only the pairs whose "file" equals that name are applied.

What it does:
  1. Finds each "old" in the text of a paragraph of word/document.xml, also when Word has split it across several
     runs (bold, italic, a spell-check mark, an rsid change). A match may not cross a tab, a line break, a field,
     a comment reference, an equation or the edge of a hyperlink or tracked change; such a pair is reported.
  2. Replaces it with "new" and compares old and new word by word. Only the inserted or changed words get a
     w:highlight; words the pair leaves unchanged stay unmarked. Every piece keeps the run properties (bold,
     italic, font, size) of the run it came from; an inserted word takes those of the word it replaces or follows.
     Deleted words cannot be highlighted and are listed in the report for the change log.
  3. Writes OUT with every other part of the package (styles, comments, numbering, media) byte-identical and every
     untouched paragraph of document.xml byte-identical. Then it counts paragraphs, comment references,
     equations (m:oMath), tables and footnote references in IN and OUT and prints both.

Exit code 1, with nothing written, when an "old" is not found, is found more than once without --all, or cannot
be replaced; and when OUT is IN. Exit code 1, with OUT removed, when any count or any other part differs.
Standard library only, Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
XML_NS = "http://www.w3.org/XML/1998/namespace"
DOC = "word/document.xml"
COLORS = ["yellow", "green", "cyan", "magenta", "blue", "red", "darkBlue", "darkCyan", "darkGreen",
          "darkMagenta", "darkRed", "darkYellow", "darkGray", "lightGray", "black"]
# schema order of the children of w:rPr; w:highlight goes after the last one that precedes it
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike", "outline",
             "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden", "color", "spacing", "w",
             "kern", "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign",
             "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"]
TOKEN = re.compile(r"\d+(?:[.,]\d+)*|\w+(?:['’-]\w+)*|\s+|[^\w\s]")
OBJECT = "￼"   # stands for anything in a paragraph that is not plain text; never matches an edit


def w(name: str) -> str:
    return f"{{{W}}}{name}"


def m(name: str) -> str:
    return f"{{{M}}}{name}"


NO_CHAR_RUN_CHILDREN = {w("rPr"), w("lastRenderedPageBreak"), w("softHyphen"), w("instrText"), w("delText")}
SKIP_CONTAINERS = {w("pPr"), w("del"), w("moveFrom")}
MARKERS = {w(n) for n in ("bookmarkStart", "bookmarkEnd", "commentRangeStart", "commentRangeEnd", "proofErr",
                          "permStart", "permEnd")}


# ---------------------------------------------------------------- package and namespaces

def root_namespaces(xml: str):
    """Prefix to URI map and the raw xmlns attributes of the root element of document.xml."""
    start = re.search(r"<(?!\?)(?!!)[^>]+>", xml)
    decls = re.findall(r'\sxmlns(?::([\w.-]+))?="([^"]*)"', start.group(0))
    nsmap = {p: u for p, u in decls}
    for p, u in decls:
        if p and not re.fullmatch(r"ns\d+", p):
            ET.register_namespace(p, u)
    raw = "".join(f' xmlns:{p}="{u}"' if p else f' xmlns="{u}"' for p, u in decls)
    return nsmap, raw


def counts(data: bytes) -> dict:
    c = Counter(el.tag for el in ET.fromstring(data).iter())
    return {"paragraphs": c[w("p")], "comment references": c[w("commentReference")], "equations": c[m("oMath")],
            "tables": c[w("tbl")], "footnote references": c[w("footnoteReference")]}


def leaf_paragraphs(xml: str, wp: str):
    """Spans of the paragraphs that contain no other paragraph (text boxes nest paragraphs), in document order."""
    tag = re.compile(rf"<(/?){re.escape(wp)}:p(?=[\s>/])[^>]*?(/?)>")
    stack, spans = [], []
    for t in tag.finditer(xml):
        if t.group(1):
            start, has_child = stack.pop()
            if not has_child:
                spans.append((start, t.end()))
            if stack:
                stack[-1][1] = True
        elif t.group(2):
            if stack:
                stack[-1][1] = True
        else:
            stack.append([t.start(), False])
    return sorted(spans)


def parse_fragment(frag: str, raw_ns: str):
    return ET.fromstring(f"<wrap{raw_ns}>{frag}</wrap>")[0]


def serialize(p, nsmap: dict) -> str:
    s = ET.tostring(p, encoding="unicode")
    return re.sub(r'\sxmlns:([\w.-]+)="([^"]*)"',
                  lambda x: "" if nsmap.get(x.group(1)) == x.group(2) else x.group(0), s)


# ---------------------------------------------------------------- text of a paragraph

def charmap(p):
    """One entry per character of paragraph text: (char, run, parent of run, child element, offset)."""
    chars = []

    def walk(el):
        for c in el:
            if c.tag == w("r"):
                for k in c:
                    if k.tag == w("t"):
                        chars.extend((ch, c, el, k, o) for o, ch in enumerate(k.text or ""))
                    elif k.tag in (w("tab"), w("ptab")):
                        chars.append(("\t", c, el, k, -1))
                    elif k.tag in (w("br"), w("cr")):
                        chars.append(("\n", c, el, k, -1))
                    elif k.tag not in NO_CHAR_RUN_CHILDREN:
                        chars.append((OBJECT, c, el, k, -1))
            elif c.tag in SKIP_CONTAINERS or c.tag in MARKERS:
                continue
            elif c.tag in (m("oMath"), m("oMathPara")):
                chars.append((OBJECT, None, el, c, -1))
            else:
                walk(c)   # hyperlink, ins, smartTag, sdt, sdtContent, fldSimple, customXml
    walk(p)
    return chars


def find_all(text: str, old: str):
    out, i = [], text.find(old)
    while i >= 0:
        out.append(i)
        i = text.find(old, i + len(old))
    return out


# ---------------------------------------------------------------- building runs

def make_t(text: str, like=None):
    t = ET.Element(w("t"), dict(like.attrib) if like is not None else {})
    t.text = text
    t.set(f"{{{XML_NS}}}space", "preserve")
    return t


def run_like(src, children, highlight=None):
    r = ET.Element(src.tag, dict(src.attrib))
    rpr = src.find(w("rPr"))
    rpr = copy.deepcopy(rpr) if rpr is not None else None
    if highlight:
        if rpr is None:
            rpr = ET.Element(w("rPr"))
        for h in rpr.findall(w("highlight")):
            rpr.remove(h)
        rank, pos = RPR_ORDER.index("highlight"), 0
        for n, c in enumerate(list(rpr)):
            name = c.tag[len(W) + 2:] if c.tag.startswith(f"{{{W}}}") else None
            if name in RPR_ORDER and RPR_ORDER.index(name) < rank:
                pos = n + 1
        rpr.insert(pos, ET.Element(w("highlight"), {w("val"): highlight}))
    if rpr is not None:
        r.append(rpr)
    r.extend(children)
    return r


def diff_pieces(old: str, new: str, src: list):
    """Characters of new with the run each comes from and whether it is highlighted; plus deleted words."""
    ot, nt = TOKEN.findall(old), TOKEN.findall(new)
    oo, no = [0], [0]
    for t in ot:
        oo.append(oo[-1] + len(t))
    for t in nt:
        no.append(no[-1] + len(t))
    out, deleted, inserted = [], [], []
    for tag, a1, a2, b1, b2 in difflib.SequenceMatcher(None, ot, nt, autojunk=False).get_opcodes():
        oa, ob, na, nb = oo[a1], oo[a2], no[b1], no[b2]
        if tag == "equal":
            out.extend((old[k], src[k], False) for k in range(oa, ob))
            continue
        if tag in ("replace", "delete") and old[oa:ob].strip():
            deleted.append(old[oa:ob].strip())
        if tag == "delete":
            continue
        run = src[oa] if tag == "replace" else (src[oa - 1] if oa > 0 else src[0])
        text = new[na:nb]
        lead, trail = len(text) - len(text.lstrip()), len(text.rstrip())
        out.extend((ch, run, lead <= k < trail) for k, ch in enumerate(text))
        if text.strip():
            inserted.append(text.strip())
    groups = []
    for ch, run, hl in out:
        if groups and groups[-1][1] is run and groups[-1][2] == hl:
            groups[-1][0] += ch
        else:
            groups.append([ch, run, hl])
    return groups, inserted, deleted


def replace_at(p, i: int, old: str, new: str, color: str):
    """Replace paragraph text [i, i+len(old)) in p. Returns (inserted, deleted) or raises ValueError."""
    cm = charmap(p)
    seg = cm[i:i + len(old)]
    if any(c[3].tag != w("t") for c in seg):
        raise ValueError("the old text spans a tab, break, field, comment reference or equation")
    parents = {id(c[2]) for c in seg}
    if len(parents) > 1:
        raise ValueError("the old text crosses the edge of a hyperlink, tracked change or content control")
    parent = seg[0][2]
    runs = list(dict.fromkeys(c[1] for c in seg))
    kids = list(parent)
    a = next(n for n, k in enumerate(kids) if k is runs[0])
    b = next(n for n, k in enumerate(kids) if k is runs[-1])
    run_ids = {id(r) for r in runs}
    keep = [k for k in kids[a:b + 1] if id(k) not in run_ids]   # bookmarks, comment ranges, empty runs

    r1, t1, o1 = seg[0][1], seg[0][3], seg[0][4]
    c1 = [c for c in r1 if c.tag != w("rPr")]
    n1 = next(n for n, c in enumerate(c1) if c is t1)
    head = [copy.deepcopy(c) for c in c1[:n1]] + ([make_t(t1.text[:o1], t1)] if o1 > 0 else [])
    rk, tk, ok = seg[-1][1], seg[-1][3], seg[-1][4]
    ck = [c for c in rk if c.tag != w("rPr")]
    nk = next(n for n, c in enumerate(ck) if c is tk)
    rest = tk.text[ok + 1:]
    tail = ([make_t(rest, tk)] if rest else []) + [copy.deepcopy(c) for c in ck[nk + 1:]]

    groups, inserted, deleted = diff_pieces(old, new, [c[1] for c in seg])
    new_kids = [run_like(r1, head)] if head else []
    new_kids += [run_like(run, [make_t(text)], color if hl else None) for text, run, hl in groups]
    new_kids += keep
    if tail:
        new_kids.append(run_like(rk, tail))
    for k in kids[a:b + 1]:
        parent.remove(k)
    for n, k in enumerate(new_kids):
        parent.insert(a + n, k)
    return inserted, deleted


# ---------------------------------------------------------------- one run over the document

def apply_edits(xml: str, edits: list, color: str, allow_all: bool):
    nsmap, raw = root_namespaces(xml)
    wp = next((pfx for pfx, u in nsmap.items() if u == W and pfx), "w")
    faults, report = [], []
    for n, e in enumerate(edits, 1):
        eid, old, new = e.get("id", f"#{n}"), e["old"], e["new"]
        if not old:
            faults.append(f"{eid}: empty 'old'")
            continue
        hits = []
        for s, t in leaf_paragraphs(xml, wp):
            p = parse_fragment(xml[s:t], raw)
            text = "".join(c[0] for c in charmap(p))
            pos = find_all(text, old)
            if pos:
                hits.append((s, t, p, pos))
        total = sum(len(h[3]) for h in hits)
        if total == 0:
            faults.append(f"{eid}: old text not found in any paragraph: {old[:70]!r}")
            continue
        if total > 1 and not allow_all:
            faults.append(f"{eid}: old text found {total} times (use --all to replace every one): {old[:70]!r}")
            continue
        try:
            for s, t, p, pos in reversed(hits):          # last paragraph first keeps earlier spans valid
                for i in reversed(pos):                    # last match first keeps earlier offsets valid
                    ins, dele = replace_at(p, i, old, new, color)
                xml = xml[:s] + serialize(p, nsmap) + xml[t:]
        except ValueError as err:
            faults.append(f"{eid}: {err}: {old[:70]!r}")
            continue
        report.append(f"{eid}: {total} place(s); highlighted {ins or '(nothing)'}"
                      + (f"; old words removed {dele} (deletions cannot be highlighted; list them in the change log)" if dele else ""))
    return xml, report, faults


def run(inp: Path, edits_path: Path, out: Path, color: str = "yellow", allow_all: bool = False,
        dry_run: bool = False, only_file: str = None) -> int:
    if out.resolve() == inp.resolve():
        print("FAULT OUT is IN: never write in place; give a new file name")
        return 1
    edits = json.loads(edits_path.read_text(encoding="utf-8"))
    if not isinstance(edits, list) or not all({"old", "new"} <= set(e) for e in edits):
        print("FAULT edits file must be a list of objects with old and new (and optionally id, file)")
        return 1
    if only_file:
        edits = [e for e in edits if e.get("file") == only_file]
    with zipfile.ZipFile(inp) as z:
        if DOC not in z.namelist():
            print(f"FAULT {inp} has no {DOC}")
            return 1
        before = z.read(DOC)
    xml, report, faults = apply_edits(before.decode("utf-8"), edits, color, allow_all)
    for line in report:
        print(line)
    for f in faults:
        print("FAULT", f)
    if faults:
        print(f"{len(faults)} faults; nothing written")
        return 1
    if dry_run:
        print(f"dry run: {len(edits)} pairs would apply; nothing written")
        return 0
    after = xml.encode("utf-8")
    with zipfile.ZipFile(inp) as zin, zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            zout.writestr(info, after if info.filename == DOC else zin.read(info.filename))
    return verify(inp, out)


def verify(inp: Path, out: Path) -> int:
    problems = []
    try:
        with zipfile.ZipFile(inp) as a, zipfile.ZipFile(out) as b:
            if a.namelist() != b.namelist():
                problems.append("the list of parts differs")
            for name in a.namelist():
                if name != DOC and name in b.namelist() and a.read(name) != b.read(name):
                    problems.append(f"{name} is not byte-identical")
            ca, cb = counts(a.read(DOC)), counts(b.read(DOC))
    except (zipfile.BadZipFile, ET.ParseError) as err:
        problems.append(f"output does not parse: {err}")
        ca = cb = {}
    for k in ca:
        print(f"{k:20s} in {ca[k]:5d}  out {cb[k]:5d}" + ("" if ca[k] == cb[k] else "   DIFFERS"))
        if ca[k] != cb[k]:
            problems.append(f"{k}: {ca[k]} in, {cb[k]} out")
    for pr in problems:
        print("FAULT", pr)
    if problems:
        out.unlink(missing_ok=True)
        print(f"{out} removed")
        return 1
    print(f"wrote {out}; count in equals count out; all other parts byte-identical")
    return 0


# ---------------------------------------------------------------- self-test

SAMPLE_NS = (f'xmlns:w="{W}" xmlns:m="{M}" '
             'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
             'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
             'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"')


def sample_docx(path: Path) -> None:
    body = (
        '<w:p w14:paraId="10000001"><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        '<w:r><w:t>Results</w:t></w:r></w:p>'
        '<w:p w14:paraId="10000002">'
        '<w:r><w:t xml:space="preserve">We find that the </w:t></w:r>'
        '<w:r><w:rPr><w:b/><w:sz w:val="24"/></w:rPr><w:t>model reaches</w:t></w:r>'
        '<w:proofErr w:type="spellStart"/>'
        '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:i/></w:rPr>'
        '<w:t xml:space="preserve"> a high score on the test set.</w:t></w:r>'
        '<w:proofErr w:type="spellEnd"/></w:p>'
        '<w:p w14:paraId="10000003"><w:commentRangeStart w:id="0"/>'
        '<w:r><w:t xml:space="preserve">We compare five methods </w:t></w:r><w:commentRangeEnd w:id="0"/>'
        '<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>'
        '<w:r><w:t xml:space="preserve">against one baseline.</w:t></w:r></w:p>'
        '<w:p w14:paraId="10000004"><w:r><w:t xml:space="preserve">The loss is </w:t></w:r>'
        '<m:oMath><m:r><m:t>L=a+b</m:t></m:r></m:oMath><w:r><w:t xml:space="preserve"> in total.</w:t></w:r>'
        '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="1"/></w:r></w:p>'
        '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/></w:tblPr><w:tblGrid><w:gridCol w:w="4000"/></w:tblGrid>'
        '<w:tr><w:tc><w:tcPr><w:tcW w:w="4000" w:type="dxa"/></w:tcPr>'
        '<w:p><w:r><w:t>A second baseline row</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>')
    doc = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {SAMPLE_NS}><w:body>{body}</w:body></w:document>'
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          '<Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>'
          '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="word/document.xml"/></Relationships>')
    drels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             f'<Relationship Id="rId1" Type="{rel}/styles" Target="styles.xml"/>'
             f'<Relationship Id="rId2" Type="{rel}/comments" Target="comments.xml"/>'
             f'<Relationship Id="rId3" Type="{rel}/footnotes" Target="footnotes.xml"/></Relationships>')
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles xmlns:w="{W}">'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
              '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>'
              '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style></w:styles>')
    comments = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:comments xmlns:w="{W}">'
                '<w:comment w:id="0" w:author="Reader" w:initials="R"><w:p><w:r><w:t>Which five?</w:t></w:r></w:p>'
                '</w:comment></w:comments>')
    foot = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:footnotes xmlns:w="{W}">'
            '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
            '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
            '<w:footnote w:id="1"><w:p><w:r><w:t>Summed over all terms.</w:t></w:r></w:p></w:footnote></w:footnotes>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in [("[Content_Types].xml", ct), ("_rels/.rels", rels), (DOC, doc),
                           ("word/_rels/document.xml.rels", drels), ("word/styles.xml", styles),
                           ("word/comments.xml", comments), ("word/footnotes.xml", foot)]:
            z.writestr(name, data)


def runs_of(path: Path):
    """(text, bold, italic, font, highlight) for every text run of document.xml."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read(DOC))
    out = []
    for r in root.iter(w("r")):
        text = "".join(t.text or "" for t in r.findall(w("t")))
        if not text:
            continue
        rpr = r.find(w("rPr"))
        get = (lambda tag: rpr.find(w(tag)) if rpr is not None else None)
        font = get("rFonts").get(w("ascii")) if get("rFonts") is not None else None
        hl = get("highlight").get(w("val")) if get("highlight") is not None else None
        out.append((text, get("b") is not None, get("i") is not None, font, hl))
    return out


def self_test() -> int:
    results = []

    def check(name, ok):
        results.append(ok)
        print(("ok    " if ok else "FAIL  ") + name)

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        src, out = d / "in.docx", d / "out.docx"
        sample_docx(src)
        edits = [{"id": "E1", "file": "main.tex", "old": "model reaches a high score",
                  "new": "model reaches a higher score"},
                 {"id": "E2", "file": "main.tex", "old": "We compare five methods",
                  "new": "We compare six methods"}]
        (d / "e.json").write_text(json.dumps(edits))
        check("two edits applied, exit 0", run(src, d / "e.json", out) == 0)
        rs = runs_of(out)
        full = "".join(r[0] for r in rs)
        check("new text in place", "the model reaches a higher score on the test set." in full
              and "We compare six methods" in full)
        check("only the changed words carry the highlight", sorted(r[0] for r in rs if r[4]) == ["higher", "six"])
        check("highlight has the requested color", all(r[4] == "yellow" for r in rs if r[4]))
        bold = [r for r in rs if r[0] == "model reaches"]
        check("bold run inside the pair kept bold and unmarked", len(bold) == 1 and bold[0][1] and not bold[0][4])
        hi = [r for r in rs if r[0] == "higher"]
        check("changed word keeps italic and font of its run", len(hi) == 1 and hi[0][2] and hi[0][3] == "Arial")
        check("unchanged neighbors keep their format", ("We find that the ", False, False, None, None) in rs
              and (" on the test set.", False, True, "Arial", None) in rs and (" a ", False, True, "Arial", None) in rs)
        with zipfile.ZipFile(src) as a, zipfile.ZipFile(out) as b:
            same = all(a.read(n) == b.read(n) for n in a.namelist() if n != DOC)
            ca, cb = counts(a.read(DOC)), counts(b.read(DOC))
            untouched = b.read(DOC).decode().count('<w:p w14:paraId="10000004">') == 1
        check("other parts byte-identical", same)
        check("counts match (1 comment, 1 equation, 1 table, 1 footnote)", ca == cb and cb["comment references"] == 1
              and cb["equations"] == 1 and cb["tables"] == 1 and cb["footnote references"] == 1)
        check("untouched paragraph byte-identical", untouched)

        def refused(pairs, **kw):
            (d / "bad.json").write_text(json.dumps(pairs))
            o = d / "bad.docx"
            return run(src, d / "bad.json", o, **kw) == 1 and not o.exists()
        check("missing old text refused, nothing written", refused([{"old": "seven methods", "new": "x"}]))
        check("double match refused without --all", refused([{"old": "baseline", "new": "reference"}]))
        (d / "all.json").write_text(json.dumps([{"old": "baseline", "new": "reference"}]))
        ok_all = run(src, d / "all.json", d / "all.docx", allow_all=True) == 0
        check("--all replaces both", ok_all and sum(r[0] == "reference" for r in runs_of(d / "all.docx")) == 2)
        check("old text across a comment reference refused",
              refused([{"old": "methods against", "new": "methods and"}]))
        check("OUT equal to IN refused", run(src, d / "e.json", src) == 1)
        check("dry run writes nothing", run(src, d / "e.json", d / "dry.docx", dry_run=True) == 0
              and not (d / "dry.docx").exists())
    n = len(results)
    print(f"{sum(results)} of {n} checks passed")
    return 0 if all(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("inp", nargs="?", help="the co-author's .docx")
    ap.add_argument("edits", nargs="?", help="edits.json: list of {id, file, old, new}")
    ap.add_argument("out", nargs="?", help="new .docx to write (never the input)")
    ap.add_argument("--color", default="yellow", choices=COLORS, help="highlight color (default yellow)")
    ap.add_argument("--all", action="store_true", help="replace every occurrence of an old text")
    ap.add_argument("--dry-run", action="store_true", help="find and report every pair, write nothing")
    ap.add_argument("--file", help="apply only the pairs whose 'file' equals this name")
    ap.add_argument("--self-test", action="store_true", help="run on a generated .docx and exit")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.inp and a.edits and a.out):
        ap.error("IN.docx, edits.json and OUT.docx are required")
    return run(Path(a.inp), Path(a.edits), Path(a.out), a.color, a.all, a.dry_run, a.file)


if __name__ == "__main__":
    sys.exit(main())
