# Reusing published figures

A book built from papers already has its figures. The agent's job is to crop, re-letter, place and caption
them, never to draw. This was stated at least eight times, the last as "please under no circumstance make
diagrams/figures here on your own, everything else exists and you are not able to make proper figures". The one
praise the figure work got ("you did a great job in figures") came after panels were cropped from the papers at
the exact print width with their letters masked.

Contents: 1 what may be done to a figure, 2 the composer pipeline, 3 print size and legibility, 4 hidden content
and fonts, 5 captions and the source line, 6 credits in captions, 7 licenses and third-party figures, 8 slides,
posters and figures from other documents, 9 the figure audit.

## 1. What may be done to a figure

| Allowed | Never |
|---|---|
| crop whole panels from the published PDF, the extended data or the supplement | TikZ, re-plotting, redrawing, a "cleaner" version |
| mask the source's panel letters and set new bold a, b, c | re-setting in-image labels, adding elements to the artwork |
| place panels side by side or stacked at one scale | rotating a figure or using a landscape page |
| resample embedded rasters to print resolution | cutting axis text, gene or feature names, keys or scale bars |
| remove logos, slide titles and footers from a slide figure | composing named panels from different papers into one new figure |
| drop a float when no figure of the author's fits, and say so | an agent-made figure "for now" |

