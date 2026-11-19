#!/usr/bin/env python3
"""Check a built report (the offline HTML from build_report.py) against the report shape, and preview its PDF.

Checks, in order (ERROR fails the run, WARN is for a person to judge):
  offline    no <script>, <link>, @import, remote src/href/url(), un-inlined image          ERROR
  opening    one answer sentence (p.answer), then a "Summary." paragraph of three sentences  WARN
             no glossary, terms, definitions or limits box before section 1                  ERROR
  openers    every numbered section opens with one bold sentence (class "msg") of <= 30 words WARN
             no bold run of more than one sentence anywhere in the body                      WARN
  figures    captions "Figure R1." .. and "Figure S1." .. numbered in reading order, no gaps  ERROR
             every Fig. Rn / Sn cited in the text exists; every main figure is cited          ERROR / WARN
             more than --max-main-figures main figures (default 10)                          WARN
             every <img> has alt text and sits in a <figure> with a <figcaption>              WARN
  words      banned words (whole words, visible text outside <blockquote>/<q>), --banned    ERROR
             em and en dashes in visible text                                                WARN
  counts     words in summary, main text, captions and appendix; --max-main-words limit      report / ERROR
  --list-bare  prints main-text sentences that hold no digit, for a person to keep or cut
  --pdf FILE --previews DIR  page count, one PNG per page and a contact sheet (needs PyMuPDF; Pillow for the sheet)

Dependencies: Python 3.9+ standard library; PyMuPDF and Pillow only for --previews.

Example:
  python3 check_report.py out/Ablation_report.html --banned ../assets/banned_words.txt \
      --pdf out/Ablation_report.pdf --previews out/pages
"""
from __future__ import annotations

import argparse
import html as htmlmod
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_report import offline_problems  # noqa: E402

TOP_BOXES = re.compile(r"\b(glossary|terms|definitions|limits|limitations|caveats|key terms)\b", re.I)
ABBREV = ("Fig.", "Figs.", "e.g.", "i.e.", "et al.", "vs.", "approx.", "Eq.", "Sec.", "No.", "Supp.", "cf.")


