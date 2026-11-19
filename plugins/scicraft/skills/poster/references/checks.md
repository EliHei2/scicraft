# Checks: gates by script, render and look, readers, printer

All commands run in the poster folder with the scripts copied to `tools/`. `make check` runs gates 2 to 5;
`make words` runs gate 6. Every script answers `--help`, prints what it checked and exits 1 on a finding.

## Gate 1. The build log

```bash
make 2>&1 | grep -E "^!|Output written"
grep -E "^! |Warning: (Reference|Citation).*undefined|Rerun" build/poster_design.log
```

XeLaTeX can exit 0 with a broken page. Read the log; both passes must run (`remember picture` places everything
on the second).

## Gate 2. Boxes: overlaps, crowding, margins

```bash
python3 -I tools/box_check.py build/poster_design.log --gap 0.2
```

Reads the `BOX name x0 y0 x1 y1` lines the template writes and reports every pair that intersects (OVERLAP) or
sits closer than 0.2 cm (crowded), and every box outside the margins (3 cm sides, 2 cm top, 1.25 cm bottom;
`--margins` changes them). `--allow a/b` accepts a pair that touches on purpose. On the poster this came from:
36 boxes, 0 findings. A node not named in the `\foreach` list is not checked.

## Gate 3. Words: text over text, size at print, page size

```bash
python3 -I tools/layout_check.py build/poster_design.pdf --scale 0.841 --minpt 14 --dpi 20 \
  --boxes build/poster_design.log --figure-boxes logo,sph,f1,f2,fa,g1,g2,t6,t9 --out build/poster
```

- **text/text**: word boxes of different lines that intersect, after trimming the ascender and descender
  padding. Brace glyphs that sit on their own labels are skipped.
- **size**: words whose estimated printed size is under `--minpt`; tokens of four characters or fewer
  (sub- and superscripts) may go down to 0.7 x minpt. The estimate is word-box height / 1.175 for Helvetica Neue;
  with the template's fallback face (Latin Modern Sans) pass `--h-per-pt 1.0`, measured on a 46 pt section title,
  or every word reads as too small.
- **page size** with `--size WxH` in cm: a page larger than declared means something is drawn outside the box.
- **text/graphics** with `--graphics NOTEXT.pdf`: words crossing strokes in a text-free build. The template does
  not build that variant; the test was used on standalone figures.
- `--out` writes `build/poster_marked.png` with every finding outlined.

Findings inside the named figure boxes are listed under "in figure, look at it" and do not fail the run. On the
poster this came from, the poster's own text gave 0 findings at 14 pt printed (its smallest text, the references,
prints at 15.1 pt), and 48 labels inside the paper's figures printed at 11 to 13 pt. Those were the paper's own
labels at the paper's proportions, kept in the camera-ready file; say in the report that they are under 14 pt. The
Makefile of that poster ran this check on the design PDF at `--minpt 14` (design pt, so 11.8 pt printed) and
without failing the build; `--scale 0.841` now makes the floor a printed size.

## Gate 4. Line breaks

```bash
python3 -I tools/line_breaks.py build/poster_design.pdf --scale 0.841 \
  --boxes build/poster_design.log --figure-boxes logo,sph,f1,f2,fa,g1,g2,t6,t9 --dump --list-hyphens
```

Reports a paragraph whose last line holds one word ("no runts") and a hyphenated line end in type of 30 pt printed
or more ("no hyphenated bold titles"). `--dump` prints the last line of every paragraph: read them once. poppler
decides what a paragraph is, so read a finding before changing the source. On the template with placeholder text
it caught one real runt in a caption, fixed by a change of wording in the placeholder.

## Gate 5. The print file

```bash
python3 -I tools/pdf_gate.py poster.pdf --size 841x1189 --max-mb 50 --forbid "old method name,working title,[superseded number]"
```

