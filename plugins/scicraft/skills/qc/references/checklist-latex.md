# Paper and book build gate

For a LaTeX paper, revision, camera-ready or book, after every batch of edits and before any PDF leaves. How to
typeset is in `latex-typesetting`; how to mark a revision is in `rebuttal`. This is the gate.

## Before revising: prove you hold the right source

A working folder can hold an older draft. One did (15.6% sentence match against the submitted PDF), and a page
count compared against it declared a revision in budget that was three pages over. Before revising, match the
source to the PDF of record:

```bash
pdftotext -layout submitted.pdf submitted.txt
python3 - <<'EOF'
import re
def grams(t, n=6):
    w = re.findall(r'[a-z]+', t.lower()); return {' '.join(w[i:i+n]) for i in range(len(w) - n)}
tex = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?|[{}$%]', ' ', open('main.tex').read())
a, b = grams(tex), grams(open('submitted.txt').read())
print(f'{len(a & b) / max(1, len(a)):.0%} of source 6-grams found in the PDF')
EOF
```

A source scores about 70% against its own PDF (macros, floats and hyphenation take the rest); an older draft
scores far lower. Get the export of record before editing if it does not match.

## Scripted, every build

```bash
bash <skill>/scripts/latex_gate.sh main.tex /tmp/gate --pages 10
```

- **Build in a scratch folder and install only after the gate passes.** The author never sees a half-built PDF.
- **Four pdflatex passes after bibtex, and fail if the log still says "Rerun to get".** A clean three-pass build
  left 64 of 76 contents, figure-list and table-list page numbers wrong in one book.
- **Zero**: `! ` errors, undefined references, undefined citations, overfull boxes, headheight warnings (a long
  running head: `\section[short]{long}`).
- **Page budget measured, never guessed.** `pdfinfo` for the page count; where the main text ends (render the end
  of the last allowed page and the start of the next; "main text ends on page 10" was the gate); report the spare
  lines in every status ("no spare line, so any addition has to replace something").
- **Page fill measured after each build, against a stated target.** `pdftotext -bbox-layout` gives the free points
  per page (the sibling `latex-typesetting` skill ships `locate_text.py --fill` for it). Hold a target such as every
  page at least 75% full; the source work started at 80% and relaxed it to 74% when the breaks got tight. Fix in
  this order: move a lead paragraph after its figure, reorder floats, add a keep-together guard before headings,
  cut a repeated sentence to a cross-reference, set the bibliography `\footnotesize` with `\bibsep 0pt plus 1pt`,
  shorten long bibliography entries. Note in the project memory where the breaks are tight.
- **Chapter start pages unchanged** after an edit that should not move them; compare `\contentsline` page numbers
  between two builds' `.toc` to find where pages appear.
- **Fonts embedded**: `pdffonts main.pdf | awk 'NR>2 && $(NF-4)=="no"'` prints nothing. No Type 3 fonts where the
  venue forbids them.
- **Raster resolution**: for each image, its pixel size against its printed box (PyMuPDF `page.get_image_rects`);
  flag anything under the venue's minimum.
- **Cited keys against the bibliography**: every key cited in the main file and appendices is defined, or aliased;
  cite keys used in the main text are never renamed.
- **Banned strings in the extracted text**, not the source: `pdftotext -layout main.pdf - | grep -nE 'PATTERN'`
  for old names, the author's banned words, `??`, `XXX`, `TODO`, doubled words, em dashes if banned. When a Word
  copy is delivered too, extract its text and run the same list on it: `sweep_terms.py --list banned.txt main.pdf
  main.docx` reads both. The final scan of one reply package printed "pdf hits: none / docx hits: none".
- **A removal is verified in every output, and what remains is reported.** When the author asks for something to
  be removed, grep for it in the built PDF text, the Word text, every content file, every generated table and the
  live figure code (`sweep_terms.py --term "[the removed thing]" main.pdf main.docx content/ tables/ code/`).
  Report each remaining hit in one line with where it is, and offer to cut it. Never report "removed" while a hit
  remains. Asked "there's no [removed analysis] right?", one sweep found a single phrase left (about a use, not the
  analysis) and offered to cut it. Text in images escapes the sweep: an image "removed" by clipping stayed embedded
  in a figure PDF, so check with `pdfimages -list` too.
- **Line references re-resolved after every rebuild.** Any text change before a cited passage shifts it; an
  introduction rewrite shifted eight references in one reply. Anchor each cited passage by a short unique phrase
  and resolve it to line numbers in the built PDF's layout text each time.
- **Revision colors**: one color for everything that differs from the submitted version, decided against the
  submitted PDF, never against the markup; check text colors in the built PDF (PyMuPDF `page.get_text("dict")`
  spans carry a color). A revision mark that opens with a space (`\new{ text}`) leaves a colored space; grep for it.
- **External links**: each URL resolves (one venue guide link was a 404).

## With eyes

Render the changed pages and a contact sheet (`page_stills.py`) and read them:

- a float stranded on a mostly empty float page (a `\FloatBarrier` stranded figures on 43 to 62% full pages and
  cost pages; dropping `p` from `[!tbp]` forced top placement);
- a wrapped figure whose caption prints over the body text (17 lines reserved where the caption needed 18 or 19);
- a near-empty last page of a chapter, a one-word last line, a heading alone at the bottom of a page;
- every changed caption against the figure it describes;
- the title page and the signed statement rendered (spaced capitals do not extract as words, so grep cannot check them).

## Formal requirements (book, camera-ready)

- Title identical everywhere it appears: title page, PDF metadata, signed statement, any echo in the text.
- Abstracts in two languages correspond sentence for sentence; every edit to one is mirrored in the other in the
  same turn.
- The AI-use statement agrees across the signed statement, the disclosures page and the captions of generated figures.
- Abbreviation list against usage; every abbreviation defined before first use.
- PDF title and author metadata, a bookmark for the contents, size under the upload cap.
- A text-only copy for a similarity check when required (`\PassOptionsToPackage{draft}{graphicx}` before the main
  file, two passes reusing the full build's aux files).
- A print copy with black text and color figures, and the count of color pages, when a print shop needs it: render
  each page, count a page as color when more than 12 pixels have a channel spread above 28 of 255 at 60 dpi.

## Hand over

The PDF of record, its light copy if a channel needs it, the changed-files zip tested in a clean folder, and the
page and line state in the report (pages, where the main text ends, spare lines, characters per reply).
