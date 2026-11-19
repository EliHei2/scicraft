#!/usr/bin/env python3
"""Prove that a rewrite changed the wording and nothing else: numbers, citations, labels, equations, code.

Usage:
    python3 preserve_diff.py BEFORE AFTER [--format auto|tex|md|txt|html] [--json OUT.json]

Run it on the snapshot taken before a humanizer pass and on the result. It checks:

  numbers        the multiset of numeric tokens (regex \\d+(?:\\.\\d+)?) is identical; numbers that appear only
                 after the pass are listed as added, the ones that vanished as missing
  citations      the set of keys in \\cite-family commands (and pandoc [@key] in Markdown), both directions
  labels, refs   the sets of \\label keys and of \\ref/\\eqref/\\cref/\\autoref targets, both directions
  equations      the count of numbered display environments (equation, align, gather, multline, eqnarray,
                 unstarred) and of all display math
  braces         TeX brace balance is unchanged
  code, links    in Markdown and plain text: inline code spans, fenced code blocks and link targets (URLs)
                 are byte-identical, since the prose may change and code may not
  duplicates     sentences that occur twice after the pass but did not before
  length         the word count of the prose and its change in percent

Why: an edit for style is read for style, so a dropped number or citation slips through by eye. In the
technical register a careful pass lengthens the text by about 3 to 5 percent (one measured run went from
35,000 to 36,274 words with every label, citation and equation intact). A shorter result usually means facts
were deleted, so a shorter text is reported as a warning to read the cuts one by one. In the general register,
cutting a closer or a filler paragraph shortens the text legitimately; the warning still asks you to look.

Exit status: 1 when any number, key, label, reference, equation count, brace balance, code span, code block or
link target differs, or a new duplicate sentence appears; 0 otherwise (warnings do not fail).
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textprep import detect_format, prose_lines, sentences, strip_tex_comments, words  # noqa: E402

NUM = re.compile(r"\d+(?:\.\d+)?")
CITE = re.compile(r"\\(?:cite|citep|citet|citealp|citealt|citeauthor|citeyear|parencite|textcite|autocite|"
                  r"footcite|nocite)\*?(?:\[[^\]]*\])*\{([^}]*)\}")
PANDOC_CITE = re.compile(r"(?<![\w.])@([A-Za-z][\w:.\-]*\w)")
LABEL = re.compile(r"\\label\{([^}]*)\}")
REF = re.compile(r"\\(?:ref|eqref|cref|Cref|autoref|pageref|vref|nameref)\*?\{([^}]*)\}")
NUMBERED_EQ = re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray|flalign|alignat)\}")
ANY_DISPLAY = re.compile(r"\\begin\{(?:equation|align|gather|multline|eqnarray|flalign|alignat|displaymath)\*?\}"
                         r"|\\\[|\$\$")
INLINE_CODE = re.compile(r"`[^`\n]+`")
FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)
LINK = re.compile(r"\]\(([^)\s]+)[^)]*\)|https?://[^\s)>\]]+")


def keys(rx, text):
    out = []
    for m in rx.finditer(text):
        out += [k.strip() for k in m.group(1).split(",") if k.strip()]
    return out


def facts(path: Path, fmt: str):
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_tex_comments(raw) if fmt == "tex" else raw
    prose = "\n".join(t for _, t in prose_lines(raw, fmt))
    f = {
        "numbers": Counter(NUM.findall(text)),
        "citations": Counter(keys(CITE, text) + (PANDOC_CITE.findall(text) if fmt == "md" else [])),
        "labels": Counter(keys(LABEL, text)),
        "refs": Counter(keys(REF, text)),
        "numbered equations": len(NUMBERED_EQ.findall(text)),
        "display math": len(ANY_DISPLAY.findall(text)),
        "brace balance": text.count("{") - text.count("}") if fmt == "tex" else 0,
        "inline code": Counter(INLINE_CODE.findall(text)) if fmt != "tex" else Counter(),
        "code blocks": Counter(m.group(0) for m in FENCE.finditer(text)) if fmt != "tex" else Counter(),
        "link targets": Counter(m.group(1) or m.group(0) for m in LINK.finditer(text)),
        "words": words(prose),
        "sentences": Counter(sentences(prose)),
    }
    return f


def main():
    ap = argparse.ArgumentParser(description="Check that a rewrite kept every number, citation, label, "
                                             "equation and code span.")
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--format", default="auto", choices=["auto", "tex", "md", "txt", "html"])
    ap.add_argument("--json", type=Path, help="also write the findings to this file")
    a = ap.parse_args()
    fmt = detect_format(a.after, a.format)
    b, c = facts(a.before, fmt), facts(a.after, fmt)
    errors, warnings, out = [], [], {}

    for k in ("numbers", "citations", "labels", "refs", "inline code", "code blocks", "link targets"):
        missing = b[k] - c[k]
        added = c[k] - b[k]
        ok = not missing and not added
        out[k] = {"before": sum(b[k].values()), "after": sum(c[k].values()),
                  "missing": dict(missing), "added": dict(added)}
        print(f"  {k:<18} before {sum(b[k].values()):>5}  after {sum(c[k].values()):>5}  {'ok' if ok else 'DIFFERS'}")
        if missing:
            errors.append(f"{k} missing after the pass: {short(missing)}")
        if added:
            errors.append(f"{k} added by the pass: {short(added)}")
    for k in ("numbered equations", "display math", "brace balance"):
        ok = b[k] == c[k]
        out[k] = {"before": b[k], "after": c[k]}
        print(f"  {k:<18} before {b[k]:>5}  after {c[k]:>5}  {'ok' if ok else 'DIFFERS'}")
        if not ok:
            errors.append(f"{k}: {b[k]} before, {c[k]} after")
    dup_new = [s for s, n in c["sentences"].items() if n > 1 and b["sentences"].get(s, 0) < n]
    out["new duplicate sentences"] = dup_new
    print(f"  {'new duplicates':<18} {len(dup_new)}  {'ok' if not dup_new else 'DIFFERS'}")
    if dup_new:
        errors.append("sentences now repeated: " + " | ".join(s[:80] for s in dup_new[:5]))
    wb, wa = b["words"], c["words"]
    delta = 100.0 * (wa - wb) / max(1, wb)
    out["words"] = {"before": wb, "after": wa, "delta_percent": round(delta, 2)}
    print(f"  {'words of prose':<18} before {wb:>5}  after {wa:>5}  ({delta:+.1f}%)")
    if wa < wb:
        warnings.append(f"the text got shorter by {wb - wa} words ({delta:+.1f}%). In technical prose a pass "
                        "usually lengthens it by 3 to 5%. Read every cut and confirm no fact went with it.")

    for e in errors:
        print("ERROR ", e)
    for w in warnings:
        print("warn  ", w)
    print("\nresult:", "FAIL" if errors else "pass", f"({len(errors)} error(s), {len(warnings)} warning(s))")
    if a.json:
        a.json.write_text(json.dumps({"errors": errors, "warnings": warnings, "checks": out}, indent=2))
    return 1 if errors else 0


def short(counter, n=12):
    items = [f"{k} x{v}" if v > 1 else str(k) for k, v in list(counter.items())[:n]]
    more = "" if len(counter) <= n else f" (+{len(counter) - n} more)"
    return ", ".join(items) + more


if __name__ == "__main__":
    sys.exit(main())
