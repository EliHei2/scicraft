# Build, gate, render, deliver

Read this before the first build of a project and before any PDF leaves your hands.

## Contents

1. The build
2. The gate
3. Rendering pages to look at them
4. The whole-document visual pass
5. Fonts and hidden text in figures
6. Print copy and color-page count
7. Size limits, previews and the text-only copy
8. What to say at hand-over

## 1. The build

**Build out of tree, gate on the log, and never trust the exit code.** The book's Makefile
recorded why: bibtex writes `main.bbl` into `build/`, pdflatex looks for it on TEXINPUTS from the
current folder, so without `TEXINPUTS=build:` "every \citep renders as [?], and the run still
exits 0". The shipped PDF had carried a bibliography-less body for a while before anyone read the
log. (Newer TeX Live versions also search the output folder; older ones and other distributions
do not, so set TEXINPUTS anyway.)

```bash
python3 scripts/build_latex.py main.tex                          # build/ + gate
python3 scripts/build_latex.py main.tex --max-main-page 9 --max-mb 50 --publish main.pdf
python3 scripts/build_latex.py main.tex --texinputs texshim      # shims kept outside the source
```

What `build_latex.py` does, step by step, so the same can be done by hand:

1. `mkdir -p build`
2. `TEXINPUTS=build:.: pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex`
   On failure, show the last 40 lines and stop.
3. If `build/main.aux` contains `\bibdata`:
   `(cd build && BIBINPUTS=..: BSTINPUTS=..: bibtex main)`; on failure grep
   `^(I couldn|Repeated|Warning--I didn)` in its output.
4. pdflatex again until the log no longer says `Rerun to get`, `Label(s) may have changed` or
   `Please rerun`, at least two passes after BibTeX, at most `--max-passes` (5). **Fail if it has
   not settled.** A clean three-pass build once left 64 of 76 contents and list page numbers wrong;
   the fix was a fourth pass and a gate on "Rerun".
5. Check that the PDF ends with `%%EOF` in its last 1024 bytes, then publish with an atomic rename
   (`--publish`), so nobody opens a half-written file.
6. Run `latex_gate.py` on the log.

- **pdflatex and BibTeX, never biber**, unless the project already uses biblatex and the install
  has biber. natbib with BibTeX worked on every machine met.
- Build in a scratch folder when other people or agents share the build folder.
- A long session fills the disk with scratch PDFs; delete scratch builds over 20 MB
  (`find <scratch> -name '*.pdf' -size +20M -delete`). A build once failed at pass 4 on a full disk.
- Variants from one source: `--variant print_colors.tex` (print copy),
  `--variant revision_clean.tex` (revision without color). The variant file is input just before
  `\begin{document}`, so line breaks stay identical.

## 2. The gate

`python3 scripts/latex_gate.py build/main.log [--max-main-page N] [--max-pages N] [--max-mb N]`
exits 1 on any failed gate and prints a state line. Gates and the defect each one caught:

| Gate | What it reads | Defect it catches |
|---|---|---|
| errors | `^! ` and `file:line:` lines | a run that continued past an error in nonstop mode |
| missing bbl | `No file main.bbl` | citations printed as [?] |
| undefined | `Reference ... undefined`, `Citation ... undefined` | "??" in the text |
| multiply defined | `Label ... multiply defined` | a second title page duplicating page labels |
| overfull | `Overfull \hbox (x pt too wide)` | text in the margin; `--overfull-pt` sets a tolerance (default 0) |
| float too large | `Float too large for page` | a table taller than the page |
| rerun | `Rerun to get`, `Label(s) may have changed` | stale contents and page numbers |
| headheight | `\headheight is too small` | fancyhdr heads shifting the text block |
| bibtex | `Warning--` and error lines in `.blg` | missing fields, unknown keys; target 0 warnings |
| fonts | `pdffonts`, emb column | an unembedded Helvetica from a plotting library |
| pages | `pdfinfo` | page count against a limit |
| main-text end | `\newlabel{mainend}` in `.aux` | the main text running past the page limit |
| size | file size | an upload limit (50 MB in one venue) |
| placeholders | `pdftotext`: `??`, `NEEDS_CITATION`, `[AUTHOR ACTION`, `TODO`, `FIXME` | unfinished text |

- Put `\label{mainend}` right after the last main-text sentence (before references or the
  checklist, as the venue counts) and pass `--max-main-page`.
- Fix a new overfull line at once (a discretionary hyphen in a short contents title, `\mbox`,
  a rewording the author approves).
- **Long typewriter identifiers** (file names, function names, URLs in text) go in `\path{}` from
  the url package, allowed to break at any character with
  `\makeatletter\g@addto@macro\UrlBreaks{\UrlOrds}\makeatother` in the preamble. A custom
  `\code{}` macro cannot break and left overfull lines in a merged supplement. In captions and
  other moving arguments write `\protect\path{...}`. Overfull boxes in boxes and tables usually need ragged right
  inside the box, `\emergencystretch`, or a TikZ node marked `overlay`.
- A gate whose tool is missing prints "not checked". Report it as not checked, never as passed.

## 3. Rendering pages to look at them

**Verify every preamble or layout change on a rendered page, not on the log.** Logs cannot see
wrapped running heads, a box 3.9 mm short of the margin, a swallowed space after a unit macro, a
contents line without leader dots, or a figure past the conclusions.

```bash
python3 scripts/render_pages.py build/main.pdf png 7 xii 12-14            # by printed label or number, 150 dpi
python3 scripts/render_pages.py build/main.pdf png 4 --clip 0 0 .5 .3 --dpi 300   # zoom into a region
python3 scripts/render_pages.py build/main.pdf png --sheet                # contact sheets, 45 dpi
python3 scripts/render_pages.py build/main.pdf --figs                     # Figure/Table number -> page
```

