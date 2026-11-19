#!/usr/bin/env python3
"""Check a bibliography against the citations in the TeX source, and optionally against Crossref.

Offline checks (always):
  ERROR  cited key with no entry (prints "?" in the PDF)
  ERROR  NEEDS_CITATION placeholder still in the source
  ERROR  duplicate key in the .bib files
  ERROR  two keys of one work inside a single \\cite (prints "?" with an alias table)
  WARN   two entries for one work (same DOI or same normalized title): print it once,
         keep both keys working with an alias, never rename a key the text uses
  WARN   article or proceedings entry without a DOI
  WARN   title with an all-caps word or a CamelCase name not protected by braces
         (sentence-casing styles such as plainnat lower-case it)
  INFO   arXiv or bioRxiv-only entry: check whether it has since been published
  INFO   entry never cited: park it in a file that is not \\input, do not delete it silently

Network check (only with --crossref, run by the user, needs internet):
  for each entry with a DOI, fetch https://api.crossref.org/works/<DOI> and compare the
  title, the year and the first author's family name. Set CROSSREF_MAILTO in the
  environment to join Crossref's polite pool.

  bib_check.py --tex main.tex sections/*.tex --bib refs.bib
  bib_check.py --tex main.tex --bib refs.bib --crossref
  bib_check.py --tex main.tex          (manual thebibliography: keys from \\bibitem)

Exit 1 on any ERROR (and, with --crossref, on any mismatch). The script never edits
the .bib file.

Needs Python 3.9+ (standard library only).
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

CITE = re.compile(r"\\(?:[cC]ite[a-zA-Z]*|[pP]arencite|[tT]extcite|nocite)\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
ALIAS = re.compile(r"\\bibkeyalias\{([^}]+)\}\{([^}]+)\}")


def read_braced(s, i):
    """s[i] is '{' or '"'. Return (content, index after the closing delimiter)."""
    if s[i] == '"':
        j, depth = i + 1, 0
        while j < len(s):
            if s[j] == "{":
                depth += 1
            elif s[j] == "}":
                depth -= 1
            elif s[j] == '"' and depth == 0:
                return s[i + 1:j], j + 1
            j += 1
        return s[i + 1:], len(s)
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def parse_bib(path):
    """Return a list of (key, type, fields) in file order."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    out = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        etype, key = m.group(1).lower(), m.group(2)
        if etype in ("comment", "string", "preamble"):
            continue
        body, _ = read_braced(text, text.index("{", m.start()))
        fields, i = {}, body.index(",") + 1 if "," in body else len(body)
        while i < len(body):
            fm = re.compile(r"\s*([A-Za-z_\-]+)\s*=\s*").match(body, i)
            if not fm:
                break
            name, j = fm.group(1).lower(), fm.end()
            if j < len(body) and body[j] in '{"':
                val, j = read_braced(body, j)
            else:
                vm = re.compile(r"[^,]*").match(body, j)
                val, j = vm.group(0).strip(), vm.end()
            fields[name] = " ".join(val.split())
            k = body.find(",", j)
            i = k + 1 if k >= 0 else len(body)
        out.append((key, etype, fields))
    return out


def norm_title(t):
    t = unicodedata.normalize("NFKD", t)
    t = re.sub(r"\\[a-zA-Z]+|[{}$\\]", "", t)
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def unprotected_caps(title):
    """Words with capitals beyond the first letter that sit outside braces."""
    depth, buf, outside = 0, "", []
    for ch in title:
        if ch == "{":
            if depth == 0:
                outside.append(buf)
                buf = ""
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0:
            buf += ch
    outside.append(buf)
    words = " ".join(outside).split()
    # a capital after a lower-case letter (ImageNet) or two capitals in a row (GNN);
    # hyphenated title case (Gradient-Based) is fine
    return [w for w in words if any(re.search(r"[a-z][A-Z]|[A-Z]{2}", part) for part in w.strip(".,:;()?").split("-"))]


def strip_comments(s):
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in s.splitlines())