- one page, 841 x 1189 mm within 1 mm;
- every font embedded (`pdffonts`, emb column);
- file size under the print shop's limit (ask; 50 MB is only the default);
- none of the forbidden strings in the text layer: retired names, superseded numbers, names that must not appear.
  `pdftotext` reads the text inside placed figure PDFs too, including text hidden under paint or outside a crop.

On the poster this came from: 1 page, 841.0 x 1189.0 mm, 25 fonts all embedded, 31.3 MB.

Fixes:

- **Unembedded Helvetica in a matplotlib PDF** (written with `pdf.use14corefonts`):
  `python3 tools/embed_base14.py fig.pdf fig_emb.pdf`, then `pdffonts fig_emb.pdf` and compare renders. It embeds
  the URW clone with the base-14 widths, so every glyph stays where viewers already put it. Needs PyMuPDF and the
  URW fonts of TeX Live (`kpsewhich uhvr8a.pfb`).
- **Hidden text in a figure** (a superseded label under a white box, a retired name): fix the source figure, or
  convert the figure's text to outlines so nothing can be copied out. One way:
  `gs -dNoOutputFonts -sDEVICE=pdfwrite -o fig_outlined.pdf fig.pdf` (Suggested, not yet tested in real work;
  Ghostscript was not available where this skill was built). Outlined text drops out of the own-words and size
  checks, so outline only figures, never the poster's own text.
- **File too large**: images in the figures are the usual cause. Resample rasters to about 450 dpi at their
  printed size (a book went from 118 to 60 MB with no visible change), or
  `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/printer -o small.pdf poster.pdf` (not run here). Never shrink the page.

## Gate 6. Own words

```bash
python3 -I tools/own_words_poster.py build/poster_design.pdf ../paper/tex \
  --boxes build/poster_design.log --figure-boxes logo,sph,defs,f1,f2,fa,g1,g2,n6,t6,t9 --allow departures.txt
```

Every sentence of five or more words outside the figures is looked up in the paper's source (TeX markup taken off,
British and American spellings folded, numbered citations removed). Passes at four pieces or fewer of one paragraph.
Lists departures from `departures.txt`; fails on anything else. `--unwrap rev,new` reads text inside the paper's
own marking macros.

## 7. Render and look

```bash
make preview                                                     # whole page, 30 dpi
pdftoppm -png -r 100 -x 0 -y 0 -W 3300 -H 1600 poster.pdf build/band1   # a band at 100 dpi (pixels at that dpi)
```

Look at the whole page, then each band, for what no script sees:

- white holes beside figures; the two bottom columns ending level;
- a label cut by a crop; a figure enlarged past its raster resolution;
- every marker, line style and color in a figure named in its caption or key;
- the results table's shading overhang at its right edge;
- a figure that makes no point for the section it sits in;
- the title's line break and the affiliations line.

## 8. Readers

When there is time, one fresh reader at a time checks the rendered poster and its text against the paper:

- the brief names what is approved and fixed (the look, the order, the figures) and asks for defects only, each
  with its place on the page (band, piece) and the fix;
- for a wording defect the reader quotes the paper's sentence that should replace it, or writes "needs the
  author's line"; readers never write new prose for the poster;
- a factual correction is stated as what is true, in positive form;
- the reader checks every number against the paper's primary tables, the paper against itself (counts against
  figures, captions against what figures draw), and the references against the bibliography;
- fix, rebuild, start a fresh reader, until a round finds nothing.

One writer applies the fixes. A fix that would change the author's words goes to the author instead. Errors found
in the paper while deriving the poster go into an errata list for the paper.

## 9. The report

- `poster.pdf` with its path and size, and the preview;
- the gate line, with the numbers of the run;
- what was checked only by eye, and what was not checked (figure labels under 14 pt, outlines not verified);
- every departure from the paper's wording;
- what the author must supply or confirm: byline, affiliations, logo, release line, contacts, the print shop's
  limits.