Then open the PNG and look. Without PyMuPDF: `pdftoppm -r 150 -f N -l N -png main.pdf pg`;
zoom with `pdftoppm -r 300 -x 0 -y 0 -W 500 -H 150 -png`.

- For a preamble change, compile a probe first: the first lines of the main file up to
  `\begin{document}`, a sample of each box, heading and float, then render and look. Prototype
  styles there before touching the real document.
- After each major change, look at the pages that carry the argument: title page, contents,
  summary or abstract, each chapter or section opening, every page whose floats moved.
- Check every wrapfigure: one reserved 17 lines while its caption needed 18 and the last line
  printed over the body text (`[17]` became `[19]`).
- To find a page: read `\newlabel{fig:x}` in the `.aux`, or loop
  `pdftotext -f $p -l $p main.pdf - | head -2`.

## 4. The whole-document visual pass

Before a hand-over of a long document:

1. Contact sheets of all pages at 45 dpi; zoom to 80 to 600 dpi where a sheet shows a defect.
2. `pdftotext -bbox` word positions for overflow, margins and label sizes;
   `scripts/locate_text.py main.pdf --fill` for pages that end early (under 80 % full) and
   `--runts` for one-word last lines.
3. Build log review: overfull, "??", raw LaTeX in the text, broken glyphs, "Float too large".
4. Report as `PDF page | problem | suggested fix (source file:line)`, ordered by importance,
   grouped Global, Front matter, Figures, Page layout. Read-only: the pass reports, one writer
   fixes.

Things this pass caught that no gate did: wrapped running heads, misaligned boxes, swallowed
spaces after a unit macro, hidden text layers, contents lines without leaders, abbreviation
columns starting at different heights, floats past conclusions, tables too tall, a symbol in a
caption that differs from the equation, stray crop marks, figure labels of 2 to 4 pt.

## 5. Fonts and hidden text in figures

- **Every font embedded.** `pdffonts main.pdf | awk 'NR>2 && $(NF-4)=="no"'` lists the others;
  Type 3 fonts are bitmaps, usually from a figure. Plotting libraries often name Helvetica without
  embedding it: `python3 scripts/embed_base14.py fig.pdf fig_embedded.pdf` adds the
  metric-compatible URW clone with unchanged glyph positions. Compare renders at 300 dpi before
  replacing the figure (in the test run, 0.07 % of the rendered bytes differed, from the clone's
  glyph shapes).
- **Scrub what a figure hides.** A white box painted over a title hides it from the eye, not from
  pdftotext, similarity checkers or screen readers; an external audit called hidden text in
  cropped figures a submission blocker.
  `python3 scripts/scan_figures.py figures/ --terms "old method name" "Under review"` searches
  every figure's text layer and font list (skipping a `_blocked/` quarantine folder).
- Remove hidden text by cropping to the visible area with text outside the crop redacted (a
  margin of 8 pt; a 1 pt margin deleted three visible edge labels), by deleting text blocks whose
  removal changes zero rendered pixels, or by converting text to outlines. Pixel-compare every
  figure against a backup at 300 dpi afterwards and look at the diff regions.
- Size figures for print: design width equals final width (`.98\linewidth`), smallest text at
  least 4 pt at print size (14 pt on posters), rasters about 450 dpi at print size, no label cut
  by a crop ("you cut the gene names!"). Keep a figure map: source, printed size, smallest text,
  raster dpi.

## 6. Print copy and color-page count

```bash
python3 scripts/build_latex.py main.tex --variant print_colors.tex      # -> build/main_print.pdf
python3 scripts/count_color_pages.py build/main_print.pdf               # 60 dpi
```

- `print_colors.tex` maps accent and link colors to black, box tints to 95 % gray, and sets
  hyperref links black; figures keep their colors. A color that must survive (a ranked results
  table) is declared with `\providecolor` and left out of the file.
- The counter renders each page; a pixel is chromatic when max minus min channel exceeds 28/255,
  a page is color when more than 12 pixels are. Cross-check: every color page has a figure or
  the kept table, the front matter is black and white. Report "N color, M black-and-white" with
  the printed page numbers. In the test run the book profile went from 6 color pages to 0.

## 7. Size limits, previews and the text-only copy

- Keep the full-quality master untouched; make separate copies for limits.
- Upload limit: `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/printer -o out.pdf in.pdf`, or resample
  rasters to 450 dpi at print size (118 MB to 60 MB with "no visible change").
- Phone preview under a messaging cap: PyMuPDF
  `doc.rewrite_images(dpi_threshold=130, dpi_target=110, quality=70)` then
  `doc.save(out, garbage=3, deflate=True)`; do not pass `clean=True` (it broke a Pattern
  resource). Split by chapter from the outline when one file is still too large.
- Similarity-check copy (text only): a main file that starts with
  `\PassOptionsToPackage{draft}{graphicx}` and inputs the real one, built two passes in a scratch
  folder with the `.aux .bbl .toc .lof .lot` of the full build copied in (about 1 MB against
  100 MB).

## 8. What to say at hand-over

One state line from the gate, then what was looked at and what was not:

> 0 LaTeX errors, 0 undefined references or citations, 0 overfull boxes, every font embedded,
> [N] pages, main text ends on page [P], [S] MB. Looked at: [pages]. Not checked: [what, and why].

- Recount any number before writing it into a README or report (one count was wrong once).
- If asked for the PDF in the middle of a check loop, send the current build labeled "not final".