def crossref(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    mail = os.environ.get("CROSSREF_MAILTO")
    if mail:
        url += "?mailto=" + urllib.parse.quote(mail)
    req = urllib.request.Request(url, headers={"User-Agent": "bib-check/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)["message"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tex", nargs="+", required=True, help="every .tex file that cites (main, sections, appendices)")
    ap.add_argument("--bib", nargs="*", default=[], help=".bib files; omit for a manual thebibliography")
    ap.add_argument("--crossref", action="store_true", help="also verify DOIs on Crossref (network; run it yourself)")
    a = ap.parse_args()

    errors, warns, infos = [], [], []
    tex = {p: strip_comments(Path(p).read_text(encoding="utf-8", errors="replace")) for p in a.tex}
    cited, groups = {}, []
    for p, s in tex.items():
        for m in CITE.finditer(s):
            keys = [k.strip() for k in m.group(1).split(",") if k.strip()]
            groups.append((p, keys))
            for k in keys:
                cited.setdefault(k, p)
        for i, line in enumerate(s.splitlines(), 1):
            if "NEEDS_CITATION" in line:
                errors.append(f"{p}:{i}: NEEDS_CITATION placeholder")
    aliases = {}
    for s in tex.values():
        for m in ALIAS.finditer(s):
            aliases[m.group(1)] = m.group(2)

    entries = []
    for b in a.bib:
        entries += parse_bib(b)
    if not a.bib:
        for p, s in tex.items():
            for m in re.finditer(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", s):
                entries.append((m.group(1).strip(), "bibitem", {}))
    keys = {}
    for k, t, f in entries:
        if k in keys:
            errors.append(f"duplicate key in bibliography: {k}")
        keys[k] = (t, f)

    for k, p in sorted(cited.items()):
        if k == "*":
            continue
        if k not in keys and aliases.get(k) not in keys:
            errors.append(f"cited but not in the bibliography: {k} (first in {p})")
    for p, ks in groups:
        resolved = [aliases.get(k, k) for k in ks]
        dup = {r for r in resolved if resolved.count(r) > 1}
        if dup:
            errors.append(f"{p}: one \\cite holds two keys of one work: {', '.join(ks)}")

    by_doi, by_title = {}, {}
    for k, (t, f) in keys.items():
        doi = f.get("doi", "").lower().replace("https://doi.org/", "")
        if doi:
            by_doi.setdefault(doi, []).append(k)
        nt = norm_title(f.get("title", ""))
        if nt:
            by_title.setdefault(nt, []).append(k)
        if t in ("article", "inproceedings") and not doi:
            warns.append(f"{k}: {t} without a DOI")
        caps = unprotected_caps(f.get("title", ""))
        if caps:
            warns.append(f"{k}: unbraced capitals in title: {' '.join(caps[:6])}")
        blob = " ".join(f.get(x, "") for x in ("journal", "booktitle", "eprint", "archiveprefix", "publisher", "note")).lower()
        if ("arxiv" in blob or "biorxiv" in blob) and t not in ("inproceedings",) and "doi" not in f:
            infos.append(f"{k}: preprint only; check whether it has been published since")
        if k not in cited and k not in aliases.values():
            infos.append(f"{k}: never cited (park it in a file that is not \\input; keep the key)")
    same_work = {}
    for d, ks in by_doi.items():
        for k in ks:
            same_work[k] = d
    for p, ks in groups:
        ds = [same_work[k] for k in ks if k in same_work]
        if len(ds) != len(set(ds)):
            errors.append(f"{p}: one \\cite holds two keys of one work: {', '.join(ks)}")
    for d, ks in by_doi.items():
        if len(ks) > 1:
            warns.append(f"one work under several keys (DOI {d}): {', '.join(ks)}")
    for t, ks in by_title.items():
        if len(ks) > 1 and not any(set(ks) <= set(v) for v in by_doi.values()):
            warns.append(f"one work under several keys (title): {', '.join(ks)}")

    mism = []
    if a.crossref:
        for k, (t, f) in keys.items():
            doi = f.get("doi", "").replace("https://doi.org/", "")
            if not doi:
                continue
            try:
                msg = crossref(doi)
            except Exception as e:  # network or 404
                mism.append(f"{k}: Crossref lookup failed for {doi}: {e}")
                continue
            ct = (msg.get("title") or [""])[0]
            sim = SequenceMatcher(None, norm_title(ct), norm_title(f.get("title", ""))).ratio()
            year = None
            for fld in ("published-print", "published-online", "issued"):
                parts = (msg.get(fld) or {}).get("date-parts") or [[None]]
                if parts[0][0]:
                    year = str(parts[0][0])
                    break
            fam = ((msg.get("author") or [{}])[0].get("family") or "").lower()
            bib_first = re.split(r"\s+and\s+", f.get("author", ""))[0]
            bib_fam = (bib_first.split(",")[0] if "," in bib_first else bib_first.split()[-1:] or [""])
            bib_fam = (bib_fam if isinstance(bib_fam, str) else bib_fam[0]).strip("{} ").lower()
            probs = []
            if sim < 0.9:
                probs.append(f"title differs ({sim:.2f}): Crossref '{ct[:70]}'")
            if year and f.get("year") and f["year"] != year:
                probs.append(f"year {f['year']} vs Crossref {year}")
            if fam and bib_fam and norm_title(fam) != norm_title(bib_fam):
                probs.append(f"first author '{bib_fam}' vs Crossref '{fam}'")
            if probs:
                mism.append(f"{k}: " + "; ".join(probs))
            else:
                print(f"crossref ok  {k}")

    print(f"checked {len(cited)} cited keys against {len(keys)} entries in {len(a.tex)} tex file(s)")
    for tag, items in (("ERROR", errors), ("MISMATCH", mism), ("WARN", warns), ("INFO", infos)):
        for x in items:
            print(f"{tag:8s} {x}")
    if not a.crossref:
        print("not checked: Crossref (run with --crossref when online)")
    return 1 if errors or mism else 0


if __name__ == "__main__":
    sys.exit(main())