def visible(fragment: str) -> str:
    t = re.sub(r"<svg\b.*?</svg>", " [math] ", fragment, flags=re.S | re.I)
    t = re.sub(r"<(style|script)\b.*?</\1>", " ", t, flags=re.S | re.I)
    t = re.sub(r'src="data:[^"]+"', "", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return " ".join(htmlmod.unescape(t).split())


def sentences(text: str):
    guard = text
    for i, ab in enumerate(ABBREV):
        guard = guard.replace(ab, f"ABBR{i}Q")
    # A sentence ends at . ! or ?, optionally followed by a closing bracket or quote, then space and a capital.
    parts = re.split(r"""(?:(?<=[.!?])|(?<=[.!?][\])"']))\s+(?=[A-Z0-9\[("])""", guard.strip())
    out = []
    for p in parts:
        for i, ab in enumerate(ABBREV):
            p = p.replace(f"ABBR{i}Q", ab)
        if p.strip():
            out.append(p.strip())
    return out


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][\w'.,%-]*", text))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("report", type=Path, help="the built .html")
    ap.add_argument("--banned", type=Path, action="append", default=[],
                    help="file with one banned word or phrase per line (# comments); repeatable")
    ap.add_argument("--max-main-words", type=int, help="fail when the main text is longer")
    ap.add_argument("--max-main-figures", type=int, default=10)
    ap.add_argument("--list-bare", action="store_true", help="print main-text sentences without a digit")
    ap.add_argument("--pdf", type=Path, help="the printed PDF, for page previews")
    ap.add_argument("--previews", type=Path, help="folder for page PNGs and contact.png (use a fresh one each round)")
    a = ap.parse_args()

    page = a.report.read_text(encoding="utf-8")
    errors, warns = [], []
    m = re.search(r"<main\b.*?</main>", page, re.S)
    main = m.group(0) if m else page

    # offline
    for p in offline_problems(page):
        errors.append(f"offline: {p}")

    # split: opening (before first numbered h2), sections, supplementary, appendix
    h2s = list(re.finditer(r"<h2\b[^>]*>(.*?)</h2>", main, re.S))
    numbered = [h for h in h2s if re.match(r"\s*\d", visible(h.group(1)))]
    first = numbered[0].start() if numbered else len(main)
    opening = main[:first]
    supp_at = next((h.start() for h in h2s if re.search(r"supplement", visible(h.group(1)), re.I)), None)
    app_at = next((h.start() for h in h2s if re.search(r"appendix", visible(h.group(1)), re.I)), None)
    tail = min([x for x in (supp_at, app_at) if x is not None], default=len(main))
    body = main[first:tail]

    # opening
    lede = re.search(r"<p\b[^>]*>\s*<(?:b|strong)>\s*Summary\.?\s*</(?:b|strong)>(.*?)</p>", opening, re.S)
    summary_words = 0
    if not lede:
        warns.append('opening: no paragraph that starts with a bold "Summary." before section 1')
    else:
        s = sentences(visible(lede.group(1)))
        summary_words = words(visible(lede.group(1)))
        if len(s) != 3:
            warns.append(f"opening: the summary has {len(s)} sentences; the accepted form has three")
        if opening.find(lede.group(0)) > opening.find("<h2") > -1:
            warns.append("opening: the summary is not the first block after the title")
    ans = re.search(r'<p class="answer">(.*?)</p>', opening, re.S)
    if not ans:
        warns.append('opening: no one-sentence answer line (p.answer) above the summary')
    else:
        na = len(sentences(visible(ans.group(1))))
        if na != 1:
            warns.append(f"opening: the answer line has {na} sentences; the accepted form has one")
        if lede and opening.find(ans.group(0)) > opening.find(lede.group(0)):
            warns.append("opening: the answer line comes after the summary; put it on top")
    for h in re.finditer(r"<(h2|h3|summary|b|strong)\b[^>]*>(.*?)</\1>", opening, re.S):
        t = visible(h.group(2))
        if TOP_BOXES.search(t) and len(t) < 40:
            errors.append(f"opening: a '{t}' heading or box before section 1; define each term where it is used")

    # openers
    for i, h in enumerate(numbered):
        end = numbered[i + 1].start() if i + 1 < len(numbered) else tail
        sec = main[h.end():end]
        title = visible(h.group(1))
        mm = re.match(r'\s*<p class="msg">(.*?)</p>', sec, re.S)
        if not mm:
            warns.append(f"openers: section '{title}' does not open with a bold one-sentence lead (p.msg)")
            continue
        t = visible(mm.group(1))
        if len(sentences(t)) > 1 or words(t) > 30:
            warns.append(f"openers: section '{title}' lead is {len(sentences(t))} sentence(s), {words(t)} words")
    for b in re.finditer(r"<(b|strong)\b[^>]*>(.*?)</\1>", main, re.S):
        t = visible(b.group(2))
        if len(sentences(t)) > 1 and words(t) > 25:
            warns.append(f"openers: bold run of {words(t)} words: '{t[:70]}...'")

    # figures
    caps = [(mm.group(1), int(mm.group(2))) for mm in
            re.finditer(r"<figcaption\b[^>]*>\s*(?:<(?:b|strong)>)?\s*Figure\s+([RS])(\d+)\.", main)]
    for kind in "RS":
        nums = [n for k, n in caps if k == kind]
        if nums and nums != list(range(1, len(nums) + 1)):
            errors.append(f"figures: {kind} figures appear in the order {nums}; expected 1..{len(nums)}")
    have = {f"{k}{n}" for k, n in caps}
    text_wo_caps = re.sub(r"<figcaption\b.*?</figcaption>", " ", main, flags=re.S)
    cited = set()
    for mm in re.finditer(r"\bFig(?:ure|s)?\.?\s+((?:[RS]\d+(?:\s*(?:,|and|to|-)\s*)?)+)", visible(text_wo_caps)):
        cited |= set(re.findall(r"[RS]\d+", mm.group(1)))
    for c in sorted(cited - have):
        errors.append(f"figures: Fig. {c} is cited but no caption 'Figure {c}.' exists")
    for c in sorted(x for x in have - cited if x.startswith("R")):
        warns.append(f"figures: Figure {c} is never cited in the text or the TL;DR")
    nmain = sum(1 for k, _ in caps if k == "R")
    if nmain > a.max_main_figures:
        warns.append(f"figures: {nmain} main figures; keep about {a.max_main_figures} and move the rest to S")
    for img in re.finditer(r"<img\b[^>]*>", main):
        if not re.search(r'\balt="[^"]+"', img.group(0)):
            warns.append("figures: an <img> without alt text")
    nfig = len(re.findall(r"<figure\b", main))
    ncap = len(re.findall(r"<figcaption\b", main))
    if ncap < nfig:
        warns.append(f"figures: {nfig - ncap} <figure> element(s) without a caption")

    # words
    vis = visible(main)
    # A quoted question (<blockquote> or <q>) is kept word for word, so banned words inside it are allowed.
    vis_own = visible(re.sub(r"<(blockquote|q)\b.*?</\1>", " ", main, flags=re.S | re.I))
    for f in a.banned:
        for line in f.read_text(encoding="utf-8").splitlines():
            w = line.split("#", 1)[0].strip()
            if not w:
                continue
            for hit in re.finditer(rf"(?<![\w-]){re.escape(w)}(?![\w-])", vis_own, re.I):
                ctx = vis_own[max(0, hit.start() - 50):hit.end() + 30]
                errors.append(f"words: banned '{w}' in '...{ctx}...'")
    nd = len(re.findall(r"[—–]", vis))
    if nd:
        warns.append(f"words: {nd} em or en dash(es) in the visible text")

    # counts
    cap_words = sum(words(visible(c)) for c in re.findall(r"<figcaption\b.*?</figcaption>", main, re.S))
    main_text = visible(re.sub(r"<figcaption\b.*?</figcaption>", " ", body, flags=re.S))
    app_words = words(visible(main[app_at:])) if app_at is not None else 0
    print(f"counts   summary {summary_words} words; main text {words(main_text)} words in {len(numbered)} sections; "
          f"captions {cap_words} words; appendix {app_words} words; figures R{nmain} S{sum(1 for k, _ in caps if k == 'S')}")
    if a.max_main_words and words(main_text) > a.max_main_words:
        errors.append(f"counts: main text {words(main_text)} words > {a.max_main_words}")
    if a.list_bare:
        bare = [s for s in sentences(main_text) if not re.search(r"\d", s)]
        print(f"bare     {len(bare)} main-text sentence(s) without a digit (keep only those that state a decision):")
        for s in bare:
            print(f"         - {s}")

    # previews
    if a.pdf:
        try:
            import fitz  # type: ignore
        except ImportError:
            warns.append("previews: PyMuPDF not installed; open the PDF and read every page yourself")
            fitz = None
        if fitz is not None:
            doc = fitz.open(str(a.pdf))
            print(f"pdf      {a.pdf} has {doc.page_count} page(s)")
            if a.previews:
                a.previews.mkdir(parents=True, exist_ok=True)
                paths = []
                for i, pg in enumerate(doc):
                    p = a.previews / f"p{i + 1:02d}.png"
                    pg.get_pixmap(dpi=110).save(str(p))
                    paths.append(p)
                try:
                    from PIL import Image  # type: ignore
                    ims = [Image.open(p) for p in paths]
                    w, h = ims[0].size
                    cols = min(4, len(ims))
                    rows = (len(ims) + cols - 1) // cols
                    sheet = Image.new("RGB", (cols * w // 2, rows * h // 2), "white")
                    for i, im in enumerate(ims):
                        sheet.paste(im.resize((w // 2, h // 2)), ((i % cols) * w // 2, (i // cols) * h // 2))
                    sheet.save(a.previews / "contact.png")
                    print(f"previews {len(paths)} page PNGs and contact.png in {a.previews}")
                except ImportError:
                    print(f"previews {len(paths)} page PNGs in {a.previews} (Pillow missing: no contact sheet)")

    for w in warns:
        print(f"WARN     {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"result   {len(errors)} error(s), {len(warns)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