- **When no figure fits a slot, drop the float and say so** ("none of your figures shows it, so that float is now
  left out"), or offer the author's closest figure. When two of the author's panels together cover a slot, place
  them side by side with the source line naming both.
- **Every subagent brief that touches figures carries the rule word for word:** "Figures may only be cropped,
  masked, arranged, resized, moved or split, never re-made." A subagent's matplotlib re-plot entered the book
  because its brief lacked the line.
- **Look for unused figures before saying none exists.** The papers' extended data and supplements, the author's
  poster and talk figures, and composed figures that no chapter includes. "You have a lot of figures that you
  don't use" was a complaint; every concept the Introduction rests on needs a figure.
- **To fill an empty concept slot, brief one adversarial chooser agent that prototypes outside the repository.**
  It returns the source PDF and page, the embedded image's xref, clip boxes in pixels, a prototype render, and
  each rejected candidate with its reason (license not verified, artwork the author already rejected). It also
  checks that the chosen picture appears nowhere else in the book. The rules of section 7 apply to its choice.
- **Panel by panel, without over-paneling.** Multi-panel figures were rebuilt panel by panel with new letters
  and a literal name per panel in the caption ("**a**, Challenges in ..."), never "top left". Later: "please
  really don't overpanel the figures". Crop the panels a paragraph discusses; keep the rest of the figure whole or
  out.
- **Pilot one figure, get it approved, then scale** to the rest (23 figures in one round, page-neutral). Once the
  text cites letters, the figure must deliver exactly those letters.

## 2. The composer pipeline

`scripts/compose_crops.py`, `scripts/gridprev.py`, `scripts/strip_invisible.py` and `assets/spec_template.py`. They
need PyMuPDF, Pillow and numpy.

1. **Stage the sources** in a folder that is not committed (`figsrc/src/`), with a script that recreates it
   (`stage_sources.sh`: `cp` from the paper repositories, `unzip` of a manuscript `.docx` for its embedded
   images, `pdfseparate -f N -l N` for one page of a PDF). Name each staged file after its paper, figure and
   version. Exclude archived figures, scratch files and anything an agent made.
2. **Choose vector over raster only when the vector equals the latest artwork.** Score a vector render against
   the latest manuscript's raster by gray-level correlation and use the raster where they differ:
   ```bash
   python3 scripts/match_artwork.py incoming/ms_v4_fig3.png figsrc/src/paper_fig3.pdf figsrc/src/old_fig3.pdf
   ```
   It renders each candidate in gray at the raster's pixel size, resizes both to one thumbnail width and prints
   the correlation: above 0.95 means the same artwork; below it the vector is an older or a different version and
   the raster from the latest manuscript wins. When a figure and the text disagree, recompute the value from the
   records; the version the records support wins, the choice is written in the spec comment and listed in
   AUTHOR_DECISIONS.md.
3. **Read crop boxes off a grid:**
   ```bash
   python3 scripts/gridprev.py figsrc/src/paper_fig2.pdf grid/fig2.png --step 25
   python3 scripts/gridprev.py figsrc/src/paper_fig2.pdf grid/fig2_zoom.png --clip 20 30 120 80 --step 5
   ```
   Coordinates are source units (PDF points or pixels), origin top-left, the units the spec uses.
4. **Declare each figure in a spec** (copy `assets/spec_template.py`): `Panel(src, (x0, y0, x1, y1),
   autoletters=True)` finds and masks bold single letters in vector sources; `masks=[(x0, y0, x1, y1)]` paints out
   letters that are part of a raster. `compose(name, rows, letters=True)` sets new letters in an embedded bold sans
   with space reserved above each panel. Helpers: `same_scale(*panels)` keeps the source's relative sizes in a
   row, `fit_row(items)` sets a row with a stacked column at one scale, `redacted(src, name, rects)` removes a
   neighboring panel's letter or frame that reaches into a crop instead of painting over it.
5. **Compose:**
   ```bash
   python3 scripts/compose_crops.py --spec figsrc/spec.py --out figures/ --measure 150 --report reports/figure_audit.json
   ```
   Each figure is built at the exact text measure (148 mm on a 150 mm measure in the source book; widening the
   measure from a sidenote layout raised paper figures from 70 % to 83 % of their journal width). Embedded rasters
   above 1.35 x 450 dpi are resampled to 450 dpi at print size (JPEG when under 60 % of the lossless size), which
   took the book PDF down from about 60 MB. The audit line per figure gives scale, smallest and median printed
   font size, effective raster dpi and letters masked; a preview PNG goes to `figures/_preview/`.
6. **Look at every preview.** Check each crop edge for split glyphs and each mask for text it covers; tile
   before/after crops when masks were placed by hand.
7. **Keep a map** from each figure label to its source paper, figure, panels and page (`FIGURE_MAP` or a gallery
   file with checksums). It is how the caption's source line and the Disclosures page are checked.

## 3. Print size and legibility

- **Smallest printed text at least 5.5 pt, 6 pt preferred.** Rebuilt from vector sources this way: 4.1 to 5.6 pt,
  4.6 to 6.0 pt, 4.0 to 5.7 pt. A schematic that printed at 2 to 3 pt was split in two. A reproduced overview
  figure at 4 to 4.5 pt was accepted once, flagged to the author. `compose_crops.py --min-font 5.5 --strict` fails on it.
- **Never cap a row's height so far that text shrinks.** Figures capped by `height_mm` printed 97 to 120 mm wide on
  a 150 mm measure with text at 2.2 to 4.4 pt and had to be recomposed at full width. A table under
  `\resizebox{0.78}` printed at 4.7 pt.
- **Never rotate.** "please never rotate a figure. please never!" overrode the author's own landscape request
  three hours earlier. Use an upright float page `[p]` up to 150 x 215 mm; a figure that needs more is split into
  `_a` and `_b` floats before its text goes below about 5.5 pt.
- **Small figures inline:** `wrapfigure{R}{50mm}` (capital R lets it float). Check the reserved line count: 16
  lines reserved for a figure that needed 17 printed text over the caption.
- **A raster shown larger than it printed in its paper looks blurry.** `compose_crops.py` warns when it happens; prefer
  the publisher's full-resolution figure (a 685 px slide copy was too blurry).

## 4. Hidden content and fonts

A similarity checker reads text a reader cannot see. An external audit called hidden text in figures a
blocker for delivery: about 150 words of invisible manuscript text in one figure, a conference's running heads
inside cropped panels, an image "removed" by clipping that was still embedded, institute logos outside the crop.

- **Text outside the crop is redacted** by `compose_crops.py` (8 pt margin; a 1 pt margin deleted three visible edge
  labels, caught by the pixel diff).
- **Invisible text inside the crop is removed** by `strip_invisible.py`, which keeps a change only if the page
  renders identically, verified at 150 and 400 dpi. `compose_crops.py` runs it on every save.
- **Check:** `pdftotext figures/name.pdf -` prints only the labels a reader sees; `pdfimages -list` shows no image
  the crop hides; after the build, `pdftotext book.pdf - | grep -i "<journal name>\|conference paper"` finds
  nothing but the author's own sentences.
- **Every font embedded:** `pdffonts book.pdf | awk 'NR>2 && $(NF-4)=="no"'` prints nothing. Figures that use
  bare base-14 Helvetica get the metric clone with `scripts/embed_base14.py IN.pdf OUT.pdf` (the same file as in
  the sibling skill `latex-typesetting`). Then render IN and OUT at 300 dpi and compare them; switch sources only
  when only glyph outlines changed.
- **Back up all figures before a cleaning pass, recompose all, and pixel-compare each against the backup at 300
  dpi.** Crop the diff regions to PNG and look at them.

## 5. Captions and the source line

A caption has a bold claim title, the panel key in the book's own letters, ONE plain source line, and at most a
per-panel credit.

| The figure is | Source line |
|---|---|
| published, changed (cropped, re-lettered, recomposed) | "Adapted from Fig. 2b of \citet{key}." |
| published, shown whole and unchanged | "Taken from Fig. 2 of \citet{key}." |
| the author's unpublished manuscript | "Adapted from the [topic] manuscript under revision at \emph{[Journal]}." No `\cite`, no figure numbers, no author list |
| the author's own unpublished schematic | no source line |
| AI-generated (rare; the author said so) | stated in the caption, the Disclosures page and the signed AI statement alike |

- **"Reproduced" is banned.** Choose the verb by checking how the exemplar books of the publisher write it (search
  their PDFs for "adapted from", "reproduced from", "taken from").
- **Never mention slides, decks, posters, presentations, drafts, a "working figure", a first submission or
  licenses in a caption.** "No one knows about the deck ... really not acceptable." A regex scan removed 38 such
  phrases. One license sentence may stand on the Disclosures page. `book_checks.py` flags them.
- **The panel key uses the book's letters:** "**a**, Name. Description." The text cites "Fig. 4.1b".
- **Paraphrase published legends.** No run over about 8 words from a published legend (agents measured at most 7
  consecutive shared words). Captions of the author's own unpublished figures stay close to the author's legends.
- **Check every panel description against the rendered figure**, colors included.
- **A caption is written with the prose.** Writing a caption early caught a figure that did not show what its
  slot claimed.

## 6. Credits in captions

- **Credit a person only for a specific panel made by their own analysis or drawing, and name the panel:**
  "Schematic by A.", "Ablations (c) by B." No whole-figure credits (sample preparation, data generation,
  "by me", "Analysis by me"). Data producers are credited through the data source citation; this is how the
  publisher's "data-producer statement in the legend" rule was met. People go to a footnote or the Disclosures page,
  following the local exemplar. Then fix any front-matter sentence the change
  makes false ("Each legend names the people who produced the data").
- **Verify figure and code credits from history before writing them:**
  `git log --format='%h %an %ad %s' --date=short -- <file>` in the figure and method repositories. Unconfirmed
  credits go to AUTHOR_DECISIONS.md as "please confirm".

## 7. Licenses and third-party figures

Every figure taken from someone else needs a traceable, citable source and a compatible license, or it goes
("for all figures taken from somewhere else you need to find sth and cite it. otherwise we can't use them!").

| License of the source | What may be done |
|---|---|
| CC BY | adapt (crop, re-letter), state the change ("Adapted from") |
| CC BY-NC-ND or other no-derivatives | reproduce whole and unchanged ("Taken from"), license named on the Disclosures page; a crop that cut a column was replaced by the publisher's full figure |
| no open license | scientific quotation at most, flagged to the author for permission before online publication |
| untraceable (a blog image, a photo with no source) | removed |

- Look up license and metadata by DOI (Europe PMC REST, Crossref).
- A corporate announcement graphic with no open license was replaced by the same content in the paper's CC BY
  figure.
- List every third-party figure on the Disclosures page. Open image rights go in AUTHOR_DECISIONS.md.
- **Prefer textbook-grade conceptual figures from top reviews** for the Introduction, cited.

## 8. Slides, posters and other documents

1. `pdfseparate -f 8 -l 8 deck.pdf slide8.pdf`; `pdfimages -list slide8.pdf` tells vector from raster and finds
   the embedded original, which is usually sharper than the slide.
2. Crop away the slide title, footer, logo and annotation text; keep only the figure.
3. Add a spec function, compose, render a check.
4. For raster masks, locate the source panel letters by pixel darkness after drawing a grid on the image.
5. When a crop cuts a label, read the band above it with PyMuPDF text blocks, extend the crop, and mask the source
   letter.
6. The caption names the published source, never the slide.

**Lifting a panel out of a report PDF with PyMuPDF**, when neighboring artwork reaches into the crop: read the
vector paths with `page.get_drawings()` first, so you know which lines and fills sit where. Remove a neighbor with
one full-page redaction, `add_redact_annot(rect, fill=False)` on each area, then
`apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
text=fitz.PDF_REDACT_TEXT_REMOVE)`. This is the default of `compose_crops.py`'s `redacted()`. The `REMOVE_IF_TOUCHED`
mode also deletes crop boxes, axes and arrows that only touch the area. Axes, crop boxes and scale bars can be
recovered from the drawing geometry (filled rectangles, thin quads, zero-height lines); test a zero-height
rectangle at its midpoint, because it never `intersects()` anything. The technique was used in a figure campaign of
another project, not in the source book.

## 9. The figure audit

An adversarial figure audit (one agent per chapter group, read-only) compares each book figure against its
source and legend. Verdicts OK, FIX or DECIDE (21 / 29 / 5 in one round). It catches: published letters still
showing next to the new ones, mask hairlines visible at 600 dpi, figure and text numbers that disagree, a crop that
cut the scale bar, the wrong panel-key style, a caption naming methods without citing them, a generated-looking
graphic credited to the author. It returns `spec_fixes.py` (re-crops) and caption edits as exact-match proposals.
After applying, check that every fix landed (diff the spec functions with `ast` and `difflib`), recompose, and
re-read every changed preview. Figure-file fixes go in at once; caption edits wait until line editors on the same
files have landed.
